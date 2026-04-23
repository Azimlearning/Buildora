"""
PDF Report Generator
====================
Generates branded PDF reports using ReportLab.

Reports include:
  - Project overview and metadata
  - Extracted fields summary
  - Compliance score and gaps
  - Alerts and recommendations
  - Timeline and milestones
"""

from typing import Dict, Any
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportGenerator:
    """PDF report generator using ReportLab."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            spaceBefore=12
        ))

    async def generate_project_report(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive project report PDF.

        Args:
            project_id:   Project identifier
            project_data: Complete project data from Firestore

        Returns:
            Path to generated PDF file
        """
        output_path = f"/tmp/buildora_report_{project_id}.pdf"
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Title page
        story.extend(self._build_title_page(project_data))
        story.append(PageBreak())

        # Project overview
        story.extend(self._build_overview_section(project_data))
        story.append(Spacer(1, 0.2 * inch))

        # Extracted fields summary
        story.extend(self._build_fields_section(project_data))
        story.append(Spacer(1, 0.2 * inch))

        # Compliance section
        story.extend(self._build_compliance_section(project_data))
        story.append(Spacer(1, 0.2 * inch))

        # Alerts section
        story.extend(self._build_alerts_section(project_data))

        # Build PDF
        doc.build(story)
        return output_path

    async def generate_compliance_summary(
        self,
        project_id: str,
        compliance_data: Dict[str, Any]
    ) -> str:
        """
        Generate compliance-focused summary PDF.

        Args:
            project_id:      Project identifier
            compliance_data: Compliance score data from Agent C

        Returns:
            Path to generated PDF file
        """
        output_path = f"/tmp/compliance_summary_{project_id}.pdf"
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Title
        story.append(Paragraph(
            "CIDB Compliance Summary",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.3 * inch))

        # Score overview
        score = compliance_data.get('score', 0)
        status = compliance_data.get('status', 'unknown')

        score_text = f"<b>Compliance Score:</b> {score:.1f}%<br/>"
        score_text += f"<b>Status:</b> {status.upper()}"
        story.append(Paragraph(score_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # Gaps table
        gaps = compliance_data.get('gaps', [])
        if gaps:
            story.append(Paragraph("Missing Documents", self.styles['SectionHeader']))

            gap_data = [['#', 'Document', 'Mandatory', 'Note']]
            for idx, gap in enumerate(gaps, 1):
                gap_data.append([
                    str(idx),
                    gap.get('description_en', 'N/A'),
                    'Yes' if gap.get('mandatory') else 'No',
                    gap.get('note', '-')
                ])

            gap_table = Table(gap_data, colWidths=[0.5*inch, 3*inch, 1*inch, 2*inch])
            gap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(gap_table)

        doc.build(story)
        return output_path

    def _build_title_page(self, project_data: Dict[str, Any]) -> list:
        """Build title page elements."""
        elements = []

        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph(
            "Buildora Project Report",
            self.styles['CustomTitle']
        ))
        elements.append(Spacer(1, 0.5 * inch))

        project = project_data.get('project', {})
        project_name = project.get('name', 'Unnamed Project')
        elements.append(Paragraph(
            f"<b>{project_name}</b>",
            self.styles['Heading2']
        ))

        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles['Normal']
        ))

        return elements

    def _build_overview_section(self, project_data: Dict[str, Any]) -> list:
        """Build project overview section."""
        elements = []
        elements.append(Paragraph("Project Overview", self.styles['SectionHeader']))

        project = project_data.get('project', {})
        overview_data = [
            ['Project ID', project.get('id', 'N/A')],
            ['Project Name', project.get('name', 'N/A')],
            ['Status', project.get('status', 'N/A')],
            ['Created', project.get('created_at', 'N/A')],
        ]

        overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(overview_table)

        return elements

    def _build_fields_section(self, project_data: Dict[str, Any]) -> list:
        """Build extracted fields section."""
        elements = []
        elements.append(Paragraph("Extracted Fields", self.styles['SectionHeader']))

        extracted = project_data.get('extracted_fields', [])
        if extracted:
            elements.append(Paragraph(
                f"Total documents processed: {len(extracted)}",
                self.styles['Normal']
            ))
        else:
            elements.append(Paragraph(
                "No extracted fields available.",
                self.styles['Normal']
            ))

        return elements

    def _build_compliance_section(self, project_data: Dict[str, Any]) -> list:
        """Build compliance section."""
        elements = []
        elements.append(Paragraph("Compliance Status", self.styles['SectionHeader']))

        compliance = project_data.get('compliance_score', {})
        score = compliance.get('score', 0)
        status = compliance.get('status', 'unknown')
        gaps = compliance.get('gaps', [])

        compliance_text = f"<b>Score:</b> {score:.1f}%<br/>"
        compliance_text += f"<b>Status:</b> {status.upper()}<br/>"
        compliance_text += f"<b>Missing Documents:</b> {len(gaps)}"

        elements.append(Paragraph(compliance_text, self.styles['Normal']))

        return elements

    def _build_alerts_section(self, project_data: Dict[str, Any]) -> list:
        """Build alerts section."""
        elements = []
        elements.append(Paragraph("Alerts & Recommendations", self.styles['SectionHeader']))

        alerts = project_data.get('alerts', [])
        if alerts:
            for alert in alerts:
                elements.append(Paragraph(
                    f"• {alert.get('message', 'N/A')}",
                    self.styles['Normal']
                ))
        else:
            elements.append(Paragraph(
                "No alerts at this time.",
                self.styles['Normal']
            ))

        return elements
