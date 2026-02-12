"""Property Overview PDF report — modern, data-rich single-page layout."""
import logging
from io import BytesIO
from datetime import datetime

import httpx
from fpdf import FPDF

from .base_report import BaseReport
from . import register_report

logger = logging.getLogger(__name__)

# ── Colour palette ───────────────────────────────────────────
NAVY = (26, 35, 50)       # #1a2332
WHITE = (255, 255, 255)
LIGHT_GREY = (245, 245, 248)
MID_GREY = (180, 180, 190)
DARK_TEXT = (30, 30, 40)
ACCENT = (59, 130, 246)   # blue highlight
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
RED = (239, 68, 68)

STATUS_COLORS = {
    "completed": GREEN,
    "signed": GREEN,
    "in_progress": AMBER,
    "pending_signature": AMBER,
    "sent": AMBER,
    "draft": MID_GREY,
    "missing": RED,
    "cancelled": RED,
    "expired": RED,
}


def _fmt_price(val) -> str:
    if val is None:
        return "N/A"
    return f"${val:,.0f}"


def _download_image(url: str, timeout: float = 10.0) -> bytes | None:
    """Download an image from URL with timeout, return bytes or None."""
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.warning(f"Failed to download image {url}: {e}")
        return None


class PropertyOverviewPDF(FPDF):
    """Custom FPDF subclass with helpers for the overview layout."""

    def _set_color(self, rgb, fill=False):
        if fill:
            self.set_fill_color(*rgb)
        else:
            self.set_text_color(*rgb)

    def section_title(self, title: str):
        self.ln(6)
        self._set_color(NAVY)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        # thin accent underline
        self._set_color(ACCENT, fill=True)
        self.rect(self.l_margin, self.get_y(), 40, 0.8, "F")
        self.ln(4)


class PropertyOverviewReport(BaseReport):
    report_type = "property_overview"
    display_name = "Property Overview"

    def generate(self, context: dict) -> BytesIO:
        prop = context.get("property", {})
        enrichment = context.get("enrichment")
        contracts = context.get("contracts", [])
        contacts = context.get("contacts", [])
        readiness = context.get("contract_readiness", {})
        photos = context.get("photos", [])
        agent_name = context.get("agent_name", "")

        pdf = PropertyOverviewPDF(orientation="P", unit="mm", format="Letter")
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pw = pdf.w - pdf.l_margin - pdf.r_margin  # printable width

        # ── HEADER BAR ───────────────────────────────────────
        pdf._set_color(NAVY, fill=True)
        pdf.rect(0, 0, pdf.w, 24, "F")
        pdf._set_color(WHITE)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_xy(pdf.l_margin, 4)
        pdf.cell(pw / 2, 16, "PROPERTY OVERVIEW", align="L")
        if agent_name:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(pw / 2, 16, agent_name, align="R")
        pdf.ln(20)

        # ── HERO: Photo + Stats ──────────────────────────────
        hero_y = pdf.get_y() + 2
        photo_w = 85
        photo_h = 60
        photo_placed = False

        if photos:
            img_bytes = _download_image(photos[0])
            if img_bytes:
                import tempfile, os
                tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                tmp.write(img_bytes)
                tmp.close()
                try:
                    pdf.image(tmp.name, x=pdf.l_margin, y=hero_y, w=photo_w, h=photo_h)
                    photo_placed = True
                except Exception as e:
                    logger.warning(f"Failed to embed photo: {e}")
                finally:
                    os.unlink(tmp.name)

        if not photo_placed:
            # placeholder rectangle
            pdf._set_color(LIGHT_GREY, fill=True)
            pdf.rect(pdf.l_margin, hero_y, photo_w, photo_h, "F")
            pdf._set_color(MID_GREY)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_xy(pdf.l_margin, hero_y + photo_h / 2 - 4)
            pdf.cell(photo_w, 8, "No Photo Available", align="C")

        # Stats box to the right of photo
        stats_x = pdf.l_margin + photo_w + 6
        stats_w = pw - photo_w - 6
        pdf.set_xy(stats_x, hero_y)

        stat_items = [
            ("List Price", _fmt_price(prop.get("price"))),
            ("Zestimate", _fmt_price(enrichment.get("zestimate")) if enrichment else "N/A"),
            ("Beds / Baths", f"{prop.get('bedrooms') or '-'} bd / {prop.get('bathrooms') or '-'} ba"),
            ("Sq Ft", f"{prop.get('square_feet'):,}" if prop.get("square_feet") else "N/A"),
            ("Year Built", str(prop.get("year_built") or "N/A")),
            ("Type", (prop.get("property_type") or "N/A").replace("_", " ").title()),
            ("Status", (prop.get("status") or "N/A").replace("_", " ").title()),
        ]

        for label, value in stat_items:
            pdf._set_color(MID_GREY)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_x(stats_x)
            pdf.cell(stats_w, 3.5, label.upper(), new_x="LMARGIN", new_y="NEXT")
            pdf._set_color(DARK_TEXT)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(stats_x)
            pdf.cell(stats_w, 5.5, value, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(0.5)

        pdf.set_y(hero_y + photo_h + 4)

        # ── ADDRESS BANNER ───────────────────────────────────
        pdf._set_color(LIGHT_GREY, fill=True)
        pdf.rect(pdf.l_margin, pdf.get_y(), pw, 10, "F")
        pdf._set_color(DARK_TEXT)
        pdf.set_font("Helvetica", "B", 11)
        address = prop.get("address", "Unknown Address")
        pdf.cell(pw, 10, address, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # ── MARKET ANALYSIS ──────────────────────────────────
        if enrichment and (enrichment.get("zestimate") or enrichment.get("rent_zestimate")):
            pdf.section_title("Market Analysis")
            pdf.set_font("Helvetica", "", 9)
            pdf._set_color(DARK_TEXT)

            price = prop.get("price")
            zest = enrichment.get("zestimate")
            if price and zest:
                diff = zest - price
                pct = (diff / price) * 100
                direction = "above" if diff > 0 else "below"
                pdf.cell(0, 5, f"List Price: {_fmt_price(price)}    |    Zestimate: {_fmt_price(zest)}    |    {abs(pct):.1f}% {direction} list", new_x="LMARGIN", new_y="NEXT")

            rent = enrichment.get("rent_zestimate")
            if rent:
                pdf.cell(0, 5, f"Rent Estimate: {_fmt_price(rent)}/month", new_x="LMARGIN", new_y="NEXT")

        # ── SCHOOLS TABLE ─────────────────────────────────────
        schools = enrichment.get("schools", []) if enrichment else []
        if schools:
            pdf.section_title("Nearby Schools")
            col_widths = [pw * 0.45, pw * 0.2, pw * 0.2, pw * 0.15]
            headers = ["School", "Grades", "Distance", "Rating"]

            # header row
            pdf._set_color(NAVY, fill=True)
            pdf._set_color(WHITE)
            pdf.set_font("Helvetica", "B", 8)
            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 6, h, border=0, fill=True, align="C" if i > 0 else "L")
            pdf.ln()

            pdf.set_font("Helvetica", "", 8)
            for idx, school in enumerate(schools[:6]):
                bg = LIGHT_GREY if idx % 2 == 0 else WHITE
                pdf._set_color(bg, fill=True)
                pdf._set_color(DARK_TEXT)

                name = school.get("name", school.get("schoolName", ""))[:40]
                grades = school.get("grades", school.get("gradeRange", ""))
                distance = school.get("distance", "")
                if isinstance(distance, (int, float)):
                    distance = f"{distance:.1f} mi"
                rating = school.get("rating", school.get("greatSchoolsRating", ""))
                rating_str = f"{rating}/10" if rating else "N/A"

                pdf.cell(col_widths[0], 5.5, name, fill=True)
                pdf.cell(col_widths[1], 5.5, str(grades), fill=True, align="C")
                pdf.cell(col_widths[2], 5.5, str(distance), fill=True, align="C")
                pdf.cell(col_widths[3], 5.5, rating_str, fill=True, align="C")
                pdf.ln()

        # ── CONTRACT STATUS TABLE ─────────────────────────────
        if contracts:
            pdf.section_title("Contract Status")
            col_widths = [pw * 0.45, pw * 0.2, pw * 0.35]
            headers = ["Contract", "Required", "Status"]

            pdf._set_color(NAVY, fill=True)
            pdf._set_color(WHITE)
            pdf.set_font("Helvetica", "B", 8)
            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 6, h, fill=True, align="C" if i > 0 else "L")
            pdf.ln()

            pdf.set_font("Helvetica", "", 8)
            for idx, c in enumerate(contracts):
                bg = LIGHT_GREY if idx % 2 == 0 else WHITE
                pdf._set_color(bg, fill=True)
                pdf._set_color(DARK_TEXT)

                name = c.get("name", "")[:40]
                required = "Yes" if c.get("is_required") else "No"
                status_val = c.get("status", "draft")
                status_label = status_val.replace("_", " ").title()

                pdf.cell(col_widths[0], 5.5, name, fill=True)
                pdf.cell(col_widths[1], 5.5, required, fill=True, align="C")

                # Color-coded status
                color = STATUS_COLORS.get(status_val, MID_GREY)
                pdf._set_color(color)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(col_widths[2], 5.5, status_label, fill=True, align="C")
                pdf.set_font("Helvetica", "", 8)
                pdf._set_color(DARK_TEXT)
                pdf.ln()

            # Readiness summary
            pdf.ln(2)
            is_ready = readiness.get("is_ready_to_close", False)
            pdf.set_font("Helvetica", "B", 9)
            if is_ready:
                pdf._set_color(GREEN)
                pdf.cell(0, 6, "READY TO CLOSE", new_x="LMARGIN", new_y="NEXT")
            else:
                completed = readiness.get("completed", 0)
                total = readiness.get("total_required", 0)
                pdf._set_color(AMBER)
                pdf.cell(0, 6, f"NOT READY - {completed}/{total} required contracts completed", new_x="LMARGIN", new_y="NEXT")

        # ── CONTACTS TABLE ────────────────────────────────────
        if contacts:
            pdf.section_title("Contacts")
            col_widths = [pw * 0.3, pw * 0.2, pw * 0.3, pw * 0.2]
            headers = ["Name", "Role", "Email", "Phone"]

            pdf._set_color(NAVY, fill=True)
            pdf._set_color(WHITE)
            pdf.set_font("Helvetica", "B", 8)
            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 6, h, fill=True, align="C" if i > 0 else "L")
            pdf.ln()

            pdf.set_font("Helvetica", "", 8)
            for idx, c in enumerate(contacts):
                bg = LIGHT_GREY if idx % 2 == 0 else WHITE
                pdf._set_color(bg, fill=True)
                pdf._set_color(DARK_TEXT)

                pdf.cell(col_widths[0], 5.5, (c.get("name") or "")[:25], fill=True)
                pdf.cell(col_widths[1], 5.5, (c.get("role") or "")[:15], fill=True, align="C")
                pdf.cell(col_widths[2], 5.5, (c.get("email") or "")[:30], fill=True, align="C")
                pdf.cell(col_widths[3], 5.5, (c.get("phone") or "")[:16], fill=True, align="C")
                pdf.ln()

        # ── DEAL SCORE BADGE ──────────────────────────────────
        score_grade = context.get("score_grade")
        deal_score = context.get("deal_score")
        if score_grade:
            pdf.section_title("Deal Score")
            grade_colors = {"A": GREEN, "B": ACCENT, "C": AMBER, "D": RED, "F": RED}
            color = grade_colors.get(score_grade[0], MID_GREY)
            pdf._set_color(color, fill=True)
            pdf._set_color(WHITE)
            pdf.set_font("Helvetica", "B", 18)
            badge_x = pdf.l_margin
            badge_y = pdf.get_y()
            pdf.rect(badge_x, badge_y, 16, 12, "F")
            pdf.set_xy(badge_x, badge_y + 1)
            pdf.cell(16, 10, score_grade, align="C")
            if deal_score is not None:
                pdf.set_xy(badge_x + 20, badge_y + 2)
                pdf._set_color(DARK_TEXT)
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(40, 8, f"Score: {deal_score:.0f}/100")
            pdf.ln(14)

        # ── FOOTER ────────────────────────────────────────────
        pdf._set_color(MID_GREY)
        pdf.set_font("Helvetica", "I", 7)
        footer_y = pdf.h - 12
        pdf.set_xy(pdf.l_margin, footer_y)
        today = datetime.now().strftime("%B %d, %Y")
        pdf.cell(pw, 4, f"Generated by AI Realtor Platform  |  Confidential  |  {today}", align="C")

        buf = BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf


# Auto-register
register_report(PropertyOverviewReport())
