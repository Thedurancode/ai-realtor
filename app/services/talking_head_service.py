"""Talking Head Video Service

Orchestrates branded talking head video generation:
1. Create/reuse HeyGen avatar from agent headshot
2. Generate TTS audio via ElevenLabs with cloned voice
3. Upload audio to HeyGen, generate lip-synced talking head video
4. Create branded intro/outro frames via FFmpeg
5. Assemble final video: [intro] + [talking head] + [outro]
"""
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.database import SessionLocal
from app.utils.circuit_breaker import circuit_breakers
from app.models.agent_brand import AgentBrand
from app.models.talking_head_video import TalkingHeadVideo
from app.services.heygen_enhanced_service import HeyGenEnhancedService

logger = logging.getLogger(__name__)

TEMP_DIR = Path(tempfile.gettempdir()) / "talking_head"
TEMP_DIR.mkdir(exist_ok=True)

# Output directory for final videos
PROJECT_ROOT = Path(__file__).parent.parent.parent
VIDEO_DIR = PROJECT_ROOT / "videos" / "talking-heads"
VIDEO_DIR.mkdir(exist_ok=True, parents=True)


def _hex_to_rgb(hex_color: str) -> str:
    """Convert '#RRGGBB' to 'RRGGBB' for FFmpeg."""
    return hex_color.lstrip("#")


async def _run_ffmpeg(cmd: list[str], label: str = "ffmpeg"):
    """Run an FFmpeg command and raise on failure."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error = stderr.decode()[:500]
        logger.error(f"{label} failed: {error}")
        raise RuntimeError(f"{label} failed: {error}")


async def _download_file(url: str, dest: Path):
    """Download a URL to a local file."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


def _update_job(job_id: int, **kwargs):
    """Update a TalkingHeadVideo record."""
    db = SessionLocal()
    try:
        job = db.query(TalkingHeadVideo).filter(TalkingHeadVideo.id == job_id).first()
        if job:
            for k, v in kwargs.items():
                setattr(job, k, v)
            db.commit()
    finally:
        db.close()


async def _generate_elevenlabs_tts(script: str, voice_id: str, output_path: Path) -> Path:
    """
    Generate TTS audio via ElevenLabs API.

    Args:
        script: Text to speak.
        voice_id: ElevenLabs voice ID (cloned or preset).
        output_path: Where to save the .mp3 file.

    Returns:
        Path to the generated audio file.
    """
    breaker = circuit_breakers.get("elevenlabs")
    if not breaker.is_available():
        raise RuntimeError("ElevenLabs API temporarily unavailable (circuit open)")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        breaker.record_success()
    except Exception as e:
        breaker.record_failure()
        raise

    logger.info(f"ElevenLabs TTS generated: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


async def generate_talking_head_video(job_id: int, agent_id: int, script: str):
    """
    Background task: full pipeline from script to branded talking head video.

    Pipeline:
    1. Load brand data (headshot, voice, logo, colors)
    2. Create or reuse HeyGen photo avatar from headshot
    3. Generate TTS audio via ElevenLabs using cloned voice
    4. Upload audio to HeyGen as asset
    5. Generate lip-synced talking head video via HeyGen
    6. Download HeyGen video
    7. Generate branded intro/outro clips via FFmpeg
    8. Concatenate: [intro] + [talking head] + [outro]
    """
    heygen = HeyGenEnhancedService()

    try:
        # --- Load brand data ---
        db = SessionLocal()
        try:
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            if not brand:
                raise ValueError("Agent brand profile not found")

            headshot_url = brand.headshot_url
            voice_clone_id = brand.voice_clone_id
            logo_url = brand.logo_url
            company_name = brand.company_name or ""
            tagline = brand.tagline or ""
            primary_color = brand.primary_color or "#1E3A8A"
            cached_avatar_id = brand.heygen_avatar_id
        finally:
            db.close()

        # --- Step 1: Create or reuse HeyGen avatar ---
        _update_job(job_id, status="creating_avatar")

        if cached_avatar_id:
            avatar_id = cached_avatar_id
            logger.info(f"Reusing cached HeyGen avatar {avatar_id} for agent {agent_id}")
        else:
            # Resolve local headshot path
            if headshot_url and headshot_url.startswith("/"):
                headshot_path = str(PROJECT_ROOT / headshot_url.removeprefix("/"))
            else:
                # Download remote headshot to temp
                headshot_path = str(TEMP_DIR / f"headshot_{job_id}.png")
                await _download_file(headshot_url, Path(headshot_path))

            # Upload to HeyGen and create photo avatar (available immediately)
            result = await heygen.create_custom_avatar(
                agent_id=agent_id,
                photo_path=headshot_path,
                name=f"Agent_{agent_id}",
            )
            avatar_id = result["avatar_id"]
            logger.info(f"Avatar created: talking_photo_id={avatar_id}")

            # Cache avatar ID on brand
            db = SessionLocal()
            try:
                brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
                if brand:
                    brand.heygen_avatar_id = avatar_id
                    db.commit()
            finally:
                db.close()

        _update_job(job_id, heygen_avatar_id=avatar_id)

        # --- Step 2: Generate TTS audio via ElevenLabs ---
        _update_job(job_id, status="generating_audio")
        audio_asset_id = None

        if voice_clone_id and settings.elevenlabs_api_key:
            tts_path = TEMP_DIR / f"tts_{job_id}.mp3"
            await _generate_elevenlabs_tts(script, voice_clone_id, tts_path)

            # Upload audio to HeyGen
            audio_asset_id = await heygen.upload_audio_asset(str(tts_path))
            logger.info(f"Audio uploaded to HeyGen: {audio_asset_id}")

        # --- Step 3: Generate talking head via HeyGen ---
        _update_job(job_id, status="generating")

        gen_result = await heygen.generate_talking_head(
            avatar_id=avatar_id,
            script=script,
            audio_asset_id=audio_asset_id,
            background_color=primary_color,
        )
        heygen_video_id = gen_result["video_id"]
        _update_job(job_id, heygen_video_id=heygen_video_id)

        # Poll until complete (HeyGen can take 10-15 min for longer videos)
        video_data = await heygen.wait_for_video(heygen_video_id, timeout=900)
        heygen_video_url = video_data.get("video_url")
        duration = video_data.get("duration", 0)

        if not heygen_video_url:
            raise RuntimeError("HeyGen returned no video URL")

        # --- Step 4: Download HeyGen video ---
        talking_head_path = TEMP_DIR / f"talking_{job_id}.mp4"
        await _download_file(heygen_video_url, talking_head_path)

        # --- Step 5: Generate branded intro/outro ---
        _update_job(job_id, status="assembling")

        intro_path = await _generate_branded_clip(
            job_id=job_id,
            label="intro",
            logo_url=logo_url,
            text=company_name,
            bg_color=primary_color,
            duration=3,
        )

        outro_path = await _generate_branded_clip(
            job_id=job_id,
            label="outro",
            logo_url=logo_url,
            text=tagline or company_name,
            bg_color=primary_color,
            duration=3,
        )

        # --- Step 6: Re-encode talking head to match intro/outro format ---
        normalized_path = TEMP_DIR / f"normalized_{job_id}.mp4"
        await _run_ffmpeg([
            "ffmpeg", "-y",
            "-i", str(talking_head_path),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-ar", "44100",
            "-r", "30",
            str(normalized_path),
        ], "normalize talking head")

        # --- Step 7: Concatenate intro + talking head + outro ---
        concat_list = TEMP_DIR / f"concat_{job_id}.txt"
        with open(concat_list, "w") as f:
            f.write(f"file '{intro_path}'\n")
            f.write(f"file '{normalized_path}'\n")
            f.write(f"file '{outro_path}'\n")

        final_filename = f"talking_head_{agent_id}_{job_id}.mp4"
        final_path = VIDEO_DIR / final_filename

        await _run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(final_path),
        ], "concatenate final video")

        video_url = f"/videos/talking-heads/{final_filename}"
        total_duration = duration + 6  # talking head + 3s intro + 3s outro

        _update_job(job_id, status="completed", video_url=video_url, duration=total_duration)
        logger.info(f"Talking head video {job_id} completed: {video_url}")

    except Exception as e:
        logger.error(f"Talking head video {job_id} failed: {e}")
        _update_job(job_id, status="failed", error=str(e)[:500])

    finally:
        await heygen.close()
        # Cleanup temp files
        for p in TEMP_DIR.glob(f"*_{job_id}*"):
            p.unlink(missing_ok=True)


async def _generate_branded_clip(
    job_id: int,
    label: str,
    logo_url: Optional[str],
    text: str,
    bg_color: str,
    duration: int = 3,
) -> Path:
    """
    Generate a short branded video clip using FFmpeg.

    Creates a solid-color background with centered logo and text below it.
    """
    output_path = TEMP_DIR / f"{label}_{job_id}.mp4"
    rgb = _hex_to_rgb(bg_color)

    if logo_url:
        # Download logo
        logo_path = TEMP_DIR / f"logo_{job_id}.png"
        if logo_url.startswith("/"):
            # Local file - copy it
            src = PROJECT_ROOT / logo_url.removeprefix("/")
            if src.exists():
                logo_path.write_bytes(src.read_bytes())
            else:
                logo_url = None  # Fall back to text-only
        else:
            try:
                await _download_file(logo_url, logo_path)
            except Exception:
                logo_url = None  # Fall back to text-only

    if logo_url:
        # Logo overlay on colored background (no drawtext — may not have libfreetype)
        await _run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x{rgb}:s=1920x1080:d={duration}:r=30",
            "-i", str(logo_path),
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-filter_complex",
            "[1:v]scale=300:-1[logo];[0:v][logo]overlay=(W-w)/2:(H-h)/2[bg]",
            "-map", "[bg]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-ar", "44100",
            "-shortest",
            str(output_path),
        ], f"generate {label} clip")
    else:
        # Plain colored background (no text — drawtext requires libfreetype)
        await _run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x{rgb}:s=1920x1080:d={duration}:r=30",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-ar", "44100",
            "-shortest",
            str(output_path),
        ], f"generate {label} clip")

    return output_path
