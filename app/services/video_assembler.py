"""Video Assembler Service

FFmpeg-based video assembly for property videos.
Combines avatar clips, property footage, and voiceover into final MP4.
"""
import os
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import httpx
import asyncio
import subprocess
import json

from app.config import settings
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class VideoAssemblerService:
    """
    Assemble final property video from components.

    Pipeline:
    1. Download all video components
    2. Concatenate videos (intro + property clips + outro)
    3. Add/mix voiceover audio
    4. Generate thumbnail
    5. Upload to S3
    6. Cleanup temp files
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "video_assembly"
        self.temp_dir.mkdir(exist_ok=True)
        self.s3_bucket = settings.aws_s3_bucket

    async def assemble_property_video(
        self,
        intro_video_url: str,
        property_clips: List[str],
        outro_video_url: str,
        voiceover_url: str,
        output_filename: str,
        add_captions: bool = False
    ) -> Dict:
        """
        Assemble final property video from all components.

        Args:
            intro_video_url: Agent intro video URL (HeyGen)
            property_clips: List of property footage URLs (PixVerse)
            outro_video_url: Call-to-action video URL (HeyGen)
            voiceover_url: Voiceover audio URL (ElevenLabs)
            output_filename: Output filename
            add_captions: Add burned-in captions (future feature)

        Returns:
            {
                "final_video_url": "https://s3...",
                "thumbnail_url": "https://s3...",
                "duration": 58.5,
                "file_size": 15728640,
                "resolution": "1080p"
            }

        Raises:
            Exception: If assembly fails
        """
        logger.info(f"Assembling property video: {output_filename}")

        try:
            # Step 1: Download all components
            logger.info("Downloading video components...")
            intro_path = await self._download_video(intro_video_url, "intro.mp4")
            clip_paths = [
                await self._download_video(url, f"clip_{i}.mp4")
                for i, url in enumerate(property_clips)
            ]
            outro_path = await self._download_video(outro_video_url, "outro.mp4")
            voiceover_path = await self._download_video(voiceover_url, "voiceover.mp3")

            # Step 2: Create file list for concatenation
            logger.info("Preparing video concatenation...")
            concat_file = self.temp_dir / "concat_list.txt"
            with open(concat_file, "w") as f:
                f.write(f"file '{intro_path.absolute()}'\n")
                for clip_path in clip_paths:
                    f.write(f"file '{clip_path.absolute()}'\n")
                f.write(f"file '{outro_path.absolute()}'\n")

            # Step 3: Concatenate videos
            logger.info("Concatenating video clips...")
            concat_output = self.temp_dir / f"concat_{output_filename}"
            await self._concatenate_videos(concat_file, concat_output)

            # Step 4: Add voiceover
            logger.info("Adding voiceover audio...")
            final_output = self.temp_dir / f"final_{output_filename}"
            await self._add_audio_track(concat_output, voiceover_path, final_output)

            # Step 5: Get video metadata
            metadata = await self._get_video_metadata(final_output)

            # Step 6: Generate thumbnail
            logger.info("Generating thumbnail...")
            thumbnail_filename = output_filename.replace(".mp4", "_thumb.jpg")
            thumbnail_path = self.temp_dir / thumbnail_filename
            thumbnail_url = await self._generate_thumbnail(final_output, thumbnail_path)

            # Step 7: Upload to S3
            logger.info("Uploading to S3...")
            s3_url = await self._upload_to_s3(final_output, output_filename)

            # Step 8: Cleanup
            logger.info("Cleaning up temp files...")
            paths_to_cleanup = [intro_path, *clip_paths, outro_path, voiceover_path, concat_output, final_output, thumbnail_path]
            for path in paths_to_cleanup:
                path.unlink(missing_ok=True)
            concat_file.unlink(missing_ok=True)

            logger.info(f"Video assembly complete: {s3_url}")

            return {
                "final_video_url": s3_url,
                "thumbnail_url": thumbnail_url,
                "duration": metadata.get("duration", 0),
                "file_size": metadata.get("size", 0),
                "resolution": metadata.get("resolution", "1080p")
            }

        except Exception as e:
            logger.error(f"Video assembly failed: {str(e)}")
            raise

    async def _download_video(self, url: str, filename: str) -> Path:
        """Download video/audio file to temp directory."""
        path = self.temp_dir / filename

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            path.write_bytes(response.content)

        logger.debug(f"Downloaded {filename}: {path.stat().st_size} bytes")
        return path

    async def _concatenate_videos(
        self,
        concat_file: Path,
        output_path: Path
    ):
        """Concatenate videos using FFmpeg."""
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-y",  # Overwrite output
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"FFmpeg concatenation error: {stderr.decode()}")
            raise Exception("Video concatenation failed")

    async def _add_audio_track(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path
    ):
        """Add/mix audio track to video using FFmpeg."""
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",  # Copy video stream without re-encoding
            "-c:a", "aac",  # Encode audio as AAC
            "-shortest",  # Use shortest duration
            "-y",
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"FFmpeg audio mixing error: {stderr.decode()}")
            raise Exception("Audio mixing failed")

    async def _get_video_metadata(self, video_path: Path) -> Dict:
        """Get video metadata using FFprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-show_entries", "format=duration,size",
            "-of", "json",
            str(video_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.warning(f"FFprobe failed, using defaults: {stderr.decode()}")
            return {"duration": 60, "size": video_path.stat().st_size, "resolution": "1080p"}

        data = json.loads(stdout.decode())
        stream = data.get("streams", [{}])[0]
        format_info = data.get("format", {})

        width = stream.get("width", 1920)
        height = stream.get("height", 1080)
        duration = float(format_info.get("duration", 60))
        size = int(format_info.get("size", video_path.stat().st_size))

        resolution = "1080p"
        if height >= 2160:
            resolution = "4k"
        elif height >= 1440:
            resolution = "1440p"
        elif height >= 1080:
            resolution = "1080p"
        elif height >= 720:
            resolution = "720p"

        return {
            "duration": duration,
            "size": size,
            "resolution": resolution
        }

    async def _generate_thumbnail(
        self,
        video_path: Path,
        output_path: Path
    ) -> str:
        """Generate thumbnail from video at 30% mark."""
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-ss", "00:00:10",  # Thumbnail at 10 seconds
            "-vframes", "1",
            "-vf", "scale=320:-1",  # Width 320, auto height
            "-y",
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.warning(f"Thumbnail generation failed: {stderr.decode()}")
            return ""

        # Upload thumbnail to S3
        thumbnail_url = await self._upload_to_s3(output_path, output_path.name)
        return thumbnail_url

    async def _upload_to_s3(self, file_path: Path, filename: str) -> str:
        """Upload file to S3 and return presigned URL."""
        try:
            import boto3

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            s3_key = f"property-videos/{filename}"
            s3.upload_file(str(file_path), self.s3_bucket, s3_key)

            # Generate presigned URL (valid for 1 year)
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=31536000  # 1 year
            )

            return url

        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            raise

    async def estimate_assembly_cost(
        self,
        num_clips: int,
        duration_seconds: int
    ) -> float:
        """
        Estimate cost for video assembly.

        Args:
            num_clips: Number of property clips
            duration_seconds: Final video duration

        Returns:
            Estimated cost in USD
        """
        # FFmpeg processing = free (self-hosted)
        # S3 storage = ~$0.023/GB/month
        # A 60-second 1080p video ≈ 50-100MB
        avg_size_mb = duration_seconds * 1.5  # Estimate
        storage_cost_per_month = (avg_size_mb / 1024) * 0.023

        # S3 download cost = ~$0.0007/GB (first 10TB free for most)
        download_cost = (avg_size_mb / 1024) * 0.0007

        # Total negligible, but track for transparency
        return storage_cost_per_month + download_cost


# ============================================================================
# Helper Functions
# ============================================================================

async def assemble_property_video(
    intro_url: str,
    clip_urls: List[str],
    outro_url: str,
    voiceover_url: str,
    output_filename: str
) -> Dict:
    """
    Convenience function to assemble property video.

    Returns final video URL and metadata.
    """
    assembler = VideoAssemblerService()
    return await assembler.assemble_property_video(
        intro_video_url=intro_url,
        property_clips=clip_urls,
        outro_video_url=outro_url,
        voiceover_url=voiceover_url,
        output_filename=output_filename
    )
