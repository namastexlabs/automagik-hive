"""
Integration tests for Automagik Hive.

These tests make REAL API calls - no mocking.
They verify agents actually work with real LLM providers.

Requirements:
- OPENAI_API_KEY in environment
- ANTHROPIC_API_KEY in environment
- Internet connectivity
- API credits/quota available

Tests are marked with @pytest.mark.integration for selective execution.
"""
