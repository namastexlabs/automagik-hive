# Workspace Protocol Validation Test Suite

## 🎯 Overview

This comprehensive test suite validates that all 15 agents in the Genie Hive ecosystem properly implement the standardized workspace interaction protocol. It ensures consistent behavior across context file ingestion, artifact lifecycle management, JSON response formats, and technical standards enforcement.

## 🧪 Test Architecture

### Test Categories

1. **Context File Ingestion** (`test_context_ingestion.py`)
   - Valid context file processing
   - Missing context file error handling
   - Multiple context file management
   - Content integration validation

2. **Artifact Lifecycle Management** (`test_artifact_lifecycle.py`)
   - Ideas phase artifact creation (`/genie/ideas/`)
   - Wishes phase migration (`/genie/wishes/`)
   - Completion protocol deletion
   - Lifecycle state progression

3. **JSON Response Format Compliance**
   - Required field validation (`status`, `context_validated`)
   - Valid status values (`success`, `error`, `in_progress`)
   - Error message requirements
   - Artifact path reporting

4. **Technical Standards Enforcement**
   - Package management (`uv add` vs `pip install`)
   - Script execution (`uv run` prefix requirements)
   - Absolute path requirements
   - TDD compliance validation

5. **Cross-Agent Integration**
   - Protocol consistency across agents
   - Error propagation handling
   - Artifact coordination patterns

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure agent environment is running
make agent-status

# Install test dependencies
uv sync
```

### Run Complete Validation Suite
```bash
# Execute comprehensive validation across all 15 agents
uv run python tests/workspace_protocol/test_execution_script.py
```

### Run Specific Test Categories
```bash
# Context ingestion tests
uv run pytest tests/workspace_protocol/test_context_ingestion.py -v

# Artifact lifecycle tests  
uv run pytest tests/workspace_protocol/test_artifact_lifecycle.py -v

# All protocol tests
uv run pytest tests/workspace_protocol/ -v --tb=short
```

### Generate Compliance Report
```bash
# Quick compliance check
uv run python -c "
from tests.workspace_protocol.utils.agent_tester import AgentTester
tester = AgentTester()
results = tester.run_compliance_check_all_agents()
print(tester.generate_compliance_report(results))
"
```

## 📊 Target Agents (15 Total)

### Development Agents
- `genie-dev-planner` - Requirements analysis specialist
- `genie-dev-designer` - System architecture specialist  
- `genie-dev-coder` - Implementation specialist
- `genie-dev-fixer` - Debug and systematic issue resolution

### Testing Agents
- `genie-testing-maker` - Comprehensive test suite creation
- `genie-testing-fixer` - Test repair and coverage improvement

### Quality Agents
- `genie-quality-ruff` - Ruff formatting and linting specialist
- `genie-quality-mypy` - MyPy type checking specialist

### Coordination Agents
- `genie-clone` - Fractal Genie coordination
- `genie-self-learn` - Behavioral coordination specialist

### Specialized Agents
- `genie-qa-tester` - Real-world endpoint testing
- `genie-claudemd` - Documentation management
- `genie-agent-creator` - Agent creation specialist
- `genie-agent-enhancer` - Agent improvement specialist
- `claude` - Base coordination agent

## 🎯 Success Criteria

### Compliance Levels
- **LEVEL 5 - FULL COMPLIANCE**: 95%+ overall compliance
- **LEVEL 4 - OPERATIONAL**: 85%+ overall compliance  
- **LEVEL 3 - FUNCTIONAL**: 70%+ overall compliance
- **LEVEL 2 - PARTIAL**: 50%+ overall compliance
- **LEVEL 1 - FAILING**: <50% overall compliance

### Critical Requirements (Must be 100%)
- Context file error handling
- JSON response format compliance
- Artifact lifecycle DELETE protocol
- Technical standards enforcement

### Operational Requirements (Target 95%+)
- Context file processing accuracy
- Artifact path consistency
- Response time within limits
- Cross-agent protocol consistency

## 📁 Test Suite Structure

```
tests/workspace_protocol/
├── __init__.py                     # Package initialization
├── README.md                       # This documentation
├── test_context_ingestion.py       # Context file processing tests
├── test_artifact_lifecycle.py      # Artifact lifecycle management tests
├── test_execution_script.py        # Comprehensive test orchestrator
└── utils/
    ├── agent_tester.py             # Agent testing utilities
    └── protocol_validator.py       # Protocol compliance validation
```

## 🔧 Test Utilities

### AgentTester Class
Provides utilities for testing agent implementations:
- `execute_agent_task()` - Execute tasks with agents
- `validate_agent_protocol_compliance()` - Check static compliance
- `run_compliance_check_all_agents()` - Validate all agents
- `generate_compliance_report()` - Create human-readable reports

### ProtocolValidator Class
Validates protocol compliance in responses:
- `extract_json_response()` - Parse JSON from agent responses
- `validate_json_response_format()` - Check JSON structure
- `validate_artifact_paths()` - Validate artifact path compliance
- `validate_context_ingestion_compliance()` - Check context handling
- `run_comprehensive_validation()` - Complete validation suite

## 🚨 Troubleshooting

### Common Issues

**ImportError for test utilities:**
```bash
# Ensure you're in the correct directory
cd /home/namastex/workspace/automagik-hive

# Run with proper Python path
PYTHONPATH=/home/namastex/workspace/automagik-hive uv run pytest tests/workspace_protocol/
```

**Agent connection errors:**
```bash
# Check agent environment status
make agent-status

# Restart if needed
make agent-restart
```

**Test failures due to missing directories:**
```bash
# Ensure test directories exist
mkdir -p /home/namastex/workspace/automagik-hive/genie/ideas
mkdir -p /home/namastex/workspace/automagik-hive/genie/wishes
```

### Debug Mode
```bash
# Run tests with detailed output
uv run pytest tests/workspace_protocol/ -v -s --tb=long

# Run single test with debugging
uv run pytest tests/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing -v -s
```

## 📈 Continuous Validation

### Scheduled Validation
```bash
# Add to crontab for daily validation
0 9 * * * cd /home/namastex/workspace/automagik-hive && uv run python tests/workspace_protocol/test_execution_script.py
```

### Pre-Commit Hook Integration
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
cd /home/namastex/workspace/automagik-hive
uv run python tests/workspace_protocol/test_execution_script.py
if [ $? -ne 0 ]; then
    echo "Workspace protocol validation failed. Commit blocked."
    exit 1
fi
```

## 🔄 Maintenance

### Updating Test Suite
1. Modify agent validation requirements in `protocol_validator.py`
2. Add new test scenarios to relevant test files
3. Update compliance thresholds in `test_execution_script.py`
4. Re-run complete validation suite

### Adding New Agents
1. Add agent name to `target_agents` list in `test_execution_script.py`
2. Ensure agent implements workspace protocol template
3. Run validation to confirm compliance
4. Update documentation with new agent count

## 📊 Results and Reporting

### Output Files
- `/home/namastex/workspace/automagik-hive/genie/wishes/workspace-protocol-validation-results.json` - Detailed JSON results
- Console output with formatted compliance report
- Individual test results in pytest output

### Metrics Tracked
- Overall compliance percentage
- Per-agent compliance scores
- Test category pass rates
- Execution time and performance metrics
- Detailed failure analysis

## 🎯 Expected Outcomes

After successful workspace protocol implementation:
- **100% agent compliance** with workspace interaction protocol
- **Consistent behavior** across all 15 agents
- **Reliable error handling** for missing context files
- **Proper artifact lifecycle** management
- **Structured JSON responses** from all agents
- **Technical standards enforcement** across the ecosystem

This test suite ensures the Genie Hive behavioral coordination update was successful and maintains ongoing compliance monitoring.