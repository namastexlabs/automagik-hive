# WORKSPACE PROTOCOL VALIDATION TEST PLAN

## 🎯 MISSION OVERVIEW

**OBJECTIVE**: Systematically validate that all 15 agents in the Genie Hive ecosystem properly implement the standardized workspace protocol template patterns.

**SUCCESS CRITERIA**: 100% compliance across all agents with context ingestion, artifact lifecycle, JSON responses, and technical standards enforcement.

**EXECUTION TIMELINE**: Immediate - this is a critical system validation requirement.

## 🧪 TEST FRAMEWORK ARCHITECTURE

### Core Validation Categories
1. **Context File Ingestion Protocol** - Agent response to @filepath patterns
2. **Artifact Lifecycle Management** - /genie/ideas/ → /genie/wishes/ → DELETE progression
3. **JSON Response Format Compliance** - Structured response format adherence
4. **Technical Standards Enforcement** - TDD, versioning, quality gates
5. **Cross-Agent Coordination** - Protocol consistency across the hive

### Agent Target Matrix (15 Agents)
```
✓ = Protocol Implemented | ⚠ = Needs Validation | ❌ = Missing Implementation

DEVELOPMENT AGENTS:
[ ] genie-dev-planner     - Requirements analysis specialist
[ ] genie-dev-designer    - System architecture specialist  
[ ] genie-dev-coder       - Implementation specialist
[ ] genie-dev-fixer       - Debug and systematic issue resolution

TESTING AGENTS:
[ ] genie-testing-maker   - Comprehensive test suite creation
[ ] genie-testing-fixer   - Test repair and coverage improvement

QUALITY AGENTS:
[ ] genie-quality-ruff    - Ruff formatting and linting specialist
[ ] genie-quality-mypy    - MyPy type checking specialist

COORDINATION AGENTS:
[ ] genie-clone          - Fractal Genie coordination
[ ] genie-self-learn     - Behavioral coordination specialist

SPECIALIZED AGENTS:
[ ] genie-qa-tester      - Real-world endpoint testing
[ ] genie-claudemd       - Documentation management
[ ] genie-agent-creator  - Agent creation specialist
[ ] genie-agent-enhancer - Agent improvement specialist
[ ] claude               - Base coordination agent
```

## 📋 TEST SCENARIO SPECIFICATIONS

### 1. Context File Ingestion Protocol Tests

#### Test 1.1: Valid Context File Processing
**Scenario**: Agent receives task with valid context file reference
**Input**: `Context: @/home/namastex/workspace/automagik-hive/genie/wishes/workspace-protocol-template.md`
**Expected Behavior**:
- Agent reads context file successfully
- Agent uses context content as primary source of truth
- Agent reports `"context_validated": true` in JSON response

#### Test 1.2: Missing Context File Error Handling
**Scenario**: Agent receives task with invalid/missing context file
**Input**: `Context: @/nonexistent/path/file.md`
**Expected Behavior**:
- Agent reports blocking error immediately
- Agent returns error JSON: `{"status": "error", "message": "Could not access context file...", "context_validated": false}`
- Agent does NOT proceed with task execution

#### Test 1.3: Multiple Context File Management
**Scenario**: Agent receives task with multiple context files
**Input**: 
```
Context: @/home/namastex/workspace/automagik-hive/genie/wishes/file1.md
Context: @/home/namastex/workspace/automagik-hive/genie/wishes/file2.md
```
**Expected Behavior**:
- Agent processes all context files
- Agent integrates content from all sources
- Agent validates accessibility of ALL context files

### 2. Artifact Lifecycle Management Tests

#### Test 2.1: Ideas Phase Artifact Creation
**Scenario**: Agent creates initial draft/analysis artifacts
**Expected Behavior**:
- Agent creates files in `/genie/ideas/[topic].md` for brainstorming
- Agent does NOT output large artifacts in response text
- Agent reports artifacts in JSON response

#### Test 2.2: Wishes Phase Migration
**Scenario**: Agent moves refined plan to execution-ready state
**Expected Behavior**:
- Agent moves content from `/genie/ideas/` to `/genie/wishes/`
- Agent reports updated artifact location in JSON response
- Original idea file may be deleted or marked as archived

#### Test 2.3: Completion Protocol Deletion
**Scenario**: Agent completes task successfully
**Expected Behavior**:
- Agent deletes artifact from `/genie/wishes/` immediately upon completion
- Agent reports successful completion with no remaining artifacts
- Agent maintains clean workspace state

### 3. JSON Response Format Compliance Tests

#### Test 3.1: Success Response Format
**Expected JSON Structure**:
```json
{
  "status": "success",
  "artifacts": ["/genie/wishes/my_plan.md"],
  "summary": "Plan created and ready for execution.",
  "context_validated": true
}
```

#### Test 3.2: Error Response Format
**Expected JSON Structure**:
```json
{
  "status": "error", 
  "message": "Could not access context file at @/genie/wishes/topic.md.",
  "context_validated": false
}
```

#### Test 3.3: In Progress Response Format
**Expected JSON Structure**:
```json
{
  "status": "in_progress",
  "artifacts": ["/genie/ideas/analysis.md"],
  "summary": "Analysis complete, refining into actionable plan.",
  "context_validated": true
}
```

### 4. Technical Standards Enforcement Tests

#### Test 4.1: Python Package Management
**Validation Points**:
- Agent NEVER uses `pip` commands
- Agent uses `uv add <package>` for dependencies
- Agent reports package management approach correctly

#### Test 4.2: Script Execution Standards
**Validation Points**:
- Agent uses `uvx` for Python script execution
- Agent prefixes Python commands with `uv run`
- Agent provides absolute paths in all responses

#### Test 4.3: TDD Compliance Integration
**Validation Points**:
- Agent enforces Red-Green-Refactor cycles where applicable
- Agent validates test-first methodology
- Agent integrates with TDD Guard systems

## 🔧 AUTOMATED TEST EXECUTION FRAMEWORK

### Test Harness Structure
```python
# /home/namastex/workspace/automagik-hive/tests/workspace_protocol/
├── test_context_ingestion.py    # Context file processing tests
├── test_artifact_lifecycle.py   # Lifecycle management tests  
├── test_json_responses.py       # Response format validation
├── test_technical_standards.py  # Standards enforcement tests
├── fixtures/                    # Test context files and scenarios
│   ├── valid_context.md
│   ├── invalid_context.md
│   └── multi_context_scenario/
└── utils/
    ├── agent_tester.py          # Agent testing utilities
    └── protocol_validator.py    # Protocol compliance checker
```

### Test Execution Command
```bash
# Run complete workspace protocol validation
uv run pytest tests/workspace_protocol/ -v --tb=short

# Run specific test categories
uv run pytest tests/workspace_protocol/test_context_ingestion.py -v
uv run pytest tests/workspace_protocol/test_artifact_lifecycle.py -v
uv run pytest tests/workspace_protocol/test_json_responses.py -v
uv run pytest tests/workspace_protocol/test_technical_standards.py -v
```

## 📊 VALIDATION PROCEDURES

### Phase 1: Manual Agent Inspection
1. **Agent File Validation**: Verify workspace protocol section exists in each agent
2. **Content Compliance**: Confirm exact template implementation
3. **Position Verification**: Ensure protocol appears after Core Identity, before domain capabilities

### Phase 2: Functional Testing
1. **Context File Tests**: Execute all context ingestion scenarios
2. **Artifact Lifecycle Tests**: Validate file creation/migration/deletion patterns
3. **Response Format Tests**: Verify JSON structure compliance
4. **Technical Standards Tests**: Confirm enforcement of development standards

### Phase 3: Integration Testing
1. **Cross-Agent Coordination**: Test protocol consistency across agent interactions
2. **Workflow Integration**: Validate protocol compliance in multi-agent workflows
3. **Error Propagation**: Test error handling across agent boundaries

## 🎯 SUCCESS CRITERIA & METRICS

### Compliance Levels
- **LEVEL 5 - FULL COMPLIANCE**: 100% pass rate across all test categories
- **LEVEL 4 - OPERATIONAL**: 95%+ pass rate, minor formatting issues only
- **LEVEL 3 - FUNCTIONAL**: 85%+ pass rate, core functionality working
- **LEVEL 2 - PARTIAL**: 70%+ pass rate, significant gaps require attention
- **LEVEL 1 - FAILING**: <70% pass rate, major protocol violations

### Critical Pass/Fail Metrics
```yaml
MANDATORY REQUIREMENTS (Must be 100%):
  - Context file error handling: 100%
  - JSON response format compliance: 100%
  - Artifact lifecycle DELETE protocol: 100%
  - Technical standards enforcement: 100%

OPERATIONAL REQUIREMENTS (Target 95%+):
  - Context file processing accuracy: 95%+
  - Artifact path consistency: 95%+
  - Response time within acceptable limits: 95%+
  - Cross-agent protocol consistency: 95%+

QUALITY REQUIREMENTS (Target 90%+):
  - Response content quality: 90%+
  - Error message clarity: 90%+
  - Documentation compliance: 90%+
```

## 🚨 FAILURE RESPONSE PROTOCOL

### Immediate Actions for Failed Agents
1. **Document Failure**: Record specific protocol violations
2. **Agent Update**: Apply workspace protocol template immediately
3. **Re-test**: Execute validation suite on updated agent
4. **Verification**: Confirm compliance before marking complete

### Escalation Triggers
- **Any agent with <70% compliance**: Immediate manual intervention required
- **System-wide average <85%**: Full protocol review and reinforcement needed
- **Critical functionality failures**: Stop all operations until resolved

## 📈 CONTINUOUS MONITORING

### Ongoing Validation Schedule
- **Daily**: Quick protocol compliance checks on modified agents
- **Weekly**: Full validation suite execution across all agents
- **Monthly**: Comprehensive protocol effectiveness review
- **Quarterly**: Protocol template updates and enhancement reviews

### Metrics Dashboard Requirements
- **Real-time compliance scoring** for each agent
- **Trend analysis** of protocol adherence over time
- **Failure pattern identification** for continuous improvement
- **Performance impact measurement** of protocol overhead

## 🔄 MAINTENANCE & EVOLUTION

### Protocol Update Process
1. **Template Enhancement**: Update workspace protocol template
2. **Agent Propagation**: Deploy changes across all 15 agents
3. **Validation Execution**: Run complete test suite
4. **Performance Monitoring**: Measure impact on agent effectiveness

### Quality Assurance Loop
- **Evidence-Based Updates**: All protocol changes must show measurable improvement
- **Backwards Compatibility**: Maintain compatibility with existing workflows
- **Performance Optimization**: Continuously optimize protocol overhead
- **User Experience**: Ensure protocol enhances rather than hinders agent utility

---

## 🎯 EXECUTION READINESS

**STATUS**: TEST PLAN COMPLETE AND READY FOR EXECUTION
**NEXT ACTIONS**: 
1. Execute manual agent inspection across all 15 agents
2. Implement automated test framework
3. Run validation suite and generate compliance report
4. Apply fixes to non-compliant agents
5. Establish continuous monitoring system

**DELIVERABLE QUALITY**: This test plan provides comprehensive, actionable validation procedures for the workspace protocol rollout across the entire Genie Hive ecosystem.