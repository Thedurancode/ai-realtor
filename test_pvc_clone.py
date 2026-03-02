#!/usr/bin/env python3
"""Test script to create a PVC voice clone from jon3.mp3"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pvc_service import PVCService
from app.database import SessionLocal
from app.models.pvc_voice import PVCVoice
from app.config import settings


async def main():
    """Create PVC voice and upload sample"""
    print("=" * 60)
    print("🎤 Creating Professional Voice Clone: Jon Voice")
    print("=" * 60)

    # Create service with API key from settings
    service = PVCService(api_key=settings.elevenlabs_api_key)

    try:
        # Step 1: Create voice
        print("\n📝 Step 1: Creating PVC voice...")
        voice_result = await service.create_pvc_voice(
            name="Jon Voice",
            language="en",
            description="Voice cloned from jon3.mp3 audio sample"
        )

        voice_id = voice_result.get("voice_id")
        print(f"✓ Voice created successfully!")
        print(f"  Voice ID: {voice_id}")
        print(f"  Status: {voice_result.get('status')}")

        # Save to database
        db = SessionLocal()
        pvc_voice = PVCVoice(
            id=voice_id,
            name="Jon Voice",
            language="en",
            description="Voice cloned from jon3.mp3 audio sample",
            status="creating"
        )
        db.add(pvc_voice)
        db.commit()
        db.close()
        print(f"✓ Voice saved to database")

        # Step 2: Upload sample
        print("\n📤 Step 2: Uploading audio sample...")
        upload_result = await service.upload_pvc_samples(
            voice_id=voice_id,
            file_paths=["/Users/edduran/Downloads/jon3.mp3"]
        )

        sample_ids = upload_result.get("sample_ids", [])
        print(f"✓ Uploaded {len(sample_ids)} sample(s)")
        print(f"  Sample IDs: {sample_ids}")

        # Update database
        db = SessionLocal()
        pvc_voice = db.query(PVCVoice).filter(PVCVoice.id == voice_id).first()
        if pvc_voice:
            pvc_voice.sample_count = len(sample_ids)
            pvc_voice.status = "processing"
            db.commit()
        db.close()
        print(f"✓ Database updated with sample count")

        # Step 3: Start speaker separation
        print("\n🎯 Step 3: Starting speaker separation...")
        separation_result = await service.start_speaker_separation(
            voice_id=voice_id,
            sample_ids=sample_ids
        )

        print(f"✓ Speaker separation started")
        print(f"  Status: {separation_result.get('status')}")
        print(f"  Sample count: {separation_result.get('sample_count')}")

        # Update database
        db = SessionLocal()
        pvc_voice = db.query(PVCVoice).filter(PVCVoice.id == voice_id).first()
        if pvc_voice:
            pvc_voice.status = "separating"
            db.commit()
        db.close()
        print(f"✓ Database updated to 'separating'")

        print("\n" + "=" * 60)
        print("✅ Voice clone process initiated!")
        print("=" * 60)
        print(f"\n📊 Voice ID: {voice_id}")
        print(f"⏱️  Expected training time: 2-6 hours")
        print(f"📧 Check status with:")
        print(f"   curl -X GET http://localhost:8000/v1/pvc/voices/{voice_id} \\")
        print(f"       -H 'x-api-key: YOUR_API_KEY'")
        print("\n💡 Email notification will be sent to emprezarioinc@gmail.com")
        print("   when the voice status becomes 'ready'")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
