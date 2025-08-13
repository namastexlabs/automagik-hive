"""Test Gmail module imports"""

import pytest

def test_gmail_module_imports():
    """Should import main classes without error"""
    try:
        from lib.gmail import GmailAuthenticator, GmailDownloader
        assert GmailAuthenticator is not None
        assert GmailDownloader is not None
    except ImportError:
        pytest.fail("Could not import Gmail classes")