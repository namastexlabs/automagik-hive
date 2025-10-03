"""Regression tests for logging level enforcement."""

import logging

import pytest
from loguru import logger

import lib.logging.config as logging_config
from lib import logging as lib_logging


@pytest.fixture
def real_logging_initializer(monkeypatch):
    """Temporarily restore the real logging initializer for validation tests."""
    monkeypatch.setattr(lib_logging, "initialize_logging", logging_config.initialize_logging)
    original_initialized = logging_config._logging_initialized
    logging_config._logging_initialized = False
    try:
        yield logging_config
    finally:
        logging_config._logging_initialized = original_initialized


def test_initialize_logging_defaults_to_info(real_logging_initializer, monkeypatch, capsys, tmp_path):
    """INFO default should suppress DEBUG chatter while emitting INFO messages."""
    monkeypatch.delenv("HIVE_LOG_LEVEL", raising=False)
    monkeypatch.setenv("AGNO_LOG_LEVEL", "WARNING")

    real_logging_initializer.initialize_logging(surface="tests.level.info", force=True)

    logger.debug("DEBUG: suppressed for INFO default")
    logger.info("INFO: emitted at default level")

    captured = capsys.readouterr()
    assert "DEBUG: suppressed for INFO default" not in captured.err
    assert "INFO: emitted at default level" in captured.err
    assert logging.getLogger().getEffectiveLevel() == logging.INFO

    sample_path = tmp_path / "info_default.log"
    sample_path.write_text(captured.err)
    saved_contents = sample_path.read_text()
    assert "INFO: emitted at default level" in saved_contents
    assert "DEBUG: suppressed for INFO default" not in saved_contents


def test_initialize_logging_supports_debug_opt_in(real_logging_initializer, monkeypatch, capsys, tmp_path):
    """DEBUG opt-in should emit debug breadcrumbs once requested."""
    monkeypatch.setenv("HIVE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AGNO_LOG_LEVEL", "WARNING")

    real_logging_initializer.initialize_logging(surface="tests.level.debug", force=True)

    logger.debug("DEBUG: visible when opt-in enabled")

    captured = capsys.readouterr()
    assert "DEBUG: visible when opt-in enabled" in captured.err
    assert "Logging bootstrap complete" in captured.err
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

    sample_path = tmp_path / "debug_opt_in.log"
    sample_path.write_text(captured.err)
    saved_contents = sample_path.read_text()
    assert "DEBUG: visible when opt-in enabled" in saved_contents
    assert "Logging bootstrap complete" in saved_contents
