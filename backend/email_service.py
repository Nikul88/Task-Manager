"""
email_service.py – SMTP email sender for OTP verification emails.
Uses Python's built-in smtplib with TLS (Gmail App Password).
"""
import os
import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Team Task Manager")
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))


def generate_otp() -> str:
    """Generate a secure 6-digit OTP."""
    return str(random.randint(100000, 999999))


def get_otp_expiry() -> datetime:
    """Return OTP expiry datetime (UTC)."""
    return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)


def _build_otp_html(name: str, otp: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8"/>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 0; }}
        .container {{ max-width: 520px; margin: 40px auto; background: #fff; border-radius: 16px;
                     box-shadow: 0 4px 24px rgba(99,102,241,0.10); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 36px 32px 24px; }}
        .header h1 {{ color: #fff; margin: 0; font-size: 24px; font-weight: 700; }}
        .header p {{ color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 14px; }}
        .body {{ padding: 32px; }}
        .body p {{ color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 16px; }}
        .otp-box {{ background: #f0f0ff; border: 2px dashed #6366f1; border-radius: 12px;
                   text-align: center; padding: 20px; margin: 24px 0; }}
        .otp-code {{ font-size: 40px; font-weight: 800; color: #6366f1; letter-spacing: 10px; }}
        .expire {{ font-size: 13px; color: #6b7280; margin-top: 8px; }}
        .footer {{ background: #f9fafb; padding: 20px 32px; text-align: center;
                   font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>✅ Verify Your Email</h1>
          <p>Team Task Manager — Secure Authentication</p>
        </div>
        <div class="body">
          <p>Hi <strong>{name}</strong>,</p>
          <p>Thank you for signing up! Use the OTP below to verify your email address and activate your account.</p>
          <div class="otp-box">
            <div class="otp-code">{otp}</div>
            <div class="expire">⏱ Expires in {OTP_EXPIRE_MINUTES} minutes</div>
          </div>
          <p>If you did not request this, please ignore this email. Your account will not be activated.</p>
        </div>
        <div class="footer">© 2025 Team Task Manager. All rights reserved.</div>
      </div>
    </body>
    </html>
    """


def send_otp_email(to_email: str, name: str, otp: str) -> bool:
    """
    Send OTP verification email via SMTP.
    Returns True on success, False on failure.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your OTP Code: {otp} — Team Task Manager"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        msg["To"] = to_email

        # Plain text fallback
        text_part = MIMEText(
            f"Hi {name},\n\nYour OTP code is: {otp}\nIt expires in {OTP_EXPIRE_MINUTES} minutes.\n\nTeam Task Manager",
            "plain",
        )
        html_part = MIMEText(_build_otp_html(name, otp), "html")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP to {to_email}: {e}")
        return False
