#!/usr/bin/env python3
"""Test script to validate genie CLI command functionality."""

import subprocess
import sys
from pathlib import Path
import pytest

def test_genie_command_in_help():
    """Test that genie command appears in help."""
    result = subprocess.run(["uv", "run", "automagik-hive", "--help"], 
                          capture_output=True, text=True)
    assert "genie" in result.stdout, "genie command not found in help"
    assert "Launch claude with GENIE.md as system prompt" in result.stdout

def test_genie_md_exists():
    """Test that GENIE.md file exists."""
    genie_path = Path("GENIE.md")
    assert genie_path.exists(), "GENIE.md not found"
    assert genie_path.stat().st_size > 1000, "GENIE.md seems too small"

def test_genie_commands_import():
    """Test that GenieCommands class can be imported."""
    from cli.commands.genie import GenieCommands
    genie = GenieCommands()
    assert hasattr(genie, 'launch_claude'), "launch_claude method not found"

def test_genie_content_reading():
    """Test that GENIE.md content can be read properly."""
    genie_path = Path("GENIE.md")
    with open(genie_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert len(content) > 1000, "GENIE.md content seems too short"
    assert "Master Genie" in content, "Content doesn't contain expected GENIE markers"
    assert "GENIE" in content, "Content doesn't contain GENIE references"

def test_claude_availability():
    """Test if claude command is available (warning only)."""
    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        pytest.skip("claude command not found - install with: npm install -g @anthropic-ai/claude-cli")

def test_genie_command_building():
    """Test that the claude command is built correctly."""
    from cli.commands.genie import GenieCommands
    from pathlib import Path
    
    genie = GenieCommands()
    genie_path = Path("GENIE.md")
    
    # Read content
    with open(genie_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Build expected command  
    expected_cmd_parts = [
        "claude",
        "--append-system-prompt",
        "--mcp-config", ".mcp.json",
        "--model", "sonnet", 
        "--dangerously-skip-permissions"
    ]
    
    # Test command building logic (mock the subprocess call)
    import subprocess
    from unittest.mock import patch, MagicMock
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = genie.launch_claude([])
        
        # Check that subprocess.run was called
        assert mock_run.called, "subprocess.run was not called"
        
        # Get the command that was passed
        call_args = mock_run.call_args[0][0]  # First positional argument
        
        # Check basic command structure
        assert call_args[0] == "claude", "First argument should be 'claude'"
        assert "--append-system-prompt" in call_args, "--append-system-prompt not found"
        assert "--mcp-config" in call_args, "--mcp-config not found"
        assert "--model" in call_args, "--model not found"
        assert "sonnet" in call_args, "sonnet model not found"
        assert "--dangerously-skip-permissions" in call_args, "--dangerously-skip-permissions not found"
        
        # Check that GENIE content is passed
        content_index = call_args.index("--append-system-prompt") + 1
        passed_content = call_args[content_index]
        assert "Master Genie" in passed_content, "GENIE content not properly passed"

if __name__ == "__main__":
    print("🧞 Testing GENIE CLI Command")
    print("=" * 50)
    
    # Run basic validation
    try:
        test_genie_command_in_help()
        print("✅ Test 1: Command appears in help")
        
        test_genie_md_exists()
        print("✅ Test 2: GENIE.md file exists")
        
        test_genie_commands_import()
        print("✅ Test 3: Command class imports successfully")
        
        test_genie_content_reading()
        print("✅ Test 4: GENIE.md content reading")
        
        try:
            test_claude_availability()
            print("✅ Test 5: Claude CLI available")
        except Exception:
            print("⚠️  Test 5: Claude CLI not found (install with: npm install -g @anthropic-ai/claude-cli)")
        
        test_genie_command_building()
        print("✅ Test 6: Command building logic")
        
        print("\n🎉 All tests passed! The genie command should work correctly.")
        print("\n📖 Usage examples:")
        print("  uv run automagik-hive genie                      # Launch with GENIE personality")
        print("  uv run automagik-hive genie --model opus         # Use different model")
        print("  uv run automagik-hive genie --help               # Show claude help")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)