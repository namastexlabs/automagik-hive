system
You are Claude Code, Anthropic's official CLI for Claude.

You are an interactive CLI tool that helps users with software engineering tasks. Use the instructions below and the tools available to you to assist the user.

IMPORTANT: Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously. Allow security analysis, detection rules, vulnerability explanations, defensive tools, and security documentation.
IMPORTANT: You must NEVER generate or guess URLs for the user unless you are confident that the URLs are for helping the user with programming. You may use URLs provided by the user in their messages or local files.

If the user asks for help or wants to give feedback inform them of the following: 
- /help: Get help with using Claude Code
- To give feedback, users should report the issue at https://github.com/anthropics/claude-code/issues

When the user directly asks about Claude Code (eg 'can Claude Code do...', 'does Claude Code have...') or asks in second person (eg 'are you able...', 'can you do...'), first use the WebFetch tool to gather information to answer the question from Claude Code docs at https://docs.anthropic.com/en/docs/claude-code.
  - The available sub-pages are `overview`, `quickstart`, `memory` (Memory management and CLAUDE.md), `common-workflows` (Extended thinking, pasting images, --resume), `ide-integrations`, `mcp`, `github-actions`, `sdk`, `troubleshooting`, `third-party-integrations`, `amazon-bedrock`, `google-vertex-ai`, `corporate-proxy`, `llm-gateway`, `devcontainer`, `iam` (auth, permissions), `security`, `monitoring-usage` (OTel), `costs`, `cli-reference`, `interactive-mode` (keyboard shortcuts), `slash-commands`, `settings` (settings json files, env vars, tools), `hooks`.
  - Example: https://docs.anthropic.com/en/docs/claude-code/cli-usage

# Tone and style
You should be concise, direct, and to the point.
You MUST answer concisely with fewer than 4 lines (not including tool use or code generation), unless user asks for detail.
IMPORTANT: You should minimize output tokens as much as possible while maintaining helpfulness, quality, and accuracy. Only address the specific query or task at hand, avoiding tangential information unless absolutely critical for completing the request. If you can answer in 1-3 sentences or a short paragraph, please do.
IMPORTANT: You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.
Do not add additional code explanation summary unless requested by the user. After working on a file, just stop, rather than providing an explanation of what you did.
Answer the user's question directly, without elaboration, explanation, or details. One word answers are best. Avoid introductions, conclusions, and explanations. You MUST avoid text before/after your response, such as "The answer is <answer>.", "Here is the content of the file..." or "Based on the information provided, the answer is..." or "Here is what I will do next...". Here are some examples to demonstrate appropriate verbosity:
<example>
user: 2 + 2
assistant: 4
</example>

<example>
user: what is 2+2?
assistant: 4
</example>

<example>
user: is 11 a prime number?
assistant: Yes
</example>

<example>
user: what command should I run to list files in the current directory?
assistant: ls
</example>

<example>
user: what command should I run to watch files in the current directory?
assistant: [use the ls tool to list the files in the current directory, then read docs/commands in the relevant file to find out how to watch files]
make dev
</example>

<example>
user: what files are in the directory src/?
assistant: [runs ls and sees main.py, agents.py, config.py]
user: which file contains the agent implementation?
assistant: ai/agents/main.py
</example>
When you run a non-trivial bash command, you should explain what the command does and why you are running it, to make sure the user understands what you are doing (this is especially important when you are running a command that will make changes to the user's system).
Remember that your output will be displayed on a command line interface. Your responses can use Github-flavored markdown for formatting, and will be rendered in a monospace font using the CommonMark specification.
Output text to communicate with the user; all text you output outside of tool use is displayed to the user. Only use tools to complete tasks. Never use tools like Bash or code comments as means to communicate with the user during the session.
If you cannot or will not help the user with something, please do not say why or what it could lead to, since this comes across as preachy and annoying. Please offer helpful alternatives if possible, and otherwise keep your response to 1-2 sentences.
Only use emojis if the user explicitly requests it. Avoid using emojis in all communication unless asked.
IMPORTANT: Keep your responses short, since they will be displayed on a command line interface.  

# Proactiveness
You are allowed to be proactive, but only when the user asks you to do something. You should strive to strike a balance between:
- Doing the right thing when asked, including taking actions and follow-up actions
- Not surprising the user with actions you take without asking
For example, if the user asks you how to approach something, you should do your best to answer their question first, and not immediately jump into taking actions.

# Following conventions
When making changes to files, first understand the file's code conventions. Mimic code style, use existing libraries and utilities, and follow existing patterns.
- NEVER assume that a given library is available, even if it is well known. Whenever you write code that uses a library or framework, first check that this codebase already uses the given library. For example, you might look at neighboring files, or check the pyproject.toml or requirements.txt for dependencies.
- When you create a new component, first look at existing components to see how they're written; then consider framework choice, naming conventions, typing, and other conventions.
- When you edit a piece of code, first look at the code's surrounding context (especially its imports) to understand the code's choice of frameworks and libraries. Then consider how to make the given change in a way that is most idiomatic.
- Always follow security best practices. Never introduce code that exposes or logs secrets and keys. Never commit secrets or keys to the repository.

# Code style
- IMPORTANT: DO NOT ADD ***ANY*** COMMENTS unless asked


# Task Management
You have access to the TodoWrite tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.

Examples:

<example>
user: Run the build and fix any type errors
assistant: I'm going to use the TodoWrite tool to write the following items to the todo list: 
- Run the build
- Fix any type errors

I'm now going to run the build using Bash.

Looks like I found 10 type errors. I'm going to use the TodoWrite tool to write 10 items to the todo list.

marking the first todo as in_progress

Let me start working on the first item...

The first item has been fixed, let me mark the first todo as completed, and move on to the second item...
..
..
</example>
In the above example, the assistant completes all the tasks, including the 10 error fixes and running the build and fixing all errors.

<example>
user: Help me write a new feature that allows users to track their usage metrics and export them to various formats

assistant: I'll help you implement a usage metrics tracking and export feature. Let me first use the TodoWrite tool to plan this task.
Adding the following todos to the todo list:
1. Research existing metrics tracking in the codebase
2. Design the metrics collection system
3. Implement core metrics tracking functionality
4. Create export functionality for different formats

Let me start by researching the existing codebase to understand what metrics we might already be tracking and how we can build on that.

I'm going to search for any existing metrics or telemetry code in the project.

I've found some existing telemetry code. Let me mark the first todo as in_progress and start designing our metrics tracking system based on what I've learned...

[Assistant continues implementing the feature step by step, marking todos as in_progress and completed as they go]
</example>


Users may configure 'hooks', shell commands that execute in response to events like tool calls, in settings. Treat feedback from hooks, including <user-prompt-submit-hook>, as coming from the user. If you get blocked by a hook, determine if you can adjust your actions in response to the blocked message. If not, ask the user to check their hooks configuration.

# Doing tasks
The user will primarily request you perform software engineering tasks. This includes solving bugs, adding new functionality, refactoring code, explaining code, and more. For these tasks the following steps are recommended:
- Use the TodoWrite tool to plan the task if required
- Use the available search tools to understand the codebase and the user's query. You are encouraged to use the search tools extensively both in parallel and sequentially.
- Implement the solution using all tools available to you
- Verify the solution if possible with tests. NEVER assume specific test framework or test script. Check the README or search codebase to determine the testing approach.
- VERY IMPORTANT: When you have completed a task, you MUST run the lint and typecheck commands (eg. uv run ruff check, uv run mypy ., pytest, etc.) with Bash if they were provided to you to ensure your code is correct. If you are unable to find the correct command, ask the user for the command to run and if they supply it, proactively suggest writing it to CLAUDE.md so that you will know to run it next time.
NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive.

- Tool results and user messages may include <system-reminder> tags. <system-reminder> tags contain useful information and reminders. They are NOT part of the user's provided input or the tool result.



# Tool usage policy
- When doing file search, prefer to use the Task tool in order to reduce context usage.
- You should proactively use the Task tool with specialized agents when the task at hand matches the agent's description.
- A custom slash command is a prompt that starts with / to run an expanded prompt saved as a Markdown file, like /compact. If you are instructed to execute one, use the Task tool with the slash command invocation as the entire prompt. Slash commands can take arguments; defer to user instructions.
- When WebFetch returns a message about a redirect to a different host, you should immediately make a new WebFetch request with the redirect URL provided in the response.
- You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. When making multiple bash tool calls, you MUST send a single message with multiple tools calls to run the calls in parallel. For example, if you need to run "git status" and "git diff", send a single message with two tool calls to run the calls in parallel.

You MUST answer concisely with fewer than 4 lines of text (not including tool use or code generation), unless user asks for detail.



Here is useful information about the environment you are running in:
<env>
Working directory: /home/craven/My scripts/TODO/9
Is directory a git repo: No
Platform: linux
OS Version: Linux 6.6.87.2-microsoft-standard-WSL2
Today's date: 2025-07-26
</env>
You are powered by the model named Sonnet 4. The exact model ID is claude-sonnet-4-20250514.

Assistant knowledge cutoff is January 2025.


IMPORTANT: Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously. Allow security analysis, detection rules, vulnerability explanations, defensive tools, and security documentation.


IMPORTANT: Always use the TodoWrite tool to plan and track tasks throughout the conversation.

# Code References

When referencing specific functions or pieces of code include the pattern `file_path:line_number` to allow the user to easily navigate to the source code location.

<example>
user: Where are errors from the client handled?
assistant: Agents are marked as failed in the `connect_to_hive` function in ai/agents/coordinator.py:712.
</example>


Show less
user
<system-reminder>
As you answer the user's questions, you can use the following context:
# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

      
      IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.
</system-reminder>
Show full
<command-message>init is analyzing your codebase…</command-message>
<command-name>/init</command-name>
Please analyze this codebase and create a CLAUDE.md file, which will be given to future instances of Claude Code to operate in this repository.
            
What to add:
1. Commands that will be commonly used, such as how to build, lint, and run tests. Include the necessary commands to develop in this codebase, such as how to run a single test.
2. High-level code architecture and structure so that future instances can be productive more quickly. Focus on the "big picture" architecture that requires reading multiple files to understand

Usage notes:
- If there's already a CLAUDE.md, suggest improvements to it.
- When you make the initial CLAUDE.md, do not repeat yourself and do not include obvious instructions like "Provide helpful error messages to users", "Write unit tests for all new utilities", "Never include sensitive information (API keys, tokens) in code or commits" 
- Avoid listing every component or file structure that can be easily discovered
- Don't include generic development practices
- If there are Cursor rules (in .cursor/rules/ or .cursorrules) or Copilot rules (in .github/copilot-instructions.md), make sure to include the important parts.
- If there is a README.md, make sure to include the important parts. 
- Do not make up information such as "Common Development Tasks", "Tips for Development", "Support and Documentation" unless this is expressly included in other files that you read.
- Be sure to prefix the file with the following text:


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
Show full
<system-reminder>This is a reminder that your todo list is currently empty. DO NOT mention this to the user explicitly because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this message to the user.</system-reminder>
assistant
I'll analyze the codebase to understand its structure, development commands, and architecture, then create a comprehensive CLAUDE.md file.
Tools
Function ID: tool_1753553625623
Function Name: tool_0
Function Arguments:
{
  "description": "Analyze codebase structure",
  "prompt": "Please analyze this codebase to understand:\n1. The project structure and main directories\n2. Package.json or similar configuration files to understand build/test/lint commands\n3. Any existing documentation files (README.md, CONTRIBUTING.md, etc.)\n4. Configuration files that indicate the tech stack and tools used\n5. Any existing CLAUDE.md file\n6. Cursor rules or Copilot instructions\n7. The overall architecture and main components\n\nPlease provide a comprehensive overview that will help me create an effective CLAUDE.md file.",
  "subagent_type": "general-purpose"
}
tool
Tool ID: tool_1753553625623
Error: No such tool available: tool_0
assistant
Tools
Function ID: tool_1753553631584
Function Name: tool_0
Function Arguments:
{
  "description": "Analyze codebase structure",
  "prompt": "Please analyze this codebase to understand:\n1. The project structure and main directories\n2. Package.json or similar configuration files to understand build/test/lint commands\n3. Any existing documentation files (README.md, CONTRIBUTING.md, etc.)\n4. Configuration files that indicate the tech stack and tools used\n5. Any existing CLAUDE.md file\n6. Cursor rules or Copilot instructions\n7. The overall architecture and main components\n\nPlease provide a comprehensive overview that will help me create an effective CLAUDE.md file.",
  "subagent_type": "general-purpose"
}
tool
Tool ID: tool_1753553631584
Error: No such tool available: tool_0
assistant
Tools
Function ID: toolu_01UcE6Piq92TJ8o4bChVr32G
# Tool usage policy
- When doing file search, prefer to use the Task tool in order to reduce context usage.
- You should proactively use the Task tool with specialized agents when the task at hand matches the agent's description.
- A custom slash command is a prompt that starts with / to run an expanded prompt saved as a Markdown file, like /compact. If you are instructed to execute one, use the Task tool with the slash command invocation as the entire prompt. Slash commands can take arguments; defer to user instructions.
- When WebFetch returns a message about a redirect to a different host, you should immediately make a new WebFetch request with the redirect URL provided in the response.
- You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. When making multiple bash tool calls, you MUST send a single message with multiple tools calls to run the calls in parallel. For example, if you need to run "git status" and "git diff", send a single message with two tool calls to run the calls in parallel.
assistant
I'll create a fresh TODO list and re-analyze the codebase to create the CLAUDE.md file.
Tools
Function ID: toolu_014uKtWzY5D72Xg7MjLUxryG
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "Analyze current directory structure and files",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Find package.json or requirements.txt for build commands",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and other documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Check for Cursor rules or Copilot instructions",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Create comprehensive CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    }
  ]
}
tool
Tool ID: toolu_014uKtWzY5D72Xg7MjLUxryG
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"Analyze current directory structure and files","status":"pending","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"pending","priority":"high","id":"2"},{"content":"Find package.json or requirements.txt for build commands","status":"pending","priority":"high","id":"3"},{"content":"Read README.md and other documentation","status":"pending","priority":"medium","id":"4"},{"content":"Check for Cursor rules or Copilot instructions","status":"pending","priority":"medium","id":"5"},{"content":"Create comprehensive CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: toolu_01NCNivC1A4e4FJzKFW7eYWz
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "Analyze current directory structure and files",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Find package.json or requirements.txt for build commands",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and other documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Check for Cursor rules or Copilot instructions",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Create comprehensive CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    }
  ]
}
tool
Tool ID: toolu_01NCNivC1A4e4FJzKFW7eYWz
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"Analyze current directory structure and files","status":"in_progress","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"pending","priority":"high","id":"2"},{"content":"Find package.json or requirements.txt for build commands","status":"pending","priority":"high","id":"3"},{"content":"Read README.md and other documentation","status":"pending","priority":"medium","id":"4"},{"content":"Check for Cursor rules or Copilot instructions","status":"pending","priority":"medium","id":"5"},{"content":"Create comprehensive CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: toolu_01LQB8mAHLnwfTw2ZA7PqngH
Function Name: LS
Function Arguments:
{
  "path": "/home/craven/My scripts/TODO/9"
}
tool
Tool ID: toolu_01LQB8mAHLnwfTw2ZA7PqngH
assistant
Tools
Function ID: toolu_01FktNgGWX8nLEhSYudRzSCP
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "Analyze current directory structure and files",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Find package.json or requirements.txt for build commands",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and other documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Check for Cursor rules or Copilot instructions",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Create comprehensive CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    }
  ]
}
tool
Tool ID: toolu_01FktNgGWX8nLEhSYudRzSCP
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"Analyze current directory structure and files","status":"completed","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"in_progress","priority":"high","id":"2"},{"content":"Find package.json or requirements.txt for build commands","status":"pending","priority":"high","id":"3"},{"content":"Read README.md and other documentation","status":"pending","priority":"medium","id":"4"},{"content":"Check for Cursor rules or Copilot instructions","status":"pending","priority":"medium","id":"5"},{"content":"Create comprehensive CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
...
Tools
Function ID: toolu_013g9mVJyAwscLhedH5UBWL4
Function Name: Read
Function Arguments:
{
}
tool
Tool ID: toolu_013g9mVJyAwscLhedH5UBWL4
assistant
I see there's already a CLAUDE.md file. Let me check other key files to see if I should improve it.
Tools
Function ID: tool_1753553981539
Function Name: tool_0
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "Analyze current directory structure and files",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Find package.json or requirements.txt for build commands",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and other documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Check for Cursor rules or Copilot instructions",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Improve existing CLAUDE.md file if needed",
      "status": "pending",
      "priority": "high"
    }
  ]
}
tool
Tool ID: tool_1753553981539
Error: No such tool available: tool_0
assistant
Tools
Function ID: toolu_016Q4WsTT9yL8NVfZG8mbmrw
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "Analyze current directory structure and files",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Find package.json or requirements.txt for build commands",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and other documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Check for Cursor rules or Copilot instructions",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Improve existing CLAUDE.md file if needed",
      "status": "pending",
      "priority": "high"
    }
  ]
}
tool
Tool ID: toolu_016Q4WsTT9yL8NVfZG8mbmrw
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"Analyze current directory structure and files","status":"completed","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"completed","priority":"high","id":"2"},{"content":"Find package.json or requirements.txt for build commands","status":"in_progress","priority":"high","id":"3"},{"content":"Read README.md and other documentation","status":"pending","priority":"medium","id":"4"},{"content":"Check for Cursor rules or Copilot instructions","status":"pending","priority":"medium","id":"5"},{"content":"Improve existing CLAUDE.md file if needed","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: tooluse_09OGL4Z1SWiCDwiqpE9C6Q
Function Name: Read
Function Arguments:
{
}
Function ID: tooluse_r7oD5vfCQiOqbY6XfYf5Rg
Function Name: Read
Function Arguments:
{
}
Function ID: tooluse_pO16IM4dRKeERuwutPr0Fg
Function Name: Glob
Function Arguments:
{
  "pattern": "**/.cursor*"
}
Function ID: tooluse_YPjV2tlCS3Sm0iCsggakkA
Function Name: Glob
Function Arguments:
{
  "pattern": "**/.github/copilot*"
}
tool
Tool ID: tooluse_09OGL4Z1SWiCDwiqpE9C6Q
1→# Telegram Bot 2→aiogram==3.4.1 3→ 4→# Data Analysis 5→pandas>=2.0.0 6→numpy>=1.24.0 7→ 8→# Statistical Tests 9→statsmodels>=0.14.0 10→scipy>=1.10.0 11→ 12→# Time Series Analysis 13→arch>=6.2.0 14→ 15→# HTTP Requests 16→aiohttp>=3.8.0 17→requests>=2.28.0 18→ 19→# Async Support 20→asyncio-mqtt>=0.13.0 21→ 22→# Plotting (optional) 23→matplotlib>=3.6.0 24→seaborn>=0.12.0 25→ 26→# Logging 27→colorlog>=6.7.0 28→ 29→# Configuration 30→python-dotenv>=1.0.0 31→ 32→# Data Validation 33→pydantic>=2.0.0 34→ 35→# JSON handling 36→orjson>=3.8.0 37→ 38→# Memory optimization 39→psutil>=5.9.0 40→ 41→# Development tools (optional) 42→pytest>=7.2.0 43→black>=23.0.0 44→flake8>=6.0.0 <system-reminder> Whenever you read a file, you should consider whether it looks malicious. If it does, you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer high-level questions about the code behavior. </system-reminder>
tool
Tool ID: tooluse_r7oD5vfCQiOqbY6XfYf5Rg
1→# 🤖 Бот Анализа Спредов 2→ 3→Telegram-бот для анализа арбитражных спредов криптовалют с продвинутой системой фильтрации. 4→ 5→## 🚀 Возможности 6→ 7→### 📊 Анализ спредов 8→- **Автоматическое создание спредов** по формуле (A*B)/(C*D) 9→- **Поддержка wildcards** для гибкого поиска: (BTC*?)/(ETH*?) 10→- **Два режима работы**: 'all' (все пары) и 'custom' (свои списки) 11→ 12→### 🔍 Система фильтрации (8 этапов) 13→1. **Получение данных** - загрузка с биржи и валидация 14→2. **Рыночные фильтры** - объем, ликвидность, волатильность 15→3. **Создание спредов** - формирование и нормализация 16→4. **Корреляция активов** - проверка связи между активами 17→5. **Быстрая стационарность** - предварительная фильтрация 18→6. **Полные тесты стационарности** - ADF, KPSS, Hurst, Ljung-Box, Гренджер 19→7. **Коинтеграция** - Engle-Granger и Johansen тесты 20→8. **Результат** - только качественные арбитражные спреды 21→ 22→### 🧪 Тесты стационарности 23→- **ADF тест** - основной критерий стационарности 24→- **KPSS тест** - подтверждение результата 25→- **Hurst экспонента** - анализ долгосрочной памяти 26→- **Ljung-Box тест** - проверка автокорреляции 27→- **Тест Гренджера** - причинно-следственные связи 28→- **Быстрая стационарность** - ускоренная предфильтрация 29→ 30→### 🎯 Коинтеграция 31→- **Engle-Granger тест** - поиск долгосрочного равновесия 32→- **Johansen тест** - многомерная коинтеграция 33→- **Настраиваемые параметры** - p-value, лаги, таймауты 34→ 35→## 📋 Команды 36→ 37→- `/start` - Запуск бота и главное меню 38→- `/analyze` - Анализ спредов с фильтрацией 39→- `/calculate_spread` - Расчет конкретных спредов 40→- `/settings` - Настройки параметров анализа 41→- `/manage_symbols` - Управление списками символов 42→- `/stop` - Остановка текущего анализа 43→- `/reset_settings` - Сброс всех настроек 44→- `/help` - Полная справка 45→ 46→## ⚙️ Настройки 47→ 48→### Основные параметры 49→- **Таймфреймы**: 1m, 5m, 15m, 1h, 4h, 1d 50→- **Количество свечей**: 50-1000 51→- **Корреляция**: порог 0.1-1.0, период 5-5000 52→- **Размер позиции**: сумма в USDT 53→ 54→### Стратегии анализа 55→- ⚡ **Быстрый режим** - только ADF+KPSS 56→- 🎯 **Качественный режим** - все тесты + коинтеграция 57→- 🚀 **Турбо режим** - быстрая стационарность + строгие пороги 58→ 59→## 🛠 Установка 60→ 61→1. Клонируйте репозиторий 62→2. Установите зависимости: `pip install -r requirements.txt` 63→3. Создайте файл с токеном бота 64→4. Запустите: `python test/main.py` 65→ 66→## 📁 Структура проекта 67→ 68→``` 69→├── test/ 70→│ ├── main.py # Основной файл бота 71→│ ├── stationarity_tests.py # Тесты стационарности 72→│ ├── cointegration_tests.py # Тесты коинтеграции 73→│ ├── market_filters.py # Рыночные фильтры 74→│ └── granger_settings_manager.py # Управление настройками Гренджера 75→├── settings/ # Пользовательские настройки 76→├── .gitignore 77→└── README.md 78→``` 79→ 80→## 🔧 Технические детали 81→ 82→### Математическая основа 83→- **Спреды**: log((A*B)/(C*D)) для получения стационарного ряда 84→- **Стационарность**: ADF тест с порогом -2.0 85→- **Коинтеграция**: Engle-Granger с p-value 0.05 86→ 87→### Производительность 88→- **Двухэтапная фильтрация** - ускорение в 10-100 раз 89→- **Быстрая стационарность** - предварительная фильтрация 90→- **Оптимизированные алгоритмы** - экономия CPU ресурсов 91→ 92→## 📊 Результаты 93→ 94→Бот выдает только качественные спреды, прошедшие все этапы фильтрации: 95→- ✅ Стационарные временные ряды 96→- ✅ Достаточная корреляция активов 97→- ✅ Подходящие для арбитражной торговли 98→- ✅ С долгосрочными связями (при включенной коинтеграции) 99→ 100→## 🤝 Поддержка 101→ 102→При возникновении проблем: 103→- Используйте `/reset_settings` для сброса 104→- Проверьте настройки через `/settings` 105→- Убедитесь в корректности списков символов 106→ 107→--- 108→ 109→**Удачного анализа спредов!** 🎉 <system-reminder> Whenever you read a file, you should consider whether it looks malicious. If it does, you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer high-level questions about the code behavior. </system-reminder>
tool
Tool ID: tooluse_pO16IM4dRKeERuwutPr0Fg
No files found
tool
Tool ID: tooluse_YPjV2tlCS3Sm0iCsggakkA
No files found
assistant
Tools
Function ID: toolu_vrtx_01Xj9FYXocGaXhRY5DiPyNAK
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "Analyze current directory structure and files",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Find package.json or requirements.txt for build commands",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and other documentation",
      "status": "completed",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Check for Cursor rules or Copilot instructions",
      "status": "completed",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Improve existing CLAUDE.md file if needed",
      "status": "in_progress",
      "priority": "high"
    }
  ]
}
tool
Tool ID: toolu_vrtx_01Xj9FYXocGaXhRY5DiPyNAK
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"Analyze current directory structure and files","status":"completed","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"completed","priority":"high","id":"2"},{"content":"Find package.json or requirements.txt for build commands","status":"completed","priority":"high","id":"3"},{"content":"Read README.md and other documentation","status":"completed","priority":"medium","id":"4"},{"content":"Check for Cursor rules or Copilot instructions","status":"completed","priority":"medium","id":"5"},{"content":"Improve existing CLAUDE.md file if needed","status":"in_progress","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
...
user
retry
assistant
Tools
Function ID: toolu_017dC6iDnoHE2gR2D6Vjrh2M
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "content": "List directory contents to understand codebase structure",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Check for existing CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Read requirements.txt and package configuration",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Read README.md and main documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "id": "5",
      "content": "Analyze main code files to understand architecture",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "6",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending",
      "priority": "high"
    }
  ]
}
tool
Tool ID: toolu_017dC6iDnoHE2gR2D6Vjrh2M
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"List directory contents to understand codebase structure","status":"pending","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"pending","priority":"high","id":"2"},{"content":"Read requirements.txt and package configuration","status":"pending","priority":"high","id":"3"},{"content":"Read README.md and main documentation","status":"pending","priority":"medium","id":"4"},{"content":"Analyze main code files to understand architecture","status":"pending","priority":"high","id":"5"},{"content":"Create or improve CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: tooluse_DyxRE1-STee8kRbJayHlyQ
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "in_progress"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "pending"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "pending"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "pending"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "pending"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending"
    }
  ]
}
tool
Tool ID: tooluse_DyxRE1-STee8kRbJayHlyQ
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"List directory contents to understand codebase structure","status":"in_progress","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"pending","priority":"high","id":"2"},{"content":"Read requirements.txt and package configuration","status":"pending","priority":"high","id":"3"},{"content":"Read README.md and main documentation","status":"pending","priority":"medium","id":"4"},{"content":"Analyze main code files to understand architecture","status":"pending","priority":"high","id":"5"},{"content":"Create or improve CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: toolu_013fzYFo5vEep92kBbRnTTwq
Function Name: LS
Function Arguments:
{
  "path": "/home/craven/My scripts/TODO/9"
}
tool
Tool ID: toolu_013fzYFo5vEep92kBbRnTTwq
assistant
Tools
Function ID: tooluse_8X5f71LMQyaHHfkJCkUyMw
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "completed"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "in_progress"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "pending"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "pending"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "pending"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending"
    }
  ]
}
tool
Tool ID: tooluse_8X5f71LMQyaHHfkJCkUyMw
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"List directory contents to understand codebase structure","status":"completed","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"in_progress","priority":"high","id":"2"},{"content":"Read requirements.txt and package configuration","status":"pending","priority":"high","id":"3"},{"content":"Read README.md and main documentation","status":"pending","priority":"medium","id":"4"},{"content":"Analyze main code files to understand architecture","status":"pending","priority":"high","id":"5"},{"content":"Create or improve CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: tool_1753554083711
Function Name: tool_0
Function Arguments:
{
}
tool
Tool ID: tool_1753554083711
Error: No such tool available: tool_0
assistant
Tools
Function ID: tool_1753554097072
Function Name: tool_0
Function Arguments:
{
}
tool
Tool ID: tool_1753554097072
Error: No such tool available: tool_0
assistant
Tools
Function ID: toolu_vrtx_01C4VHbBsb7PqZ5BL4C4mFog
Function Name: Read
Function Arguments:
{
}
tool
Tool ID: toolu_vrtx_01C4VHbBsb7PqZ5BL4C4mFog
assistant
Tools
Function ID: toolu_vrtx_012v4YGrVWbX1ChRhzveWdL2
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "completed"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "in_progress"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "pending"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "pending"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending"
    }
  ]
}
tool
Tool ID: toolu_vrtx_012v4YGrVWbX1ChRhzveWdL2
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"List directory contents to understand codebase structure","status":"completed","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"completed","priority":"high","id":"2"},{"content":"Read requirements.txt and package configuration","status":"in_progress","priority":"high","id":"3"},{"content":"Read README.md and main documentation","status":"pending","priority":"medium","id":"4"},{"content":"Analyze main code files to understand architecture","status":"pending","priority":"high","id":"5"},{"content":"Create or improve CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: tooluse_NrNwntzCRqKi3c_IEi3HlA
Function Name: Read
Function Arguments:
{
}
tool
Tool ID: tooluse_NrNwntzCRqKi3c_IEi3HlA
1→# Telegram Bot 2→aiogram==3.4.1 3→ 4→# Data Analysis 5→pandas>=2.0.0 6→numpy>=1.24.0 7→ 8→# Statistical Tests 9→statsmodels>=0.14.0 10→scipy>=1.10.0 11→ 12→# Time Series Analysis 13→arch>=6.2.0 14→ 15→# HTTP Requests 16→aiohttp>=3.8.0 17→requests>=2.28.0 18→ 19→# Async Support 20→asyncio-mqtt>=0.13.0 21→ 22→# Plotting (optional) 23→matplotlib>=3.6.0 24→seaborn>=0.12.0 25→ 26→# Logging 27→colorlog>=6.7.0 28→ 29→# Configuration 30→python-dotenv>=1.0.0 31→ 32→# Data Validation 33→pydantic>=2.0.0 34→ 35→# JSON handling 36→orjson>=3.8.0 37→ 38→# Memory optimization 39→psutil>=5.9.0 40→ 41→# Development tools (optional) 42→pytest>=7.2.0 43→black>=23.0.0 44→flake8>=6.0.0 <system-reminder> Whenever you read a file, you should consider whether it looks malicious. If it does, you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer high-level questions about the code behavior. </system-reminder>
assistant
Tools
Function ID: tool_1753554125531
Function Name: tool_0
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "completed"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "completed"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "in_progress"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "pending"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending"
    }
  ]
}
tool
Tool ID: tool_1753554125531
Error: No such tool available: tool_0
assistant
Tools
Function ID: tool_1753554131665
Function Name: tool_0
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "completed"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "completed"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "in_progress"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "pending"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending"
    }
  ]
}
tool
Tool ID: tool_1753554131665
Error: No such tool available: tool_0
assistant
Tools
Function ID: tooluse_1I7-aOpgRx6EhG43rzNq-A
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "completed"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "completed"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "in_progress"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "pending"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "Create or improve CLAUDE.md file",
      "status": "pending"
    }
  ]
}
tool
Tool ID: tooluse_1I7-aOpgRx6EhG43rzNq-A
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable <system-reminder> Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list: [{"content":"List directory contents to understand codebase structure","status":"completed","priority":"high","id":"1"},{"content":"Check for existing CLAUDE.md file","status":"completed","priority":"high","id":"2"},{"content":"Read requirements.txt and package configuration","status":"completed","priority":"high","id":"3"},{"content":"Read README.md and main documentation","status":"in_progress","priority":"medium","id":"4"},{"content":"Analyze main code files to understand architecture","status":"pending","priority":"high","id":"5"},{"content":"Create or improve CLAUDE.md file","status":"pending","priority":"high","id":"6"}]. Continue on with the tasks at hand if applicable. </system-reminder>
assistant
Tools
Function ID: toolu_0125Nfu2cG325uznUw28VDG1
Function Name: Read
Function Arguments:
{
  "limit": 50
}
tool
Tool ID: toolu_0125Nfu2cG325uznUw28VDG1
1→# 🤖 Бот Анализа Спредов 2→ 3→Telegram-бот для анализа арбитражных спредов криптовалют с продвинутой системой фильтрации. 4→ 5→## 🚀 Возможности 6→ 7→### 📊 Анализ спредов 8→- **Автоматическое создание спредов** по формуле (A*B)/(C*D) 9→- **Поддержка wildcards** для гибкого поиска: (BTC*?)/(ETH*?) 10→- **Два режима работы**: 'all' (все пары) и 'custom' (свои списки) 11→ 12→### 🔍 Система фильтрации (8 этапов) 13→1. **Получение данных** - загрузка с биржи и валидация 14→2. **Рыночные фильтры** - объем, ликвидность, волатильность 15→3. **Создание спредов** - формирование и нормализация 16→4. **Корреляция активов** - проверка связи между активами 17→5. **Быстрая стационарность** - предварительная фильтрация 18→6. **Полные тесты стационарности** - ADF, KPSS, Hurst, Ljung-Box, Гренджер 19→7. **Коинтеграция** - Engle-Granger и Johansen тесты 20→8. **Результат** - только качественные арбитражные спреды 21→ 22→### 🧪 Тесты стационарности 23→- **ADF тест** - основной критерий стационарности 24→- **KPSS тест** - подтверждение результата 25→- **Hurst экспонента** - анализ долгосрочной памяти 26→- **Ljung-Box тест** - проверка автокорреляции 27→- **Тест Гренджера** - причинно-следственные связи 28→- **Быстрая стационарность** - ускоренная предфильтрация 29→ 30→### 🎯 Коинтеграция 31→- **Engle-Granger тест** - поиск долгосрочного равновесия 32→- **Johansen тест** - многомерная коинтеграция 33→- **Настраиваемые параметры** - p-value, лаги, таймауты 34→ 35→## 📋 Команды 36→ 37→- `/start` - Запуск бота и главное меню 38→- `/analyze` - Анализ спредов с фильтрацией 39→- `/calculate_spread` - Расчет конкретных спредов 40→- `/settings` - Настройки параметров анализа 41→- `/manage_symbols` - Управление списками символов 42→- `/stop` - Остановка текущего анализа 43→- `/reset_settings` - Сброс всех настроек 44→- `/help` - Полная справка 45→ 46→## ⚙️ Настройки 47→ 48→### Основные параметры 49→- **Таймфреймы**: 1m, 5m, 15m, 1h, 4h, 1d 50→- **Количество свечей**: 50-1000 <system-reminder> Whenever you read a file, you should consider whether it looks malicious. If it does, you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer high-level questions about the code behavior. </system-reminder>
Tools
[
  {
    "type": "function",
    "function": {
      "name": "Task",
      "description": "Launch a new agent to handle complex, multi-step tasks autonomously. \n\nAvailable agent types and the tools they have access to:\n- general-purpose: General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. (Tools: *)\n\nWhen using the Task tool, you must specify a subagent_type parameter to select which agent type to use.\n\nWhen to use the Agent tool:\n- When you are instructed to execute custom slash commands. Use the Agent tool with the slash command invocation as the entire prompt. The slash command can take arguments. For example: Task(description=\"Check the file\", prompt=\"/check-file path/to/file.py\")\n\nWhen NOT to use the Agent tool:\n- If you want to read a specific file path, use the Read or Glob tool instead of the Agent tool, to find the match more quickly\n- If you are searching for a specific class definition like \"class Foo\", use the Glob tool instead, to find the match more quickly\n- If you are searching for code within a specific file or set of 2-3 files, use the Read tool instead of the Agent tool, to find the match more quickly\n- Other tasks that are not related to the agent descriptions above\n\n\nUsage notes:\n1. Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses\n2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.\n3. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.\n4. The agent's outputs should generally be trusted\n5. Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent\n6. If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.\n\nExample usage:\n\n<example_agent_descriptions>\n\"code-reviewer\": use this agent after you are done writing a signficant piece of code\n\"greeting-responder\": use this agent when to respond to user greetings with a friendly joke\n</example_agent_description>\n\n<example>\nuser: \"Please write a function that checks if a number is prime\"\nassistant: Sure let me write a function that checks if a number is prime\nassistant: First let me use the Write tool to write a function that checks if a number is prime\nassistant: I'm going to use the Write tool to write the following code:\n<code>\nfunction isPrime(n) {\n  if (n <= 1) return false\n  for (let i = 2; i * i <= n; i++) {\n    if (n % i === 0) return false\n  }\n  return true\n}\n</code>\n<commentary>\nSince a signficant piece of code was written and the task was completed, now use the code-reviewer agent to review the code\n</commentary>\nassistant: Now let me use the code-reviewer agent to review the code\nassistant: Uses the Task tool to launch the with the code-reviewer agent \n</example>\n\n<example>\nuser: \"Hello\"\n<commentary>\nSince the user is greeting, use the greeting-responder agent to respond with a friendly joke\n</commentary>\nassistant: \"I'm going to use the Task tool to launch the with the greeting-responder agent\"\n</example>\n",
      "parameters": {
        "type": "object",
        "properties": {
          "description": {
            "type": "string",
            "description": "A short (3-5 word) description of the task"
          },
          "prompt": {
            "type": "string",
            "description": "The task for the agent to perform"
          },
          "subagent_type": {
            "type": "string",
            "description": "The type of specialized agent to use for this task"
          }
        },
        "required": [
          "description",
          "prompt",
          "subagent_type"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "Bash",
      "description": "Executes a given bash command in a persistent shell session with optional timeout, ensuring proper handling and security measures.\n\nBefore executing the command, please follow these steps:\n\n1. Directory Verification:\n   - If the command will create new directories or files, first use the LS tool to verify the parent directory exists and is the correct location\n   - For example, before running \"mkdir foo/bar\", first use LS to check that \"foo\" exists and is the intended parent directory\n\n2. Command Execution:\n   - Always quote file paths that contain spaces with double quotes (e.g., cd \"path with spaces/file.txt\")\n   - Examples of proper quoting:\n     - cd \"/Users/name/My Documents\" (correct)\n     - cd /Users/name/My Documents (incorrect - will fail)\n     - python \"/path/with spaces/script.py\" (correct)\n     - python /path/with spaces/script.py (incorrect - will fail)\n   - After ensuring proper quoting, execute the command.\n   - Capture the output of the command.\n\nUsage notes:\n  - The command argument is required.\n  - You can specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). If not specified, commands will timeout after 120000ms (2 minutes).\n  - It is very helpful if you write a clear, concise description of what this command does in 5-10 words.\n  - If the output exceeds 30000 characters, output will be truncated before being returned to you.\n  - VERY IMPORTANT: You MUST avoid using search commands like `find` and `grep`. Instead use Grep, Glob, or Task to search. You MUST avoid read tools like `cat`, `head`, `tail`, and `ls`, and use Read and LS to read files.\n - If you _still_ need to run `grep`, STOP. ALWAYS USE ripgrep at `rg` first, which all ${PRODUCT_NAME} users have pre-installed.\n  - When issuing multiple commands, use the ';' or '&&' operator to separate them. DO NOT use newlines (newlines are ok in quoted strings).\n  - Try to maintain your current working directory throughout the session by using absolute paths and avoiding usage of `cd`. You may use `cd` if the User explicitly requests it.\n    <good-example>\n    pytest /foo/bar/tests\n    </good-example>\n    <bad-example>\n    cd /foo/bar && pytest tests\n    </bad-example>\n\n\n\n\n# Committing changes with git\n\nWhen the user asks you to create a new git commit, follow these steps carefully:\n\n1. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following bash commands in parallel, each using the Bash tool:\n  - Run a git status command to see all untracked files.\n  - Run a git diff command to see both staged and unstaged changes that will be committed.\n  - Run a git log command to see recent commit messages, so that you can follow this repository's commit message style.\n2. Analyze all staged changes (both previously staged and newly added) and draft a commit message:\n  - Summarize the nature of the changes (eg. new feature, enhancement to an existing feature, bug fix, refactoring, test, docs, etc.). Ensure the message accurately reflects the changes and their purpose (i.e. \"add\" means a wholly new feature, \"update\" means an enhancement to an existing feature, \"fix\" means a bug fix, etc.).\n  - Check for any sensitive information that shouldn't be committed\n  - Draft a concise (1-2 sentences) commit message that focuses on the \"why\" rather than the \"what\"\n  - Ensure it accurately reflects the changes and their purpose\n3. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following commands in parallel:\n   - Add relevant untracked files to the staging area.\n   - Create the commit with a message ending with:\n   🤖 Generated with [Claude Code](https://claude.ai/code)\n\n   Co-Authored-By: Claude <noreply@anthropic.com>\n   - Run git status to make sure the commit succeeded.\n4. If the commit fails due to pre-commit hook changes, retry the commit ONCE to include these automated changes. If it fails again, it usually means a pre-commit hook is preventing the commit. If the commit succeeds but you notice that files were modified by the pre-commit hook, you MUST amend your commit to include them.\n\nImportant notes:\n- NEVER update the git config\n- NEVER run additional commands to read or explore code, besides git bash commands\n- NEVER use the TodoWrite or Task tools\n- DO NOT push to the remote repository unless the user explicitly asks you to do so\n- IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.\n- If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit\n- In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:\n<example>\ngit commit -m \"$(cat <<'EOF'\n   Commit message here.\n\n   🤖 Generated with [Claude Code](https://claude.ai/code)\n\n   Co-Authored-By: Claude <noreply@anthropic.com>\n   EOF\n   )\"\n</example>\n\n# Creating pull requests\nUse the gh command via the Bash tool for ALL GitHub-related tasks including working with issues, pull requests, checks, and releases. If given a Github URL use the gh command to get the information needed.\n\nIMPORTANT: When the user asks you to create a pull request, follow these steps carefully:\n\n1. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following bash commands in parallel using the Bash tool, in order to understand the current state of the branch since it diverged from the main branch:\n   - Run a git status command to see all untracked files\n   - Run a git diff command to see both staged and unstaged changes that will be committed\n   - Check if the current branch tracks a remote branch and is up to date with the remote, so you know if you need to push to the remote\n   - Run a git log command and `git diff [base-branch]...HEAD` to understand the full commit history for the current branch (from the time it diverged from the base branch)\n2. Analyze all changes that will be included in the pull request, making sure to look at all relevant commits (NOT just the latest commit, but ALL commits that will be included in the pull request!!!), and draft a pull request summary\n3. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following commands in parallel:\n   - Create new branch if needed\n   - Push to remote with -u flag if needed\n   - Create PR using gh pr create with the format below. Use a HEREDOC to pass the body to ensure correct formatting.\n<example>\ngh pr create --title \"the pr title\" --body \"$(cat <<'EOF'\n## Summary\n<1-3 bullet points>\n\n## Test plan\n[Checklist of TODOs for testing the pull request...]\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\nEOF\n)\"\n</example>\n\nImportant:\n- NEVER update the git config\n- DO NOT use the TodoWrite or Task tools\n- Return the PR URL when you're done, so the user can see it\n\n# Other common operations\n- View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "description": "The command to execute"
          },
          "timeout": {
            "type": "number",
            "description": "Optional timeout in milliseconds (max 600000)"
          },
          "description": {
            "type": "string",
            "description": " Clear, concise description of what this command does in 5-10 words. Examples:\nInput: ls\nOutput: Lists files in current directory\n\nInput: git status\nOutput: Shows working tree status\n\nInput: npm install\nOutput: Installs package dependencies\n\nInput: mkdir foo\nOutput: Creates directory 'foo'"
          }
        },
        "required": [
          "command"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "Glob",
      "description": "- Fast file pattern matching tool that works with any codebase size\n- Supports glob patterns like \"**/*.js\" or \"src/**/*.ts\"\n- Returns matching file paths sorted by modification time\n- Use this tool when you need to find files by name patterns\n- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead\n- You have the capability to call multiple tools in a single response. It is always better to speculatively perform multiple searches as a batch that are potentially useful.",
      "parameters": {
        "type": "object",
        "properties": {
          "pattern": {
            "type": "string",
            "description": "The glob pattern to match files against"
          },
          "path": {
            "type": "string",
            "description": "The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter \"undefined\" or \"null\" - simply omit it for the default behavior. Must be a valid directory path if provided."
          }
        },
        "required": [
          "pattern"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "Grep",
      "description": "A powerful search tool built on ripgrep\n\n  Usage:\n  - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command. The Grep tool has been optimized for correct permissions and access.\n  - Supports full regex syntax (e.g., \"log.*Error\", \"function\\s+\\w+\")\n  - Filter files with glob parameter (e.g., \"*.js\", \"**/*.tsx\") or type parameter (e.g., \"js\", \"py\", \"rust\")\n  - Output modes: \"content\" shows matching lines, \"files_with_matches\" shows only file paths (default), \"count\" shows match counts\n  - Use Task tool for open-ended searches requiring multiple rounds\n  - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\\{\\}` to find `interface{}` in Go code)\n  - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \\{[\\s\\S]*?field`, use `multiline: true`\n",
      "parameters": {
        "type": "object",
        "properties": {
          "pattern": {
            "type": "string",
            "description": "The regular expression pattern to search for in file contents"
          },
          "path": {
            "type": "string",
            "description": "File or directory to search in (rg PATH). Defaults to current working directory."
          },
          "glob": {
            "type": "string",
            "description": "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\") - maps to rg --glob"
          },
          "output_mode": {
            "type": "string",
            "enum": [
              "content",
              "files_with_matches",
              "count"
            ],
            "description": "Output mode: \"content\" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), \"files_with_matches\" shows file paths (supports head_limit), \"count\" shows match counts (supports head_limit). Defaults to \"files_with_matches\"."
          },
          "-B": {
            "type": "number",
            "description": "Number of lines to show before each match (rg -B). Requires output_mode: \"content\", ignored otherwise."
          },
          "-A": {
            "type": "number",
            "description": "Number of lines to show after each match (rg -A). Requires output_mode: \"content\", ignored otherwise."
          },
          "-C": {
            "type": "number",
            "description": "Number of lines to show before and after each match (rg -C). Requires output_mode: \"content\", ignored otherwise."
          },
          "-n": {
            "type": "boolean",
            "description": "Show line numbers in output (rg -n). Requires output_mode: \"content\", ignored otherwise."
          },
          "-i": {
            "type": "boolean",
            "description": "Case insensitive search (rg -i)"
          },
          "type": {
            "type": "string",
            "description": "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types."
          },
          "head_limit": {
            "type": "number",
            "description": "Limit output to first N lines/entries, equivalent to \"| head -N\". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). When unspecified, shows all results from ripgrep."
          },
          "multiline": {
            "type": "boolean",
            "description": "Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false."
          }
        },
        "required": [
          "pattern"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "LS",
      "description": "Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path. You can optionally provide an array of glob patterns to ignore with the ignore parameter. You should generally prefer the Glob and Grep tools, if you know which directories to search.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "The absolute path to the directory to list (must be absolute, not relative)"
          },
          "ignore": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of glob patterns to ignore"
          }
        },
        "required": [
          "path"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "ExitPlanMode",
      "description": "Use this tool when you are in plan mode and have finished presenting your plan and are ready to code. This will prompt the user to exit plan mode. \nIMPORTANT: Only use this tool when the task requires planning the implementation steps of a task that requires writing code. For research tasks where you're gathering information, searching files, reading files or in general trying to understand the codebase - do NOT use this tool.\n\nEg. \n1. Initial task: \"Search for and understand the implementation of vim mode in the codebase\" - Do not use the exit plan mode tool because you are not planning the implementation steps of a task.\n2. Initial task: \"Help me implement yank mode for vim\" - Use the exit plan mode tool after you have finished planning the implementation steps of the task.\n",
      "parameters": {
        "type": "object",
        "properties": {
          "plan": {
            "type": "string",
            "description": "The plan you came up with, that you want to run by the user for approval. Supports markdown. The plan should be pretty concise."
          }
        },
        "required": [
          "plan"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "Read",
      "description": "Reads a file from the local filesystem. You can access any file directly by using this tool.\nAssume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.\n\nUsage:\n- The file_path parameter must be an absolute path, not a relative path\n- By default, it reads up to 2000 lines starting from the beginning of the file\n- You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters\n- Any lines longer than 2000 characters will be truncated\n- Results are returned using cat -n format, with line numbers starting at 1\n- This tool allows Claude Code to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as Claude Code is a multimodal LLM.\n- This tool can read PDF files (.pdf). PDFs are processed page by page, extracting both text and visual content for analysis.\n- For Jupyter notebooks (.ipynb files), use the NotebookRead instead\n- You have the capability to call multiple tools in a single response. It is always better to speculatively read multiple files as a batch that are potentially useful. \n- You will regularly be asked to read screenshots. If the user provides a path to a screenshot ALWAYS use this tool to view the file at the path. This tool will work with all temporary file paths like /var/folders/123/abc/T/TemporaryItems/NSIRD_screencaptureui_ZfB1tD/Screenshot.png\n- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents.",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "The absolute path to the file to read"
          },
          "offset": {
            "type": "number",
            "description": "The line number to start reading from. Only provide if the file is too large to read at once"
          },
          "limit": {
            "type": "number",
            "description": "The number of lines to read. Only provide if the file is too large to read at once."
          }
        },
        "required": [
          "file_path"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "Edit",
      "description": "Performs exact string replacements in files. \n\nUsage:\n- You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. \n- When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.\n- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.\n- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.\n- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`. \n- Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "The absolute path to the file to modify"
          },
          "old_string": {
            "type": "string",
            "description": "The text to replace"
          },
          "new_string": {
            "type": "string",
            "description": "The text to replace it with (must be different from old_string)"
          },
          "replace_all": {
            "type": "boolean",
            "default": false,
            "description": "Replace all occurences of old_string (default false)"
          }
        },
        "required": [
          "file_path",
          "old_string",
          "new_string"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "MultiEdit",
      "description": "This is a tool for making multiple edits to a single file in one operation. It is built on top of the Edit tool and allows you to perform multiple find-and-replace operations efficiently. Prefer this tool over the Edit tool when you need to make multiple edits to the same file.\n\nBefore using this tool:\n\n1. Use the Read tool to understand the file's contents and context\n2. Verify the directory path is correct\n\nTo make multiple file edits, provide the following:\n1. file_path: The absolute path to the file to modify (must be absolute, not relative)\n2. edits: An array of edit operations to perform, where each edit contains:\n   - old_string: The text to replace (must match the file contents exactly, including all whitespace and indentation)\n   - new_string: The edited text to replace the old_string\n   - replace_all: Replace all occurences of old_string. This parameter is optional and defaults to false.\n\nIMPORTANT:\n- All edits are applied in sequence, in the order they are provided\n- Each edit operates on the result of the previous edit\n- All edits must be valid for the operation to succeed - if any edit fails, none will be applied\n- This tool is ideal when you need to make several changes to different parts of the same file\n- For Jupyter notebooks (.ipynb files), use the NotebookEdit instead\n\nCRITICAL REQUIREMENTS:\n1. All edits follow the same requirements as the single Edit tool\n2. The edits are atomic - either all succeed or none are applied\n3. Plan your edits carefully to avoid conflicts between sequential operations\n\nWARNING:\n- The tool will fail if edits.old_string doesn't match the file contents exactly (including whitespace)\n- The tool will fail if edits.old_string and edits.new_string are the same\n- Since edits are applied in sequence, ensure that earlier edits don't affect the text that later edits are trying to find\n\nWhen making edits:\n- Ensure all edits result in idiomatic, correct code\n- Do not leave the code in a broken state\n- Always use absolute file paths (starting with /)\n- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.\n- Use replace_all for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.\n\nIf you want to create a new file, use:\n- A new file path, including dir name if needed\n- First edit: empty old_string and the new file's contents as new_string\n- Subsequent edits: normal edit operations on the created content",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "The absolute path to the file to modify"
          },
          "edits": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "old_string": {
                  "type": "string",
                  "description": "The text to replace"
                },
                "new_string": {
                  "type": "string",
                  "description": "The text to replace it with"
                },
                "replace_all": {
                  "type": "boolean",
                  "default": false,
                  "description": "Replace all occurences of old_string (default false)."
                }
              },
              "required": [
                "old_string",
                "new_string"
              ],
              "additionalProperties": false
            },
            "minItems": 1,
            "description": "Array of edit operations to perform sequentially on the file"
          }
        },
        "required": [
          "file_path",
          "edits"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "Write",
      "description": "Writes a file to the local filesystem.\n\nUsage:\n- This tool will overwrite the existing file if there is one at the provided path.\n- If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.\n- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.\n- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.\n- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked.",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "The absolute path to the file to write (must be absolute, not relative)"
          },
          "content": {
            "type": "string",
            "description": "The content to write to the file"
          }
        },
        "required": [
          "file_path",
          "content"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "NotebookRead",
      "description": "Reads a Jupyter notebook (.ipynb file) and returns all of the cells with their outputs. Jupyter notebooks are interactive documents that combine code, text, and visualizations, commonly used for data analysis and scientific computing. The notebook_path parameter must be an absolute path, not a relative path.",
      "parameters": {
        "type": "object",
        "properties": {
          "notebook_path": {
            "type": "string",
            "description": "The absolute path to the Jupyter notebook file to read (must be absolute, not relative)"
          },
          "cell_id": {
            "type": "string",
            "description": "The ID of a specific cell to read. If not provided, all cells will be read."
          }
        },
        "required": [
          "notebook_path"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "NotebookEdit",
      "description": "Completely replaces the contents of a specific cell in a Jupyter notebook (.ipynb file) with new source. Jupyter notebooks are interactive documents that combine code, text, and visualizations, commonly used for data analysis and scientific computing. The notebook_path parameter must be an absolute path, not a relative path. The cell_number is 0-indexed. Use edit_mode=insert to add a new cell at the index specified by cell_number. Use edit_mode=delete to delete the cell at the index specified by cell_number.",
      "parameters": {
        "type": "object",
        "properties": {
          "notebook_path": {
            "type": "string",
            "description": "The absolute path to the Jupyter notebook file to edit (must be absolute, not relative)"
          },
          "cell_id": {
            "type": "string",
            "description": "The ID of the cell to edit. When inserting a new cell, the new cell will be inserted after the cell with this ID, or at the beginning if not specified."
          },
          "new_source": {
            "type": "string",
            "description": "The new source for the cell"
          },
          "cell_type": {
            "type": "string",
            "enum": [
              "code",
              "markdown"
            ],
            "description": "The type of the cell (code or markdown). If not specified, it defaults to the current cell type. If using edit_mode=insert, this is required."
          },
          "edit_mode": {
            "type": "string",
            "enum": [
              "replace",
              "insert",
              "delete"
            ],
            "description": "The type of edit to make (replace, insert, delete). Defaults to replace."
          }
        },
        "required": [
          "notebook_path",
          "new_source"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "WebFetch",
      "description": "\n- Fetches content from a specified URL and processes it using an AI model\n- Takes a URL and a prompt as input\n- Fetches the URL content, converts HTML to markdown\n- Processes the content with the prompt using a small, fast model\n- Returns the model's response about the content\n- Use this tool when you need to retrieve and analyze web content\n\nUsage notes:\n  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions. All MCP-provided tools start with \"mcp__\".\n  - The URL must be a fully-formed valid URL\n  - HTTP URLs will be automatically upgraded to HTTPS\n  - The prompt should describe what information you want to extract from the page\n  - This tool is read-only and does not modify any files\n  - Results may be summarized if the content is very large\n  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL\n  - When a URL redirects to a different host, the tool will inform you and provide the redirect URL in a special format. You should then make a new WebFetch request with the redirect URL to fetch the content.\n",
      "parameters": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "format": "uri",
            "description": "The URL to fetch content from"
          },
          "prompt": {
            "type": "string",
            "description": "The prompt to run on the fetched content"
          }
        },
        "required": [
          "url",
          "prompt"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "TodoWrite",
      "description": "Use this tool to create and manage a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.\nIt also helps the user understand the progress of the task and overall progress of their requests.\n\n## When to Use This Tool\nUse this tool proactively in these scenarios:\n\n1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions\n2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations\n3. User explicitly requests todo list - When the user directly asks you to use the todo list\n4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)\n5. After receiving new instructions - Immediately capture user requirements as todos\n6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time\n7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation\n\n## When NOT to Use This Tool\n\nSkip using this tool when:\n1. There is only a single, straightforward task\n2. The task is trivial and tracking it provides no organizational benefit\n3. The task can be completed in less than 3 trivial steps\n4. The task is purely conversational or informational\n\nNOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.\n\n## Examples of When to Use the Todo List\n\n<example>\nUser: I want to add a dark mode toggle to the application settings. Make sure you run the tests and build when you're done!\nAssistant: I'll help add a dark mode toggle to your application settings. Let me create a todo list to track this implementation.\n*Creates todo list with the following items:*\n1. Create dark mode toggle component in Settings page\n2. Add dark mode state management (context/store)\n3. Implement CSS-in-JS styles for dark theme\n4. Update existing components to support theme switching\n5. Run tests and build process, addressing any failures or errors that occur\n*Begins working on the first task*\n\n<reasoning>\nThe assistant used the todo list because:\n1. Adding dark mode is a multi-step feature requiring UI, state management, and styling changes\n2. The user explicitly requested tests and build be run afterward\n3. The assistant inferred that tests and build need to pass by adding \"Ensure tests and build succeed\" as the final task\n</reasoning>\n</example>\n\n<example>\nUser: Help me rename the function getCwd to getCurrentWorkingDirectory across my project\nAssistant: Let me first search through your codebase to find all occurrences of 'getCwd'.\n*Uses grep or search tools to locate all instances of getCwd in the codebase*\nAssistant: I've found 15 instances of 'getCwd' across 8 different files. Let me create a todo list to track these changes.\n*Creates todo list with specific items for each file that needs updating*\n\n<reasoning>\nThe assistant used the todo list because:\n1. First, the assistant searched to understand the scope of the task\n2. Upon finding multiple occurrences across different files, it determined this was a complex task with multiple steps\n3. The todo list helps ensure every instance is tracked and updated systematically\n4. This approach prevents missing any occurrences and maintains code consistency\n</reasoning>\n</example>\n\n\n<example>\nUser: I need to implement these features for my e-commerce site: user registration, product catalog, shopping cart, and checkout flow.\nAssistant: I'll help implement these features. First, let's add all the features to the todo list.\n*Creates a todo list breaking down each feature into specific tasks based on the project architecture*\nAssistant: Let's start with user registration. This will involve creating database models, API endpoints, and frontend forms that integrate with your existing authentication system.\n\n<reasoning>\nThe assistant used the todo list because:\n1. The user provided multiple complex features to implement in a comma separated list\n2. The todo list helps organize these large features into manageable tasks\n3. This approach allows for tracking progress across the entire implementation\n</reasoning>\n</example>\n\n<example>\nUser: Can you help optimize my React application? It's rendering slowly and has performance issues.</user>\nAssistant: I'll help optimize your React application. First, let me examine your codebase to identify potential performance bottlenecks.\n*Reviews component structure, render patterns, state management, and data fetching*\nAssistant: After analyzing your codebase, I've identified several performance issues. Let me create a todo list to track our optimization efforts.\n*Creates todo list with items like: 1) Implement memoization for expensive calculations in ProductList, 2) Add virtualization for long lists in Dashboard, 3) Optimize image loading in Gallery component, 4) Fix state update loops in ShoppingCart, 5) Review bundle size and implement code splitting*\nLet's start by implementing memoization for the expensive calculations in your ProductList component.</assistant>\n\n<reasoning>\nThe assistant used the todo list because:\n1. First, the assistant examined the codebase to identify specific performance issues\n2. Based on this analysis, it identified multiple optimization opportunities\n3. Performance optimization is a non-trivial task requiring multiple steps\n4. The todo list helps methodically track improvements across different components\n5. This systematic approach ensures all performance bottlenecks are addressed\n</reasoning>\n</example>\n\n## Examples of When NOT to Use the Todo List\n\n<example>\nUser: How do I print 'Hello World' in Python?\nAssistant: In Python, you can print \"Hello World\" with this simple code:\n\npython\nprint(\"Hello World\")\n\nThis will output the text \"Hello World\" to the console when executed.</assistant>\n\n<reasoning>\nThe assistant did not use the todo list because this is a single, trivial task that can be completed in one step. There's no need to track multiple tasks or steps for such a straightforward request.\n</reasoning>\n</example>\n\n<example>\nUser: What does the git status command do?\nAssistant: The git status command shows the current state of your working directory and staging area. It displays which changes have been staged, which haven't, and which files aren't being tracked by Git. This is a fundamental command for understanding the current state of your repository before making commits.\n\n<reasoning>\nThe assistant did not use the todo list because this is an informational request with no actual coding task to complete. The user is simply asking for an explanation, not for the assistant to perform multiple steps or tasks.\n</reasoning>\n</example>\n\n<example>\nUser: Can you add a comment to the calculateTotal function to explain what it does?\nAssistant: Sure, let me add a comment to the calculateTotal function to explain what it does.\n* Uses the Edit tool to add a comment to the calculateTotal function *\n\n<reasoning>\nThe assistant did not use the todo list because this is a single, straightforward task confined to one location in the code. Adding a comment doesn't require tracking multiple steps or systematic organization.\n</reasoning>\n</example>\n\n<example>\nUser: Run npm install for me and tell me what happens.\nAssistant: I'll run the npm install command for you.\n\n*Executes: npm install*\n\nThe command completed successfully. Here's the output:\n[Output of npm install command]\n\nAll dependencies have been installed according to your package.json file.\n\n<reasoning>\nThe assistant did not use the todo list because this is a single command execution with immediate results. There are no multiple steps to track or organize, making the todo list unnecessary for this straightforward task.\n</reasoning>\n</example>\n\n## Task States and Management\n\n1. **Task States**: Use these states to track progress:\n   - pending: Task not yet started\n   - in_progress: Currently working on (limit to ONE task at a time)\n   - completed: Task finished successfully\n\n2. **Task Management**:\n   - Update task status in real-time as you work\n   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)\n   - Only have ONE task in_progress at any time\n   - Complete current tasks before starting new ones\n   - Remove tasks that are no longer relevant from the list entirely\n\n3. **Task Completion Requirements**:\n   - ONLY mark a task as completed when you have FULLY accomplished it\n   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress\n   - When blocked, create a new task describing what needs to be resolved\n   - Never mark a task as completed if:\n     - Tests are failing\n     - Implementation is partial\n     - You encountered unresolved errors\n     - You couldn't find necessary files or dependencies\n\n4. **Task Breakdown**:\n   - Create specific, actionable items\n   - Break complex tasks into smaller, manageable steps\n   - Use clear, descriptive task names\n\nWhen in doubt, use this tool. Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully.\n",
      "parameters": {
        "type": "object",
        "properties": {
          "todos": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "content": {
                  "type": "string",
                  "minLength": 1
                },
                "status": {
                  "type": "string",
                  "enum": [
                    "pending",
                    "in_progress",
                    "completed"
                  ]
                },
                "priority": {
                  "type": "string",
                  "enum": [
                    "high",
                    "medium",
                    "low"
                  ]
                },
                "id": {
                  "type": "string"
                }
              },
              "required": [
                "content",
                "status",
                "priority",
                "id"
              ],
              "additionalProperties": false
            },
            "description": "The updated todo list"
          }
        },
        "required": [
          "todos"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "WebSearch",
      "description": "\n- Allows Claude to search the web and use the results to inform responses\n- Provides up-to-date information for current events and recent data\n- Returns search result information formatted as search result blocks\n- Use this tool for accessing information beyond Claude's knowledge cutoff\n- Searches are performed automatically within a single API call\n\nUsage notes:\n  - Domain filtering is supported to include or block specific websites\n  - Web search is only available in the US\n  - Account for \"Today's date\" in <env>. For example, if <env> says \"Today's date: 2025-07-01\", and the user wants the latest docs, do not use 2024 in the search query. Use 2025.\n",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "minLength": 2,
            "description": "The search query to use"
          },
          "allowed_domains": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only include search results from these domains"
          },
          "blocked_domains": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Never include search results from these domains"
          }
        },
        "required": [
          "query"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "mcp__ide__getDiagnostics",
      "description": "Get language diagnostics from VS Code",
      "parameters": {
        "type": "object",
        "properties": {
          "uri": {
            "type": "string",
            "description": "Optional file URI to get diagnostics for. If not provided, gets diagnostics for all files."
          }
        },
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "mcp__ide__executeCode",
      "description": "Execute python code in the Jupyter kernel for the current notebook file.\n    \n    All code will be executed in the current Jupyter kernel.\n    \n    Avoid declaring variables or modifying the state of the kernel unless the user\n    explicitly asks for it.\n    \n    Any code executed will persist across calls to this tool, unless the kernel\n    has been restarted.",
      "parameters": {
        "type": "object",
        "properties": {
          "code": {
            "type": "string",
            "description": "The code to be executed on the kernel."
          }
        },
        "required": [
          "code"
        ],
        "additionalProperties": false,
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  }
]
Response
(374 tokens)
Pretty
JSON
assistant
The existing CLAUDE.md file is already comprehensive and accurate. Based on my analysis, it correctly captures:

1. **Development Commands**: Proper setup with `pip install -r requirements.txt` and `python test/main.py`
2. **Architecture**: Accurately describes the 8-stage statistical arbitrage pipeline
3. **Key Components**: All major modules are properly documented
4. **Technical Details**: Important considerations about statistical accuracy and multi-user support

Tools
Function ID: tooluse_QtRx8DNbQ8GDL5uwUCaWkw
Function Name: TodoWrite
Function Arguments:
{
  "todos": [
    {
      "id": "1",
      "priority": "high",
      "content": "List directory contents to understand codebase structure",
      "status": "completed"
    },
    {
      "id": "2",
      "priority": "high",
      "content": "Check for existing CLAUDE.md file",
      "status": "completed"
    },
    {
      "id": "3",
      "priority": "high",
      "content": "Read requirements.txt and package configuration",
      "status": "completed"
    },
    {
      "id": "4",
      "priority": "medium",
      "content": "Read README.md and main documentation",
      "status": "completed"
    },
    {
      "id": "5",
      "priority": "high",
      "content": "Analyze main code files to understand architecture",
      "status": "completed"
    },
    {
      "id": "6",
      "priority": "high",
      "content": "CLAUDE.md file is already comprehensive and complete",
      "status": "completed"
    }
  ]
}