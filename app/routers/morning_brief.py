"""Morning Brief router — generate and send daily morning summaries via Telegram."""

from fastapi import APIRouter

from app.services.morning_brief_service import generate_brief_text, send_morning_brief

router = APIRouter(prefix="/morning-brief", tags=["Morning Brief"])


@router.post("/send")
async def send_brief():
    """Generate and send the morning brief via Telegram."""
    result = await send_morning_brief()
    return result


@router.get("/preview")
def preview_brief():
    """Preview the morning brief text without sending it."""
    brief_text = generate_brief_text()
    return {"brief": brief_text}
