#!/usr/bin/env python3
"""
Test script for adquirencia agent refactor validation
Tests configuration loading and structure without requiring database
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, Any

def test_config_loading():
    """Test that YAML configuration loads correctly"""
    config_path = Path(__file__).parent / "config.yaml"
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        print("✅ Configuration loaded successfully")
        return config
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return None

def test_required_sections(config: Dict[str, Any]):
    """Test that all required sections are present"""
    required_sections = [
        "agent", "model", "memory", "storage", "streaming", 
        "events", "context", "display", "knowledge", "instructions"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in config:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing required sections: {missing_sections}")
        return False
    
    print("✅ All required sections present")
    return True

def test_agent_section(config: Dict[str, Any]):
    """Test agent section structure"""
    agent_config = config.get("agent", {})
    
    required_fields = ["name", "agent_id", "version", "description"]
    missing_fields = [field for field in required_fields if field not in agent_config]
    
    if missing_fields:
        print(f"❌ Agent section missing fields: {missing_fields}")
        return False
    
    # Test version bump
    if agent_config.get("version") != 37:
        print(f"❌ Agent version should be 37, got {agent_config.get('version')}")
        return False
    
    print("✅ Agent section structure valid")
    return True

def test_model_section(config: Dict[str, Any]):
    """Test model section structure"""
    model_config = config.get("model", {})
    
    required_fields = ["provider", "id", "temperature", "max_tokens"]
    missing_fields = [field for field in required_fields if field not in model_config]
    
    if missing_fields:
        print(f"❌ Model section missing fields: {missing_fields}")
        return False
    
    # Test thinking mode added
    if "thinking" not in model_config:
        print("❌ Model section missing thinking configuration")
        return False
    
    print("✅ Model section structure valid")
    return True

def test_knowledge_filtering(config: Dict[str, Any]):
    """Test knowledge filtering configuration"""
    knowledge_config = config.get("knowledge", {})
    knowledge_filter = config.get("knowledge_filter", {})
    
    if not knowledge_config.get("enable_agentic_knowledge_filters"):
        print("❌ Agentic knowledge filters should be enabled")
        return False
    
    if knowledge_filter.get("business_unit") != "Adquirência Web":
        print(f"❌ Business unit should be 'Adquirência Web', got {knowledge_filter.get('business_unit')}")
        return False
    
    print("✅ Knowledge filtering configuration valid")
    return True

def test_instructions_cleanup(config: Dict[str, Any]):
    """Test that instructions are clean and concise"""
    instructions = config.get("instructions", "")
    
    if not instructions:
        print("❌ Instructions are empty")
        return False
    
    # Check for verbose/emoji patterns that should be cleaned
    if "💰" in instructions or "💡" in instructions or "🔍" in instructions:
        print("❌ Instructions still contain emojis (should be cleaned)")
        return False
    
    if "Oii!" in instructions:
        print("❌ Instructions still contain informal greetings")
        return False
    
    print("✅ Instructions are clean and professional")
    return True

def test_escalation_triggers(config: Dict[str, Any]):
    """Test escalation triggers configuration"""
    escalation = config.get("escalation_triggers", {})
    
    if not escalation.get("high_value_threshold"):
        print("❌ Missing high value threshold")
        return False
    
    if not escalation.get("fraud_keywords"):
        print("❌ Missing fraud keywords")
        return False
    
    if not escalation.get("blocked_keywords"):
        print("❌ Missing blocked keywords")
        return False
    
    print("✅ Escalation triggers configuration valid")
    return True

def run_all_tests():
    """Run all validation tests"""
    print("🧪 Testing Adquirencia Agent Configuration Refactor\n")
    
    config = test_config_loading()
    if not config:
        return False
    
    tests = [
        test_required_sections,
        test_agent_section,
        test_model_section,
        test_knowledge_filtering,
        test_instructions_cleanup,
        test_escalation_triggers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test(config):
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Adquirencia agent refactor successful.")
        return True
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)