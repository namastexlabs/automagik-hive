"""
Gmail Authentication Module

Handles OAuth2 authentication flow and credential management for Gmail API.
"""

import os
import json
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from lib.logging import logger


class GmailAuthenticator:
    """Gmail OAuth2 authentication handler"""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Initialize authenticator with credential file paths"""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        self._credentials: Optional[Credentials] = None
    
    def _token_exists(self) -> bool:
        """Check if token file exists"""
        return os.path.exists(self.token_file)
    
    def _load_existing_token(self) -> Optional[Credentials]:
        """Load existing token from file"""
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            logger.info(f"🔑 Loaded existing token from {self.token_file}")
            return creds
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing token: {str(e)}")
            return None
    
    def _refresh_token(self, creds: Credentials) -> Credentials:
        """Refresh expired token"""
        try:
            creds.refresh(Request())
            logger.info("🔄 Token refreshed successfully")
            self._save_token(creds)
            return creds
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {str(e)}")
            raise
    
    def _authorize_new_token(self) -> Credentials:
        """Perform OAuth2 authorization flow"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.scopes
            )
            # Use localhost flow instead of console flow for better compatibility
            creds = flow.run_local_server(port=8080, open_browser=True)
            logger.info("✅ New token authorized successfully")
            self._save_token(creds)
            return creds
        except Exception as e:
            logger.error(f"❌ Authorization failed: {str(e)}")
            raise
    
    def _save_token(self, creds: Credentials) -> None:
        """Save credentials to token file"""
        try:
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"💾 Token saved to {self.token_file}")
        except Exception as e:
            logger.error(f"❌ Could not save token: {str(e)}")
            raise
    
    def authenticate(self) -> Credentials:
        """Main authentication flow"""
        creds = None
        
        # Try to load existing token
        if self._token_exists():
            creds = self._load_existing_token()
        
        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Try to refresh expired token
                try:
                    creds = self._refresh_token(creds)
                except Exception:
                    # Refresh failed, need new authorization
                    logger.warning("🔄 Token refresh failed, requesting new authorization")
                    creds = self._authorize_new_token()
            else:
                # No valid credentials, need new authorization
                logger.info("🔑 No valid credentials found, requesting authorization")
                creds = self._authorize_new_token()
        
        self._credentials = creds
        return creds
    
    def get_gmail_service(self):
        """Build and return Gmail API service"""
        if not self._credentials:
            self.authenticate()
        
        try:
            service = build('gmail', 'v1', credentials=self._credentials)
            logger.info("🚀 Gmail API service created successfully")
            return service
        except Exception as e:
            logger.error(f"❌ Failed to build Gmail service: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test Gmail API connection"""
        try:
            service = self.get_gmail_service()
            # Try to get user profile to test connection
            profile = service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            logger.info(f"✅ Gmail connection successful for: {email}")
            return True
        except HttpError as e:
            logger.error(f"❌ Gmail connection failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error testing connection: {str(e)}")
            return False