# /test

---
allowed-tools: mcp__zen__testgen(*), Read(*), Write(*), Edit(*), Bash(*), Glob(*)
description: Generate comprehensive test suites with optional model selection
---

Create thorough test suites with edge case coverage for specific functions, classes, or modules.

## Usage

```bash
# Default (uses Claude)
/test "Generate tests for User.login() method"

# With specific model
/test "Test payment processing validation" model="o3"
/test "Create tests for auth error handling" model="grok"
/test "Generate integration tests for API" model="gemini"
```

## Model Strengths

- **Claude** (default): Project-aware tests, follows existing patterns
- **O3**: Systematic test coverage, edge case identification
- **Grok**: Complex scenario generation
- **Gemini**: Creative test scenarios, pattern-based tests

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

## Automatic Execution

/mcp__zen__testgen "$ARGUMENTS" model="${MODEL:-claude}" thinking_mode="${MODE:-medium}"

---

**Smart Test Generation**: Comprehensive test suites that follow your project's patterns and catch edge cases.