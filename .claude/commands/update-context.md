# update-context

Update and synchronize all project context files with the current codebase state. This command ensures documentation stays accurate as the project evolves.

## Usage

```
/update-context
```

## Implementation

The actual update logic is defined in `update-context-prompt.md` which executes parallel tasks to analyze and update all context files.

## What it does

This command performs a comprehensive review and update of all project context files by:

1. **Analyzing Current Codebase**
   - Scans for new patterns, removed features, and structural changes
   - Identifies new dependencies, APIs, and integration points
   - Detects deprecated or removed components

2. **Updating Documentation** (in parallel)
   - **CLAUDE.md**: Project overview, development guidelines, and MCP integrations
   - **project-structure.md**: Technology stack and directory structure
   - **MCP-ASSISTANT-RULES.md**: Coding standards for Gemini consultation
   - **sensitive-patterns.json**: Security patterns and whitelist entries

3. **Validation**
   - Ensures all file paths referenced in docs exist
   - Verifies technology versions match pyproject.toml
   - Confirms all agents in registry are documented

## Process Flow

The command executes these tasks in parallel for efficiency:

### Task 1: Code Analysis
```
- Scan agents/ for new agent directories
- Check pyproject.toml for dependency updates
- Review api/routes/ for new endpoints
- Examine workflows/ for new patterns
- Analyze config/ for new settings
```

### Task 2: Update CLAUDE.md
```
- Update project phase/status
- Refresh MCP server integration examples
- Update agent-specific instructions
- Sync with new development patterns
```

### Task 3: Update project-structure.md
```
- Refresh technology versions from pyproject.toml
- Update directory tree with new/removed files
- Document new agent factories
- Update integration services
```

### Task 4: Update MCP-ASSISTANT-RULES.md
```
- Sync with latest Agno patterns
- Update code organization standards
- Refresh API design patterns
- Update performance considerations
```

### Task 5: Update sensitive-patterns.json
```
- Add new API key patterns
- Update sensitive file patterns
- Refresh whitelist with new placeholders
- Remove obsolete patterns
```

## Output

The command will:
1. Show a summary of all changes detected
2. Update each file with current information
3. Report any inconsistencies found
4. Provide a change summary for each file

## Example Output

```
🔍 Analyzing codebase changes...

📝 Updates Applied:

CLAUDE.md:
- Added new WhatsApp notification agent documentation
- Updated Agno version to 1.8.0
- Added new workflow patterns section

project-structure.md:
- Added 3 new agent directories
- Updated FastAPI to 0.117.0
- Removed deprecated legacy/ directory

MCP-ASSISTANT-RULES.md:
- Added new session management patterns
- Updated performance guidelines
- Added new Agno Team routing examples

sensitive-patterns.json:
- Added WHATSAPP_BUSINESS_TOKEN pattern
- Removed obsolete AWS_SECRET pattern
- Added 5 new whitelist entries

✅ All context files updated successfully!
```

## Best Practices

1. Run this command:
   - After major feature additions
   - When adding new agents or workflows
   - After dependency updates
   - Before major releases

2. The command will:
   - Preserve custom sections you've added
   - Only update factual information
   - Maintain formatting consistency
   - Create backups before changes

3. Review the changes:
   - Check git diff after updates
   - Ensure critical custom docs weren't overwritten
   - Validate new patterns make sense

## Notes

- This command uses parallel Task execution for speed
- It reads the actual codebase to ensure accuracy
- Security patterns are carefully validated
- All updates maintain backward compatibility