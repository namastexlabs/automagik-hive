---
allowed-tools: Read, Write, LS, Bash
description: Simple test command for command-executor validation
---

# Test Command

Simple test command that creates a timestamp file to validate command execution.

## Usage
```
/test-cmd <filename>
```

## Instructions

1. **Validate input**: Ensure filename is provided and valid (alphanumeric + hyphens only)

2. **Create test file**: 
   ```bash
   echo "Test executed at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "/tmp/test-${ARGUMENTS}.txt"
   ```

3. **Confirm success**:
   ```
   ✅ Test command completed
   📁 Created: /tmp/test-${ARGUMENTS}.txt
   🕒 Timestamp: [current time]
   ```

## Expected Behavior
- Takes any valid filename
- Creates timestamped file in /tmp/
- Returns confirmation with file location