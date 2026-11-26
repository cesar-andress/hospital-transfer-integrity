"""Outbound mail helpers (MailHog in local compose)."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
FROM_EMAIL = "no-reply@saas-eu-transfer.local"


def send_transfer_email(
    recipient_email: str,
    sender_email: str,
    file_name: str,
    download_url: str,
    otp_code: str,
):
    """Send download link + OTP code to the transfer recipient."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Secure file received: {file_name}"
    msg["From"] = FROM_EMAIL
    msg["To"] = recipient_email

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #18181b;">
        <h2>Secure Transfer (EU-hosted demo)</h2>
        <p><strong>{sender_email}</strong> sent you the file: <code>{file_name}</code></p>
        <p>
          <a href="{download_url}"
             style="background-color: #be123c; color: white; padding: 10px 18px;
                    text-decoration: none; border-radius: 6px; display: inline-block;">
            Download file
          </a>
        </p>
        <p>Your <strong>OTP</strong> verification code is:</p>
        <p style="font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #be123c;">
          {otp_code}
        </p>
        <hr/>
        <small>This link and code expire in 24 hours. GDPR-oriented demo trail.</small>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, recipient_email, msg.as_string())
    except Exception as exc:
        print(f"SMTP send error (MailHog): {exc}")
