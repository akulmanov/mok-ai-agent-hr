import logging
import os
from typing import Optional, Dict
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to candidates."""
    
    def __init__(self):
        # Use Mailpit in development if no SMTP credentials provided
        use_mailpit = os.getenv("USE_MAILPIT", "true").lower() == "true"
        has_smtp_creds = os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD")
        
        if use_mailpit and not has_smtp_creds:
            # Use Mailpit for development
            self.smtp_host = os.getenv("SMTP_HOST", "mailpit")
            self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
            self.smtp_user = None
            self.smtp_password = None
            self.from_email = os.getenv("SMTP_FROM_EMAIL", "hr-screening@example.com")
            self.use_tls = False
            logger.info("Using Mailpit for email testing (SMTP_HOST=mailpit, PORT=1025)")
        else:
            # Use configured SMTP
            self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_user = os.getenv("SMTP_USER")
            self.smtp_password = os.getenv("SMTP_PASSWORD")
            self.from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
            self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    async def send_review_result(
        self,
        to_email: str,
        candidate_name: Optional[str],
        subject: str,
        body: str
    ) -> bool:
        """
        Send review result email to candidate.
        
        Args:
            to_email: Recipient email address
            candidate_name: Name of candidate (optional)
            subject: Email subject
            body: Email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Mailpit doesn't require authentication
        if self.smtp_user is None and self.smtp_password is None:
            # Using Mailpit, no auth needed
            pass
        elif not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending disabled.")
            return False
        
        if not to_email:
            logger.warning("No email address provided")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add body
            text_part = MIMEText(body, "plain", "utf-8")
            message.attach(text_part)
            
            # Send email
            send_kwargs = {
                "hostname": self.smtp_host,
                "port": self.smtp_port,
                "use_tls": self.use_tls,
            }
            
            # Only add auth if credentials are provided (not using Mailpit)
            if self.smtp_user and self.smtp_password:
                send_kwargs["username"] = self.smtp_user
                send_kwargs["password"] = self.smtp_password
            
            await aiosmtplib.send(message, **send_kwargs)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def get_available_channels(self, candidate_profile: Dict) -> Dict[str, Optional[str]]:
        """
        Get available communication channels for a candidate.
        
        Returns:
            Dict with channel names and values (or None if not available)
        """
        profile = candidate_profile.get("structured_profile", {}) if isinstance(candidate_profile, dict) else candidate_profile
        
        return {
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "telegram": profile.get("telegram"),
            "whatsapp": profile.get("whatsapp")
        }
