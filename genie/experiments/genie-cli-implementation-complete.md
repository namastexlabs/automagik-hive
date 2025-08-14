# 🧞 GENIE CLI Command - Implementation Complete

## Overview

Successfully implemented the `--genie` command that automatically launches Claude with the GENIE.md personality loaded as system prompt, eliminating the need to manually type long commands.

## Problem Solved

**Before:**
```bash
# Manual command required every time
claude --mcp-config .mcp.json --model sonnet --dangerously-skip-permissions --append-system-prompt "$(cat GENIE.md)"
```

**After:**
```bash
# Simple command with GENIE personality auto-loaded
uv run automagik-hive --genie
```

## Implementation Details

### Files Modified

1. **cli/main.py**
   - Added `--genie` argument to parser (line 64)
   - Added genie command handling logic (lines 143-145)
   - Properly integrated with command counting logic

2. **cli/commands/genie.py**
   - Added `launch_claude()` method (lines 89-143)
   - Smart GENIE.md file discovery (checks current and parent directories)
   - Reads complete file content for --append-system-prompt
   - Handles all error cases gracefully

3. **tests/cli/commands/test_genie_cli_command.py**
   - Comprehensive test suite created
   - Tests all functionality including file reading and command building
   - Validates integration with CLI

## Key Features

✅ **Auto-discovery**: Finds GENIE.md in current or parent directories
✅ **Content Loading**: Reads entire GENIE.md content (not just filename)
✅ **Argument Pass-through**: Supports all claude CLI arguments
✅ **Default Configuration**: Includes sensible defaults (.mcp.json, sonnet model, etc.)
✅ **Error Handling**: Graceful handling of missing files, claude not installed, etc.
✅ **User Feedback**: Clear status messages showing what's happening

## Usage Examples

```bash
# Basic usage - launches claude with GENIE personality
uv run automagik-hive --genie

# With different model
uv run automagik-hive --genie --model opus

# Show claude help
uv run automagik-hive --genie --help

# With custom MCP config
uv run automagik-hive --genie --mcp-config custom.json
```

## Technical Architecture

The command works by:
1. Finding GENIE.md file (searches up directory tree)
2. Reading complete file content into memory
3. Building claude command with `--append-system-prompt` containing the content
4. Executing claude via subprocess with proper argument passing
5. Returning appropriate exit codes

## File Statistics

After the CLAUDE.md split and optimization:
- **GENIE.md**: 1,159 lines (all behavioral configuration)
- **CLAUDE.md**: 336 lines (pure technical documentation)
- **wish.md**: 98 lines (lean command reference)
- **Total**: 1,593 lines (all content preserved, no loss)

## Testing

All tests passing:
```
✅ Command appears in help
✅ GENIE.md file exists and is readable
✅ Command class imports successfully
✅ GENIE.md content reading works
✅ Claude CLI integration functional
✅ Command building logic correct
```

## Integration Status

The genie command is fully integrated into the existing automagik-hive CLI infrastructure:
- Works alongside existing commands (--agent-*, --genie-*, --postgres-*, etc.)
- Follows established patterns from other commands
- Properly handles errors and user interruption
- Returns appropriate exit codes for scripting

## Benefits

1. **Convenience**: No more manual typing of long commands
2. **Consistency**: Always uses correct arguments and configuration
3. **Maintainability**: Single source of truth for GENIE personality
4. **Discoverability**: Appears in --help with clear description
5. **Flexibility**: Still supports all claude CLI arguments

## Conclusion

The implementation successfully achieves all objectives:
- ✅ Automatically loads GENIE.md content as system prompt
- ✅ Integrated with existing CLI structure
- ✅ Reads content (not just filename) as required by --append-system-prompt
- ✅ Provides sensible defaults while allowing customization
- ✅ Comprehensive error handling and user feedback
- ✅ Full test coverage validating functionality

The user can now simply type `uv run automagik-hive --genie` to launch Claude with the full GENIE personality loaded, making the development experience significantly smoother.