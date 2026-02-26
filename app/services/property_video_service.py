"""
Property Video Generation Service with ElevenLabs Voiceover

Creates professional property showcase videos with:
- Company logo intro
- Property photo slideshow
- Property details overlay
- AI-generated voiceover
"""
import os
import json
import tempfile
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from elevenlabs import ElevenLabs, Voice

from app.models.property import Property
from app.models.agent_brand import AgentBrand
from app.models.zillow_enrichment import ZillowEnrichment


class PropertyVideoService:
    """Service for generating property showcase videos with AI voiceover."""

    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.remotion_project = os.path.join(
            os.path.dirname(__file__), "..", "..", "remotion"
        )

    async def generate_property_video(
        self,
        db: Session,
        property_id: int,
        agent_id: int,
        output_path: Optional[str] = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default male voice
    ) -> Dict[str, Any]:
        """
        Generate a complete property showcase video with voiceover.

        Returns:
            Dict with video path, audio path, and metadata
        """
        # Fetch property data
        property = db.query(Property).filter_by(id=property_id).first()
        if not property:
            raise ValueError(f"Property {property_id} not found")

        # Fetch agent branding
        brand = db.query(AgentBrand).filter_by(agent_id=agent_id).first()

        # Fetch Zillow enrichment for photos
        enrichment = db.query(ZillowEnrichment).filter_by(property_id=property_id).first()

        # Extract photos
        photos = []
        if enrichment and enrichment.photos:
            photos = json.loads(enrichment.photos) if isinstance(enrichment.photos, str) else enrichment.photos

        # Generate voiceover script
        script = self._generate_script(property, enrichment)

        # Generate audio with ElevenLabs
        audio_path = await self._generate_voiceover(script, voice_id, output_path)

        # Calculate video duration
        logo_duration = 90  # 3 seconds
        photo_duration = 120  # 4 seconds per photo
        total_photos = min(len(photos), 10) if photos else 1
        total_duration = logo_duration + (total_photos * photo_duration) + 30  # +30 for transitions

        # Prepare Remotion props
        remotion_props = {
            "logoUrl": brand.logo_url if brand else None,
            "companyName": brand.company_name if brand else "Your Real Estate Experts",
            "tagline": brand.tagline if brand else "Finding Your Dream Home",
            "primaryColor": brand.primary_color if brand else "#1E40AF",
            "secondaryColor": brand.secondary_color if brand else "#3B82F6",
            "propertyAddress": f"{property.address}, {property.city}, {property.state}",
            "propertyPrice": f"${property.price:,.0f}" if property.price else "Price Upon Request",
            "propertyDetails": {
                "bedrooms": property.bedrooms,
                "bathrooms": int(property.bathrooms) if property.bathrooms else None,
                "squareFeet": property.square_feet,
                "propertyType": property.property_type.value if property.property_type else "House",
            },
            "propertyPhotos": photos[:10] if photos else [],  # Max 10 photos
            "audioUrl": audio_path,
            "logoDuration": logo_duration,
            "photoDuration": photo_duration,
        }

        # Render video
        video_path = await self._render_video(
            remotion_props,
            total_duration,
            output_path
        )

        return {
            "video_path": video_path,
            "audio_path": audio_path,
            "script": script,
            "duration_seconds": total_duration / 30,
            "property_id": property_id,
            "photos_used": len(remotion_props["propertyPhotos"]),
            "brand": {
                "company_name": brand.company_name if brand else None,
                "logo_url": brand.logo_url if brand else None,
            }
        }

    def _generate_script(
        self,
        property: Property,
        enrichment: Optional[ZillowEnrichment]
    ) -> str:
        """Generate voiceover script for property."""
        parts = []

        # Intro
        parts.append("Welcome to this exceptional property offering.")

        # Address and price
        parts.append(
            f"Located at {property.address} in {property.city}, {property.state}, "
            f"priced at ${property.price:,.0f}."
        )

        # Property details
        if property.bedrooms or property.bathrooms or property.square_feet:
            details = []
            if property.bedrooms:
                details.append(f"{property.bedrooms} bedrooms")
            if property.bathrooms:
                details.append(f"{int(property.bathrooms)} bathrooms")
            if property.square_feet:
                details.append(f"{property.square_feet:,.0f} square feet")

            if details:
                parts.append(f"This home features {', '.join(details)}.")

        # Property type
        if property.property_type:
            parts.append(f"A beautiful {property.property_type.value.replace('_', ' ')}.")

        # Zillow description excerpt
        if enrichment and enrichment.description:
            # Take first 200 characters of description
            desc = enrichment.description[:200]
            if len(enrichment.description) > 200:
                desc = desc.rsplit(' ', 1)[0] + "..."
            parts.append(desc)

        # Call to action
        parts.append("Contact us today to schedule your private viewing.")

        return " ".join(parts)

    async def _generate_voiceover(
        self,
        script: str,
        voice_id: str,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate audio using ElevenLabs Text-to-Speech."""
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set")

        # Create temp file for audio
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            audio_path = os.path.join(output_dir, "voiceover.mp3")
        else:
            fd, audio_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

        try:
            # Generate audio using ElevenLabs client
            client = ElevenLabs(api_key=self.elevenlabs_api_key)

            # Generate speech
            audio = client.text_to_speech.convert(
                text=script,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )

            # Save audio to file
            with open(audio_path, "wb") as f:
                f.write(audio)

            return audio_path

        except Exception as e:
            # Clean up file on error
            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise Exception(f"Failed to generate voiceover: {str(e)}")

    async def _render_video(
        self,
        props: Dict[str, Any],
        duration_frames: int,
        output_path: Optional[str] = None
    ) -> str:
        """Render video using Remotion CLI."""
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            props_file = os.path.join(temp_dir, "props.json")
            video_output = os.path.join(temp_dir, "output.mp4")

            # Write props
            with open(props_file, "w") as f:
                json.dump(props, f)

            # Build Remotion command
            cmd = [
                "npx", "remotion", "render",
                f"{self.remotion_project}/src/index.tsx",
                "PropertyShowcase",
                video_output,
                "--props", props_file,
                "--jpeg-quality", "80",
                "--overwrite"
            ]

            # Run render
            print(f"🎬 Rendering video with {len(props.get('propertyPhotos', []))} photos...")
            print(f"   Duration: {duration_frames / 30:.1f} seconds")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.remotion_project,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for completion
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                raise Exception(f"Remotion render failed: {error_msg}")

            # Move to final location
            if output_path:
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
                import shutil
                shutil.copy(video_output, output_path)
                return output_path
            else:
                # Return temp file (caller is responsible for cleanup)
                import shutil
                final_path = os.path.join(tempfile.gettempdir(), f"property_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                shutil.copy(video_output, final_path)
                return final_path

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available ElevenLabs voices."""
        if not self.elevenlabs_api_key:
            return []

        try:
            client = ElevenLabs(api_key=self.elevenlabs_api_key)
            voices = client.voices.get_all()
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, "category", "unknown"),
                    "labels": getattr(voice, "labels", {}),
                }
                for voice in voices.voices
            ]
        except Exception as e:
            print(f"Failed to fetch voices: {e}")
            return []
