#!/usr/bin/env python3
"""Delete a PVC voice from ElevenLabs"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.pvc_service import PVCService
from app.config import settings
from app.database import SessionLocal
from app.models.pvc_voice import PVCVoice


async def delete_pvc_voice(voice_id: str):
    """Delete a PVC voice"""
    print("=" * 60)
    print(f"🗑️  Deleting PVC Voice: {voice_id}")
    print("=" * 60)

    # Check if voice exists in database
    db = SessionLocal()
    pvc_voice = db.query(PVCVoice).filter(PVCVoice.id == voice_id).first()

    if pvc_voice:
        print(f"\n📋 Voice found in database:")
        print(f"  Name: {pvc_voice.name}")
        print(f"  Status: {pvc_voice.status}")
        print(f"  Language: {pvc_voice.language}")

        # Delete from database
        db.delete(pvc_voice)
        db.commit()
        print(f"\n✅ Voice deleted from database")
    else:
        print(f"\n⚠️  Voice not found in database (may be only on ElevenLabs)")

    db.close()

    # Delete from ElevenLabs
    print(f"\n🌐 Deleting from ElevenLabs...")
    service = PVCService(api_key=settings.elevenlabs_api_key)

    try:
        # Note: ElevenLabs API doesn't have a delete endpoint for PVC voices
        # You need to delete it from the dashboard at https://elevenlabs.io/app/voices
        print(f"⚠️  PVC voices must be deleted from the ElevenLabs dashboard:")
        print(f"   https://elevenlabs.io/app/voices")
        print(f"   Navigate to the voice and click 'Delete'")
        print(f"\n   Voice ID: {voice_id}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_pvc_voice.py <voice_id>")
        print("\nExample: python delete_pvc_voice.py unVNvzXQxVJ10LTwzTdx")
        sys.exit(1)

    voice_id = sys.argv[1]
    asyncio.run(delete_pvc_voice(voice_id))
