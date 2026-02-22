"""
MuleShield AI - SAR PDF Generator
Generates professional PDF reports for Suspicious Activity Reports (SAR)

Features:
- Professional FinCEN-style formatting
- Risk assessment visualization
- Transaction summaries
- Network analysis results
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
import os

# PDF Generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class SARPDFGenerator:
    """
    Generates professional PDF reports for SAR filings.
    
    Reports follow FinCEN-inspired format with:
    - Institution header
    - Subject information
    - Risk assessment breakdown
    - Transaction analysis
    - Network analysis
    - AI reasoning
    """
    
    def __init__(self):
        self.institution_name = "INDIAN OVERSEAS BANK"
        self.institution_id = "IOB-AML-2024"
        
    def generate_pdf(self, report_data: Dict) -> bytes:
        """
        Generate PDF from SAR report data.
        
        Args:
            report_data: Complete SAR report dictionary
            
        Returns:
            PDF as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )
        
        # Build document elements
        elements = []
        styles = self._get_styles()
        
        # Header
        elements.extend(self._build_header(report_data, styles))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Subject Information
        elements.extend(self._build_subject_section(report_data, styles))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Risk Assessment
        elements.extend(self._build_risk_section(report_data, styles))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Suspicious Activity Description
        elements.extend(self._build_activity_section(report_data, styles))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Transaction Analysis
        elements.extend(self._build_transaction_section(report_data, styles))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Network Analysis (if available)
        if report_data.get("network_analysis"):
            elements.extend(self._build_network_section(report_data, styles))
            elements.append(Spacer(1, 0.2 * inch))
        
        # Recommendation
        elements.extend(self._build_recommendation_section(report_data, styles))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Footer
        elements.extend(self._build_footer(report_data, styles))
        
        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _get_styles(self):
        """Get custom styles for PDF elements."""
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a365d'),
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceBefore=12,
            spaceAfter=6,
            borderColor=colors.HexColor('#e53e3e'),
            borderWidth=2,
            borderPadding=4
        ))
        
        styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#718096'),
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='FieldValue',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2d3748')
        ))
        
        styles.add(ParagraphStyle(
            name='RiskHigh',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#c53030'),
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='RiskMedium',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#dd6b20'),
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='RiskLow',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#38a169'),
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='AIReasoning',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_JUSTIFY,
            leading=12
        ))
        
        return styles
    
    def _build_header(self, report_data: Dict, styles) -> List:
        """Build report header section."""
        elements = []
        
        # Institution banner
        elements.append(Paragraph(
            f"<b>{self.institution_name}</b>",
            styles['ReportTitle']
        ))
        elements.append(Paragraph(
            "SUSPICIOUS ACTIVITY REPORT (SAR)",
            styles['ReportTitle']
        ))
        elements.append(Paragraph(
            "MuleShield AI - Automated AML Detection System",
            styles['ReportSubtitle']
        ))
        
        # Horizontal line
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor('#e53e3e'),
            spaceBefore=6,
            spaceAfter=6
        ))
        
        # Report metadata table
        report_number = report_data.get("report_number", "N/A")
        generated_at = report_data.get("generated_at", datetime.now().isoformat())
        status = report_data.get("status", "draft").upper()
        
        meta_data = [
            ["Report Number:", report_number, "Generated:", self._format_datetime(generated_at)],
            ["Status:", status, "Generated By:", report_data.get("generated_by", "MuleShield AI")],
            ["Case ID:", report_data.get("case_id") or "Not Assigned", "Institution ID:", self.institution_id]
        ]
        
        meta_table = Table(meta_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#718096')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#718096')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(meta_table)
        
        return elements
    
    def _build_subject_section(self, report_data: Dict, styles) -> List:
        """Build subject information section."""
        elements = []
        
        elements.append(Paragraph("SECTION 1: SUBJECT INFORMATION", styles['SectionHeader']))
        
        subject = report_data.get("subject_information", {})
        
        # Build info table
        data = [
            ["Account ID:", subject.get("account_id", "N/A"), "Account Number:", subject.get("account_number", "N/A")],
            ["Account Holder:", subject.get("account_holder_name", "N/A"), "Account Type:", subject.get("account_type", "N/A")],
            ["Email:", subject.get("email", "N/A"), "Phone:", subject.get("phone", "N/A")],
            ["Location:", f"{subject.get('city', 'N/A')}, {subject.get('country', 'N/A')}", "KYC Status:", subject.get("kyc_status", "N/A")],
            ["Account Opened:", self._format_datetime(subject.get("account_opened")), "Current Status:", subject.get("current_status", "N/A")]
        ]
        
        info_table = Table(data, colWidths=[1.3*inch, 2*inch, 1.3*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#718096')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#718096')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(info_table)
        
        return elements
    
    def _build_risk_section(self, report_data: Dict, styles) -> List:
        """Build risk assessment section."""
        elements = []
        
        elements.append(Paragraph("SECTION 2: RISK ASSESSMENT", styles['SectionHeader']))
        
        risk = report_data.get("risk_assessment", {})
        score = risk.get("composite_risk_score", 0)
        category = risk.get("risk_category", "unknown").upper()
        mule_prob = risk.get("mule_probability", 0)
        confidence = risk.get("confidence_score", 0)
        
        # Risk category color
        if score >= 70:
            risk_style = styles['RiskHigh']
            risk_color = colors.HexColor('#c53030')
        elif score >= 40:
            risk_style = styles['RiskMedium']
            risk_color = colors.HexColor('#dd6b20')
        else:
            risk_style = styles['RiskLow']
            risk_color = colors.HexColor('#38a169')
        
        # Summary table
        summary_data = [
            ["COMPOSITE RISK SCORE:", f"{score:.1f}/100", "RISK CATEGORY:", category],
            ["Mule Probability:", f"{mule_prob:.1%}", "AI Confidence:", f"{confidence:.1%}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (1, 0), (1, 0), risk_color),
            ('TEXTCOLOR', (3, 0), (3, 0), risk_color),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fef5f5') if score >= 70 else colors.HexColor('#fffaf0') if score >= 40 else colors.HexColor('#f0fff4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.1 * inch))
        
        # Component scores table
        elements.append(Paragraph("<b>Risk Component Breakdown:</b>", styles['FieldValue']))
        elements.append(Spacer(1, 0.05 * inch))
        
        components = risk.get("component_scores", {})
        component_data = [
            ["Component", "Score", "Weight", "Contribution"],
            ["Transaction Velocity", f"{components.get('transaction_velocity', 0):.1f}", "18%", self._get_score_bar(components.get('transaction_velocity', 0))],
            ["Beneficiary Diversity", f"{components.get('beneficiary_diversity', 0):.1f}", "15%", self._get_score_bar(components.get('beneficiary_diversity', 0))],
            ["Account Age Risk", f"{components.get('account_age', 0):.1f}", "12%", self._get_score_bar(components.get('account_age', 0))],
            ["Device Reuse Risk", f"{components.get('device_reuse', 0):.1f}", "20%", self._get_score_bar(components.get('device_reuse', 0))],
            ["Graph Centrality", f"{components.get('graph_centrality', 0):.1f}", "20%", self._get_score_bar(components.get('graph_centrality', 0))],
            ["Behavior Deviation", f"{components.get('behavior_deviation', 0):.1f}", "15%", self._get_score_bar(components.get('behavior_deviation', 0))]
        ]
        
        component_table = Table(component_data, colWidths=[2*inch, 0.8*inch, 0.7*inch, 2.5*inch])
        component_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')])
        ]))
        
        elements.append(component_table)
        
        return elements
    
    def _build_activity_section(self, report_data: Dict, styles) -> List:
        """Build suspicious activity description section."""
        elements = []
        
        elements.append(Paragraph("SECTION 3: SUSPICIOUS ACTIVITY DESCRIPTION", styles['SectionHeader']))
        
        activity = report_data.get("suspicious_activity", {})
        
        # Summary
        summary = activity.get("summary", "No summary available.")
        elements.append(Paragraph(f"<b>Summary:</b> {summary}", styles['AIReasoning']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Identified patterns
        patterns = activity.get("identified_patterns", [])
        if patterns:
            elements.append(Paragraph("<b>Identified Suspicious Patterns:</b>", styles['FieldValue']))
            
            pattern_data = [["Pattern Type", "Severity", "Description", "Score"]]
            for p in patterns[:6]:  # Limit to 6 patterns
                pattern_data.append([
                    p.get("pattern_type", "").replace("_", " ").title(),
                    p.get("severity", "").upper(),
                    p.get("description", "")[:50] + "..." if len(p.get("description", "")) > 50 else p.get("description", ""),
                    f"{p.get('indicator_score', 0):.0f}"
                ])
            
            pattern_table = Table(pattern_data, colWidths=[1.5*inch, 0.8*inch, 3*inch, 0.6*inch])
            pattern_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#742a2a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            
            elements.append(pattern_table)
            elements.append(Spacer(1, 0.1 * inch))
        
        # AI Reasoning
        ai_reasoning = activity.get("ai_reasoning", [])
        if ai_reasoning:
            elements.append(Paragraph("<b>AI Analysis Reasoning:</b>", styles['FieldValue']))
            # Handle both list and dict formats
            if isinstance(ai_reasoning, list):
                for reason in ai_reasoning[:6]:  # Limit to 6 reasons
                    elements.append(Paragraph(f"• {reason}", styles['AIReasoning']))
            elif isinstance(ai_reasoning, dict):
                reasoning_text = ai_reasoning.get("detailed_analysis", "No detailed analysis available.")
                elements.append(Paragraph(reasoning_text, styles['AIReasoning']))
        
        return elements
    
    def _build_transaction_section(self, report_data: Dict, styles) -> List:
        """Build transaction analysis section."""
        elements = []
        
        elements.append(Paragraph("SECTION 4: TRANSACTION ANALYSIS", styles['SectionHeader']))
        
        txn = report_data.get("transaction_analysis", {})
        
        # Summary stats table
        stats_data = [
            ["Total Transactions:", str(txn.get("transaction_count", 0)), "Suspicious Count:", str(txn.get("suspicious_transaction_count", 0))],
            ["Incoming:", f"₹{txn.get('total_incoming_amount', 0):,.2f}", "Outgoing:", f"₹{txn.get('total_outgoing_amount', 0):,.2f}"],
            ["Net Flow:", f"₹{txn.get('net_flow', 0):,.2f}", "Avg Amount:", f"₹{txn.get('average_transaction_amount', 0):,.2f}"],
            ["Unique Counterparties:", str(txn.get("unique_counterparties", 0)), "Analysis Period:", self._format_date_range(txn.get("period_start"), txn.get("period_end"))]
        ]
        
        stats_table = Table(stats_data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.8*inch])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#718096')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#718096')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 0.1 * inch))
        
        # Sample transactions
        samples = txn.get("sample_transactions", [])
        if samples:
            elements.append(Paragraph("<b>Highest Value Transactions:</b>", styles['FieldValue']))
            
            sample_data = [["Type", "Amount", "Date", "Suspicious", "Reason"]]
            for s in samples[:5]:
                sample_data.append([
                    s.get("type", "").upper(),
                    f"₹{s.get('amount', 0):,.2f}",
                    self._format_datetime(s.get("timestamp"))[:10] if s.get("timestamp") else "N/A",
                    "Yes" if s.get("is_suspicious") else "No",
                    (s.get("suspicious_reason") or "")[:30]
                ])
            
            sample_table = Table(sample_data, colWidths=[0.8*inch, 1.2*inch, 1*inch, 0.8*inch, 2.5*inch])
            sample_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(sample_table)
        
        return elements
    
    def _build_network_section(self, report_data: Dict, styles) -> List:
        """Build network analysis section."""
        elements = []
        
        elements.append(Paragraph("SECTION 5: NETWORK ANALYSIS", styles['SectionHeader']))
        
        network = report_data.get("network_analysis", {})
        
        # Network stats
        stats_data = [
            ["Connected Accounts:", str(len(network.get("connected_accounts", []))), "Cluster ID:", network.get("cluster_id", "N/A")],
            ["Network Centrality:", f"{network.get('centrality_score', 0):.3f}", "PageRank:", f"{network.get('pagerank_score', 0):.4f}"],
            ["Is Hub Account:", "Yes" if network.get("is_hub_account") else "No", "Circular Flows:", str(len(network.get("circular_flow_involvement", [])))]
        ]
        
        stats_table = Table(stats_data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.8*inch])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bee3f8')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    def _build_recommendation_section(self, report_data: Dict, styles) -> List:
        """Build recommendation section."""
        elements = []
        
        elements.append(Paragraph("SECTION 6: RECOMMENDATION", styles['SectionHeader']))
        
        rec = report_data.get("recommendation", {})
        risk = report_data.get("risk_assessment", {})
        
        action = rec.get("recommended_action", "review").upper()
        priority = rec.get("priority", "medium").upper()
        confidence = risk.get("confidence_score", 0)
        
        # Action and priority with color coding
        action_color = colors.HexColor('#c53030') if action in ['FILE_SAR', 'CLOSE_ACCOUNT', 'IMMEDIATE_REVIEW'] else colors.HexColor('#dd6b20') if action in ['ENHANCED_MONITORING', 'RESTRICT', 'URGENT_INVESTIGATION'] else colors.HexColor('#38a169')
        
        rec_text = f"""
        <b>Recommended Action:</b> <font color="{action_color}">{action}</font><br/>
        <b>Priority:</b> {priority}<br/>
        <b>AI Confidence:</b> {confidence:.0%}<br/><br/>
        <b>Description:</b> {rec.get('description', 'Based on automated analysis.')}
        """
        
        elements.append(Paragraph(rec_text, styles['AIReasoning']))
        
        # Suggested actions - check both possible keys
        actions = rec.get("suggested_actions", []) or rec.get("suggested_next_steps", [])
        if actions:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("<b>Suggested Investigation Steps:</b>", styles['FieldValue']))
            for i, action_item in enumerate(actions[:5], 1):
                elements.append(Paragraph(f"{i}. {action_item}", styles['AIReasoning']))
        
        return elements
    
    def _build_footer(self, report_data: Dict, styles) -> List:
        """Build report footer."""
        elements = []
        
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceBefore=12,
            spaceAfter=6
        ))
        
        footer_text = f"""
        <b>CONFIDENTIAL - FOR AUTHORIZED USE ONLY</b><br/>
        This report was generated by MuleShield AI Anti-Money Laundering Detection System.<br/>
        Report ID: {report_data.get('id', 'N/A')} | Generated: {self._format_datetime(report_data.get('generated_at'))}<br/>
        Institution: {self.institution_name} | System Version: {report_data.get('generated_by', 'MuleShield AI v1.0')}
        """
        
        elements.append(Paragraph(footer_text, ParagraphStyle(
            name='Footer',
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER
        )))
        
        return elements
    
    def _format_datetime(self, dt_str: Optional[str]) -> str:
        """Format datetime string for display."""
        if not dt_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", ""))
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return str(dt_str)[:16] if dt_str else "N/A"
    
    def _format_date_range(self, start: Optional[str], end: Optional[str]) -> str:
        """Format date range for display."""
        start_str = self._format_datetime(start)[:10] if start else "N/A"
        end_str = self._format_datetime(end)[:10] if end else "N/A"
        return f"{start_str} to {end_str}"
    
    def _get_score_bar(self, score: float) -> str:
        """Generate text-based score visualization."""
        filled = int(score / 10)
        empty = 10 - filled
        if score >= 70:
            return "█" * filled + "░" * empty + f" {score:.0f}%"
        elif score >= 40:
            return "▓" * filled + "░" * empty + f" {score:.0f}%"
        else:
            return "▒" * filled + "░" * empty + f" {score:.0f}%"


def create_pdf_generator() -> SARPDFGenerator:
    """Factory function to create PDF generator instance."""
    return SARPDFGenerator()
