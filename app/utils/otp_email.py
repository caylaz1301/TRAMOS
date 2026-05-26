"""
OTP Email Sender for Dashboard Authentication
Uses existing SMTP config to send verification codes
"""

import logging
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


def generate_otp(length=6) -> str:
    """Generate a random numeric OTP code"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(to_email: str, otp_code: str, user_name: str = "") -> bool:
    """Send OTP verification email using SMTP config from .env"""
    
    subject = f"TRAMOS — Kode Verifikasi: {otp_code}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Inter', -apple-system, sans-serif; background: #f1f5f9; margin: 0; padding: 40px 20px; }}
            .container {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }}
            .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 32px 32px 24px; text-align: center; }}
            .header h1 {{ color: #ffffff; font-size: 28px; margin: 0; letter-spacing: 4px; font-weight: 800; }}
            .body {{ padding: 32px; }}
            .greeting {{ font-size: 16px; color: #334155; margin-bottom: 16px; }}
            .message {{ font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 24px; }}
            .otp-box {{ background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; }}
            .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #1e293b; font-family: 'SF Mono', 'Fira Code', monospace; }}
            .expiry {{ font-size: 12px; color: #94a3b8; margin-top: 8px; }}
            .warning {{ font-size: 12px; color: #94a3b8; line-height: 1.5; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
            .footer {{ background: #f8fafc; padding: 16px 32px; text-align: center; font-size: 11px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TRAMOS</h1>
            </div>
            <div class="body">
                <div class="greeting">Halo{' ' + user_name if user_name else ''},</div>
                <div class="message">
                    Gunakan kode verifikasi berikut untuk menyelesaikan pendaftaran akun TRAMOS Dashboard kamu.
                </div>
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                    <div class="expiry">Berlaku selama 10 menit</div>
                </div>
                <div class="warning">
                    Jika kamu tidak mendaftar di TRAMOS, abaikan email ini. 
                    Jangan berikan kode ini kepada siapapun.
                </div>
            </div>
            <div class="footer">
                &copy; 2026 TRAMOS AI Support System
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        
        # Plain text fallback
        plain_text = f"TRAMOS — Kode Verifikasi\n\nHalo {user_name},\n\nKode OTP kamu: {otp_code}\n\nBerlaku 10 menit.\n\nJika kamu tidak mendaftar, abaikan email ini."
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"OTP email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        return False
