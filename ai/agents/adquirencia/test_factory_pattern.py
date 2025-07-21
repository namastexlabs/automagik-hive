#!/usr/bin/env python3
"""Test minimal factory pattern for adquirencia agent"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.logging import logger
from agent import get_adquirencia_agent


def test_basic_factory():
    """Test basic agent creation via factory"""
    try:
        agent = get_adquirencia_agent(session_id="test")
        logger.info("🤖 Factory function works - agent created")
        print("✅ Factory function works - agent created")
        return True
    except Exception as e:
        logger.error("🤖 Factory failed", error=str(e))
        print(f"❌ Factory failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🤖 Testing Minimal Factory Pattern")
    print("🧪 Testing Minimal Factory Pattern")
    success = test_basic_factory()
    if success:
        logger.info("🤖 Ready for custom logic!")
        print("🎉 Ready for custom logic!")
    else:
        logger.error("🤖 Fix factory function")
        print("❌ Fix factory function")