"""
Listing Presentation Builder Service

Feed it an address -> generates full CMA + video script + social media posts + marketing plan.
Uses Claude (Anthropic SDK) to generate all components from a single property address.
Generates branded PDF using fpdf2.
"""

import logging
import json
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any

import anthropic
import resend
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.config import settings
from app.models.agent_brand import AgentBrand

logger = logging.getLogger(__name__)

# ── Default agent info ──────────────────────────────────────────────────

DEFAULT_AGENT = {
    "name": "Ed Duran",
    "company": "Emprezario Inc",
    "phone": "201-300-5189",
    "email": "emprezarioinc@gmail.com",
    "website": "https://www.emprezario.com",
}

# ── Brand colors ────────────────────────────────────────────────────────

NAVY = (26, 54, 93)      # #1a365d
GOLD = (212, 168, 67)    # #d4a843
WHITE = (255, 255, 255)
LIGHT_GRAY = (245, 245, 245)
DARK_TEXT = (30, 30, 30)


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert #RRGGBB to (R, G, B) tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _get_agent_info(db: Session) -> dict:
    """Fetch agent branding info from DB, fall back to defaults."""
    try:
        brand = db.query(AgentBrand).first()
        if brand:
            return {
                "name": brand.license_display_name or DEFAULT_AGENT["name"],
                "company": brand.company_name or DEFAULT_AGENT["company"],
                "phone": brand.display_phone or DEFAULT_AGENT["phone"],
                "email": brand.display_email or DEFAULT_AGENT["email"],
                "website": brand.website_url or DEFAULT_AGENT["website"],
                "logo_url": brand.logo_url,
                "tagline": brand.tagline,
                "primary_color": brand.primary_color or "#1a365d",
                "secondary_color": brand.secondary_color or "#d4a843",
                "bio": brand.bio,
                "headshot_url": brand.headshot_url,
            }
    except Exception as e:
        logger.warning("Could not load agent brand: %s", e)
    return {**DEFAULT_AGENT, "logo_url": None, "tagline": None,
            "primary_color": "#1a365d", "secondary_color": "#d4a843",
            "bio": None, "headshot_url": None}


# ── Claude AI generation ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a top-producing real estate listing agent's marketing assistant.
Generate comprehensive listing presentation materials. Be specific, professional, and persuasive.
Always respond with valid JSON matching the exact schema requested. No markdown wrapping."""

GENERATION_PROMPT = """Generate a complete listing presentation for the property at: {address}

Property details (if available): {property_details}

Agent: {agent_name}, {agent_company}

Return a JSON object with these exact keys:

{{
  "cma_summary": {{
    "estimated_value": "<dollar amount>",
    "price_range_low": "<dollar amount>",
    "price_range_high": "<dollar amount>",
    "recommended_list_price": "<dollar amount>",
    "reasoning": "<2-3 sentences explaining the recommended price>",
    "market_conditions": "<current market summary for the area>",
    "days_on_market_avg": "<number>",
    "comparable_notes": "<brief notes on comparable sales>"
  }},
  "marketing_plan": [
    "Professional Photography & Drone Aerials: <specific plan>",
    "Virtual Tour & 3D Walkthrough: <specific plan>",
    "Video Walkthrough & Property Showcase: <specific plan>",
    "Social Media Campaign: <specific plan with platforms>",
    "Email Blast to Buyer Network: <specific plan>",
    "Open House Strategy: <specific plan with dates>",
    "Broker Outreach & MLS Optimization: <specific plan>",
    "Print Materials & Direct Mail: <specific plan>"
  ],
  "video_script": {{
    "duration": "60 seconds",
    "intro": "<opening hook, 10 seconds>",
    "body": "<main property features, 40 seconds>",
    "call_to_action": "<closing CTA, 10 seconds>",
    "full_script": "<complete narration script>"
  }},
  "social_media_posts": {{
    "instagram": "<caption with emojis and hashtags>",
    "facebook": "<engaging post with description>",
    "twitter": "<concise tweet with hashtags, under 280 chars>",
    "linkedin": "<professional post for networking>",
    "tiktok": "<fun description with trending hashtags>"
  }},
  "property_description": "<MLS-ready listing description, approximately 150 words>",
  "email_blast": {{
    "subject_line": "<compelling email subject>",
    "preview_text": "<email preview text>",
    "body": "<Just Listed email body in plain text, 200-300 words>"
  }},
  "talking_points": [
    "<selling point 1>",
    "<selling point 2>",
    "<selling point 3>",
    "<selling point 4>",
    "<selling point 5>",
    "<selling point 6>",
    "<selling point 7>",
    "<selling point 8>",
    "<selling point 9>",
    "<selling point 10>"
  ],
  "timeline": {{
    "week_1": "<Pre-launch activities>",
    "week_2": "<Launch week activities>",
    "week_3": "<Active marketing activities>",
    "week_4": "<Follow-up and adjustment activities>"
  }}
}}"""


async def generate_presentation(
    db: Session,
    address: str,
    property_details: Optional[Dict[str, Any]] = None,
) -> dict:
    """Generate a complete listing presentation using Claude AI."""
    agent_info = _get_agent_info(db)
    details_str = json.dumps(property_details) if property_details else "Not provided - use your best judgment based on the address and area."

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = GENERATION_PROMPT.format(
        address=address,
        property_details=details_str,
        agent_name=agent_info["name"],
        agent_company=agent_info["company"],
    )

    logger.info("Generating listing presentation for: %s", address)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

    presentation = json.loads(raw_text)
    presentation["address"] = address
    presentation["agent"] = agent_info
    presentation["generated_at"] = datetime.utcnow().isoformat()
    presentation["property_details"] = property_details

    return presentation


# ── PDF Generation ──────────────────────────────────────────────────────

class PresentationPDF(FPDF):
    """Branded listing presentation PDF."""

    def __init__(self, agent_info: dict):
        super().__init__()
        self.agent = agent_info
        self.navy = NAVY
        self.gold = GOLD
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return  # Cover page has its own header
        self.set_fill_color(*self.navy)
        self.rect(0, 0, 210, 12, "F")
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        self.set_xy(10, 3)
        self.cell(0, 6, f"{self.agent.get('company', '')}  |  {self.agent.get('phone', '')}", align="L")
        self.set_xy(10, 3)
        self.cell(0, 6, f"{self.agent.get('name', '')}", align="R")
        self.ln(14)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self.navy)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        # Gold underline
        self.set_draw_color(*self.gold)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 100, self.get_y())
        self.ln(6)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_TEXT)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bullet_point(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_TEXT)
        x = self.get_x()
        self.set_x(x + 4)
        # Gold bullet
        self.set_fill_color(*self.gold)
        self.circle(x + 2, self.get_y() + 2.5, 1.2, "F")
        self.set_x(x + 8)
        self.multi_cell(0 - 8, 5.5, text)
        self.ln(1.5)

    def label_value(self, label: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.navy)
        self.cell(55, 6, label + ":")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_TEXT)
        self.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def circle(self, x, y, r, style=""):
        """Draw a filled circle (bullet)."""
        # Use FPDF ellipse as circle
        self.ellipse(x - r, y - r, r * 2, r * 2, style)


def _build_cover_page(pdf: PresentationPDF, address: str):
    """Build the cover page."""
    pdf.add_page()
    # Full navy background
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 297, "F")

    # Gold accent bar
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 100, 210, 3, "F")

    # Title
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_y(115)
    pdf.cell(0, 14, "LISTING PRESENTATION", align="C", new_x="LMARGIN", new_y="NEXT")

    # Address
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*GOLD)
    pdf.ln(8)
    pdf.cell(0, 10, address, align="C", new_x="LMARGIN", new_y="NEXT")

    # Agent info
    pdf.set_y(200)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Prepared by {pdf.agent.get('name', '')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, pdf.agent.get("company", ""), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, pdf.agent.get("phone", ""), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, pdf.agent.get("email", ""), align="C", new_x="LMARGIN", new_y="NEXT")

    # Date
    pdf.set_y(260)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(180, 180, 200)
    pdf.cell(0, 8, f"Prepared on {datetime.now().strftime('%B %d, %Y')}", align="C")


def _build_cma_page(pdf: PresentationPDF, cma: dict):
    """Page 2: CMA Summary."""
    pdf.add_page()
    pdf.section_title("Comparative Market Analysis")

    pdf.label_value("Estimated Value", cma.get("estimated_value", "N/A"))
    pdf.label_value("Price Range", f"{cma.get('price_range_low', 'N/A')} - {cma.get('price_range_high', 'N/A')}")
    pdf.label_value("Recommended List Price", cma.get("recommended_list_price", "N/A"))
    pdf.label_value("Avg Days on Market", str(cma.get("days_on_market_avg", "N/A")))
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Pricing Rationale", new_x="LMARGIN", new_y="NEXT")
    pdf.body_text(cma.get("reasoning", ""))

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Market Conditions", new_x="LMARGIN", new_y="NEXT")
    pdf.body_text(cma.get("market_conditions", ""))

    if cma.get("comparable_notes"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, "Comparable Sales Notes", new_x="LMARGIN", new_y="NEXT")
        pdf.body_text(cma.get("comparable_notes", ""))


def _build_marketing_plan_page(pdf: PresentationPDF, plan: list):
    """Page 3: Marketing Plan."""
    pdf.add_page()
    pdf.section_title("8-Point Marketing Plan")

    for i, point in enumerate(plan[:8], 1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*NAVY)
        # Split on first colon for title/description
        if ":" in point:
            title, desc = point.split(":", 1)
            pdf.cell(0, 7, f"{i}. {title.strip()}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*DARK_TEXT)
            pdf.set_x(18)
            pdf.multi_cell(0 - 8, 5.5, desc.strip())
        else:
            pdf.cell(0, 7, f"{i}. {point}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)


def _build_timeline_page(pdf: PresentationPDF, timeline: dict):
    """Page 4: Marketing Timeline."""
    pdf.add_page()
    pdf.section_title("4-Week Marketing Timeline")

    week_labels = {
        "week_1": "Week 1: Pre-Launch",
        "week_2": "Week 2: Launch",
        "week_3": "Week 3: Active Marketing",
        "week_4": "Week 4: Follow-Up & Adjust",
    }

    for key, label in week_labels.items():
        content = timeline.get(key, "")
        # Week header with gold accent
        pdf.set_fill_color(*GOLD)
        pdf.rect(10, pdf.get_y(), 3, 8, "F")
        pdf.set_x(16)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(16)
        pdf.body_text(content)
        pdf.ln(4)


def _build_video_script_page(pdf: PresentationPDF, script: dict):
    """Page 5: Video Script."""
    pdf.add_page()
    pdf.section_title("Video Script (60 Seconds)")

    pdf.label_value("Duration", script.get("duration", "60 seconds"))
    pdf.ln(4)

    sections = [
        ("Opening Hook (0-10s)", script.get("intro", "")),
        ("Property Features (10-50s)", script.get("body", "")),
        ("Call to Action (50-60s)", script.get("call_to_action", "")),
    ]
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.body_text(content)
        pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Full Script", new_x="LMARGIN", new_y="NEXT")
    pdf.set_fill_color(*LIGHT_GRAY)
    y_start = pdf.get_y()
    pdf.set_x(12)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(186, 5.5, f'"{script.get("full_script", "")}"')


def _build_social_media_page(pdf: PresentationPDF, posts: dict):
    """Page 6: Social Media Posts."""
    pdf.add_page()
    pdf.section_title("Social Media Posts")

    platforms = [
        ("Instagram", posts.get("instagram", "")),
        ("Facebook", posts.get("facebook", "")),
        ("Twitter / X", posts.get("twitter", "")),
        ("LinkedIn", posts.get("linkedin", "")),
        ("TikTok", posts.get("tiktok", "")),
    ]

    for platform, content in platforms:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*GOLD)
        pdf.cell(0, 7, platform, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        # Encode to latin-1 safe text for fpdf2
        safe_content = content.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 5, safe_content)
        pdf.ln(4)


def _build_description_email_page(pdf: PresentationPDF, description: str, email_blast: dict):
    """Page 7: Property Description + Email Blast."""
    pdf.add_page()
    pdf.section_title("MLS Property Description")
    pdf.body_text(description)
    pdf.ln(8)

    pdf.section_title("Just Listed Email Blast")
    pdf.label_value("Subject", email_blast.get("subject_line", ""))
    pdf.label_value("Preview", email_blast.get("preview_text", ""))
    pdf.ln(4)
    pdf.body_text(email_blast.get("body", ""))


def _build_back_cover(pdf: PresentationPDF, address: str, talking_points: list):
    """Back cover: Talking Points + Agent Contact."""
    pdf.add_page()
    pdf.section_title("Key Selling Points")

    for i, point in enumerate(talking_points[:10], 1):
        pdf.bullet_point(f"{point}")

    # Agent contact block at bottom
    pdf.ln(10)
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 240, 210, 57, "F")

    pdf.set_y(248)
    pdf.set_text_color(*GOLD)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Ready to Get Started?", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, pdf.agent.get("name", ""), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, pdf.agent.get("company", ""), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"{pdf.agent.get('phone', '')}  |  {pdf.agent.get('email', '')}", align="C", new_x="LMARGIN", new_y="NEXT")
    if pdf.agent.get("website"):
        pdf.cell(0, 7, pdf.agent.get("website", ""), align="C")


async def generate_presentation_pdf(
    db: Session,
    address: str,
    property_details: Optional[Dict[str, Any]] = None,
) -> tuple[dict, str]:
    """Generate listing presentation and return (presentation_data, pdf_file_path)."""
    presentation = await generate_presentation(db, address, property_details)
    agent_info = presentation.get("agent", _get_agent_info(db))

    pdf = PresentationPDF(agent_info)

    _build_cover_page(pdf, address)
    _build_cma_page(pdf, presentation.get("cma_summary", {}))
    _build_marketing_plan_page(pdf, presentation.get("marketing_plan", []))
    _build_timeline_page(pdf, presentation.get("timeline", {}))
    _build_video_script_page(pdf, presentation.get("video_script", {}))
    _build_social_media_page(pdf, presentation.get("social_media_posts", {}))
    _build_description_email_page(
        pdf,
        presentation.get("property_description", ""),
        presentation.get("email_blast", {}),
    )
    _build_back_cover(pdf, address, presentation.get("talking_points", []))

    # Write to temp file
    safe_name = address.replace(" ", "_").replace(",", "").replace("/", "-")[:60]
    tmp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(tmp_dir, f"listing_presentation_{safe_name}.pdf")
    pdf.output(pdf_path)

    logger.info("PDF generated: %s (%d pages)", pdf_path, pdf.pages_count)
    return presentation, pdf_path


# ── Email Delivery ──────────────────────────────────────────────────────

async def email_presentation(
    db: Session,
    address: str,
    recipient_email: str,
    recipient_name: str,
    property_details: Optional[Dict[str, Any]] = None,
) -> dict:
    """Generate listing presentation PDF and email it to the recipient."""
    presentation, pdf_path = await generate_presentation_pdf(db, address, property_details)
    agent_info = presentation.get("agent", _get_agent_info(db))

    # Read PDF bytes
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Clean up temp file
    try:
        os.unlink(pdf_path)
        os.rmdir(os.path.dirname(pdf_path))
    except OSError:
        pass

    filename = f"Listing_Presentation_{address.replace(' ', '_').replace(',', '')[:40]}.pdf"

    resend.api_key = settings.resend_api_key

    email_result = resend.Emails.send({
        "from": settings.resend_from_email,
        "to": [recipient_email],
        "subject": f"Listing Presentation for {address} | {agent_info.get('company', '')}",
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1a365d; padding: 30px; text-align: center;">
                <h1 style="color: #d4a843; margin: 0;">Listing Presentation</h1>
                <p style="color: white; margin-top: 10px;">{address}</p>
            </div>
            <div style="padding: 30px;">
                <p>Dear {recipient_name},</p>
                <p>Thank you for considering me to represent your property at <strong>{address}</strong>.</p>
                <p>Attached you'll find a comprehensive listing presentation that includes:</p>
                <ul>
                    <li>Comparative Market Analysis (CMA)</li>
                    <li>8-Point Marketing Plan</li>
                    <li>4-Week Marketing Timeline</li>
                    <li>Video & Social Media Strategy</li>
                    <li>MLS Property Description</li>
                </ul>
                <p>I look forward to discussing this with you. Please don't hesitate to reach out.</p>
                <p>Best regards,<br>
                <strong>{agent_info.get('name', '')}</strong><br>
                {agent_info.get('company', '')}<br>
                {agent_info.get('phone', '')}<br>
                {agent_info.get('email', '')}</p>
            </div>
            <div style="background-color: #1a365d; padding: 15px; text-align: center;">
                <p style="color: #d4a843; margin: 0; font-size: 12px;">
                    {agent_info.get('website', '')}
                </p>
            </div>
        </div>
        """,
        "attachments": [
            {
                "filename": filename,
                "content": list(pdf_bytes),
            }
        ],
    })

    return {
        "status": "sent",
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
        "address": address,
        "email_id": email_result.get("id") if isinstance(email_result, dict) else str(email_result),
        "presentation": presentation,
    }
