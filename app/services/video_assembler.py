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
        # Local storage directory instead of S3 (in project directory)
        project_root = Path(__file__).parent.parent.parent  # Go up from app/services/ to project root
        self.video_storage_dir = project_root / "videos"
        self.video_storage_dir.mkdir(exist_ok=True, parents=True)
        self.video_url_base = "/videos"  # Base URL for serving videos

    async def assemble_property_video(
        self,
        intro_video_url: Optional[str],
        property_clips: List[str],
        outro_video_url: Optional[str],
        voiceover_url: str,
        output_filename: str,
        add_captions: bool = False,
        property_photos: Optional[List[str]] = None,
        agent_headshot_url: Optional[str] = None
    ) -> Dict:
        """
        Assemble final property video from all components.

        Args:
            intro_video_url: Agent intro video URL (HeyGen) - optional
            property_clips: List of property footage URLs (PixVerse)
            outro_video_url: Call-to-action video URL (HeyGen) - optional
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
            # If no video clips but we have photos, create slideshow
            if not property_clips and property_photos:
                logger.info("No video clips available, creating slideshow from photos")
                return await self._create_photo_slideshow(
                    photo_urls=property_photos,
                    voiceover_url=voiceover_url,
                    output_filename=output_filename,
                    agent_headshot_url=agent_headshot_url
                )

            # Step 1: Download all components
            logger.info("Downloading video components...")
            videos_to_concat = []

            # Download intro if provided
            if intro_video_url:
                intro_path = await self._download_video(intro_video_url, "intro.mp4")
                videos_to_concat.append(intro_path)
            else:
                logger.info("Skipping intro video (not provided)")
                intro_path = None

            # Download property clips
            clip_paths = [
                await self._download_video(url, f"clip_{i}.mp4")
                for i, url in enumerate(property_clips)
            ]
            videos_to_concat.extend(clip_paths)

            # Download outro if provided
            if outro_video_url:
                outro_path = await self._download_video(outro_video_url, "outro.mp4")
                videos_to_concat.append(outro_path)
            else:
                logger.info("Skipping outro video (not provided)")
                outro_path = None

            # Handle voiceover (might be local file path or URL)
            if voiceover_url.startswith('/'):
                # It's a local file path
                logger.info(f"Using local voiceover file: {voiceover_url}")
                voiceover_path = Path(voiceover_url)
            else:
                # It's a URL, download it
                voiceover_path = await self._download_video(voiceover_url, "voiceover.mp3")

            # Step 2: Create file list for concatenation
            logger.info("Preparing video concatenation...")
            concat_file = self.temp_dir / "concat_list.txt"
            with open(concat_file, "w") as f:
                for video_path in videos_to_concat:
                    f.write(f"file '{video_path.absolute()}'\n")

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

            # Step 7: Save to local filesystem
            logger.info("Saving to local filesystem...")
            video_url = await self._save_to_local_filesystem(final_output, output_filename)

            # Step 8: Cleanup
            logger.info("Cleaning up temp files...")
            paths_to_cleanup = [voiceover_path, concat_output, final_output, thumbnail_path]
            if intro_path:
                paths_to_cleanup.append(intro_path)
            paths_to_cleanup.extend(clip_paths)
            if outro_path:
                paths_to_cleanup.append(outro_path)

            for path in paths_to_cleanup:
                path.unlink(missing_ok=True)
            concat_file.unlink(missing_ok=True)

            logger.info(f"Video assembly complete: {video_url}")

            return {
                "final_video_url": video_url,
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

        # Save thumbnail to local filesystem
        thumbnail_url = await self._save_to_local_filesystem(output_path, output_path.name)
        return thumbnail_url

    async def _create_photo_slideshow(
        self,
        photo_urls: List[str],
        voiceover_url: str,
        output_filename: str,
        agent_headshot_url: Optional[str] = None
    ) -> Dict:
        """
        Create a slideshow video from property photos with voiceover.

        This is a fallback when AI video generation fails.
        Optionally includes agent headshot as intro frame.
        """
        logger.info(f"Creating photo slideshow with {len(photo_urls)} photos")

        try:
            # Download all photos
            photo_paths = []

            # Add agent headshot as first frame if provided
            if agent_headshot_url:
                logger.info("Adding agent headshot as intro frame")
                try:
                    headshot_path = await self._download_video(agent_headshot_url, "agent_headshot.jpg")
                    photo_paths.insert(0, headshot_path)  # Add at beginning
                except Exception as e:
                    logger.warning(f"Failed to download agent headshot: {str(e)}")

            for i, url in enumerate(photo_urls):
                photo_path = await self._download_video(url, f"photo_{i}.jpg")
                photo_paths.append(photo_path)

            # Download voiceover
            if voiceover_url.startswith('/'):
                voiceover_path = Path(voiceover_url)
            else:
                voiceover_path = await self._download_video(voiceover_url, "voiceover.mp3")

            # Get voiceover duration
            voiceover_duration = await self._get_audio_duration(voiceover_path)
            photo_duration = voiceover_duration / len(photo_paths) if photo_paths else 5

            # Create slideshow video
            logger.info(f"Creating {photo_duration:.2f}s per photo slideshow")
            slideshow_output = self.temp_dir / f"slideshow_{output_filename}"

            # Build FFmpeg command for slideshow
            # First, create concat file for photos with duration
            photo_concat_file = self.temp_dir / "photo_concat.txt"
            with open(photo_concat_file, "w") as f:
                for photo_path in photo_paths:
                    f.write(f"file '{photo_path.absolute()}'\n")
                    f.write(f"duration {photo_duration:.2f}\n")
                # Repeat last photo to fill remaining time
                f.write(f"file '{photo_paths[-1].absolute()}'\n")

            # Create video from photos
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(photo_concat_file),
                "-vf", "fps=1/5,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-t", str(voiceover_duration),
                str(slideshow_output)
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Slideshow creation error: {stderr.decode()}")
                raise Exception("Failed to create photo slideshow")

            # Add voiceover
            logger.info("Adding voiceover to slideshow")
            final_output = self.temp_dir / f"final_{output_filename}"
            await self._add_audio_track(slideshow_output, voiceover_path, final_output)

            # Get metadata
            metadata = await self._get_video_metadata(final_output)

            # Generate thumbnail
            thumbnail_filename = output_filename.replace(".mp4", "_thumb.jpg")
            thumbnail_path = self.temp_dir / thumbnail_filename
            thumbnail_url = await self._generate_thumbnail(final_output, thumbnail_path)

            # Save to local filesystem
            video_url = await self._save_to_local_filesystem(final_output, output_filename)

            # Cleanup
            paths_to_cleanup = photo_paths + [voiceover_path, slideshow_output, final_output, thumbnail_path]
            for path in paths_to_cleanup:
                path.unlink(missing_ok=True)
            photo_concat_file.unlink(missing_ok=True)

            logger.info(f"Photo slideshow complete: {video_url}")

            return {
                "final_video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "duration": metadata.get("duration", 0),
                "file_size": metadata.get("size", 0),
                "resolution": metadata.get("resolution", "1080p")
            }

        except Exception as e:
            logger.error(f"Photo slideshow creation failed: {str(e)}")
            raise

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds using FFprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.warning(f"FFprobe failed, using default duration: {stderr.decode()}")
            return 60.0

        try:
            return float(stdout.decode().strip())
        except:
            return 60.0

    async def _save_to_local_filesystem(self, file_path: Path, filename: str) -> str:
        """Save file to local filesystem and return URL path."""
        try:
            # Create target path
            target_path = self.video_storage_dir / filename

            # Copy file to permanent storage
            import shutil
            shutil.copy2(str(file_path), str(target_path))

            # Return relative URL path
            url_path = f"{self.video_url_base}/{filename}"

            logger.info(f"Saved {filename} to local filesystem: {target_path}")
            logger.info(f"File size: {target_path.stat().st_size} bytes")

            return url_path

        except Exception as e:
            logger.error(f"Local filesystem save failed: {str(e)}")
            raise Exception(f"Failed to save video locally: {str(e)}")

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
        # Local filesystem storage = free (server disk space)
        # Total assembly cost = $0.00
        return 0.0


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
