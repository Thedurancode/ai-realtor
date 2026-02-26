"""Remotion async render service with Redis queue."""
import os
import json
import asyncio
import subprocess
import tempfile
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from redis import Redis
import httpx

from app.models.render_job import RenderJob
from app.config import settings


# Redis connection
redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=False  # Keep bytes for binary data
)

# S3 client for video storage
try:
    import boto3
    from botocore.exceptions import ClientError

    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    s3_client = None

S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'ai-realtor-renders')


class RemotionService:
    """Service for managing Remotion render jobs."""

    # Queue name
    QUEUE_NAME = 'render-jobs'

    @staticmethod
    async def create_render_job(
        db: Session,
        agent_id: int,
        template_id: str,
        composition_id: str,
        input_props: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> RenderJob:
        """Create a new render job and enqueue it."""
        # Create DB record
        job = RenderJob(
            agent_id=agent_id,
            template_id=template_id,
            composition_id=composition_id,
            input_props=input_props,
            webhook_url=webhook_url,
            status='queued'
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Enqueue in Redis (LPUSH to the queue)
        queue_item = json.dumps({
            'render_id': job.id,
            'agent_id': agent_id,
            'template_id': template_id,
            'composition_id': composition_id,
            'input_props': input_props
        })
        redis_client.lpush(RemotionService.QUEUE_NAME, queue_item)

        return job

    @staticmethod
    def get_render_job(db: Session, render_id: str) -> Optional[RenderJob]:
        """Get a render job by ID."""
        return db.query(RenderJob).filter(RenderJob.id == render_id).first()

    @staticmethod
    def list_render_jobs(db: Session, agent_id: int) -> list[RenderJob]:
        """List all render jobs for an agent."""
        return db.query(RenderJob).filter(RenderJob.agent_id == agent_id).order_by(RenderJob.created_at.desc()).all()

    @staticmethod
    async def cancel_render_job(db: Session, render_id: str) -> Optional[RenderJob]:
        """Cancel a render job."""
        job = db.query(RenderJob).filter(RenderJob.id == render_id).first()
        if not job:
            return None

        # Set canceled flag (worker will check this)
        job.status = 'canceled'
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)

        return job

    @staticmethod
    async def process_render_job(db: Session):
        """Worker process to handle render jobs from the queue."""
        print("🎬 Worker ready to process jobs...")

        while True:
            try:
                # Blocking pop from queue (timeout 1 second)
                result = redis_client.brpop(RemotionService.QUEUE_NAME, timeout=1)

                if not result:
                    # No job available, continue loop
                    await asyncio.sleep(0.1)
                    continue

                # Parse job data
                queue_name, job_data = result
                job_data = json.loads(job_data)

                render_id = job_data['render_id']
                template_id = job_data['template_id']
                composition_id = job_data['composition_id']
                input_props = job_data['input_props']

                print(f"📼 Processing render job: {render_id}")

                # Get job from DB
                render_job = db.query(RenderJob).filter(RenderJob.id == render_id).first()
                if not render_job:
                    print(f"❌ Render job {render_id} not found in DB")
                    continue

                # Check if canceled
                db.refresh(render_job)
                if render_job.status == 'canceled':
                    print(f"⚠️  Render job {render_id} was canceled")
                    continue

                # Process the render
                await RemotionService._render_video(render_job, db, composition_id, input_props)

            except Exception as e:
                print(f"❌ Worker error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

    @staticmethod
    async def _render_video(render_job: RenderJob, db: Session, composition_id: str, input_props: Dict[str, Any]):
        """Render a video using Remotion CLI."""
        render_id = render_job.id

        try:
            # Update status to rendering
            render_job.status = 'rendering'
            render_job.started_at = datetime.utcnow()
            db.commit()

            # Create temp directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'output.mp4')
                props_path = os.path.join(temp_dir, 'props.json')

                # Write input props to file
                with open(props_path, 'w') as f:
                    json.dump(input_props, f)

                # Call Remotion render CLI
                remotion_project = os.path.join(os.path.dirname(__file__), '..', '..', 'remotion')
                cmd = [
                    'npx', 'remotion', 'render',
                    f'{remotion_project}/src/index.tsx',
                    composition_id,
                    output_path,
                    '--props', props_path,
                    '--jpeg-quality', '80',
                    '--overwrite'
                ]

                print(f"🎬 Starting render: {' '.join(cmd)}")

                # Start render process
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=remotion_project
                )

                # Monitor progress
                last_progress_update = asyncio.get_event_loop().time()

                while True:
                    # Check if job was canceled
                    db.refresh(render_job)
                    if render_job.status == 'canceled':
                        print(f"⚠️  Render {render_id} canceled during rendering")
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=5.0)
                        except asyncio.TimeoutError:
                            process.kill()
                        return

                    # Read line from stdout
                    line = await process.stdout.readline()
                    if not line:
                        break

                    # Try to parse progress
                    try:
                        output = line.decode().strip()
                        if output:
                            # Look for progress indicators in Remotion output
                            # Remotion outputs progress like: "Rendering frame 45/300 (15%)"
                            if "frame" in output.lower() and "/" in output:
                                parts = output.split("/")
                                if len(parts) >= 2:
                                    try:
                                        current_part = parts[-2].split()[-1]
                                        total_part = parts[-1].split()[0]
                                        render_job.current_frame = int(current_part)
                                        render_job.total_frames = int(total_part)
                                        render_job.progress = render_job.current_frame / render_job.total_frames

                                        # Throttle DB updates (max 2 per second)
                                        now = asyncio.get_event_loop().time()
                                        if now - last_progress_update > 0.5:
                                            db.commit()
                                            last_progress_update = now
                                    except (ValueError, IndexError):
                                        pass
                    except Exception:
                        pass

                # Wait for process to complete
                returncode = await process.wait()

                if returncode != 0:
                    stderr = await process.stderr.read()
                    error_msg = stderr.decode()
                    raise Exception(f"Remotion render failed with code {returncode}: {error_msg}")

                print(f"✅ Render {render_id} complete, uploading to S3...")

                # Upload to S3
                render_job.status = 'uploading'
                db.commit()

                if S3_AVAILABLE and s3_client:
                    s3_key = f"renders/{render_id}.mp4"
                    s3_client.upload_file(
                        output_path,
                        S3_BUCKET,
                        s3_key,
                        ExtraArgs={'ContentType': 'video/mp4'}
                    )

                    # Generate presigned URL (valid for 24 hours)
                    output_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': S3_BUCKET, 'Key': s3_key},
                        ExpiresIn=86400
                    )

                    render_job.output_url = output_url
                    render_job.output_bucket = S3_BUCKET
                    render_job.output_key = s3_key
                else:
                    # If S3 not available, store locally
                    render_job.output_url = f"file://{output_path}"

                # Update job as completed
                render_job.status = 'completed'
                render_job.progress = 1.0
                render_job.finished_at = datetime.utcnow()
                db.commit()

                print(f"✅ Render {render_id} complete!")

                # Send webhook if configured
                if render_job.webhook_url:
                    await RemotionService._send_webhook(render_job, db)

        except Exception as e:
            print(f"❌ Render {render_id} failed: {e}")
            import traceback
            traceback.print_exc()

            # Update job as failed
            render_job.status = 'failed'
            render_job.error_message = str(e)
            render_job.error_details = {'type': type(e).__name__}
            render_job.finished_at = datetime.utcnow()
            db.commit()

            # Send webhook if configured
            if render_job.webhook_url:
                await RemotionService._send_webhook(render_job, db)

    @staticmethod
    async def _send_webhook(render_job: RenderJob, db: Session):
        """Send webhook notification for completed render job."""
        payload = {
            'id': render_job.id,
            'status': render_job.status,
            'output_url': render_job.output_url,
            'error_message': render_job.error_message,
            'progress': render_job.progress,
            'created_at': render_job.created_at.isoformat() if render_job.created_at else None,
            'finished_at': render_job.finished_at.isoformat() if render_job.finished_at else None
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    render_job.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                if response.status_code == 200:
                    render_job.webhook_sent = 'sent'
                else:
                    render_job.webhook_sent = 'failed'
                    print(f"⚠️  Webhook failed with status {response.status_code}")
        except Exception as e:
            render_job.webhook_sent = 'failed'
            print(f"❌ Webhook error: {e}")

        db.commit()


def start_render_worker(db_session_factory):
    """Start the render worker process."""
    print("🎬 Starting Remotion render worker...")
    print(f"   Redis: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
    print(f"   Concurrency: {os.getenv('WORKER_CONCURRENCY', 1)}")
    print(f"   S3 Bucket: {S3_BUCKET}")
    print(f"   S3 Available: {S3_AVAILABLE}")
    print()

    # Create DB session
    db = db_session_factory()

    try:
        # Run the worker loop
        asyncio.run(RemotionService.process_render_job(db))
    except KeyboardInterrupt:
        print("\n⚠️  Worker stopped by user")
    except Exception as e:
        print(f"\n❌ Worker error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
