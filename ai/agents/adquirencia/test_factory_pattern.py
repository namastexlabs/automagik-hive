#!/usr/bin/env python3
"""Test minimal factory pattern for adquirencia agent"""

from agent import get_adquirencia_agent


def test_basic_factory():
    """Test basic agent creation via factory"""
    try:
        agent = get_adquirencia_agent(session_id="test")
        print("✅ Factory function works - agent created")
        return True
    except Exception as e:
        print(f"❌ Factory failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Minimal Factory Pattern")
    success = test_basic_factory()
    print("🎉 Ready for custom logic!" if success else "❌ Fix factory function")