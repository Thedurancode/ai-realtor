"""
Report Generator Service

Generates PDF reports for analytics and performance data.
Uses reportlab for PDF generation.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
import io


class ReportGenerator:
    """Generate PDF reports from analytics data."""

    def __init__(self):
        """Initialize report generator."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas

            self.SimpleDocTemplate = SimpleDocTemplate
            self.Table = Table
            self.TableStyle = TableStyle
            self.Paragraph = Paragraph
            self.Spacer = Spacer
            self.Image = Image
            self.getSampleStyleSheet = getSampleStyleSheet
            self.ParagraphStyle = ParagraphStyle
            self.TA_CENTER = TA_CENTER
            self.TA_LEFT = TA_LEFT
            self.TA_RIGHT = TA_RIGHT
            self.colors = colors
            self.letter = letter
            self.inch = inch
            self.canvas = canvas

            self.available = True
        except ImportError:
            self.available = False

    def generate_performance_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF performance report.

        Args:
            report_data: Report data from analytics endpoint

        Returns:
            PDF bytes
        """
        if not self.available:
            raise ImportError("reportlab is not installed")

        # Create PDF buffer
        buffer = io.BytesIO()

        # PDF metadata
        pdf_doc = SimpleDocTemplate(
            buffer,
            pagesize=self.letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Styles
        styles = self.getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="Title",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=self.colors.HexColor("#1e40af"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Subtitle",
                parent=styles["Heading2"],
                fontSize=18,
                textColor=self.colors.HexColor("#3b82f6"),
                spaceAfter=12,
            )
        )

        # Build story (content)
        story = []

        # Title
        title = f"Performance Report"
        story.append(self.Paragraph(title, style="Title"))
        story.append(self.Spacer(1, 0.2 * self.inch))

        # Report info
        report_info = f"""
        Generated: {report_data.get('generated_at', 'N/A')}
        Period: Last {report_data.get('period_days', 30)} days
        Agent ID: {report_data.get('agent_id', 'N/A')}
        """
        story.append(self.Paragraph(report_info, styles["BodyText"]))
        story.append(self.Spacer(1, 0.3 * self.inch))

        # Overview Section
        story.append(self.Paragraph("Overview", style="Subtitle"))
        story.append(self.Spacer(1, 0.1 * self.inch))

        overview = report_data.get("overview", {})
        overview_data = [
            ["Metric", "Value"],
            ["Property Views", str(overview.get("property_views", 0))],
            ["Leads Created", str(overview.get("leads_created", 0))],
            ["Conversions", str(overview.get("conversions", 0))],
            ["Conversion Rate", f"{overview.get('conversion_rate', 0)}%"],
            ["Active Properties", str(overview.get("active_properties", 0))],
            ["New Properties", str(overview.get("new_properties", 0))],
            ["Contracts Signed", str(overview.get("contracts_signed", 0))],
        ]

        overview_table = self.Table(overview_data, hAligns=[TA_LEFT, TA_RIGHT])
        overview_table.setStyle(self._get_table_style())
        story.append(overview_table)
        story.append(self.Spacer(1, 0.3 * self.inch))

        # Conversion Funnel Section
        funnel = report_data.get("funnel", [])
        if funnel:
            story.append(self.Paragraph("Conversion Funnel", style="Subtitle"))
            story.append(self.Spacer(1, 0.1 * self.inch))

            funnel_data = [["Stage", "Count"]] + [
                [stage["stage"], str(stage["count"])] for stage in funnel
            ]

            funnel_table = self.Table(funnel_data, hAligns=[TA_LEFT, TA_RIGHT])
            funnel_table.setStyle(self._get_table_style())
            story.append(funnel_table)
            story.append(self.Spacer(1, 0.3 * self.inch))

        # Top Properties Section
        top_properties = report_data.get("top_properties", [])
        if top_properties:
            story.append(self.Paragraph("Top Properties", style="Subtitle"))
            story.append(self.Spacer(1, 0.1 * self.inch))

            props_data = [["Address", "City", "State", "Views"]] + [
                [
                    p.get("address", "N/A"),
                    p.get("city", "N/A"),
                    p.get("state", "N/A"),
                    str(p.get("view_count", 0)),
                ]
                for p in top_properties[:10]
            ]

            props_table = self.Table(props_data, hAligns=[TA_LEFT] * 3 + [TA_RIGHT])
            props_table.setStyle(self._get_table_style())
            story.append(props_table)
            story.append(self.Spacer(1, 0.3 * self.inch))

        # Traffic Sources Section
        traffic_sources = report_data.get("traffic_sources", [])
        if traffic_sources:
            story.append(self.Paragraph("Traffic Sources", style="Subtitle"))
            story.append(self.Spacer(1, 0.1 * self.inch))

            traffic_data = [["Source", "Visitors", "Percentage"]] + [
                [
                    source["source"],
                    str(source["count"]),
                    f"{source['percentage']}%",
                ]
                for source in traffic_sources
            ]

            traffic_table = self.Table(traffic_data, hAligns=[TA_LEFT, TA_RIGHT, TA_RIGHT])
            traffic_table.setStyle(self._get_table_style())
            story.append(traffic_table)

        # Build PDF
        pdf_doc.build(story)

        # Get bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _get_table_style(self) -> TableStyle:
        """Get default table style for reports."""
        style = TableStyle([
            ("BACKGROUND", (0, 0), self.colors.grey),
            ("TEXTCOLOR", (0, 0), self.colors.black),
            ("ALIGN", (0, 0), "LEFT"),
            ("FONTNAME", (0, 0), "Helvetica"),
            ("FONTSIZE", (0, 0), 10),
            ("BOTTOMPADDING", (0, 0), 12),
            ("BACKGROUND", (0, 1), self.colors.grey),
            ("GRID", (0, 0), 1, 1, self.colors.whitesmoke),
            ("TEXTCOLOR", (0, 1), self.colors.black),
            ("ALIGN", (0, 1), "LEFT"),
            ("FONTNAME", (0, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), 10),
            ("BOTTOMPADDING", (0, 1), 12),
            ("BACKGROUND", (0, 0), self.colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), self.colors.whitesmoke),
        ])
        return style


# Singleton instance
report_generator = ReportGenerator()
