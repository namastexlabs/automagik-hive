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
    
    def _search_emails_with_attachments(self, label: str = "mc-tech-não-processado", max_results: int = 10) -> List[Dict]:
        """Search for emails with Excel attachments using robust query building"""
        try:
            # Build Gmail search query with proper label checking
            query_parts = []
            
            # Add label filter if specified
            if label:
                query_parts.append(f'label:"{label}"')
            
            # Add attachment filter for Excel files
            query_parts.append('has:attachment')
            query_parts.append('(filename:xlsx OR filename:xlsb OR filename:xls)')
            
            query = ' '.join(query_parts)
            logger.info(f"📧 Gmail search query: {query}")
            
            results = self.gmail_service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info(f"📧 No emails found matching query: {query}")
                return []
            
            logger.info(f"📧 Found {len(messages)} emails with potential Excel attachments")
            return messages
            
        except HttpError as e:
            logger.error(f"❌ Gmail search failed: {str(e)}")
            # Don't raise - return empty list to continue processing
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error searching emails: {str(e)}")
            return []
    
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
    
    def _get_label_id_by_name(self, label_name: str) -> Optional[str]:
        """Get label ID by exact name match, with robust search"""
        try:
            # List all labels
            labels_result = self.gmail_service.users().labels().list(userId='me').execute()
            labels = labels_result.get('labels', [])
            
            # Look for exact match first
            for label in labels:
                if label['name'] == label_name:
                    logger.debug(f"🏷️ Found exact label match: {label_name} -> {label['id']}")
                    return label['id']
            
            # Try case-insensitive match as fallback
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    logger.debug(f"🏷️ Found case-insensitive label match: {label_name} -> {label['id']}")
                    return label['id']
            
            logger.info(f"🏷️ Label not found: {label_name}")
            return None
            
        except HttpError as e:
            logger.error(f"❌ Failed to list labels: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error listing labels: {str(e)}")
            return None

    def _create_label_if_needed(self, label_name: str) -> Optional[str]:
        """Create Gmail label if it doesn't exist"""
        try:
            logger.info(f"🏷️ Creating Gmail label: {label_name}")
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.gmail_service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            logger.info(f"✅ Successfully created label: {label_name} -> {created_label['id']}")
            return created_label['id']
            
        except HttpError as e:
            if e.resp.status == 409:
                logger.info(f"🏷️ Label {label_name} already exists, attempting to find it...")
                return self._get_label_id_by_name(label_name)
            else:
                logger.error(f"❌ Failed to create label {label_name}: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating label {label_name}: {str(e)}")
            return None

    def _get_or_create_label_id(self, label_name: str) -> Optional[str]:
        """Get label ID by name, create if it doesn't exist - robust implementation"""
        # First try to find existing label
        label_id = self._get_label_id_by_name(label_name)
        if label_id:
            return label_id
        
        # If not found, try to create it
        label_id = self._create_label_if_needed(label_name)
        if label_id:
            return label_id
        
        # Final attempt - maybe it was created by another process
        logger.info(f"🏷️ Final attempt to find label: {label_name}")
        return self._get_label_id_by_name(label_name)

    def _mark_email_as_processed(self, message_id: str) -> bool:
        """Mark email as processed by updating labels with robust label management"""
        try:
            logger.debug(f"🏷️ Starting label update for email {message_id}")
            
            # Get or create the "processed" label
            processed_label_id = self._get_or_create_label_id('MC Tech/Processado')
            if not processed_label_id:
                logger.warning(f"⚠️ Could not get/create 'MC Tech/Processado' label for email {message_id}")
                return False
            
            # Try to get the "unprocessed" label (but don't create it if it doesn't exist)
            unprocessed_label_id = self._get_label_id_by_name('MC Tech/Não Processado')
            
            # Prepare label modifications - always add the processed label
            modifications = {
                'addLabelIds': [processed_label_id]
            }
            
            # Only remove unprocessed label if we actually found it
            if unprocessed_label_id:
                modifications['removeLabelIds'] = [unprocessed_label_id]
                logger.debug(f"🏷️ Will add '{processed_label_id}' and remove '{unprocessed_label_id}' from email {message_id}")
            else:
                logger.debug(f"🏷️ Will add '{processed_label_id}' to email {message_id} (no unprocessed label to remove)")
            
            # Apply label modifications
            result = self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body=modifications
            ).execute()
            
            logger.info(f"🏷️ Successfully updated labels for email {message_id}")
            return True
            
        except HttpError as e:
            # Check if it's a specific "label not found" error
            if "Label not found" in str(e) or "Invalid label" in str(e):
                logger.warning(f"⚠️ Label issue for email {message_id}: {str(e)}. Attempting label recreation...")
                # Could implement retry logic here if needed
                return False
            else:
                logger.warning(f"⚠️ Gmail API error updating labels for {message_id}: {str(e)}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error updating labels for {message_id}: {str(e)}")
            return False
    
    def download_excel_attachments(self, max_emails: int = 10, label_filter: str = "MC Tech/Não Processado") -> List[Dict[str, Any]]:
        """Download Excel attachments from Gmail emails with robust error handling"""
        logger.info(f"🚀 Starting Excel attachment download (max {max_emails} emails) from label: {label_filter}")
        
        downloaded_files = []
        processed_emails = 0
        failed_emails = 0
        
        try:
            # Search for emails with attachments using robust search
            messages = self._search_emails_with_attachments(label=label_filter, max_results=max_emails)
            
            if not messages:
                logger.info("📧 No emails found matching search criteria")
                return downloaded_files
            
            logger.info(f"📧 Processing {len(messages)} emails...")
            
            for message_ref in messages:
                message_id = message_ref['id']
                logger.info(f"📧 Processing email: {message_id}")
                
                try:
                    # Get message details with full format
                    message = self.gmail_service.users().messages().get(
                        userId='me', 
                        id=message_id,
                        format='full'
                    ).execute()
                    
                    # Extract attachments from message payload
                    payload = message.get('payload', {})
                    parts = payload.get('parts', [])
                    
                    # If no parts, check if payload itself has attachment
                    if not parts and payload.get('body', {}).get('attachmentId'):
                        parts = [payload]
                    
                    # Filter Excel attachments
                    excel_parts = self._filter_excel_attachments(parts)
                    
                    if not excel_parts:
                        logger.info(f"📧 No Excel attachments found in email {message_id}")
                        processed_emails += 1
                        continue
                    
                    # Download each Excel attachment
                    email_downloaded_files = []
                    for part in excel_parts:
                        filename = part['filename']
                        attachment_id = part['body']['attachmentId']
                        
                        logger.info(f"📥 Downloading: {filename}")
                        
                        try:
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
                            email_downloaded_files.append(file_info)
                            
                            logger.info(f"✅ Downloaded: {filename} -> {file_path}")
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to download attachment {filename} from email {message_id}: {str(e)}")
                            continue
                    
                    # Mark email as processed if we successfully downloaded attachments
                    if email_downloaded_files:
                        success = self._mark_email_as_processed(message_id)
                        if success:
                            logger.info(f"✅ Email {message_id} processed successfully with {len(email_downloaded_files)} attachments and marked as processed")
                        else:
                            logger.warning(f"⚠️ Email {message_id} processed with {len(email_downloaded_files)} attachments but label marking failed")
                    else:
                        logger.info(f"📧 Email {message_id} had no Excel attachments to download")
                    
                    processed_emails += 1
                    
                except HttpError as e:
                    logger.error(f"❌ Gmail API error processing email {message_id}: {str(e)}")
                    failed_emails += 1
                    continue
                except Exception as e:
                    logger.error(f"❌ Unexpected error processing email {message_id}: {str(e)}")
                    failed_emails += 1
                    continue
            
            logger.info(f"🎉 Download completed: {len(downloaded_files)} files downloaded from {processed_emails} emails (failed: {failed_emails})")
            return downloaded_files
            
        except HttpError as e:
            logger.error(f"❌ Gmail API error during download process: {str(e)}")
            return downloaded_files  # Return what we got so far
        except Exception as e:
            logger.error(f"❌ Download process failed: {str(e)}")
            return downloaded_files  # Return what we got so far
    
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