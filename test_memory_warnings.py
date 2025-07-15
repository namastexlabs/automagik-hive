#!/usr/bin/env python3
"""
NUCLEAR VALIDATION - Memory Warnings Test

Focused test to validate that "WARNING MemoryDb not provided" warnings
are eliminated after the nuclear fix.
"""

import os
import sys
import io
import contextlib
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Environment setup
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"

# Imports
from agents.registry import get_agent
from agents.version_factory import create_versioned_agent
from teams.ana.team import get_ana_team
from context.memory.memory_manager import create_memory_manager


def capture_warnings_and_logs():
    """Capture both warnings and log messages"""
    # Set up logging capture
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    
    # Get the root logger and add our handler
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    root_logger.addHandler(handler)
    
    # Also capture stderr
    stderr_capture = io.StringIO()
    
    return log_capture, stderr_capture, handler, original_handlers


def test_for_memory_warnings():
    """Test various agent creation paths for memory warnings"""
    
    print("🔍 Testing for MemoryDb warnings during agent creation...")
    print("=" * 60)
    
    # Set up memory system
    try:
        memory_manager = create_memory_manager()
        memory = memory_manager.memory
        memory_db = memory_manager.memory_db
        print(f"✅ Memory system initialized")
        print(f"   - Memory: {type(memory)}")
        print(f"   - Memory DB: {type(memory_db)}")
    except Exception as e:
        print(f"❌ Memory system initialization failed: {e}")
        return False
    
    # Test cases
    test_cases = [
        {
            "name": "Version Factory Direct",
            "func": lambda: create_versioned_agent(
                agent_id="pagbank-specialist",
                session_id="test_session",
                memory=memory,
                memory_db=memory_db
            )
        },
        {
            "name": "Registry Get Agent",
            "func": lambda: get_agent(
                name="pagbank",
                session_id="test_session",
                memory=memory,
                memory_db=memory_db
            )
        },
        {
            "name": "Ana Team Creation",
            "func": lambda: get_ana_team(
                session_id="test_session",
                user_id="test_user",
                agent_names=["pagbank"]
            )
        },
        {
            "name": "Multiple Agents",
            "func": lambda: [
                get_agent(name="pagbank", session_id="test_session", memory=memory, memory_db=memory_db),
                get_agent(name="adquirencia", session_id="test_session", memory=memory, memory_db=memory_db),
                get_agent(name="emissao", session_id="test_session", memory=memory, memory_db=memory_db)
            ]
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        
        # Set up capture
        log_capture, stderr_capture, handler, original_handlers = capture_warnings_and_logs()
        
        try:
            # Run the test with output capture
            with contextlib.redirect_stderr(stderr_capture):
                result = test_case["func"]()
                
                # Check that agent/team was created successfully
                if result is None:
                    print(f"❌ {test_case['name']}: Failed to create agent/team")
                    all_passed = False
                    continue
                
                # Check captured output for warnings
                log_output = log_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                # Look for memory warnings
                memory_warnings = []
                
                if "WARNING MemoryDb not provided" in log_output:
                    memory_warnings.append("LOG: WARNING MemoryDb not provided")
                if "WARNING MemoryDb not provided" in stderr_output:
                    memory_warnings.append("STDERR: WARNING MemoryDb not provided")
                if "MemoryDb not provided" in log_output:
                    memory_warnings.append("LOG: MemoryDb not provided")
                if "MemoryDb not provided" in stderr_output:
                    memory_warnings.append("STDERR: MemoryDb not provided")
                
                if memory_warnings:
                    print(f"❌ {test_case['name']}: Memory warnings found:")
                    for warning in memory_warnings:
                        print(f"   - {warning}")
                    all_passed = False
                else:
                    print(f"✅ {test_case['name']}: No memory warnings detected")
                
                # Show any other relevant output (for debugging)
                if stderr_output.strip():
                    print(f"   Debug output: {stderr_output.strip()[:100]}...")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: Error during test: {e}")
            all_passed = False
        
        finally:
            # Clean up logging
            root_logger = logging.getLogger()
            root_logger.removeHandler(handler)
            # Restore original handlers
            for h in original_handlers:
                if h not in root_logger.handlers:
                    root_logger.addHandler(h)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SUCCESS: No MemoryDb warnings detected!")
        print("✅ The nuclear fix is working correctly.")
        print("✅ Memory parameters are properly flowing through all agent creation paths.")
    else:
        print("⚠️ ISSUES FOUND: Some tests detected MemoryDb warnings.")
        print("❌ The nuclear fix may need additional work.")
    
    return all_passed


if __name__ == "__main__":
    # Activate virtual environment if needed
    if "VIRTUAL_ENV" not in os.environ:
        venv_path = Path(__file__).parent / ".venv"
        if venv_path.exists():
            activate_script = venv_path / "bin" / "activate"
            if activate_script.exists():
                print(f"🔧 Virtual environment detected at {venv_path}")
    
    success = test_for_memory_warnings()
    sys.exit(0 if success else 1)