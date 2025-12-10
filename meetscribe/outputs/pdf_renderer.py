"""
PDF OUTPUT renderer for MeetScribe.

Generates formatted PDF meeting minutes using ReportLab.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from ..core.models import Minutes
from ..core.providers import OutputRenderer

logger = logging.getLogger(__name__)


class PDFRenderer(OutputRenderer):
    """
    PDF OUTPUT renderer using ReportLab.

    Generates professionally formatted PDF meeting minutes.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PDF renderer.

        Config params:
            output_dir: Directory to save output (default: ./meetings)
            filename_template: Template for filename (default: minutes.pdf)
            page_size: Page size (A4, LETTER, default: A4)
            font_name: Base font name (default: Helvetica)
            title_font_size: Title font size (default: 18)
            heading_font_size: Heading font size (default: 14)
            body_font_size: Body font size (default: 11)
            include_logo: Include logo (default: False)
            logo_path: Path to logo file
            company_name: Company name for header
        """
        super().__init__(config)
        self.output_dir = Path(config.get("output_dir", "./meetings"))
        self.filename_template = config.get("filename_template", "minutes.pdf")
        self.page_size_name = config.get("page_size", "A4")
        self.font_name = config.get("font_name", "Helvetica")
        self.title_font_size = config.get("title_font_size", 18)
        self.heading_font_size = config.get("heading_font_size", 14)
        self.body_font_size = config.get("body_font_size", 11)
        self.include_logo = config.get("include_logo", False)
        self.logo_path = config.get("logo_path")
        self.company_name = config.get("company_name", "")

        # Initialize reportlab
        self._init_reportlab()

    def _init_reportlab(self):
        """Initialize ReportLab components."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, LETTER
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import cm, inch
            from reportlab.platypus import (
                ListFlowable,
                ListItem,
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            self.reportlab_available = True

            # Set page size
            self.page_size = A4 if self.page_size_name == "A4" else LETTER

            # Store modules for later use
            self._rl_colors = colors
            self._rl_inch = inch
            self._rl_cm = cm

        except ImportError:
            logger.warning(
                "reportlab not installed. Run: pip install reportlab\n"
                "Running in mock mode - will generate placeholder file."
            )
            self.reportlab_available = False

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to PDF file.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Path to generated PDF file
        """
        logger.info(f"Rendering PDF output for {meeting_id}")

        # Create output directory
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        output_path = meeting_dir / self.filename_template

        if self.reportlab_available:
            self._generate_pdf(minutes, meeting_id, output_path)
        else:
            self._generate_placeholder(minutes, meeting_id, output_path)

        logger.info(f"PDF saved to: {output_path}")
        return str(output_path)

    def _generate_pdf(self, minutes: Minutes, meeting_id: str, output_path: Path):
        """Generate actual PDF using ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=self.title_font_size,
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=self.heading_font_size,
            spaceAfter=12,
            spaceBefore=20,
        )

        body_style = ParagraphStyle(
            "CustomBody", parent=styles["Normal"], fontSize=self.body_font_size, spaceAfter=10
        )

        # Build document content
        content = []

        # Title
        title = f"Meeting Minutes: {meeting_id}"
        content.append(Paragraph(title, title_style))

        # Metadata
        meta_text = f"Generated: {minutes.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        if self.company_name:
            meta_text = f"{self.company_name} | {meta_text}"
        content.append(Paragraph(meta_text, styles["Normal"]))
        content.append(Spacer(1, 20))

        # Summary
        content.append(Paragraph("Summary", heading_style))
        content.append(Paragraph(minutes.summary, body_style))

        # Key Points
        if minutes.key_points:
            content.append(Paragraph("Key Points", heading_style))
            for point in minutes.key_points:
                content.append(Paragraph(f"• {point}", body_style))

        # Participants
        if minutes.participants:
            content.append(Paragraph("Participants", heading_style))
            participants_text = ", ".join(minutes.participants)
            content.append(Paragraph(participants_text, body_style))

        # Decisions
        if minutes.decisions:
            content.append(Paragraph("Decisions", heading_style))
            for i, decision in enumerate(minutes.decisions, 1):
                decision_text = f"<b>{i}.</b> {decision.description}"
                if decision.responsible:
                    decision_text += f" <i>(Responsible: {decision.responsible})</i>"
                if decision.deadline:
                    decision_text += f" <i>(Deadline: {decision.deadline})</i>"
                content.append(Paragraph(decision_text, body_style))

        # Action Items Table
        if minutes.action_items:
            content.append(Paragraph("Action Items", heading_style))

            # Table data
            table_data = [["#", "Description", "Assignee", "Deadline", "Priority"]]
            for i, item in enumerate(minutes.action_items, 1):
                table_data.append(
                    [
                        str(i),
                        item.description,
                        item.assignee or "-",
                        item.deadline or "-",
                        item.priority or "-",
                    ]
                )

            # Create table
            table = Table(table_data, colWidths=[30, 200, 80, 80, 60])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("ALIGN", (1, 1), (1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            content.append(table)

        # Footer
        content.append(Spacer(1, 30))
        footer_text = "<i>Generated by MeetScribe</i>"
        if minutes.url:
            footer_text += f" | <a href='{minutes.url}'>View in NotebookLM</a>"
        content.append(Paragraph(footer_text, styles["Normal"]))

        # Build PDF
        doc.build(content)

    def _generate_placeholder(self, minutes: Minutes, meeting_id: str, output_path: Path):
        """Generate placeholder when ReportLab not available."""
        # Create a simple text file with .pdf extension as placeholder
        content = f"""MeetScribe PDF Minutes
======================

Meeting ID: {meeting_id}
Generated: {minutes.generated_at.isoformat()}

Summary:
{minutes.summary}

Note: This is a placeholder file. Install reportlab to generate actual PDFs:
pip install reportlab
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def validate_config(self) -> bool:
        """Validate renderer configuration."""
        valid_sizes = ["A4", "LETTER"]
        if self.page_size_name not in valid_sizes:
            raise ValueError(f"page_size must be one of: {valid_sizes}")
        return True
