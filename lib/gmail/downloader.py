"""
Gmail Downloader Module

Handles email fetching and Excel attachment downloading from Gmail.
"""

import os
import base64
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from pathlib import Path

from googleapiclient.errors import HttpError

from lib.logging import logger
from .auth import GmailAuthenticator


class GmailDownloader:
    """Gmail email and attachment downloader"""
    
    def __init__(self, authenticator: Optional[GmailAuthenticator] = None):
        """Initialize downloader with Gmail service"""
        self.authenticator = authenticator or GmailAuthenticator()
        self.gmail_service = self.authenticator.get_gmail_service()
        self.download_dir = "mctech/sheets"
    
    def _filter_excel_attachments(self, parts: List[Dict]) -> List[Dict]:
        """Filter message parts to only Excel attachments"""
        excel_extensions = ('.xlsx', '.xlsb', '.xls')
        excel_parts = []
        
        for part in parts:
            filename = part.get('filename', '')
            if filename and filename.lower().endswith(excel_extensions):
                if part.get('body', {}).get('attachmentId'):
                    excel_parts.append(part)
                    logger.debug(f"📋 Found Excel attachment: {filename}")
        
        return excel_parts
    
    def _decode_attachment_data(self, encoded_data: str) -> bytes:
        """Decode base64 attachment data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encoded_data)
            return decoded_data
        except Exception as e:
            logger.error(f"❌ Failed to decode attachment data: {str(e)}")
            raise
    
    def _calculate_file_checksum(self, file_data: bytes) -> str:
        """Calculate SHA-256 checksum for file data"""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_data)
        return sha256_hash.hexdigest()
    
    def _save_attachment_to_file(self, file_data: bytes, filename: str) -> str:
        """Save attachment data to file"""
        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)
        
        file_path = os.path.join(self.download_dir, filename)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"💾 Saved attachment: {file_path} ({len(file_data)} bytes)")
            return file_path
        except Exception as e:
            logger.error(f"❌ Failed to save file {file_path}: {str(e)}")
            raise
    
    def _search_emails_with_attachments(self, label: str = "mc-tech-não-processado") -> List[Dict]:
        """Search for emails with Excel attachments"""
        try:
            # Gmail search query for emails with Excel attachments
            query = f'label:{label} has:attachment filename:xlsx OR filename:xlsb'
            
            results = self.gmail_service.users().messages().list(
                userId='me', 
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"📧 Found {len(messages)} emails with potential Excel attachments")
            return messages
            
        except HttpError as e:
            logger.error(f"❌ Gmail search failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error searching emails: {str(e)}")
            raise
    
    def _get_message_details(self, message_id: str) -> Dict:
        """Get detailed message information"""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me', 
                id=message_id
            ).execute()
            
            logger.debug(f"📧 Retrieved message details for: {message_id}")
            return message
            
        except HttpError as e:
            logger.error(f"❌ Failed to get message {message_id}: {str(e)}")
            raise
    
    def _download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download specific attachment"""
        try:
            attachment = self.gmail_service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            # Decode attachment data
            file_data = self._decode_attachment_data(attachment['data'])
            logger.debug(f"📥 Downloaded attachment {attachment_id} ({len(file_data)} bytes)")
            return file_data
            
        except HttpError as e:
            logger.error(f"❌ Failed to download attachment {attachment_id}: {str(e)}")
            raise
    
    def _mark_email_as_processed(self, message_id: str) -> None:
        """Mark email as processed by updating labels"""
        try:
            # Add 'mc-tech-processado' label and remove 'mc-tech-não-processado'
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={
                    'addLabelIds': ['mc-tech-processado'],
                    'removeLabelIds': ['mc-tech-não-processado']
                }
            ).execute()
            
            logger.info(f"🏷️ Marked email {message_id} as processed")
            
        except HttpError as e:
            logger.warning(f"⚠️ Failed to update email labels {message_id}: {str(e)}")
            # Don't raise - label update failure shouldn't stop processing
    
    def download_excel_attachments(self, max_emails: int = 10) -> List[Dict[str, Any]]:
        """Download Excel attachments from Gmail emails"""
        logger.info(f"🚀 Starting Excel attachment download (max {max_emails} emails)")
        
        downloaded_files = []
        
        try:
            # Search for emails with attachments
            messages = self._search_emails_with_attachments()
            
            # Limit number of emails processed
            messages = messages[:max_emails]
            
            for message_ref in messages:
                message_id = message_ref['id']
                logger.info(f"📧 Processing email: {message_id}")
                
                try:
                    # Get message details
                    message = self._get_message_details(message_id)
                    
                    # Extract attachments from message payload
                    payload = message.get('payload', {})
                    parts = payload.get('parts', [])
                    
                    # If no parts, check if payload itself has attachment
                    if not parts and payload.get('body', {}).get('attachmentId'):
                        parts = [payload]
                    
                    # Filter Excel attachments
                    excel_parts = self._filter_excel_attachments(parts)
                    
                    # Download each Excel attachment
                    for part in excel_parts:
                        filename = part['filename']
                        attachment_id = part['body']['attachmentId']
                        
                        logger.info(f"📥 Downloading: {filename}")
                        
                        # Download attachment data
                        file_data = self._download_attachment(message_id, attachment_id)
                        
                        # Save to file
                        file_path = self._save_attachment_to_file(file_data, filename)
                        
                        # Calculate checksum
                        checksum = self._calculate_file_checksum(file_data)
                        
                        # Add to results
                        file_info = {
                            "filename": filename,
                            "path": file_path,
                            "size_bytes": len(file_data),
                            "checksum": checksum,
                            "email_id": message_id,
                            "downloaded_at": datetime.now(UTC).isoformat()
                        }
                        downloaded_files.append(file_info)
                        
                        logger.info(f"✅ Downloaded: {filename} -> {file_path}")
                    
                    # Mark email as processed if we downloaded attachments
                    if excel_parts:
                        self._mark_email_as_processed(message_id)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing email {message_id}: {str(e)}")
                    # Continue with next email
                    continue
            
            logger.info(f"🎉 Download completed: {len(downloaded_files)} files downloaded")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"❌ Download process failed: {str(e)}")
            raise
    
    def test_gmail_access(self) -> bool:
        """Test Gmail API access"""
        try:
            # Try to list first message to test access
            results = self.gmail_service.users().messages().list(
                userId='me', 
                maxResults=1
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"✅ Gmail access test successful ({len(messages)} messages available)")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Gmail access test failed: {str(e)}")
            return False