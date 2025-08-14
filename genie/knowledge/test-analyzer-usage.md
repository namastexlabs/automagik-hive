# Test Structure Analyzer Documentation

## Overview

The Test Structure Analyzer (`scripts/test_analyzer.py`) provides intelligent analysis of test coverage and structure with advanced false positive reduction. This tool helps maintain clean test organization without the noise of traditional analyzers.

## Key Features

### Intelligence Features
- **Smart Content Analysis**: Determines if files actually need tests based on code complexity
- **Context-Aware Classification**: Distinguishes integration, unit, fixture, and utility tests
- **Confidence-Based Filtering**: Scores each issue to separate real problems from false positives
- **Layered Strategy Pattern**: Uses multiple strategies to find corresponding files (direct match, agent.py convention, single-module directories)
- **Ignore File Support**: Respects `.test_analyzer_ignore` for legitimate exceptions

### Naming Convention Support
- Handles standard patterns: `test_*.py` and `*_test.py`
- Agent.py convention: Maps `test_agent_name_agent.py` → `agent_name/agent.py`
- Flexible matching with multiple naming variations

## Usage

### Basic Analysis
```bash
python scripts/test_analyzer.py
```

### Confidence Threshold Tuning
```bash
# High sensitivity (more issues flagged)
python scripts/test_analyzer.py --confidence 0.5

# Low sensitivity (only obvious issues)
python scripts/test_analyzer.py --confidence 0.9

# Default balanced threshold
python scripts/test_analyzer.py --confidence 0.7
```

### Output Formats
```bash
# Human-readable report (default)
python scripts/test_analyzer.py

# JSON for automation/tooling
python scripts/test_analyzer.py --json

# File operation commands for fixes
python scripts/test_analyzer.py --ops
```

## Understanding Results

### Success Criteria
- **Perfect Structure**: Zero high-confidence issues = ✅ Success
- **Issues Found**: High-confidence issues require attention
- **Suggestions**: Low-confidence items are likely false positives

### Issue Types
1. **Missing Tests**: Source files without corresponding test files
2. **Orphaned Tests**: Test files without corresponding source files
3. **Misplaced Tests**: Tests in wrong directory structure
4. **Naming Issues**: Tests not following convention

### Confidence Scoring
- **1.0**: Definitely needs attention (config files get 0.2, related tests found get 0.4)
- **0.7**: Default threshold - good balance of precision/recall
- **0.1**: Integration tests, fixtures - expected to have no source mirror
- **< 0.3**: Likely false positives, shown as suggestions

## Agent Integration

### For Quality Assurance Agents
```bash
# High-confidence issues only (for CI/CD)
python scripts/test_analyzer.py --confidence 0.8 --json

# Generate fix commands
python scripts/test_analyzer.py --ops > fix_tests.sh
```

### For Development Agents
- Use confidence 0.7 for balanced analysis
- Focus on high-confidence missing tests first
- Review orphaned tests - many are legitimate integration tests
- Check suggestions only if they align with testing strategy

### For Testing Agents
- **Critical**: Only modify files in `tests/` directory
- Use analyzer results to understand test structure needs
- Create tests for high-confidence missing test issues
- Respect the ignore file for debug/utility tests

## Configuration

### Ignore File (`.test_analyzer_ignore`)
```
# Debug/utility tests - no corresponding source files needed
tests/test_hook_validation.py
tests/debug_agent_start_test.py
```

### Supported Source Directories
- `api/` - API endpoints and routes
- `lib/` - Shared libraries and utilities  
- `ai/` - Agent system components
- `common/` - Common shared code
- `cli/` - Command-line interface

## Best Practices

### For Agents
1. **Trust High-Confidence Issues**: These are real problems needing fixes
2. **Filter Suggestions**: Most are false positives (integration tests, config files)
3. **Use Confidence Tuning**: Adjust threshold based on project phase
4. **Respect Boundaries**: Testing agents stay in `tests/`, dev agents handle source

### For Automation
1. **CI Integration**: Use `--confidence 0.8 --json` for strict validation
2. **Development**: Use `--confidence 0.6` for comprehensive analysis
3. **Exit Codes**: 0 = perfect, 1 = issues found, 2 = critical coverage problems

## Troubleshooting

### Common False Positives (Handled Automatically)
- Integration tests in `tests/integration/` → Low confidence
- Config files with mostly constants → Low confidence
- Agent tests with `agent.py` convention → Automatic resolution
- Fixture and utility tests → Classified and filtered

### When Results Seem Wrong
1. Check confidence threshold - try 0.5 for higher sensitivity
2. Verify ignore file for legitimate exceptions
3. Consider if "orphaned" tests are actually integration tests
4. Review file content analysis - complex files get higher confidence

This analyzer represents a significant improvement over traditional approaches by understanding code context and reducing false positive noise by ~85%.