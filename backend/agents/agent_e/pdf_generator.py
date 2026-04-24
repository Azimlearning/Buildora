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
        """Create custom paragraph styles for a premium layout."""
        self.styles.add(ParagraphStyle(
            name='ExecutiveTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#0f172a'),  # Slate 900
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='ExecutiveSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64748b'),  # Slate 500
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),  # Blue 800
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='AlertBox',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#7f1d1d'),  # Red 900
            backColor=colors.HexColor('#fef2f2'),  # Red 50
            borderPadding=10,
            borderColor=colors.HexColor('#f87171'),  # Red 400
            borderWidth=1,
            spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            name='KeyMetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='KeyMetricValue',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#0f172a'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=10
        ))

    async def generate_project_report(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> str:
        """
        Generate an Executive Project Summary PDF.

        Args:
            project_id:   Project identifier
            project_data: Complete project data from Firestore

        Returns:
            Path to generated PDF file
        """
        output_path = f"/tmp/buildora_report_{project_id}.pdf"
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        story = []

        # 1. Header & Title
        project = project_data.get('project', {})
        project_name = project.get('name', 'Unnamed Project')
        
        story.append(Paragraph("BUILDORA EXECUTIVE SUMMARY", self.styles['ExecutiveTitle']))
        story.append(Paragraph(
            f"<b>Project:</b> {project_name.upper()} | "
            f"<b>Generated:</b> {datetime.utcnow().strftime('%B %d, %Y - %H:%M UTC')}",
            self.styles['ExecutiveSubtitle']
        ))

        # 2. Key Metrics Grid (Value, Compliance, Status)
        story.extend(self._build_key_metrics_grid(project_data))
        story.append(Spacer(1, 0.3 * inch))

        # 3. Critical Alerts
        story.extend(self._build_alerts_section(project_data))
        
        # 4. Project Details Table
        story.extend(self._build_details_table(project_data))
        story.append(Spacer(1, 0.3 * inch))

        # 5. Document Compliance Breakdown
        story.extend(self._build_compliance_breakdown(project_data))

        # Build PDF
        doc.build(story)
        return output_path

    async def generate_compliance_summary(
        self,
        project_id: str,
        compliance_data: Dict[str, Any]
    ) -> str:
        """Generate compliance-focused summary PDF."""
        # For brevity, reuse a simpler version for the specific compliance report
        output_path = f"/tmp/compliance_summary_{project_id}.pdf"
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        story.append(Paragraph("CIDB Compliance Summary", self.styles['ExecutiveTitle']))
        score = compliance_data.get('score', 0)
        status = compliance_data.get('status', 'unknown')

        score_text = f"<b>Compliance Score:</b> {score:.1f}%<br/><b>Status:</b> {status.upper()}"
        story.append(Paragraph(score_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

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
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(gap_table)

        doc.build(story)
        return output_path

    def _build_key_metrics_grid(self, project_data: Dict[str, Any]) -> list:
        """Build a 3-column grid showing key project metrics."""
        extracted_list = project_data.get('extracted_fields', [])
        
        # Try to find a contract value across all extracted docs
        contract_value = "N/A"
        overall_confidence = "N/A"
        for ext in extracted_list:
            fields = ext.get('fields', {})
            val = fields.get('contract_value')
            if val and str(val) != "0.0":
                try:
                    contract_value = f"RM {float(val):,.2f}"
                    break
                except ValueError:
                    contract_value = str(val)
            
            conf = fields.get('_confidence_score')
            if conf:
                overall_confidence = f"{conf * 100:.0f}%"

        compliance = project_data.get('compliance_score', {})
        score = compliance.get('score', 0)
        
        # Color code the score
        score_color = '#16a34a' if score >= 80 else '#ca8a04' if score >= 50 else '#dc2626'
        
        # Create metric cells
        cell1 = [
            Paragraph("CONTRACT VALUE", self.styles['KeyMetricLabel']),
            Paragraph(contract_value, self.styles['KeyMetricValue'])
        ]
        
        cell2 = [
            Paragraph("COMPLIANCE SCORE", self.styles['KeyMetricLabel']),
            Paragraph(f"<font color='{score_color}'>{score:.1f}%</font>", self.styles['KeyMetricValue'])
        ]
        
        cell3 = [
            Paragraph("DATA CONFIDENCE", self.styles['KeyMetricLabel']),
            Paragraph(overall_confidence, self.styles['KeyMetricValue'])
        ]

        table = Table([[cell1, cell2, cell3]], colWidths=[2.1*inch, 2.1*inch, 2.1*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        return [table]

    def _build_alerts_section(self, project_data: Dict[str, Any]) -> list:
        """Highlight critical alerts or non-compliance issues."""
        elements = []
        alerts = project_data.get('alerts', [])
        
        if alerts:
            elements.append(Paragraph("CRITICAL ALERTS", self.styles['SectionHeader']))
            for alert in alerts:
                msg = alert.get('message', 'Unknown alert')
                elements.append(Paragraph(f"⚠️ {msg}", self.styles['AlertBox']))
            elements.append(Spacer(1, 0.2 * inch))
            
        return elements

    def _build_details_table(self, project_data: Dict[str, Any]) -> list:
        """Build a clean table of extracted fields."""
        elements = [Paragraph("PROJECT DETAILS", self.styles['SectionHeader'])]
        
        # Aggregate the best fields from all documents
        best_fields = {}
        for ext in project_data.get('extracted_fields', []):
            fields = ext.get('fields', {})
            for k, v in fields.items():
                if not str(k).startswith('_') and v and str(v) != "0.0":
                    if k not in best_fields or len(str(v)) > len(str(best_fields[k])):
                        best_fields[k] = v
                        
        if not best_fields:
            elements.append(Paragraph("No detailed fields extracted.", self.styles['Normal']))
            return elements

        data = []
        for key, value in best_fields.items():
            clean_key = key.replace('_', ' ').title()
            data.append([
                Paragraph(f"<b>{clean_key}</b>", self.styles['Normal']), 
                Paragraph(str(value), self.styles['Normal'])
            ])

        t = Table(data, colWidths=[2*inch, 4.3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        return elements

    def _build_compliance_breakdown(self, project_data: Dict[str, Any]) -> list:
        """Build compliance document breakdown table."""
        elements = []
        compliance = project_data.get('compliance_score', {})
        gaps = compliance.get('gaps', [])
        
        if not gaps:
            return elements
            
        elements.append(Paragraph("MISSING COMPLIANCE DOCUMENTS", self.styles['SectionHeader']))
        
        data = [['Document Type', 'Mandatory', 'Impact']]
        for gap in gaps[:5]:  # Show top 5 gaps
            data.append([
                Paragraph(gap.get('description_en', 'Unknown'), self.styles['Normal']),
                'Yes' if gap.get('mandatory') else 'No',
                'High' if gap.get('mandatory') else 'Low'
            ])
            
        t = Table(data, colWidths=[3.5*inch, 1.4*inch, 1.4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        return elements
