"""
Test Gmail Downloader Module

Tests for email fetching and Excel attachment downloading.
"""

import pytest
import base64
import tempfile
import os
from unittest.mock import Mock, patch, call
from pathlib import Path

from lib.gmail.downloader import GmailDownloader


class TestGmailDownloader:
    """Test Gmail download functionality"""
    
    @patch('lib.gmail.downloader.GmailAuthenticator')
    def test_downloader_initialization(self, mock_auth_class):
        """Should initialize with Gmail service"""
        mock_auth = Mock()
        mock_service = Mock()
        mock_auth.get_gmail_service.return_value = mock_service
        mock_auth_class.return_value = mock_auth
        
        downloader = GmailDownloader()
        assert downloader.gmail_service == mock_service
        mock_auth.get_gmail_service.assert_called_once()
    
    def test_filter_excel_attachments(self):
        """Should filter only Excel attachments"""
        downloader = GmailDownloader.__new__(GmailDownloader)
        
        parts = [
            {'filename': 'document.xlsx', 'body': {'attachmentId': 'att1'}},
            {'filename': 'image.png', 'body': {'attachmentId': 'att2'}},
            {'filename': 'spreadsheet.xlsb', 'body': {'attachmentId': 'att3'}},
            {'filename': 'text.txt', 'body': {'attachmentId': 'att4'}}
        ]
        
        excel_parts = downloader._filter_excel_attachments(parts)
        assert len(excel_parts) == 2
        assert excel_parts[0]['filename'] == 'document.xlsx'
        assert excel_parts[1]['filename'] == 'spreadsheet.xlsb'
    
    def test_decode_attachment_data(self):
        """Should decode base64 attachment data"""
        downloader = GmailDownloader.__new__(GmailDownloader)
        
        test_data = b'Hello, World!'
        encoded_data = base64.urlsafe_b64encode(test_data).decode()
        
        decoded_data = downloader._decode_attachment_data(encoded_data)
        assert decoded_data == test_data
    
    @patch('lib.gmail.downloader.os.makedirs')
    @patch('builtins.open', create=True)
    def test_save_attachment_to_file(self, mock_open, mock_makedirs):
        """Should save attachment data to file"""
        downloader = GmailDownloader.__new__(GmailDownloader)
        
        test_data = b'Excel file content'
        filename = 'test.xlsx'
        expected_path = 'mctech/sheets/test.xlsx'
        
        file_path = downloader._save_attachment_to_file(test_data, filename)
        
        mock_makedirs.assert_called_once_with('mctech/sheets', exist_ok=True)
        mock_open.assert_called_once_with(expected_path, 'wb')
        assert file_path == expected_path
    
    @patch('lib.gmail.downloader.GmailAuthenticator')
    def test_search_emails_with_attachments(self, mock_auth_class):
        """Should search for emails with correct label and attachment filter"""
        mock_service = Mock()
        mock_auth_class.return_value.get_gmail_service.return_value = mock_service
        
        # Mock search results
        mock_results = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'}
            ]
        }
        mock_service.users().messages().list().execute.return_value = mock_results
        
        downloader = GmailDownloader()
        messages = downloader._search_emails_with_attachments()
        
        # Verify search query
        mock_service.users().messages().list.assert_called_once_with(
            userId='me',
            q='label:mc-tech-não-processado has:attachment filename:xlsx OR filename:xlsb'
        )
        assert messages == mock_results.get('messages', [])
    
    @patch('lib.gmail.downloader.GmailAuthenticator')
    def test_download_excel_attachments_integration(self, mock_auth_class):
        """Should integrate all download steps"""
        mock_service = Mock()
        mock_auth_class.return_value.get_gmail_service.return_value = mock_service
        
        # Mock search results
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}]
        }
        
        # Mock message details
        mock_service.users().messages().get().execute.return_value = {
            'id': 'msg1',
            'payload': {
                'parts': [
                    {
                        'filename': 'test.xlsx',
                        'body': {'attachmentId': 'att1'}
                    }
                ]
            }
        }
        
        # Mock attachment data
        test_content = base64.urlsafe_b64encode(b'Excel content').decode()
        mock_service.users().messages().attachments().get().execute.return_value = {
            'data': test_content
        }
        
        with patch.object(GmailDownloader, '_save_attachment_to_file') as mock_save:
            mock_save.return_value = 'mctech/sheets/test.xlsx'
            
            downloader = GmailDownloader()
            files = downloader.download_excel_attachments()
            
            assert len(files) == 1
            assert files[0]['filename'] == 'test.xlsx'
            assert files[0]['path'] == 'mctech/sheets/test.xlsx'
            assert files[0]['email_id'] == 'msg1'