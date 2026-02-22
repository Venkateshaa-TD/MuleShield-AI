"""
MuleShield AI - Email Service
Sends SAR reports via email with PDF attachments

Features:
- SMTP email sending
- PDF attachment support
- Multiple recipients
- Professional email templates
- Error handling and logging
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, List, Optional
from datetime import datetime
import os


class EmailService:
    """
    Email service for sending SAR reports.
    
    Supports:
    - SMTP with TLS
    - Gmail, Outlook, and custom SMTP servers
    - PDF attachments
    - HTML formatted emails
    """
    
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        sender_email: str = None,
        sender_password: str = None
    ):
        """
        Initialize email service.
        
        Args:
            smtp_server: SMTP server address (default from env)
            smtp_port: SMTP port (default 587 for TLS)
            sender_email: Sender email address
            sender_password: Sender email password/app password
        """
        # Try environment variables first, then fall back to parameters
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", "")
        self.sender_password = sender_password or os.getenv("SENDER_PASSWORD", "")
        
        # Institution details
        self.institution_name = "INDIAN OVERSEAS BANK"
        self.department = "AML Compliance Department"
    
    def configure(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str
    ) -> None:
        """
        Configure email settings at runtime.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            sender_email: Sender email address
            sender_password: Sender email password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_sar_report(
        self,
        recipient_emails: List[str],
        report_data: Dict,
        pdf_attachment: bytes = None,
        cc_emails: List[str] = None,
        custom_message: str = None
    ) -> Dict:
        """
        Send SAR report via email.
        
        Args:
            recipient_emails: List of recipient email addresses
            report_data: SAR report data dictionary
            pdf_attachment: PDF file as bytes (optional)
            cc_emails: List of CC email addresses (optional)
            custom_message: Custom message to include (optional)
            
        Returns:
            Result dictionary with status and details
        """
        if not self.sender_email or not self.sender_password:
            return {
                "success": False,
                "error": "Email credentials not configured. Please configure SMTP settings.",
                "details": "Set SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, and SENDER_PASSWORD environment variables or configure via API."
            }
        
        if not recipient_emails:
            return {
                "success": False,
                "error": "No recipient email addresses provided"
            }
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._generate_subject(report_data)
            msg["From"] = f"{self.department} <{self.sender_email}>"
            msg["To"] = ", ".join(recipient_emails)
            
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            
            # Generate email body
            text_body = self._generate_text_body(report_data, custom_message)
            html_body = self._generate_html_body(report_data, custom_message)
            
            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Attach PDF if provided
            if pdf_attachment:
                report_number = report_data.get("report_number", "SAR-Report")
                pdf_filename = f"{report_number}.pdf"
                
                pdf_part = MIMEApplication(pdf_attachment, _subtype="pdf")
                pdf_part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=pdf_filename
                )
                msg.attach(pdf_part)
            
            # Send email
            all_recipients = recipient_emails + (cc_emails or [])
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    all_recipients,
                    msg.as_string()
                )
            
            return {
                "success": True,
                "message": f"SAR report sent successfully to {len(recipient_emails)} recipient(s)",
                "recipients": recipient_emails,
                "cc": cc_emails,
                "report_number": report_data.get("report_number"),
                "sent_at": datetime.now().isoformat(),
                "has_attachment": pdf_attachment is not None
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "SMTP authentication failed. Please check email credentials.",
                "details": "For Gmail, use an App Password instead of your regular password."
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}",
                "details": "Please verify SMTP server settings and try again."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }
    
    def _generate_subject(self, report_data: Dict) -> str:
        """Generate email subject line."""
        report_number = report_data.get("report_number", "N/A")
        risk_category = report_data.get("risk_assessment", {}).get("risk_category", "unknown").upper()
        account_name = report_data.get("subject_information", {}).get("account_holder_name", "Unknown")
        
        return f"[{risk_category}] SAR Report {report_number} - {account_name} | {self.institution_name}"
    
    def _generate_text_body(self, report_data: Dict, custom_message: str = None) -> str:
        """Generate plain text email body."""
        subject = report_data.get("subject_information", {})
        risk = report_data.get("risk_assessment", {})
        rec = report_data.get("recommendation", {})
        
        body = f"""
{self.institution_name}
{self.department}
MuleShield AI - Suspicious Activity Report
{'=' * 60}

Report Number: {report_data.get('report_number', 'N/A')}
Generated: {report_data.get('generated_at', 'N/A')}
Status: {report_data.get('status', 'draft').upper()}

SUBJECT INFORMATION
-------------------
Account Holder: {subject.get('account_holder_name', 'N/A')}
Account Number: {subject.get('account_number', 'N/A')}
Account Type: {subject.get('account_type', 'N/A')}

RISK ASSESSMENT
---------------
Composite Risk Score: {risk.get('composite_risk_score', 0):.1f}/100
Risk Category: {risk.get('risk_category', 'N/A').upper()}
Mule Probability: {risk.get('mule_probability', 0):.1%}
AI Confidence: {risk.get('confidence_score', 0):.1%}

RECOMMENDATION
--------------
Action: {rec.get('recommended_action', 'N/A').upper()}
Priority: {rec.get('priority', 'N/A').upper()}
Justification: {rec.get('justification', 'N/A')}

"""
        if custom_message:
            body += f"""
ADDITIONAL NOTES
----------------
{custom_message}

"""
        
        body += f"""
{'=' * 60}
This is an automated report generated by MuleShield AI.
For questions, contact the AML Compliance Department.

CONFIDENTIAL - FOR AUTHORIZED USE ONLY
This email and any attachments are confidential and intended 
solely for the addressee(s). If you are not the intended 
recipient, please notify the sender immediately.
"""
        
        return body
    
    def _generate_html_body(self, report_data: Dict, custom_message: str = None) -> str:
        """Generate HTML email body."""
        subject = report_data.get("subject_information", {})
        risk = report_data.get("risk_assessment", {})
        rec = report_data.get("recommendation", {})
        
        score = risk.get("composite_risk_score", 0)
        risk_color = "#c53030" if score >= 70 else "#dd6b20" if score >= 40 else "#38a169"
        risk_bg = "#fef5f5" if score >= 70 else "#fffaf0" if score >= 40 else "#f0fff4"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #2d3748; margin: 0; padding: 20px; background: #f7fafc; }}
        .container {{ max-width: 650px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #1a365d 0%, #2d3748 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 22px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.9; font-size: 14px; }}
        .alert-banner {{ background: {risk_bg}; border-left: 4px solid {risk_color}; padding: 15px 20px; }}
        .alert-banner .score {{ font-size: 28px; font-weight: bold; color: {risk_color}; }}
        .alert-banner .label {{ color: #718096; font-size: 12px; text-transform: uppercase; }}
        .content {{ padding: 25px; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 14px; font-weight: bold; color: #1a365d; border-bottom: 2px solid #e53e3e; padding-bottom: 5px; margin-bottom: 15px; text-transform: uppercase; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .info-item {{ padding: 8px 12px; background: #f7fafc; border-radius: 4px; }}
        .info-item .label {{ font-size: 11px; color: #718096; text-transform: uppercase; }}
        .info-item .value {{ font-size: 14px; color: #2d3748; font-weight: 500; }}
        .recommendation {{ background: #f0f9ff; border-radius: 6px; padding: 15px; }}
        .recommendation .action {{ font-size: 18px; font-weight: bold; color: #2b6cb0; }}
        .footer {{ background: #f7fafc; padding: 20px; text-align: center; font-size: 11px; color: #718096; border-radius: 0 0 8px 8px; }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; }}
        .badge-critical {{ background: #fed7d7; color: #c53030; }}
        .badge-high {{ background: #feebc8; color: #c05621; }}
        .badge-medium {{ background: #fefcbf; color: #975a16; }}
        .badge-low {{ background: #c6f6d5; color: #276749; }}
        .custom-message {{ background: #fffaf0; border: 1px solid #fbd38d; border-radius: 6px; padding: 15px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ {self.institution_name}</h1>
            <p>Suspicious Activity Report (SAR) - MuleShield AI</p>
        </div>
        
        <div class="alert-banner">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="label">Risk Score</div>
                    <div class="score">{score:.1f}/100</div>
                </div>
                <div style="text-align: right;">
                    <span class="badge badge-{'critical' if score >= 70 else 'high' if score >= 50 else 'medium' if score >= 30 else 'low'}">{risk.get('risk_category', 'N/A').upper()}</span>
                    <div style="margin-top: 5px; font-size: 12px; color: #718096;">
                        Report: {report_data.get('report_number', 'N/A')}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-title">Subject Information</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="label">Account Holder</div>
                        <div class="value">{subject.get('account_holder_name', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Account Number</div>
                        <div class="value">{subject.get('account_number', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Account Type</div>
                        <div class="value">{subject.get('account_type', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Location</div>
                        <div class="value">{subject.get('city', 'N/A')}, {subject.get('country', 'N/A')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Risk Assessment</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="label">Mule Probability</div>
                        <div class="value">{risk.get('mule_probability', 0):.1%}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">AI Confidence</div>
                        <div class="value">{risk.get('confidence_score', 0):.1%}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Recommendation</div>
                <div class="recommendation">
                    <div class="action">📋 {rec.get('recommended_action', 'REVIEW').upper()}</div>
                    <div style="margin-top: 8px; font-size: 13px;">
                        <strong>Priority:</strong> {rec.get('priority', 'N/A').upper()}<br>
                        <strong>Justification:</strong> {rec.get('justification', 'Based on automated analysis.')}
                    </div>
                </div>
            </div>
            
            {'<div class="custom-message"><strong>📝 Additional Notes:</strong><br>' + custom_message + '</div>' if custom_message else ''}
            
            <div style="margin-top: 25px; padding: 15px; background: #edf2f7; border-radius: 6px; font-size: 12px;">
                📎 <strong>Full SAR report attached as PDF</strong> - Please review the complete report for detailed analysis.
            </div>
        </div>
        
        <div class="footer">
            <strong>CONFIDENTIAL - FOR AUTHORIZED USE ONLY</strong><br>
            This email was generated automatically by MuleShield AI Anti-Money Laundering Detection System.<br>
            Generated: {report_data.get('generated_at', 'N/A')}<br><br>
            If you received this email in error, please delete it and notify the sender immediately.
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def test_connection(self) -> Dict:
        """
        Test SMTP connection without sending an email.
        
        Returns:
            Dictionary with connection test results
        """
        if not self.smtp_server or not self.sender_email:
            return {
                "success": False,
                "error": "SMTP settings not configured"
            }
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                
            return {
                "success": True,
                "message": "SMTP connection successful",
                "server": self.smtp_server,
                "port": self.smtp_port,
                "sender": self.sender_email
            }
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed",
                "details": "Please check your email credentials. For Gmail, use an App Password."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def create_email_service() -> EmailService:
    """Factory function to create email service instance."""
    return EmailService()
