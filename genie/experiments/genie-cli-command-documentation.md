# GENIE CLI Command Implementation

## Overview

Successfully implemented a new `--genie` command in the automagik-hive CLI that launches claude with GENIE.md automatically loaded as the system prompt.

## Implementation Details

### Files Modified

1. **cli/main.py**
   - Added `--genie` argument to the argument parser
   - Added routing logic to handle the `--genie` command
   - Updated command counting logic to include the new command

2. **cli/commands/genie.py** 
   - Added `launch_claude()` method to the GenieCommands class
   - Implemented GENIE.md file discovery (checks current directory and parent directories)
   - Built claude command with proper arguments and content passing

3. **tests/cli/commands/test_genie_cli_command.py**
   - Created comprehensive test suite to validate the implementation
   - Tests command availability, file reading, content validation, and command building

### Command Structure

```bash
uv run automagik-hive --genie [additional_claude_args...]
```

The command automatically:
- Finds GENIE.md file (current directory or parent directories)
- Reads the complete GENIE.md content
- Launches claude with `--append-system-prompt` containing the GENIE content
- Includes default flags: `--mcp-config .mcp.json --model sonnet --dangerously-skip-permissions`
- Passes through any additional user arguments to claude

### Usage Examples

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

### Key Features

1. **Smart File Discovery**: Automatically finds GENIE.md in current directory or parent directories
2. **Content Validation**: Reads and validates GENIE.md content before launching
3. **Error Handling**: Graceful error handling for missing files or claude command
4. **Argument Pass-through**: Supports all claude CLI arguments
5. **User-Friendly Output**: Clear status messages and command information

### Error Handling

The command handles several error conditions:
- GENIE.md file not found
- GENIE.md file read errors (permissions, encoding, etc.)
- claude command not installed
- Subprocess execution errors
- Keyboard interruption (Ctrl+C)

### Technical Implementation

The `launch_claude()` method:
1. Searches for GENIE.md file starting from current directory
2. Reads the entire file content into memory
3. Builds the claude command array with content and default arguments
4. Executes claude via subprocess.run()
5. Returns success/failure status

### Testing

Comprehensive test suite validates:
- Command appears in CLI help
- GENIE.md file exists and is readable
- Content contains expected GENIE personality markers
- Command building logic works correctly
- Error handling for missing dependencies

## Future Enhancements

Possible future improvements:
1. **Caching**: Cache GENIE.md content to avoid re-reading
2. **Validation**: Validate GENIE.md format/structure
3. **Multiple Files**: Support loading multiple personality files
4. **Interactive Mode**: Interactive selection of personality files
5. **Dry Run**: Add `--dry-run` flag to show command without executing

## Integration Status

✅ **Complete**: The genie command is fully integrated and functional
✅ **Tested**: Comprehensive test suite validates all functionality  
✅ **Documented**: Usage examples and implementation details provided
✅ **Error Handling**: Robust error handling for common failure cases

The implementation successfully meets all the original requirements:
- Reads GENIE.md content (not just filename)
- Launches claude with `--append-system-prompt` containing the content
- Includes sensible default arguments
- Supports passing through additional claude arguments
- Provides helpful output when starting
- Handles errors gracefully