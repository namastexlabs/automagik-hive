# Code Reviewer Agent Example

An expert code review agent that analyzes code quality, security, and best practices.

## What This Agent Does

- Reviews code for bugs, security issues, and performance problems
- Provides actionable feedback with examples
- Integrates with GitHub for PR reviews
- Educational tone focused on learning

## Features

✅ **Security Analysis** - Checks for OWASP Top 10 vulnerabilities
✅ **Performance Review** - Identifies bottlenecks and inefficiencies
✅ **Best Practices** - Ensures code follows industry standards
✅ **GitHub Integration** - Can review PRs directly
✅ **Educational Feedback** - Explains "why" behind suggestions

## Quick Start

### 1. Configure Environment

Add to `.env`:

```bash
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/hive
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: for GitHub integration
GITHUB_TOKEN=your_github_token_here
```

### 2. Run the Agent

```python
from hive.scaffolder.generator import generate_agent_from_yaml

# Load agent
agent = generate_agent_from_yaml("examples/agents/code-reviewer/config.yaml")

# Review code
code = """
def process_user_input(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return db.execute(query)
"""

response = agent.run(f"Review this code:\n{code}")
print(response.content)
```

### 3. Example Output

```
🔴 CRITICAL ISSUES:

1. SQL Injection Vulnerability
   Location: Line 2
   Issue: User input is directly concatenated into SQL query
   Risk: Attacker can manipulate query to access/modify data

   ❌ BAD:
   query = "SELECT * FROM users WHERE name = '" + user_input + "'"

   ✅ GOOD:
   query = "SELECT * FROM users WHERE name = %s"
   db.execute(query, (user_input,))

   Why: Parameterized queries prevent SQL injection by properly
        escaping user input.

RECOMMENDATION: Request changes
This code has a critical security vulnerability that must be fixed
before merging.
```

## Configuration Explained

### Model Choice

Uses `claude-sonnet-4` because:
- Excellent code understanding
- Strong security awareness
- Good at explaining concepts
- Consistent, thoughtful reviews

### Temperature (0.3)

Low temperature ensures:
- Consistent review criteria
- Focused on facts, not creative interpretation
- Reproducible results

### Tools

- **file_reader** - Read code files from disk/repo
- **github_api** - Fetch PRs, post comments, approve/reject
- **web_search** - Look up best practices and security advisories

## Use Cases

### 1. Local File Review

```python
agent = generate_agent_from_yaml("config.yaml")

# Review a local file
response = agent.run("Review the file: ./src/api/auth.py")
print(response.content)
```

### 2. GitHub PR Review

```python
# Review a pull request
response = agent.run(
    "Review pull request #123 in github.com/user/repo"
)
print(response.content)
```

### 3. Code Snippet Review

```python
# Quick code review
code = """
async def fetch_data(url):
    response = requests.get(url)
    return response.json()
"""

response = agent.run(f"Review this code:\n{code}")
```

## Review Categories

### Security (OWASP Top 10)

- SQL Injection
- Cross-Site Scripting (XSS)
- Authentication/Authorization issues
- Sensitive data exposure
- XML External Entities (XXE)
- Broken access control
- Security misconfiguration
- Insecure deserialization
- Insufficient logging

### Performance

- Inefficient algorithms (O(n²) loops)
- Missing database indexes
- N+1 query problems
- Memory leaks
- Blocking I/O operations

### Code Quality

- Code duplication
- Complex functions (>50 lines)
- Poor naming conventions
- Missing error handling
- Lack of type hints (Python)

### Testing

- Insufficient test coverage
- Missing edge case tests
- Flaky tests
- Integration test gaps

## Customization

### Focus on Specific Areas

```yaml
instructions: |
  Focus your review on:
  - Security vulnerabilities ONLY
  - Ignore style/formatting issues
```

### Adjust Strictness

```yaml
instructions: |
  Review criteria:
  - Be lenient on style issues
  - CRITICAL for security and correctness
  - OPTIONAL for performance optimizations
```

### Add Domain-Specific Rules

```yaml
instructions: |
  Additional checks for our codebase:
  - All API endpoints must have rate limiting
  - Database queries must use prepared statements
  - All functions must have type hints
```

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/review.yml
name: Code Review
on: pull_request

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: AI Code Review
        run: |
          hive review-pr ${{ github.event.pull_request.number }}
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Review staged changes
git diff --cached | hive review-stdin
```

### VS Code Extension

```json
{
  "hive.reviewOnSave": true,
  "hive.agent": "examples/agents/code-reviewer/config.yaml"
}
```

## Performance

- **Review Time**: 10-30 seconds (depends on code size)
- **Cost**: ~$0.01-0.05 per review (using Claude)
- **Accuracy**: High (catches most common issues)

## Limitations

**What it's good at:**
- Common vulnerabilities (SQL injection, XSS)
- Code style and readability
- Best practices violations
- Logic errors

**What it struggles with:**
- Domain-specific business logic
- Complex state management
- Race conditions in concurrent code
- Performance in production (needs profiling)

## Production Tips

### 1. Rate Limiting

```python
# Review at most 10 PRs per hour
rate_limiter = RateLimiter(max_requests=10, period=3600)
```

### 2. Caching Reviews

```python
# Don't re-review unchanged code
cache_key = hash(code_content)
if cache_key in review_cache:
    return review_cache[cache_key]
```

### 3. Human-in-the-Loop

```python
# Flag uncertain reviews for human check
if review.confidence < 0.8:
    notify_human_reviewer(review)
```

## Troubleshooting

### Agent Missing Security Issues

**Fix**: Lower temperature, add specific instructions:

```yaml
settings:
  temperature: 0.2  # More focused

instructions: |
  Check EVERY line for:
  - SQL injection
  - XSS vulnerabilities
  - Authentication bypasses
```

### Reviews Too Strict/Lenient

**Fix**: Adjust review criteria:

```yaml
instructions: |
  Severity levels:
  - CRITICAL: Security, data loss, crashes
  - MAJOR: Performance, maintainability
  - MINOR: Style, optimization opportunities
```

### GitHub Integration Not Working

**Fix**: Verify GitHub token:

```bash
export GITHUB_TOKEN=your_token_here

# Test access
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

## Next Steps

1. **Customize Rules** - Add your team's coding standards
2. **CI/CD Integration** - Automate PR reviews
3. **Knowledge Base** - Add your security policies
4. **Team Training** - Use reviews as learning tool

## Learn More

- [Security Best Practices](../../../docs/security.md)
- [Code Review Guide](../../../docs/code-review.md)
- [GitHub Integration](../../../docs/github.md)
