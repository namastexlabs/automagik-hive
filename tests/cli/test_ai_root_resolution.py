import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from lib.utils.ai_root import resolve_ai_root
from lib.config.settings import settings

@pytest.fixture
def mock_path_exists(monkeypatch):
    def mock_exists(path):
        if 'missing' in str(path):
            return False
        return True
    monkeypatch.setattr('pathlib.Path.exists', mock_exists)

@pytest.fixture
def mock_os_environ(monkeypatch):
    monkeypatch.delenv('HIVE_AI_ROOT', raising=False)

class TestAIRootResolution:
    def test_default_ai_root(self, mock_os_environ):
        result = resolve_ai_root(None, settings())
        assert result == Path('ai')

    def test_cli_arg_override(self):
        arg_path = '/tmp/custom-ai'
        result = resolve_ai_root(arg_path, settings())
        assert result == Path(arg_path)

    def test_env_override(self, monkeypatch):
        env_path = '/tmp/env-ai'
        monkeypatch.setenv('HIVE_AI_ROOT', env_path)
        result = resolve_ai_root(None, settings())
        assert result == Path(env_path)

    def test_precedence_cli_over_env(self, monkeypatch):
        monkeypatch.setenv('HIVE_AI_ROOT', '/tmp/env-ai')
        cli_path = '/tmp/cli-ai'
        result = resolve_ai_root(cli_path, settings())
        assert result == Path(cli_path)

    def test_missing_dir_error(self, mock_path_exists):
        with pytest.raises(ValueError, match='must contain agents/, teams/, workflows/'):
            resolve_ai_root('/tmp/missing', settings())

    def test_settings_fallback(self):
        assert settings().ai_root_path == Path('ai')