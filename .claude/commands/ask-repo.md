# /ask-repo

---
allowed-tools: mcp__ask-repo-agent__ask_question(*), mcp__ask-repo-agent__read_wiki_structure(*), mcp__ask-repo-agent__read_wiki_contents(*)
description: Interactive Q&A with GitHub repositories for real-time documentation access
---

Ask questions about GitHub repositories and get intelligent responses based on the latest repository content, including code, documentation, and issues.

## Usage

```bash
# Ask questions about repositories
/ask-repo "agno-agi/agno" "How do I create a new agent?"
/ask-repo "facebook/react" "What's new in React 18?"
/ask-repo "microsoft/typescript" "How to configure strict mode?"

# Browse repository documentation
/ask-repo "agno-agi/agno" --wiki
/ask-repo "vercel/next.js" --structure
```

## Key Features

- **Real-time Access**: Query live GitHub repositories
- **Intelligent Responses**: AI-powered answers based on repository content
- **Documentation Browsing**: Access wiki and structure information
- **Latest Information**: Always up-to-date with repository changes
- **Context Aware**: Understands repository-specific patterns and conventions

## Target Repositories

Primary use cases:
- **Agno Framework**: `agno-agi/agno` for development guidance
- **React**: `facebook/react` for latest features and patterns
- **Next.js**: `vercel/next.js` for web development
- **TypeScript**: `microsoft/typescript` for type system help

## Question Types

Effective question patterns:
- "How do I implement X in this framework?"
- "What's the recommended pattern for Y?"
- "How has feature Z changed recently?"
- "What are the configuration options for X?"
- "Can you show me an example of Y?"

## Security

- Repository names validated for injection attacks
- Questions scanned for sensitive information
- Path traversal prevention
- Only reads public repository information

## Automatic Execution

```bash
# Parse arguments for repo and question
if [[ "$ARGUMENTS" == *"--wiki"* ]]; then
    REPO=$(echo "$ARGUMENTS" | cut -d' ' -f1 | tr -d '"')
    /mcp__ask-repo-agent__read_wiki_contents repoName="$REPO"
elif [[ "$ARGUMENTS" == *"--structure"* ]]; then
    REPO=$(echo "$ARGUMENTS" | cut -d' ' -f1 | tr -d '"')
    /mcp__ask-repo-agent__read_wiki_structure repoName="$REPO"
else
    # Extract repo and question from arguments
    REPO=$(echo "$ARGUMENTS" | cut -d' ' -f1 | tr -d '"')
    QUESTION=$(echo "$ARGUMENTS" | cut -d' ' -f2- | tr -d '"')
    /mcp__ask-repo-agent__ask_question repoName="$REPO" question="$QUESTION"
fi
```

---

**Agno Integration**: Essential for accessing latest Agno framework documentation and patterns during development. Use `agno-agi/agno` as the repository name.