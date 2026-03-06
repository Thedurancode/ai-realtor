"""CMA (Comparative Market Analysis) Report Service.

Generates professional PDF comp reports with AI-powered market narratives,
comparable sales/rental tables, pricing analysis, and agent branding.
"""

import io
import logging
from datetime import datetime, timezone
from typing import Optional

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.config import settings
from app.models.property import Property
from app.models.agent_brand import AgentBrand
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.comps_dashboard_service import comps_dashboard_service
from app.services.resend_service import resend_service

logger = logging.getLogger(__name__)

# ── Brand defaults ──
DEFAULT_AGENT_NAME = "Ed Duran"
DEFAULT_COMPANY = "Emprezario Inc"
DEFAULT_PHONE = "201-300-5189"
DEFAULT_EMAIL = "emprezarioinc@gmail.com"
DEFAULT_WEBSITE = "https://www.emprezario.com"

# Colors (RGB tuples)
NAVY = (26, 54, 93)        # #1a365d
GOLD = (212, 168, 67)      # #d4a843
WHITE = (255, 255, 255)
LIGHT_GRAY = (245, 245, 245)
MEDIUM_GRAY = (180, 180, 180)
DARK_GRAY = (80, 80, 80)
BLACK = (30, 30, 30)


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return NAVY
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


class BrandInfo:
    """Resolved branding info for the report."""

    def __init__(
        self,
        agent_name: str = DEFAULT_AGENT_NAME,
        company_name: str = DEFAULT_COMPANY,
        phone: str = DEFAULT_PHONE,
        email: str = DEFAULT_EMAIL,
        website: str = DEFAULT_WEBSITE,
        logo_url: Optional[str] = None,
        primary_color: tuple = NAVY,
        accent_color: tuple = GOLD,
        tagline: str = "",
        license_number: str = "",
    ):
        self.agent_name = agent_name
        self.company_name = company_name
        self.phone = phone
        self.email = email
        self.website = website
        self.logo_url = logo_url
        self.primary_color = primary_color
        self.accent_color = accent_color
        self.tagline = tagline
        self.license_number = license_number

    @classmethod
    def from_agent_brand(cls, brand: AgentBrand) -> "BrandInfo":
        agent = brand.agent if brand.agent else None
        return cls(
            agent_name=agent.name if agent else DEFAULT_AGENT_NAME,
            company_name=brand.company_name or DEFAULT_COMPANY,
            phone=brand.display_phone or DEFAULT_PHONE,
            email=brand.display_email or DEFAULT_EMAIL,
            website=brand.website_url or DEFAULT_WEBSITE,
            logo_url=brand.logo_url,
            primary_color=_hex_to_rgb(brand.primary_color) if brand.primary_color else NAVY,
            accent_color=_hex_to_rgb(brand.accent_color) if brand.accent_color else GOLD,
            tagline=brand.tagline or "",
            license_number=brand.license_number or "",
        )


class CMAPdf(FPDF):
    """Custom FPDF subclass for CMA reports."""

    def __init__(self, brand: BrandInfo):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.brand = brand
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        # Skip header on first page (cover page draws its own)
        if self.page_no() == 1:
            return
        self._draw_header_bar()

    def footer(self):
        self.set_y(-20)
        # Gold accent line
        self.set_draw_color(*self.brand.accent_color)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        # Footer text
        self.set_y(-17)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*DARK_GRAY)
        footer = f"{self.brand.agent_name} | {self.brand.company_name} | {self.brand.phone} | {self.brand.email}"
        if self.brand.license_number:
            footer += f" | Lic# {self.brand.license_number}"
        self.cell(0, 4, footer, align="C")
        self.ln(4)
        self.set_font("Helvetica", "", 6)
        self.set_text_color(*MEDIUM_GRAY)
        self.cell(0, 3, f"Page {self.page_no()} | Generated {datetime.now(timezone.utc).strftime('%B %d, %Y')}", align="C")

    def _draw_header_bar(self):
        self.set_fill_color(*self.brand.primary_color)
        self.rect(0, 0, self.w, 14, "F")
        self.set_xy(15, 3)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        self.cell(0, 8, f"Comparative Market Analysis | {self.brand.company_name}", align="L")

    def section_title(self, title: str):
        """Draw a styled section title."""
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.brand.primary_color)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        # Gold underline
        y = self.get_y()
        self.set_draw_color(*self.brand.accent_color)
        self.set_line_width(0.8)
        self.line(15, y, 80, y)
        self.ln(4)

    def body_text(self, text: str):
        """Write body text paragraph."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, text)
        self.ln(2)


# ── AI narrative generation ──

def _generate_ai_narrative(subject: dict, comp_sales: list, comp_rentals: list, metrics: dict, rental_metrics: dict) -> dict:
    """Use Claude to generate market analysis narrative, price recommendation, and neighborhood highlights."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except Exception as e:
        logger.warning("Anthropic client unavailable, using fallback narrative: %s", e)
        return _fallback_narrative(subject, metrics)

    address = subject.get("address", "Unknown")
    price = subject.get("price")
    beds = subject.get("beds")
    baths = subject.get("baths")
    sqft = subject.get("sqft")
    zestimate = subject.get("zestimate")

    comp_summary_lines = []
    for i, c in enumerate(comp_sales[:10], 1):
        line = f"  {i}. {c.get('address', 'N/A')} - ${c.get('sale_price', 0):,.0f}"
        if c.get("sqft"):
            line += f", {c['sqft']} sqft"
        if c.get("beds"):
            line += f", {c['beds']}bd/{c.get('baths', '?')}ba"
        if c.get("sale_date"):
            line += f", sold {c['sale_date']}"
        if c.get("distance_mi") is not None:
            line += f", {c['distance_mi']:.1f} mi away"
        comp_summary_lines.append(line)

    rental_lines = []
    for i, r in enumerate(comp_rentals[:5], 1):
        line = f"  {i}. {r.get('address', 'N/A')} - ${r.get('rent', 0):,.0f}/mo"
        if r.get("beds"):
            line += f", {r['beds']}bd/{r.get('baths', '?')}ba"
        rental_lines.append(line)

    prompt = f"""You are a real estate market analyst writing a CMA (Comparative Market Analysis) report.

Subject Property: {address}
List Price: ${price:,.0f} if price else 'Not listed'
Beds/Baths: {beds or '?'}/{baths or '?'}
Square Feet: {sqft or 'Unknown'}
Zestimate: ${zestimate:,.0f} if zestimate else 'N/A'

Market Metrics:
- Comp count: {metrics.get('comp_count', 0)}
- Median comp sale price: ${metrics.get('median_sale_price', 0):,.0f} if metrics.get('median_sale_price') else 'N/A'
- Avg price/sqft: ${metrics.get('avg_price_per_sqft', 0):,.0f}/sqft if metrics.get('avg_price_per_sqft') else 'N/A'
- Price trend: {metrics.get('price_trend', 'unknown')}
- Subject vs market: {metrics.get('subject_vs_market', 'unknown')} ({metrics.get('subject_difference_pct', 0):.1f}%)

Comparable Sales:
{chr(10).join(comp_summary_lines) if comp_summary_lines else '  No comparable sales data available.'}

Comparable Rentals:
{chr(10).join(rental_lines) if rental_lines else '  No rental data available.'}
Median rent: ${rental_metrics.get('median_rent', 0):,.0f}/mo if rental_metrics.get('median_rent') else 'N/A'

Write exactly 3 sections in this JSON format (no markdown, raw JSON only):
{{
  "market_analysis": "2-3 paragraph market analysis narrative. Discuss the local market conditions, how the subject compares to recent sales, price trends, and supply/demand dynamics. Be specific with numbers.",
  "price_recommendation": "1-2 paragraphs with a specific recommended price range and reasoning. Include the estimated market value range (low/mid/high) and justify it based on the comps.",
  "neighborhood_highlights": "1 paragraph highlighting the neighborhood appeal, nearby amenities inference, and investment potential."
}}

Be professional, data-driven, and concise. Use dollar amounts and percentages. Do NOT use markdown formatting."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = response.content[0].text.strip()
        # Try to parse JSON from the response
        if text.startswith("{"):
            return json.loads(text)
        # Try to find JSON in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        logger.warning("AI narrative generation failed: %s", e)

    return _fallback_narrative(subject, metrics)


def _fallback_narrative(subject: dict, metrics: dict) -> dict:
    """Generate a simple fallback narrative without AI."""
    address = subject.get("address", "the subject property")
    price = subject.get("price")
    median = metrics.get("median_sale_price")
    comp_count = metrics.get("comp_count", 0)

    analysis = f"This Comparative Market Analysis examines {address} in the context of recent comparable sales activity in the area."
    if comp_count > 0 and median:
        analysis += f" Based on {comp_count} comparable sales, the median sale price in the area is ${median:,.0f}."
        if price:
            diff_pct = metrics.get("subject_difference_pct", 0)
            vs = metrics.get("subject_vs_market", "at_market")
            if vs == "above_market":
                analysis += f" The subject property's list price of ${price:,.0f} is approximately {abs(diff_pct):.1f}% above the market median."
            elif vs == "below_market":
                analysis += f" The subject property's list price of ${price:,.0f} is approximately {abs(diff_pct):.1f}% below the market median, suggesting potential value."
            else:
                analysis += f" The list price of ${price:,.0f} is in line with current market values."
    else:
        analysis += " Limited comparable sales data is available. Additional research is recommended."

    recommendation = "Based on available market data"
    if median:
        low = int(median * 0.95)
        high = int(median * 1.05)
        recommendation += f", the estimated market value range is ${low:,.0f} to ${high:,.0f}."
    else:
        recommendation += ", insufficient data is available to provide a specific price recommendation. Enriching the property with Zillow data and running agentic research is recommended."

    highlights = f"The area surrounding {address} shows steady market activity. Buyers and investors should consider local amenities, school ratings, and recent development trends when evaluating this property."

    return {
        "market_analysis": analysis,
        "price_recommendation": recommendation,
        "neighborhood_highlights": highlights,
    }


# ── PDF generation ──

def _build_pdf(
    subject: dict,
    comp_sales: list,
    comp_rentals: list,
    metrics: dict,
    rental_metrics: dict,
    narrative: dict,
    brand: BrandInfo,
    enrichment_data: Optional[dict] = None,
) -> bytes:
    """Build the full CMA PDF and return bytes."""
    pdf = CMAPdf(brand)
    pdf.set_title("Comparative Market Analysis")
    pdf.set_author(brand.agent_name)

    # ── Page 1: Cover ──
    pdf.add_page()
    # Navy background block
    pdf.set_fill_color(*brand.primary_color)
    pdf.rect(0, 0, pdf.w, 120, "F")
    # Gold accent stripe
    pdf.set_fill_color(*brand.accent_color)
    pdf.rect(0, 120, pdf.w, 4, "F")

    # Title
    pdf.set_xy(20, 30)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 14, "Comparative Market", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(20)
    pdf.cell(0, 14, "Analysis", new_x="LMARGIN", new_y="NEXT")

    # Address
    address = subject.get("address", "Unknown Property")
    pdf.ln(8)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(220, 220, 220)
    pdf.multi_cell(pdf.w - 40, 8, address)

    # Property quick stats
    pdf.set_y(135)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLACK)

    stats_parts = []
    if subject.get("beds"):
        stats_parts.append(f"{subject['beds']} Beds")
    if subject.get("baths"):
        stats_parts.append(f"{subject['baths']} Baths")
    if subject.get("sqft"):
        stats_parts.append(f"{subject['sqft']:,} Sq Ft")
    if subject.get("property_type"):
        stats_parts.append(subject["property_type"].replace("_", " ").title())
    if stats_parts:
        pdf.cell(0, 7, " | ".join(stats_parts), new_x="LMARGIN", new_y="NEXT")

    # Price and Zestimate
    pdf.ln(3)
    pdf.set_x(20)
    price = subject.get("price")
    if price:
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*brand.primary_color)
        pdf.cell(0, 12, f"List Price: ${price:,.0f}", new_x="LMARGIN", new_y="NEXT")

    zestimate = subject.get("zestimate")
    if zestimate:
        pdf.set_x(20)
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(0, 7, f"Zillow Zestimate: ${zestimate:,.0f}", new_x="LMARGIN", new_y="NEXT")

    rent_zestimate = subject.get("rent_zestimate")
    if rent_zestimate:
        pdf.set_x(20)
        pdf.cell(0, 7, f"Rent Estimate: ${rent_zestimate:,.0f}/mo", new_x="LMARGIN", new_y="NEXT")

    # Photo placeholder
    pdf.ln(6)
    pdf.set_x(20)
    pdf.set_draw_color(*MEDIUM_GRAY)
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.rect(20, pdf.get_y(), pdf.w - 40, 50, "DF")
    pdf.set_xy(20, pdf.get_y() + 20)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(*MEDIUM_GRAY)
    pdf.cell(pdf.w - 40, 10, "[ Property Photo ]", align="C")

    # Agent branding on cover
    pdf.set_y(pdf.h - 50)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*brand.primary_color)
    pdf.cell(0, 7, f"Prepared by {brand.agent_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(0, 5, brand.company_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(20)
    pdf.cell(0, 5, f"{brand.phone} | {brand.email}", new_x="LMARGIN", new_y="NEXT")
    if brand.website:
        pdf.set_x(20)
        pdf.cell(0, 5, brand.website, new_x="LMARGIN", new_y="NEXT")
    if brand.tagline:
        pdf.set_x(20)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, brand.tagline, new_x="LMARGIN", new_y="NEXT")

    # ── Page 2: Executive Summary ──
    pdf.add_page()
    pdf.set_y(20)
    pdf.section_title("Executive Summary")

    # Key metrics boxes
    _draw_metric_boxes(pdf, subject, metrics, rental_metrics, brand)

    pdf.ln(6)
    pdf.section_title("Market Analysis")
    pdf.body_text(narrative.get("market_analysis", "No analysis available."))

    # ── Page 3: Comparable Sales ──
    pdf.add_page()
    pdf.set_y(20)
    pdf.section_title("Comparable Sales")

    if comp_sales:
        _draw_comp_sales_table(pdf, comp_sales[:15], brand)
    else:
        pdf.body_text("No comparable sales data available. Consider enriching the property with Zillow data and running agentic research for additional comparables.")

    # ── Page 4: Price Analysis ──
    pdf.add_page()
    pdf.set_y(20)
    pdf.section_title("Price Analysis")
    pdf.body_text(narrative.get("price_recommendation", "No price recommendation available."))

    # Estimated value range visual
    median = metrics.get("median_sale_price")
    if median:
        pdf.ln(4)
        _draw_value_range(pdf, median, subject.get("price"), brand)

    # Price per sqft analysis
    if metrics.get("avg_price_per_sqft"):
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*brand.primary_color)
        pdf.cell(0, 7, "Price Per Square Foot Analysis", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*BLACK)
        pdf.cell(0, 6, f"Average: ${metrics['avg_price_per_sqft']:,.0f}/sqft", new_x="LMARGIN", new_y="NEXT")
        if metrics.get("median_price_per_sqft"):
            pdf.cell(0, 6, f"Median: ${metrics['median_price_per_sqft']:,.0f}/sqft", new_x="LMARGIN", new_y="NEXT")
        if subject.get("sqft") and subject.get("price"):
            subject_ppsf = subject["price"] / subject["sqft"]
            pdf.cell(0, 6, f"Subject Property: ${subject_ppsf:,.0f}/sqft", new_x="LMARGIN", new_y="NEXT")

    # ── Page 5: Rental Comps + Market Trends ──
    pdf.add_page()
    pdf.set_y(20)
    pdf.section_title("Rental Comparables")

    if comp_rentals:
        _draw_comp_rentals_table(pdf, comp_rentals[:10], brand)
    else:
        pdf.body_text("No rental comparable data available.")

    if rental_metrics.get("median_rent"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*brand.primary_color)
        pdf.cell(0, 6, f"Median Rent: ${rental_metrics['median_rent']:,.0f}/mo", new_x="LMARGIN", new_y="NEXT")
        if rental_metrics.get("rent_range"):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.cell(0, 6, f"Range: ${rental_metrics['rent_range']['min']:,.0f} - ${rental_metrics['rent_range']['max']:,.0f}/mo", new_x="LMARGIN", new_y="NEXT")

    # Market trends
    pdf.ln(6)
    pdf.section_title("Market Trends")

    trend = metrics.get("price_trend", "insufficient_data")
    trend_pct = metrics.get("trend_pct")
    if trend != "insufficient_data":
        trend_label = trend.replace("_", " ").title()
        trend_text = f"Market Trend: {trend_label}"
        if trend_pct is not None:
            trend_text += f" ({trend_pct:+.1f}%)"
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*brand.primary_color)
        pdf.cell(0, 7, trend_text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    else:
        pdf.body_text("Insufficient historical data to determine a reliable price trend. Additional comparable sales are needed.")

    # Neighborhood highlights
    pdf.ln(4)
    pdf.section_title("Neighborhood Highlights")
    pdf.body_text(narrative.get("neighborhood_highlights", "No neighborhood data available."))

    # ── Output ──
    return pdf.output()


def _draw_metric_boxes(pdf: CMAPdf, subject: dict, metrics: dict, rental_metrics: dict, brand: BrandInfo):
    """Draw key metric summary boxes."""
    boxes = []
    if metrics.get("median_sale_price"):
        boxes.append(("Median Comp Price", f"${metrics['median_sale_price']:,.0f}"))
    if metrics.get("comp_count"):
        boxes.append(("Comparables Found", str(metrics["comp_count"])))
    if subject.get("zestimate"):
        boxes.append(("Zestimate", f"${subject['zestimate']:,.0f}"))
    if rental_metrics.get("median_rent"):
        boxes.append(("Median Rent", f"${rental_metrics['median_rent']:,.0f}/mo"))
    if metrics.get("avg_price_per_sqft"):
        boxes.append(("Avg $/SqFt", f"${metrics['avg_price_per_sqft']:,.0f}"))
    vs = metrics.get("subject_vs_market")
    diff = metrics.get("subject_difference_pct")
    if vs and diff is not None:
        label = vs.replace("_", " ").title()
        boxes.append(("vs Market", f"{label} ({diff:+.1f}%)"))

    if not boxes:
        return

    # Draw up to 3 boxes per row
    box_w = (pdf.w - 40) / min(len(boxes), 3)
    box_h = 22
    x_start = 15
    y_start = pdf.get_y()

    for i, (label, value) in enumerate(boxes[:6]):
        col = i % 3
        row = i // 3
        x = x_start + col * box_w + 2
        y = y_start + row * (box_h + 4)

        pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_draw_color(*brand.accent_color)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, box_w - 4, box_h, "DF")

        pdf.set_xy(x + 3, y + 3)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(box_w - 10, 4, label)

        pdf.set_xy(x + 3, y + 9)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*brand.primary_color)
        pdf.cell(box_w - 10, 8, value)

    rows_used = (min(len(boxes), 6) + 2) // 3
    pdf.set_y(y_start + rows_used * (box_h + 4) + 2)


def _draw_comp_sales_table(pdf: CMAPdf, comps: list, brand: BrandInfo):
    """Draw comparable sales table."""
    col_widths = [62, 28, 18, 18, 20, 28]  # address, price, sqft, bd/ba, dist, date
    headers = ["Address", "Sale Price", "SqFt", "Bd/Ba", "Dist (mi)", "Sale Date"]

    # Header row
    pdf.set_fill_color(*brand.primary_color)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    x_start = 15
    for i, header in enumerate(headers):
        pdf.set_xy(x_start + sum(col_widths[:i]), pdf.get_y())
        pdf.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
    pdf.ln(7)

    # Data rows
    pdf.set_font("Helvetica", "", 7.5)
    for idx, comp in enumerate(comps):
        if pdf.get_y() > pdf.h - 30:
            pdf.add_page()
            pdf.set_y(20)
            # Re-draw header
            pdf.set_fill_color(*brand.primary_color)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 8)
            for i, header in enumerate(headers):
                pdf.set_xy(x_start + sum(col_widths[:i]), pdf.get_y())
                pdf.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
            pdf.ln(7)
            pdf.set_font("Helvetica", "", 7.5)

        fill = idx % 2 == 0
        if fill:
            pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_text_color(*BLACK)

        y = pdf.get_y()
        addr = (comp.get("address") or "N/A")[:35]
        price = f"${comp.get('sale_price', 0):,.0f}" if comp.get("sale_price") else "N/A"
        sqft = f"{comp.get('sqft', 0):,}" if comp.get("sqft") else "-"
        bd_ba = f"{comp.get('beds', '-')}/{comp.get('baths', '-')}"
        dist = f"{comp.get('distance_mi', 0):.1f}" if comp.get("distance_mi") is not None else "-"
        date = str(comp.get("sale_date", "-"))[:10] if comp.get("sale_date") else "-"

        row_data = [addr, price, sqft, bd_ba, dist, date]
        aligns = ["L", "R", "R", "C", "R", "C"]
        for i, (val, align) in enumerate(zip(row_data, aligns)):
            pdf.set_xy(x_start + sum(col_widths[:i]), y)
            pdf.cell(col_widths[i], 6, val, border=1, fill=fill, align=align)
        pdf.ln(6)


def _draw_comp_rentals_table(pdf: CMAPdf, rentals: list, brand: BrandInfo):
    """Draw comparable rentals table."""
    col_widths = [70, 30, 22, 22, 30]
    headers = ["Address", "Rent/Mo", "SqFt", "Bd/Ba", "Listed"]

    pdf.set_fill_color(*brand.primary_color)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    x_start = 15
    for i, header in enumerate(headers):
        pdf.set_xy(x_start + sum(col_widths[:i]), pdf.get_y())
        pdf.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 7.5)
    for idx, rental in enumerate(rentals):
        fill = idx % 2 == 0
        if fill:
            pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_text_color(*BLACK)

        y = pdf.get_y()
        addr = (rental.get("address") or "N/A")[:40]
        rent = f"${rental.get('rent', 0):,.0f}" if rental.get("rent") else "N/A"
        sqft = f"{rental.get('sqft', 0):,}" if rental.get("sqft") else "-"
        bd_ba = f"{rental.get('beds', '-')}/{rental.get('baths', '-')}"
        listed = str(rental.get("date_listed", "-"))[:10] if rental.get("date_listed") else "-"

        row_data = [addr, rent, sqft, bd_ba, listed]
        aligns = ["L", "R", "R", "C", "C"]
        for i, (val, align) in enumerate(zip(row_data, aligns)):
            pdf.set_xy(x_start + sum(col_widths[:i]), y)
            pdf.cell(col_widths[i], 6, val, border=1, fill=fill, align=align)
        pdf.ln(6)


def _draw_value_range(pdf: CMAPdf, median: float, subject_price: Optional[float], brand: BrandInfo):
    """Draw estimated value range bar chart."""
    low = int(median * 0.93)
    mid = int(median)
    high = int(median * 1.07)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*brand.primary_color)
    pdf.cell(0, 7, "Estimated Value Range", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    bar_x = 25
    bar_w = pdf.w - 50
    bar_h = 12
    y = pdf.get_y()

    # Background bar
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*MEDIUM_GRAY)
    pdf.rect(bar_x, y, bar_w, bar_h, "DF")

    # Green range bar (low to high)
    pdf.set_fill_color(76, 175, 80)  # green
    pdf.rect(bar_x + bar_w * 0.15, y + 2, bar_w * 0.7, bar_h - 4, "F")

    # Mid marker
    pdf.set_fill_color(*brand.accent_color)
    mid_x = bar_x + bar_w * 0.5
    pdf.rect(mid_x - 1, y, 2, bar_h, "F")

    # Subject price marker
    if subject_price and low > 0:
        ratio = (subject_price - low) / (high - low) if high != low else 0.5
        ratio = max(0, min(1, ratio))
        subj_x = bar_x + bar_w * ratio
        pdf.set_fill_color(244, 67, 54)  # red
        pdf.rect(subj_x - 1.5, y - 2, 3, bar_h + 4, "F")

    # Labels
    pdf.set_y(y + bar_h + 3)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*DARK_GRAY)
    pdf.set_x(bar_x)
    pdf.cell(bar_w * 0.33, 5, f"Low: ${low:,.0f}", align="L")
    pdf.cell(bar_w * 0.34, 5, f"Mid: ${mid:,.0f}", align="C")
    pdf.cell(bar_w * 0.33, 5, f"High: ${high:,.0f}", align="R")
    pdf.ln(6)

    if subject_price:
        pdf.set_x(bar_x)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(244, 67, 54)
        pdf.cell(0, 5, f"Subject list price: ${subject_price:,.0f} (red marker)")
        pdf.ln(5)


# ── Public API ──

def generate_cma_report(
    db: Session,
    property_id: int,
    agent_brand_id: Optional[int] = None,
) -> tuple[bytes, str]:
    """
    Generate a CMA PDF report for a property.

    Returns:
        Tuple of (pdf_bytes, filename)
    """
    # Load property
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise ValueError(f"Property {property_id} not found")

    # Resolve branding
    brand = BrandInfo()
    if agent_brand_id:
        agent_brand = db.query(AgentBrand).filter(AgentBrand.id == agent_brand_id).first()
        if agent_brand:
            brand = BrandInfo.from_agent_brand(agent_brand)
    elif prop.agent_id:
        agent_brand = db.query(AgentBrand).filter(AgentBrand.agent_id == prop.agent_id).first()
        if agent_brand:
            brand = BrandInfo.from_agent_brand(agent_brand)

    # Get comp data via service
    try:
        sales_data = comps_dashboard_service.get_sales(db, property_id)
    except ValueError:
        sales_data = {"subject": {}, "comp_sales": [], "market_metrics": {}}

    try:
        rentals_data = comps_dashboard_service.get_rentals(db, property_id)
    except ValueError:
        rentals_data = {"subject": {}, "comp_rentals": [], "rental_metrics": {}}

    subject = sales_data.get("subject", {})
    comp_sales = sales_data.get("comp_sales", [])
    metrics = sales_data.get("market_metrics", {})
    comp_rentals = rentals_data.get("comp_rentals", [])
    rental_metrics = rentals_data.get("rental_metrics", {})

    # Enrichment extras
    enrichment = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).first()
    enrichment_data = None
    if enrichment:
        enrichment_data = {
            "year_built": enrichment.year_built,
            "home_type": enrichment.home_type,
            "lot_size": enrichment.lot_size,
        }

    # AI narrative
    narrative = _generate_ai_narrative(subject, comp_sales, comp_rentals, metrics, rental_metrics)

    # Build PDF
    pdf_bytes = _build_pdf(
        subject=subject,
        comp_sales=comp_sales,
        comp_rentals=comp_rentals,
        metrics=metrics,
        rental_metrics=rental_metrics,
        narrative=narrative,
        brand=brand,
        enrichment_data=enrichment_data,
    )

    # Filename
    address_slug = (prop.address or "property").replace(" ", "_").replace(",", "")[:40]
    filename = f"CMA_{address_slug}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"

    return pdf_bytes, filename


def get_cma_preview(db: Session, property_id: int) -> dict:
    """
    Get CMA data as JSON for frontend preview (no PDF generation).
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise ValueError(f"Property {property_id} not found")

    try:
        sales_data = comps_dashboard_service.get_sales(db, property_id)
    except ValueError:
        sales_data = {"subject": {}, "comp_sales": [], "market_metrics": {}}

    try:
        rentals_data = comps_dashboard_service.get_rentals(db, property_id)
    except ValueError:
        rentals_data = {"subject": {}, "comp_rentals": [], "rental_metrics": {}}

    subject = sales_data.get("subject", {})
    comp_sales = sales_data.get("comp_sales", [])
    metrics = sales_data.get("market_metrics", {})
    comp_rentals = rentals_data.get("comp_rentals", [])
    rental_metrics = rentals_data.get("rental_metrics", {})

    narrative = _generate_ai_narrative(subject, comp_sales, comp_rentals, metrics, rental_metrics)

    return {
        "property_id": property_id,
        "subject": subject,
        "comp_sales": comp_sales[:15],
        "comp_rentals": comp_rentals[:10],
        "market_metrics": metrics,
        "rental_metrics": rental_metrics,
        "narrative": narrative,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def email_cma_report(
    db: Session,
    property_id: int,
    recipient_email: str,
    recipient_name: str = "Client",
    agent_brand_id: Optional[int] = None,
) -> dict:
    """
    Generate a CMA report and email it via Resend.

    Returns:
        Dict with success status, email result, and filename.
    """
    pdf_bytes, filename = generate_cma_report(db, property_id, agent_brand_id)

    prop = db.query(Property).filter(Property.id == property_id).first()
    address = f"{prop.address}, {prop.city}, {prop.state}" if prop else "Unknown Property"

    email_result = resend_service.send_report_email(
        to_email=recipient_email,
        to_name=recipient_name,
        report_name="Comparative Market Analysis",
        property_address=address,
        pdf_content=pdf_bytes,
        pdf_filename=filename,
    )

    return {
        "success": email_result.get("success", False),
        "email": email_result,
        "filename": filename,
        "property_id": property_id,
        "property_address": address,
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
    }
