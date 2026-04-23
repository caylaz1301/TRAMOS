"""
Email Notification Service
Sends email alerts to operators when new tickets are created
"""

import logging
import smtplib
import asyncio
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications to operators"""
    
    def __init__(self):
        """Initialize email service from configuration"""
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.operator_emails = settings.OPERATOR_EMAILS
        self.enabled = self._verify_config()
    
    def _verify_config(self) -> bool:
        """Verify email configuration is complete"""
        required_fields = [
            self.smtp_server,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.from_email,
        ]
        
        is_valid = all(required_fields)
        
        if not is_valid:
            logger.warning("⚠️ Email notification service not fully configured. Required fields: SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL")
        elif not self.operator_emails:
            logger.warning("⚠️ No operator emails configured. Set OPERATOR_EMAILS in .env")
        
        return is_valid
    
    def send_new_ticket_notification(self, ticket_data: dict) -> bool:
        """
        Send email notification about new ticket to operators
        
        Args:
            ticket_data: Dictionary with ticket information
                {
                    'ticket_id': '123456',
                    'subject': 'GPS Not Working',
                    'user_name': 'John Driver',
                    'user_contact': '+6281234567890',
                    'category': 'GPS',
                    'priority': 'high',
                    'message': 'Problem description',
                    'created_at': '2026-02-26 10:30:00'
                }
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("📧 Email notifications disabled (not configured)")
            return False
        
        if not self.operator_emails:
            logger.warning("⚠️ No operator emails to notify")
            return False
        
        try:
            # Build email content
            subject = f"🎫 New Ticket #{ticket_data.get('ticket_id', 'N/A')} - {ticket_data.get('subject', 'No Subject')}"
            
            html_body = self._build_ticket_notification_html(ticket_data)
            text_body = self._build_ticket_notification_text(ticket_data)
            
            # Send email
            success = self._send_email(
                to_emails=self.operator_emails,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if success:
                logger.info(f"✅ Ticket notification sent to {len(self.operator_emails)} operator(s)")
            else:
                logger.error("❌ Failed to send ticket notification")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Error sending ticket notification: {str(e)}")
            return False
    
    def send_ticket_status_update(self, ticket_data: dict, status: str, operator_name: str = "") -> bool:
        """
        Send email notification about ticket status update
        
        Args:
            ticket_data: Dictionary with ticket information
            status: New status (In Progress, Resolved, etc.)
            operator_name: Name of operator who updated it
        
        Returns:
            bool: True if email sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            subject = f"🔄 Ticket #{ticket_data.get('ticket_id')} Status Update - {status}"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #0066cc;">Ticket Status Updated</h2>
                    <p><strong>Ticket ID:</strong> #{ticket_data.get('ticket_id')}</p>
                    <p><strong>Subject:</strong> {ticket_data.get('subject')}</p>
                    <p><strong>New Status:</strong> <span style="background-color: #e8f4f8; padding: 5px 10px; border-radius: 3px;">{status}</span></p>
                    <p><strong>Updated by:</strong> {operator_name}</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        TRAMOS Support System<br>
                        Please do not reply to this email.
                    </p>
                </body>
            </html>
            """
            
            text_body = f"""
            Ticket Status Updated
            
            Ticket ID: #{ticket_data.get('ticket_id')}
            Subject: {ticket_data.get('subject')}
            New Status: {status}
            Updated by: {operator_name}
            
            ---
            TRAMOS Support System
            """
            
            return self._send_email(
                to_emails=self.operator_emails,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
        
        except Exception as e:
            logger.error(f"❌ Error sending status update notification: {str(e)}")
            return False
    
    def _build_ticket_notification_html(self, ticket_data: dict) -> str:
        """Build HTML email body for new ticket notification"""
        priority_color = self._get_priority_color(ticket_data.get('priority', 'normal'))
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #0066cc; border-bottom: 3px solid #0066cc; padding-bottom: 10px;">
                        🎫 New Ticket Created
                    </h2>
                    
                    <div style="background-color: #f0f8ff; padding: 15px; border-left: 4px solid #0066cc; margin: 15px 0;">
                        <p style="margin: 0;"><strong>Ticket ID:</strong> <span style="font-size: 18px; color: #0066cc;">#{ ticket_data.get('ticket_id', 'N/A')}</span></p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px; font-weight: bold; width: 30%;">Subject</td>
                            <td style="padding: 10px;">{ticket_data.get('subject', 'N/A')}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee; background-color: #f9f9f9;">
                            <td style="padding: 10px; font-weight: bold;">User</td>
                            <td style="padding: 10px;">{ticket_data.get('user_name', 'Unknown')}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px; font-weight: bold;">Contact</td>
                            <td style="padding: 10px;">
                                <a href="https://wa.me/{ticket_data.get('user_contact', '').replace('+', '')}" style="color: #0066cc; text-decoration: none;">
                                    {ticket_data.get('user_contact', 'N/A')}
                                </a>
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee; background-color: #f9f9f9;">
                            <td style="padding: 10px; font-weight: bold;">Category</td>
                            <td style="padding: 10px;">{ticket_data.get('category', 'General')}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px; font-weight: bold;">Priority</td>
                            <td style="padding: 10px;">
                                <span style="background-color: {priority_color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">
                                    {ticket_data.get('priority', 'Normal').upper()}
                                </span>
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee; background-color: #f9f9f9;">
                            <td style="padding: 10px; font-weight: bold;">Created</td>
                            <td style="padding: 10px;">{ticket_data.get('created_at', 'N/A')}</td>
                        </tr>
                    </table>
                    
                    <div style="margin-top: 20px;">
                        <p style="font-weight: bold;">Problem Description:</p>
                        <div style="background-color: #f9f9f9; padding: 10px; border-left: 3px solid #ddd; margin: 10px 0;">
                            {ticket_data.get('message', 'No description provided')}
                        </div>
                    </div>
                    
                    <a href="{ settings.OSTICKET_BASE_URL}/tickets" style="display: inline-block; background-color: #0066cc; color: white; padding: 10px 20px; border-radius: 3px; text-decoration: none; margin-top: 15px; font-weight: bold;">
                        View in osTicket
                    </a>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0 20px; ">
                    
                    <p style="color: #666; font-size: 12px; margin: 0;">
                        <strong>TRAMOS Support System</strong><br>
                        WhatsApp-Based Issue Reporting & Analytics<br>
                        Please do not reply to this email. Use osTicket dashboard to respond to tickets.
                    </p>
                </div>
            </body>
        </html>
        """
        return html
    
    def _build_ticket_notification_text(self, ticket_data: dict) -> str:
        """Build plain text email body for new ticket notification"""
        text = f"""
        New Ticket Created
        
        Ticket ID: #{ticket_data.get('ticket_id', 'N/A')}
        Subject: {ticket_data.get('subject', 'N/A')}
        User: {ticket_data.get('user_name', 'Unknown')}
        Contact: {ticket_data.get('user_contact', 'N/A')}
        Category: {ticket_data.get('category', 'General')}
        Priority: {ticket_data.get('priority', 'Normal').upper()}
        Created: {ticket_data.get('created_at', 'N/A')}
        
        Problem Description:
        {ticket_data.get('message', 'No description provided')}
        
        ---
        View in osTicket: {settings.OSTICKET_BASE_URL}/tickets
        
        TRAMOS Support System
        WhatsApp-Based Issue Reporting & Analytics
        Please do not reply to this email.
        """
        return text.strip()
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color code for priority level"""
        colors = {
            'critical': '#ff0000',  # Red
            'high': '#ff9800',      # Orange
            'normal': '#2196f3',    # Blue
            'low': '#4caf50',       # Green
        }
        return colors.get(priority.lower(), '#2196f3')
    
    def _send_email(self, to_emails: List[str], subject: str, html_body: str, text_body: str) -> bool:
        """
        Send email using SMTP
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Attach both plain text and HTML (most clients will prefer HTML)
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # Use TLS if configured
                if settings.SMTP_USE_TLS:
                    server.starttls()
                
                # Login if credentials provided
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                # Send message
                server.sendmail(self.from_email, to_emails, msg.as_string())
            
            return True
        
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {str(e)}")
            return False


# Singleton instance
email_notification_service = EmailNotificationService()
