# Update Context Implementation Prompt

You need to update and synchronize all project context files with the current codebase state. Execute these tasks in parallel for efficiency:

## Task 1: Analyze Codebase Changes
Use the Task tool to analyze the current codebase structure:
- Scan `/agents/` directory for all agent definitions
- Check `pyproject.toml` for current dependency versions
- Review `/api/routes/` for current endpoints
- Examine `/workflows/` for workflow patterns
- List all configuration files in `/config/`

## Task 2: Update CLAUDE.md
Use the Task tool to update the main context file:
- Review current `/home/namastex/workspace/genie-agents/CLAUDE.md`
- Update project phase and status if changed
- Refresh MCP server integration sections with current patterns
- Update agent-specific instructions based on new agents found
- Ensure all sections reflect current architecture

## Task 3: Update project-structure.md
Use the Task tool to update the structure documentation:
- Review `/home/namastex/workspace/genie-agents/docs/ai-context/project-structure.md`
- Update all technology versions from `pyproject.toml`
- Regenerate directory tree based on actual file system
- Document all agent factories found in `/agents/`
- Update integration services and APIs

## Task 4: Update MCP-ASSISTANT-RULES.md
Use the Task tool to update Gemini coding standards:
- Review `/home/namastex/workspace/genie-agents/MCP-ASSISTANT-RULES.md`
- Update with latest Agno Framework patterns
- Refresh code organization standards based on current structure
- Update API patterns from actual route implementations
- Sync performance considerations with monitoring setup

## Task 5: Update sensitive-patterns.json
Use the Task tool to update security patterns:
- Review `/home/namastex/workspace/genie-agents/.claude/hooks/config/sensitive-patterns.json`
- Scan codebase for new API key patterns (grep for _KEY, _TOKEN, _SECRET)
- Identify new sensitive file patterns
- Update whitelist with commonly used placeholders
- Remove patterns for deprecated services

## Final Summary
After all tasks complete:
1. Summarize all changes made to each file
2. List any inconsistencies or issues found
3. Provide a change count for each file
4. Suggest any additional updates that might be needed

Remember to:
- Preserve custom documentation sections
- Only update factual information (versions, paths, etc.)
- Maintain consistent formatting
- Keep all examples working and current