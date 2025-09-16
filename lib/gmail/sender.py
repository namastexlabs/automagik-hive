import os
import mimetypes
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from dataclasses import dataclass

from .auth import GmailAuthenticator
from lib.logging import logger

@dataclass
class EmailResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

class GmailSender:
    """Robust email sender using existing Gmail authentication"""

    def __init__(self, authenticator=None):
        self.authenticator = authenticator or GmailAuthenticator()
        self.service = self.authenticator.get_gmail_service()

    def send_invoice_email(self, to_email: str, po_number: str,
                          protocol: str, cliente: str, attachments: List[str]) -> EmailResult:
        """Send invoice email with ZIP attachments"""
        try:
            # Create email subject and body
            subject = f"Pedido {po_number} protocolo {protocol}"
            body = f"Segue kit referente ao protocolo {protocol} e cliente {cliente}"

            logger.info(f"📧 Sending email to: {to_email}")
            logger.info(f"📋 Subject: {subject}")
            logger.info(f"📎 Attachments: {len(attachments)} files")

            # Use robust email sending method
            result = self.send_email_with_attachments(
                to=to_email,
                subject=subject,
                message=body,
                attachment_paths=attachments,
                content_type="text/plain"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Failed to send invoice email: {str(e)}")
            return EmailResult(success=False, error=str(e))

    def send_email_with_attachments(self, to: str, subject: str, message: str,
                                  attachment_paths: List[str], content_type: str = "text/plain",
                                  cc: Optional[List[str]] = None) -> EmailResult:
        """Robust email sending with multiple attachments"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['to'] = to
            msg['subject'] = subject

            if cc:
                msg['cc'] = ', '.join(cc)

            # Add body
            msg.attach(MIMEText(message, content_type.split('/')[-1]))

            # Add attachments
            for file_path in attachment_paths:
                if not os.path.exists(file_path):
                    logger.warning(f"⚠️ Attachment not found: {file_path}")
                    continue

                self._attach_file(msg, file_path)

            # Send email
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            message_id = result.get('id')
            logger.info(f"✅ Email sent successfully! Message ID: {message_id}")

            return EmailResult(success=True, message_id=message_id)

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return EmailResult(success=False, error=str(e))

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> None:
        """Attach file to email message"""
        try:
            # Guess the content type based on the file's extension
            ctype, encoding = mimetypes.guess_type(file_path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'

            main_type, sub_type = ctype.split('/', 1)

            with open(file_path, 'rb') as fp:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(fp.read())

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(attachment)

            # Add header as key/value pair to attachment part
            filename = os.path.basename(file_path)
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=filename
            )

            msg.attach(attachment)
            logger.debug(f"📎 Attached file: {filename} ({ctype})")

        except Exception as e:
            logger.error(f"❌ Failed to attach file {file_path}: {str(e)}")
            raise