# Automagik Hive

Enterprise multi-agent AI framework built on **Agno** that enables rapid development of sophisticated multi-agent systems through YAML configuration. Production-ready boilerplate for building intelligent agents, routing teams, and business workflows with enterprise-grade deployment capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
uv sync

# Setup agent environment (Docker containers)
make install-agent

# Start agent services
make agent

# Your isolated agent environment:
# - Agent API: http://localhost:38886
# - Agent DB: postgresql://localhost:35532
```

---

## 📊 ProcessamentoFaturas Workflow

**Automated CTE Invoice Processing Pipeline** - A comprehensive workflow that automates the complete lifecycle of CTE (Conhecimento de Transporte Eletrônico) invoice processing from email monitoring to API orchestration.

### 🎯 Overview

The ProcessamentoFaturas workflow transforms manual CTE invoice processing into a fully automated 5-stage pipeline:

1. **📧 Email Monitoring** - OAuth2 Gmail integration with attachment extraction
2. **📊 Data Extraction** - Excel processing with CTE/MINUTA differentiation  
3. **🏗️ JSON Generation** - Consolidated JSON structure per Excel file
4. **🔗 API Orchestration** - Sequential Browser API calls with proper state management
5. **✅ Workflow Completion** - Comprehensive metrics and status reporting

### 🏗️ Architecture

#### **Workflow Type**: Agno Workflows 2.0
Built using **step-based sequential execution** with specialized agents as internal components:

```python
Workflow(
    name="processamento_faturas",
    steps=[
        Step("email_monitoring", executor=execute_email_monitoring_step),
        Step("data_extraction", executor=execute_data_extraction_step), 
        Step("json_generation", executor=execute_json_generation_step),
        Step("api_orchestration", executor=execute_api_orchestration_step),
        Step("workflow_completion", executor=execute_workflow_completion_step)
    ],
    storage=PostgresStorage(auto_upgrade_schema=True)
)
```

#### **5 Specialized Agents**
Each step utilizes dedicated agents with specific expertise:

- **📧 EmailProcessor** - Gmail OAuth2 integration, attachment validation
- **📊 DataExtractor** - Excel processing, CTE data extraction, MINUTA filtering
- **🏗️ JSONGenerator** - Consolidated JSON structure generation
- **🔗 APIOrchestrator** - Browser API sequential calls with retry logic
- **📁 FileManager** - File integrity management with SHA-256 checksums

### 📋 Data Flow

#### **Input**: Gmail Account with CTE Excel Attachments
- OAuth2 authenticated Gmail access
- Excel files containing CTE and MINUTA entries
- Automated attachment validation and download

#### **Processing**: CTE Extraction & Validation
```json
{
  "600708542": {
    "values": [
      {
        "index": 154,
        "NF_CTE": "96765", 
        "value": 1644.67,
        "empresa_origem": "CLARO NXT",
        "cnpj_claro": "66970229041351",
        "competencia": "04/2025"
      }
    ],
    "total_value": 1644.67,
    "cte_count": 1,
    "status": "PENDING"
  }
}
```

#### **Output**: Consolidated JSON Structure
```json
{
  "batch_id": "batch_20250112_143052",
  "source_file": "faturas_janeiro_2025.xlsx",
  "processing_timestamp": "2025-01-12T14:30:52Z",
  "total_ctes": 15,
  "total_pos": 8,
  "total_value": 45230.89,
  "client_data": ["CLARO NXT", 66970229041351],
  "type": "CTE",
  "orders": [
    {
      "po_number": "600708542",
      "cte_entries": [...],
      "total_value": 1644.67,
      "status": "PENDING"
    }
  ]
}
```

### 🔗 Browser API Integration

#### **Sequential API Orchestration**
The workflow integrates with Browser API through 4 sequential endpoints:

1. **`/api/invoiceGen`** - Invoice generation initiation
2. **`/api/statusMonitoring`** - Processing status monitoring  
3. **`/api/downloadInvoices`** - Generated invoice download
4. **`/api/uploadToSystem`** - Final system upload

#### **API Response Format (API_RESULT)**
```json
{
  "success": true,
  "data": {
    "job_id": "job_12345",
    "status": "processing",
    "message": "Invoice generation started"
  },
  "error": null,
  "timestamp": "2025-01-12T14:30:52Z"
}
```

#### **Error Handling**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid PO format",
    "details": "PO number must be numeric"
  },
  "timestamp": "2025-01-12T14:30:52Z"
}
```

### 💾 State Management

#### **PostgreSQL Persistence**
- **Session State**: Cross-step data sharing with automatic persistence
- **Processing Status**: Individual PO status tracking throughout pipeline
- **Error Recovery**: Automatic retry logic with exponential backoff
- **Metrics Collection**: Comprehensive performance monitoring

#### **Status Transitions**
```
PENDING → PROCESSING → WAITING_MONITORING → MONITORED 
       ↓              ↓                    ↓
FAILED_EXTRACTION  FAILED_GENERATION  FAILED_MONITORING
                                           ↓
                                      DOWNLOADED
                                           ↓
                                      UPLOADED
                                           ↓
                                      COMPLETED
```

### 🧪 Testing

#### **Comprehensive Test Suite (70+ Test Cases)**
```bash
# Run complete test suite
uv run pytest ai/workflows/processamento-faturas/tests.py -v

# Test categories:
# - Unit Tests: Component-level validation
# - Integration Tests: Agent interaction validation  
# - End-to-End Tests: Complete workflow execution
# - Performance Tests: Response time compliance
# - Error Scenarios: Failure handling validation
```

#### **TDD Methodology**
- **Red-Green-Refactor** cycle compliance
- **Test-first** implementation approach
- **Mocking strategies** for external dependencies
- **Coverage targets**: >90% code coverage

### ⚡ Performance Targets

- **Email Processing**: <5s per email batch
- **Data Extraction**: <10s per Excel file
- **JSON Generation**: <2s per consolidation
- **API Orchestration**: <30s per complete cycle
- **Total Workflow**: <60s end-to-end

### 🔧 Configuration

#### **Environment Setup**
```bash
# Required environment variables (.env)
GMAIL_CLIENT_ID=your_gmail_oauth_client_id
GMAIL_CLIENT_SECRET=your_gmail_oauth_secret
BROWSER_API_BASE_URL=https://api.browser-system.com
POSTGRES_CONNECTION_STRING=postgresql://user:pass@localhost:5432/db
```

#### **Agent Configuration** 
```yaml
# ai/workflows/processamento-faturas/config.yaml
name: "processamento_faturas"
version: "1.0.0"
description: "CTE Invoice Processing Pipeline"
agents:
  email_processor:
    model: "claude-3-sonnet"
    temperature: 0.2
    tools: ["gmail_oauth", "file_validator"]
  data_extractor:
    model: "claude-3-sonnet"  
    temperature: 0.1
    tools: ["excel_processor", "data_validator"]
```

### 🚀 Deployment

#### **Local Development**
```bash
# Start workflow service
uv run python api/main.py

# Access playground
open http://localhost:8000
```

#### **Production Deployment**
```bash
# Docker deployment
docker build -t hive-workflows .
docker run -p 8000:8000 hive-workflows

# Environment scaling
export WORKERS=4
export MAX_CONCURRENT_WORKFLOWS=10
```

### 📊 Monitoring & Metrics

#### **Workflow Metrics**
- **Execution Time**: Total workflow duration
- **API Success Rate**: Browser API call success percentage
- **Processing Volume**: CTEs processed per batch
- **Error Rates**: Failure rates by step and error type

#### **Agent Performance**
- **Response Times**: Individual agent execution times
- **Memory Usage**: Agent memory consumption patterns
- **Retry Patterns**: Automatic recovery success rates

### 🔒 Security & Compliance

#### **Data Protection**
- **OAuth2 Security**: Secure Gmail integration with token refresh
- **File Integrity**: SHA-256 checksums for all processed files
- **State Encryption**: Sensitive data encryption in PostgreSQL
- **Audit Logging**: Complete processing audit trail

#### **Error Recovery**
- **Exponential Backoff**: Smart retry strategies for API failures
- **State Persistence**: Recovery from any step failure
- **Graceful Degradation**: Partial processing success handling

### 🛠️ Development

#### **Adding New Features**
```bash
# 1. Extend workflow steps
# Edit: ai/workflows/processamento-faturas/workflow.py

# 2. Add corresponding tests
# Edit: ai/workflows/processamento-faturas/tests.py

# 3. Update configuration
# Edit: ai/workflows/processamento-faturas/config.yaml

# 4. Run quality checks
uv run ruff check --fix
uv run mypy .
uv run pytest
```

#### **Agent Customization**
```python
# Create specialized agent variations
def create_custom_extractor_agent():
    return Agent(
        name="Custom Data Extractor",
        instructions=["Custom extraction logic"],
        tools=[custom_excel_tool],
        model=create_workflow_model()
    )
```

### 📚 Technical References

- **Framework**: [Agno Documentation](https://docs.agno.ai)
- **Workflow Patterns**: [Agno Workflows 2.0](https://docs.agno.ai/workflows)
- **Agent Architecture**: [Multi-Agent Systems](https://docs.agno.ai/agents)
- **PostgreSQL Storage**: [Agno Storage](https://docs.agno.ai/storage)

---

## 🧞 Genie Hive Architecture

Multi-layer orchestration system with specialized agents for different domains:

### 🎯 Three-Layer Coordination
```
🧞 GENIE TEAM (Strategic Coordination)
    ↓ spawns via Task tool
🎯 DOMAIN ORCHESTRATORS (ai/agents/)
    ├── genie-dev → Development coordination
    ├── genie-testing → Testing coordination  
    ├── genie-quality → Quality coordination
    └── genie-workflows → Workflow coordination
    ↓ spawns via Task tool
🤖 EXECUTION LAYER (.claude/agents/)
    ├── Specialized task execution
    ├── TDD methodology compliance
    └── Context-aware heavy lifting
```

### 🚀 Quick Commands

```bash
# Package management (NEVER use pip directly)
uv add <package>              # Add dependencies
uv run ruff check --fix       # Lint and fix code
uv run mypy .                 # Type checking
uv run pytest               # Run tests

# Agent environment 
make agent                   # Start services
make agent-status           # Check status
make agent-logs             # View logs
make agent-stop             # Stop services

# Development workflow
uv run python api/main.py    # Start playground
uv run python api/serve.py   # Start production server
```

### 📁 Project Structure

```
🧭 NAVIGATION ESSENTIALS
├── pyproject.toml              # UV package manager
🤖 MULTI-AGENT CORE
├── ai/
│   ├── agents/                 # Individual AI agents
│   ├── teams/                  # Multi-agent teams  
│   └── workflows/              # Step-based workflows
│       └── processamento-faturas/  # CTE Processing Pipeline
🌐 API LAYER
├── api/
│   ├── serve.py               # Production server
│   ├── main.py                # Development playground
│   └── routes/                # API endpoints
📚 SHARED SERVICES
├── lib/
│   ├── config/                # Configuration management
│   ├── knowledge/             # CSV-based RAG system
│   ├── auth/                  # API authentication
│   └── utils/                 # Utility functions
🧪 TESTING
└── tests/                     # Test scenarios
```

Co-Authored-By: Automagik Genie <genie@namastex.ai>
