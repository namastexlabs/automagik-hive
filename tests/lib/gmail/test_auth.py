"""
Test Gmail Authentication Module

Tests for OAuth2 authentication flow and credential management.
"""

import pytest
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from lib.gmail.auth import GmailAuthenticator


class TestGmailAuthenticator:
    """Test Gmail authentication functionality"""
    
    def test_authenticator_initialization(self):
        """Should initialize with correct credentials path"""
        auth = GmailAuthenticator()
        assert auth.credentials_file == "credentials.json"
        assert auth.token_file == "token.json"
    
    def test_custom_credentials_path(self):
        """Should accept custom credentials path"""
        auth = GmailAuthenticator(credentials_file="custom_creds.json")
        assert auth.credentials_file == "custom_creds.json"
    
    @patch('lib.gmail.auth.os.path.exists')
    def test_token_exists_check(self, mock_exists):
        """Should check if token file exists"""
        mock_exists.return_value = True
        auth = GmailAuthenticator()
        assert auth._token_exists() is True
        mock_exists.assert_called_with("token.json")
    
    def test_scopes_configuration(self):
        """Should have correct Gmail API scopes"""
        auth = GmailAuthenticator()
        expected_scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        assert auth.scopes == expected_scopes
    
    @patch('lib.gmail.auth.Credentials.from_authorized_user_file')
    @patch('lib.gmail.auth.os.path.exists')
    def test_load_existing_token(self, mock_exists, mock_from_file):
        """Should load existing valid token"""
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        
        auth = GmailAuthenticator()
        creds = auth.authenticate()
        
        assert creds == mock_creds
        mock_from_file.assert_called_once_with('token.json')
    
    @patch('lib.gmail.auth.build')
    @patch('lib.gmail.auth.Credentials.from_authorized_user_file')
    @patch('lib.gmail.auth.os.path.exists')
    def test_build_gmail_service(self, mock_exists, mock_from_file, mock_build):
        """Should build Gmail API service"""
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        auth = GmailAuthenticator()
        service = auth.get_gmail_service()
        
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
        assert service == mock_service