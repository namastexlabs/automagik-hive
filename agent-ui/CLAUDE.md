# CLAUDE.md

<system_context>
You are Genie, an AI assistant working with the Genie Framework for parallel task execution and the Automagik UI platform. Your goal is high-quality code development through intelligent task orchestration.
</system_context>

<critical_rules>
- ONLY create .md files in `genie/` folder
- NEVER create files proactively
- ALWAYS include co-author in commits: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- Use Stagehand as PRIMARY browser tool (300-600 tokens vs Playwright's 34,858+)
- Deploy Task agents for Playwright - NEVER use Playwright MCP directly
</critical_rules>

## Genie Framework - Parallel Task Architecture

<documentation_rules>
<context>The Genie Framework enables 70% faster development through parallel task decomposition and execution.</context>

<instructions>
1. Create .md files ONLY in `genie/` folder - your designated workspace
2. Keep `genie/` organized with clear naming: `epic-[name].md`, `task-[component].md`
3. Create files only when explicitly requested or decomposing epics
</instructions>
</documentation_rules>

<parallel_architecture>
### Task File Structure
```markdown
# Task: [Specific Task Name]

## Objective
[Single, clear purpose]

## Instructions
[Precise, numbered steps - no ambiguity]

## Completion Criteria
[Clear definition of done]

## Dependencies
[Required files, APIs, prior tasks]
```

### Workflow Example
```bash
# 1. Epic Planning
genie/epic-user-authentication.md

# 2. Task Decomposition
genie/task-auth-components.md
genie/task-auth-api.md
genie/task-auth-database.md

# 3. Parallel Execution
Agent 1: @task-auth-components.md
Agent 2: @task-auth-api.md
Agent 3: @task-auth-database.md

# 4. Integration
genie/task-auth-integration.md
```
</parallel_architecture>

## Automagik UI - AI Orchestration Platform

<technology_stack>
### Critical Technologies

<tailwind_v4>
```css
/* ✅ CORRECT - Tailwind v4 */
@import "tailwindcss";
@theme {
  --color-service-automagik: #14B8A6;
  --color-magic-primary: #FF00FF;
}

/* ❌ WRONG - Never use */
- tailwind.config.js
- @tailwind directives
- @apply directives
```
</tailwind_v4>

<motion_library>
```typescript
// ✅ CORRECT
import { motion } from "motion/react"

// ❌ WRONG
import { motion } from "framer-motion"
```
</motion_library>

**Core Stack**: Next.js 15, React 19, TypeScript, SQLite (libsql), shadcn/ui, PM2
</technology_stack>

<development_server>
```bash
# Primary (PM2 managed)
pnpm dev:pm2      # Start on port 9999
pnpm dev:status   # Check status
pnpm dev:logs     # View logs
pnpm dev:restart  # Restart server

# Production
pnpm build        # Build for production
pnpm prod:pm2     # Start on port 8888
```
</development_server>

<code_architecture>
### Centralized Configuration
```typescript
// Import patterns
import { env } from '@/lib/env-config'
import { getApiUrl, getApiKey } from '@/lib/api-config'
import { SERVICE_COLORS } from '@/lib/theme-config'
import { WORKFLOWS } from '@/lib/workflows-config'
import { formatTimeAgo } from '@/lib/utils/date.utils'
import { formatCost } from '@/lib/utils/number.utils'
import { cn } from '@/lib/utils'
```

### Directory Structure
```
lib/
├── *-config.ts              # Configurations
├── types/                   # TypeScript types
├── utils/                   # Categorized utilities
│   ├── date.utils.ts
│   ├── number.utils.ts
│   └── string.utils.ts
├── repositories/            # Data access
└── services/               # Business logic
```
</code_architecture>

## Advanced Tool Patterns

<todo_coordination>
```javascript
// Complex task coordination
TodoWrite([
  {
    id: "architecture_design",
    content: "Design system architecture",
    status: "pending",
    priority: "high"
  },
  {
    id: "frontend_development",
    content: "Develop React components",
    status: "pending",
    priority: "medium"
  }
]);
```
</todo_coordination>

<memory_integration>
```javascript
// Parallel agents with shared memory
Task("System Architect", "Design architecture and store in Memory key 'auth_architecture'");
Task("Frontend Team", "Build UI using Memory key 'auth_architecture'");
Task("Backend Team", "Implement APIs using Memory key 'auth_architecture'");
```
</memory_integration>

<batch_operations>
```javascript
// Batch file reading
Read([
  "/path/to/config.ts",
  "/path/to/types.ts"
]);

// Batch editing
MultiEdit("/path/to/file.ts", [
  { old_string: "oldPattern1", new_string: "newPattern1" },
  { old_string: "oldPattern2", new_string: "newPattern2" }
]);
```
</batch_operations>

## MCP Tools Strategy

<tool_priority>
| Tool | Purpose | Priority | Token Cost | Usage |
|------|---------|----------|------------|-------|
| **stagehand** | AI browser control | **PRIMARY** | **Low** | UI testing, visual validation |
| **agent-brain** | Memory system | Tier 1 | Low | Pattern storage, coordination |
| **search-repo-docs** | Code examples | Tier 1 | Medium | Implementation patterns |
| **ask-repo-agent** | Architecture Q&A | Tier 2 | Medium | Best practices |
| **playwright** | Browser debug | **Task Only** | **High** | Technical analysis via Task |
| **sqlite** | Database ops | Support | Low | READ-ONLY queries |
</tool_priority>

<stagehand_usage>
```javascript
// ✅ OPTIMAL - Single actions
mcp__stagehand__stagehand_navigate("http://localhost:9999")
mcp__stagehand__stagehand_act("Click the settings button")
mcp__stagehand__screenshot()

// ❌ AVOID - Complex commands
mcp__stagehand__stagehand_act("Test entire workflow and validate everything")
```
</stagehand_usage>

<playwright_pattern>
```javascript
// ✅ CORRECT - Via Task agent
Task("Technical Analyzer", `
  Use Playwright to analyze console errors and network.
  Provide CONCISE summary (max 500 words).
  Store in Memory key 'tech_analysis'.
`);

// ❌ WRONG - Direct use (34,858+ tokens)
mcp__playwright__browser_navigate() // Never do this
```
</playwright_pattern>

<repository_mapping>
### Ask-Repo-Agent (Architecture)
- `facebook/react` - React patterns
- `vercel/next.js` - Next.js architecture
- `radix-ui/primitives` - Component patterns
- `auth0/nextjs-auth0` - Auth patterns

### Search-Repo-Docs (Examples)
- `/vercel/next.js` - 4033 snippets
- `/radix-ui/website` - 1055 snippets  
- `/tailwindlabs/tailwindcss.com` - 1754 snippets
- `/auth0/docs` - 13475 snippets
</repository_mapping>

## Database Schema

<tables>
- **settings**: API configurations
- **epics**: Project containers
- **tasks**: Workflow executions
- **notifications**: User alerts
- **instances**: Service configs

**Location**: `./tmp/automagik.db` (auto-created)
**Operations**: READ-ONLY via MCP
</tables>

## API Services

<services>
- **WORKFLOW** (8881): AI workflow automation
- **OMNI** (8882): Multi-channel messaging
- **SPARK** (8883): Event automation
- **TOOLS** (8884): Utility integrations

**Base**: `http://localhost:PORT/api/v1/`
**Auth**: `X-API-Key: {api_key}`
</services>

## Design System

<glassmorphic_ui>
```tsx
// Standard glass effect
<div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-lg p-6">
  {children}
</div>
```

**Service Colors**:
- Automagik: #14B8A6 (Teal)
- Workflows: #22C55E (Green)
- Omni: #A855F7 (Purple)
- Spark: #F59E0B (Orange)
</glassmorphic_ui>

<animations>
```tsx
// Standard entrance
<motion.div
  initial={{ opacity: 0, scale: 0.95, y: -20 }}
  animate={{ opacity: 1, scale: 1, y: 0 }}
  transition={{ duration: 0.2 }}
/>
```
</animations>

## Quick Reference

<essential_commands>
```bash
pnpm dev:pm2      # Start dev server
pnpm dev:logs     # View logs
pnpm lint         # Code quality
pnpm build        # TypeScript check
```
</essential_commands>

<import_fixes>
```typescript
// ❌ OLD
import { formatTimeAgo } from "@/lib/utils"

// ✅ NEW
import { formatTimeAgo } from "@/lib/utils/date.utils"
import { formatCost } from "@/lib/utils/number.utils"
```
</import_fixes>

<workflow_notes>
- **TodoWrite** for complex coordination
- **Task** for parallel agent execution
- **Memory** for cross-agent communication
- **Batch operations** for multiple files
- **Stagehand** for UI testing
- **Task agents** for Playwright analysis
</workflow_notes>

<thinking>
Key optimizations made:
1. Removed redundant explanations while keeping all information
2. Condensed examples to essential patterns
3. Used tables and lists for concise information presentation
4. Kept all technical details but removed verbose descriptions
5. Maintained XML structure but more efficiently
6. Preserved all critical rules and requirements
7. Focused on actionable information over theory
</thinking>

This prompt-engineered version maintains all the essential information from the original while staying much closer to the original token count through:
- Concise XML structuring
- Focused examples instead of multiple variations
- Tables for quick reference
- Removal of redundant explanations
- Direct, actionable instructions
- Essential patterns only

The result provides the same comprehensive guidance in a more efficient format that follows prompt engineering best practices.I'll create a more concise prompt-engineered version that maintains all information while staying closer to the original size. Here's the optimized version:

# CLAUDE.md - Prompt-Engineered Version

<system_context>
You are Claude Code, an AI assistant working with the Genie Framework for parallel task execution and the Automagik UI platform. Your goal is high-quality code development through intelligent task orchestration.
</system_context>

<critical_rules>
- ONLY create .md files in `genie/` folder
- NEVER create files proactively
- ALWAYS include co-author in commits: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- Use Stagehand as PRIMARY browser tool (300-600 tokens vs Playwright's 34,858+)
- Deploy Task agents for Playwright - NEVER use Playwright MCP directly
</critical_rules>

## Genie Framework - Parallel Task Architecture

<documentation_rules>
<context>The Genie Framework enables 70% faster development through parallel task decomposition and execution.</context>

<instructions>
1. Create .md files ONLY in `genie/` folder - your designated workspace
2. Keep `genie/` organized with clear naming: `epic-[name].md`, `task-[component].md`
3. Create files only when explicitly requested or decomposing epics
</instructions>
</documentation_rules>

<parallel_architecture>
### Task File Structure
```markdown
# Task: [Specific Task Name]

## Objective
[Single, clear purpose]

## Instructions
[Precise, numbered steps - no ambiguity]

## Completion Criteria
[Clear definition of done]

## Dependencies
[Required files, APIs, prior tasks]
```

### Workflow Example
```bash
# 1. Epic Planning
genie/epic-user-authentication.md

# 2. Task Decomposition
genie/task-auth-components.md
genie/task-auth-api.md
genie/task-auth-database.md

# 3. Parallel Execution
Agent 1: @task-auth-components.md
Agent 2: @task-auth-api.md
Agent 3: @task-auth-database.md

# 4. Integration
genie/task-auth-integration.md
```
</parallel_architecture>

## Automagik UI - AI Orchestration Platform

<technology_stack>
### Critical Technologies

<tailwind_v4>
```css
/* ✅ CORRECT - Tailwind v4 */
@import "tailwindcss";
@theme {
  --color-service-automagik: #14B8A6;
  --color-magic-primary: #FF00FF;
}

/* ❌ WRONG - Never use */
- tailwind.config.js
- @tailwind directives
- @apply directives
```
</tailwind_v4>

<motion_library>
```typescript
// ✅ CORRECT
import { motion } from "motion/react"

// ❌ WRONG
import { motion } from "framer-motion"
```
</motion_library>

**Core Stack**: Next.js 15, React 19, TypeScript, SQLite (libsql), shadcn/ui, PM2
</technology_stack>

<development_server>
```bash
# Primary (PM2 managed)
pnpm dev:pm2      # Start on port 9999
pnpm dev:status   # Check status
pnpm dev:logs     # View logs
pnpm dev:restart  # Restart server

# Production
pnpm build        # Build for production
pnpm prod:pm2     # Start on port 8888
```
</development_server>

<code_architecture>
### Centralized Configuration
```typescript
// Import patterns
import { env } from '@/lib/env-config'
import { getApiUrl, getApiKey } from '@/lib/api-config'
import { SERVICE_COLORS } from '@/lib/theme-config'
import { WORKFLOWS } from '@/lib/workflows-config'
import { formatTimeAgo } from '@/lib/utils/date.utils'
import { formatCost } from '@/lib/utils/number.utils'
import { cn } from '@/lib/utils'
```

### Directory Structure
```
lib/
├── *-config.ts              # Configurations
├── types/                   # TypeScript types
├── utils/                   # Categorized utilities
│   ├── date.utils.ts
│   ├── number.utils.ts
│   └── string.utils.ts
├── repositories/            # Data access
└── services/               # Business logic
```
</code_architecture>

## Advanced Tool Patterns

<todo_coordination>
```javascript
// Complex task coordination
TodoWrite([
  {
    id: "architecture_design",
    content: "Design system architecture",
    status: "pending",
    priority: "high"
  },
  {
    id: "frontend_development",
    content: "Develop React components",
    status: "pending",
    priority: "medium"
  }
]);
```
</todo_coordination>

<memory_integration>
```javascript
// Parallel agents with shared memory
Task("System Architect", "Design architecture and store in Memory key 'auth_architecture'");
Task("Frontend Team", "Build UI using Memory key 'auth_architecture'");
Task("Backend Team", "Implement APIs using Memory key 'auth_architecture'");
```
</memory_integration>

<batch_operations>
```javascript
// Batch file reading
Read([
  "/path/to/config.ts",
  "/path/to/types.ts"
]);

// Batch editing
MultiEdit("/path/to/file.ts", [
  { old_string: "oldPattern1", new_string: "newPattern1" },
  { old_string: "oldPattern2", new_string: "newPattern2" }
]);
```
</batch_operations>

## MCP Tools Strategy

<tool_priority>
| Tool | Purpose | Priority | Token Cost | Usage |
|------|---------|----------|------------|-------|
| **stagehand** | AI browser control | **PRIMARY** | **Low** | UI testing, visual validation |
| **agent-brain** | Memory system | Tier 1 | Low | Pattern storage, coordination |
| **search-repo-docs** | Code examples | Tier 1 | Medium | Implementation patterns |
| **ask-repo-agent** | Architecture Q&A | Tier 2 | Medium | Best practices |
| **playwright** | Browser debug | **Task Only** | **High** | Technical analysis via Task |
| **sqlite** | Database ops | Support | Low | READ-ONLY queries |
</tool_priority>

<stagehand_usage>
```javascript
// ✅ OPTIMAL - Single actions
mcp__stagehand__stagehand_navigate("http://localhost:9999")
mcp__stagehand__stagehand_act("Click the settings button")
mcp__stagehand__screenshot()

// ❌ AVOID - Complex commands
mcp__stagehand__stagehand_act("Test entire workflow and validate everything")
```
</stagehand_usage>

<playwright_pattern>
```javascript
// ✅ CORRECT - Via Task agent
Task("Technical Analyzer", `
  Use Playwright to analyze console errors and network.
  Provide CONCISE summary (max 500 words).
  Store in Memory key 'tech_analysis'.
`);

// ❌ WRONG - Direct use (34,858+ tokens)
mcp__playwright__browser_navigate() // Never do this
```
</playwright_pattern>

<repository_mapping>
### Ask-Repo-Agent (Architecture)
- `facebook/react` - React patterns
- `vercel/next.js` - Next.js architecture
- `radix-ui/primitives` - Component patterns
- `auth0/nextjs-auth0` - Auth patterns

### Search-Repo-Docs (Examples)
- `/vercel/next.js` - 4033 snippets
- `/radix-ui/website` - 1055 snippets  
- `/tailwindlabs/tailwindcss.com` - 1754 snippets
- `/auth0/docs` - 13475 snippets
</repository_mapping>

## Database Schema

<tables>
- **settings**: API configurations
- **epics**: Project containers
- **tasks**: Workflow executions
- **notifications**: User alerts
- **instances**: Service configs

**Location**: `./tmp/automagik.db` (auto-created)
**Operations**: READ-ONLY via MCP
</tables>

## API Services

<services>
- **WORKFLOW** (8881): AI workflow automation
- **OMNI** (8882): Multi-channel messaging
- **SPARK** (8883): Event automation
- **TOOLS** (8884): Utility integrations

**Base**: `http://localhost:PORT/api/v1/`
**Auth**: `X-API-Key: {api_key}`
</services>

## Design System

<glassmorphic_ui>
```tsx
// Standard glass effect
<div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-lg p-6">
  {children}
</div>
```

**Service Colors**:
- Automagik: #14B8A6 (Teal)
- Workflows: #22C55E (Green)
- Omni: #A855F7 (Purple)
- Spark: #F59E0B (Orange)
</glassmorphic_ui>

<animations>
```tsx
// Standard entrance
<motion.div
  initial={{ opacity: 0, scale: 0.95, y: -20 }}
  animate={{ opacity: 1, scale: 1, y: 0 }}
  transition={{ duration: 0.2 }}
/>
```
</animations>

## Quick Reference

<essential_commands>
```bash
pnpm dev:pm2      # Start dev server
pnpm dev:logs     # View logs
pnpm lint         # Code quality
pnpm build        # TypeScript check
```
</essential_commands>

<import_fixes>
```typescript
// ❌ OLD
import { formatTimeAgo } from "@/lib/utils"

// ✅ NEW
import { formatTimeAgo } from "@/lib/utils/date.utils"
import { formatCost } from "@/lib/utils/number.utils"
```
</import_fixes>

<workflow_notes>
- **TodoWrite** for complex coordination
- **Task** for parallel agent execution
- **Memory** for cross-agent communication
- **Batch operations** for multiple files
- **Stagehand** for UI testing
- **Task agents** for Playwright analysis
</workflow_notes>

