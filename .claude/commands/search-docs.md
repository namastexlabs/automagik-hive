# /search-docs

---
allowed-tools: mcp__search-repo-docs__resolve-library-id(*), mcp__search-repo-docs__get-library-docs(*)
description: Search and retrieve up-to-date documentation for libraries and frameworks
---

Search for library documentation using Context7's comprehensive documentation database. Perfect for accessing the latest docs, API references, and code examples.

## Usage

```bash
# Search for a library and get docs
/search-docs "next.js"
/search-docs "mongodb"
/search-docs "supabase"

# Get specific library with topic focus
/search-docs "react" topic="hooks"
/search-docs "express.js" topic="middleware"

# Use exact library ID (if known)
/search-docs "/vercel/next.js/v14.3.0" topic="routing"
```

## Key Features

- **Latest Documentation**: Access up-to-date library docs from Context7
- **Smart Matching**: Automatically resolves library names to correct IDs
- **Topic Filtering**: Focus on specific aspects (hooks, routing, auth, etc.)
- **Code Examples**: Get real implementation examples
- **Version Support**: Access specific library versions when available

## Library Examples

Common libraries available:
- **Frontend**: react, vue, svelte, next.js, nuxt
- **Backend**: express, fastapi, django, rails
- **Databases**: mongodb, postgresql, redis, supabase
- **Tools**: webpack, vite, typescript, eslint

## Security

- Automatically scans for suspicious injection patterns
- Validates library IDs and search terms
- Blocks potentially malicious requests

## Automatic Execution

```bash
# If library ID format (/org/project), use directly
if [[ "$ARGUMENTS" =~ ^/.+/.+ ]]; then
    /mcp__search-repo-docs__get-library-docs context7CompatibleLibraryID="$ARGUMENTS" ${TOPIC:+topic="$TOPIC"}
else
    # Resolve library name first
    /mcp__search-repo-docs__resolve-library-id libraryName="$ARGUMENTS"
fi
```

---

**Context Integration**: Essential for accessing latest Agno framework documentation and other library references during development.