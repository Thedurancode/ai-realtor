"""Daily digest router — generate, retrieve, and browse digests."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.daily_digest_service import daily_digest_service

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("/latest")
def get_latest_digest(db: Session = Depends(get_db)):
    """Get the most recent daily digest."""
    digest = daily_digest_service.get_latest_digest(db)
    if not digest:
        return {"message": "No digest generated yet. Trigger one with POST /digest/generate."}
    return digest


@router.post("/generate")
async def generate_digest(db: Session = Depends(get_db)):
    """Manually trigger a daily digest generation."""
    digest = await daily_digest_service.generate_digest(db)
    return digest


@router.get("/history")
def get_digest_history(days: int = 7, db: Session = Depends(get_db)):
    """Get past digests."""
    history = daily_digest_service.get_digest_history(db, days=days)
    return {"digests": history, "total": len(history), "days": days}
