# /test

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Bash(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*
description: Generate comprehensive test suites
---

Generate comprehensive test suites with edge case coverage and expert guidance.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Usage

```bash
# Default (uses Claude)
/test "Generate tests for User.login() method"

# With specific model
/test "Test payment processing validation" model="o3"
/test "Create tests for auth error handling" model="grok"
/test "Generate integration tests for API" model="gemini"
```

## Intelligent Test Strategy

### Step 1: Test Analysis
Parse user request: "$ARGUMENTS"

**Test Categories:**
- **Unit Tests** → Individual function/method testing
- **Integration Tests** → Component interaction testing
- **Edge Case Tests** → Boundary and error condition testing
- **Performance Tests** → Load and stress testing

## Thinking Modes

- **low**: Simple functions (8% depth)
- **medium**: Standard modules (33% depth) - DEFAULT
- **high**: Complex systems with many interactions (67% depth)
- **max**: Critical systems requiring exhaustive coverage (100% depth)

## Test Types

Generates:
- Unit tests with mocking
- Integration tests
- Edge case scenarios
- Error handling tests
- Performance tests (when applicable)
- Security tests (when applicable)

## Examples

```bash
# Specific function tests
/test "Test UserService.authenticate() with all edge cases"

# Module testing
/test "Generate tests for entire payment module" model="o3"

# Complex integration
/test "Test agent routing with 20+ scenarios" thinking_mode="high"

# Critical system
/test "Exhaustive tests for encryption module" model="gemini" thinking_mode="max"
```

## Best Practices

- **Be Specific**: Target specific functions/classes rather than "test everything"
- **Provide Context**: Include what the code does if not obvious
- **Follow Patterns**: Tests will match your existing test framework
- **Review Coverage**: Generated tests aim for high coverage

## Expert Consultation & Notifications

For complex test scenarios:

```python
# Complex test design consultation
mcp__gemini__consult_gemini(
    specific_question="How to test [complex component]?",
    problem_description="Need comprehensive tests for [functionality]",
    code_context="Component has [patterns and complexity]...",
    attached_files=["component/files.py"],
    preferred_approach="test"
)

# Notify when critical components lack tests
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="⚠️ TEST COVERAGE: Critical component [name] needs test coverage. Generated comprehensive test suite.",
    number="5511986780008@s.whatsapp.net"
)
```

## Automatic Memory Integration

Every test generation automatically updates memory:

```python
# Store testing patterns
mcp__genie_memory__add_memory(
    content="PATTERN: Testing [component] - Used [framework] with [approach] #testing"
)

# Store test discoveries
mcp__genie_memory__add_memory(
    content="FOUND: [Component] tested with [edge cases] - Coverage [%] #coverage"
)

# Search for existing test patterns
mcp__genie_memory__search_memory(
    query="PATTERN testing [similar component]"
)
```

## Automatic Execution

```bash
# Search for existing test patterns
mcp__genie_memory__search_memory query="PATTERN testing $ARGUMENTS"

# For critical components, notify about test generation
if [[ "$ARGUMENTS" =~ critical|auth|payment|security ]]; then
    mcp__send_whatsapp_message__send_text_message \
        instance="SofIA" \
        message="⚠️ TEST: Generating tests for critical component: $ARGUMENTS" \
        number="5511986780008@s.whatsapp.net"
fi

# Get testing best practices
mcp__search-repo-docs__get-library-docs \
    context7CompatibleLibraryID="/context7/agno" \
    topic="Testing patterns and best practices" \
    tokens=6000
```

---

**Smart Test Generation**: Comprehensive test suites that follow your project's patterns and catch edge cases.