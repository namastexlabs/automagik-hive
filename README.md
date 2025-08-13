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

The ProcessamentoFaturas workflow is a **daily scheduled system** that transforms manual CTE invoice processing into an automated, status-based pipeline with individual PO tracking and incremental processing:

1. **🌅 Daily Initialization** - Dual scan for new emails AND existing JSON files with backlog processing
2. **🔍 JSON Analysis** - Individual PO status extraction and categorization from all JSON files
3. **🎯 Status-Based Routing** - Smart routing of each PO to appropriate processing step based on current status
4. **⚙️ Individual PO Processing** - Status-specific API calls with batch and individual processing modes
5. **🏁 Daily Completion** - JSON file updates, status persistence, and next execution scheduling

### 🔄 **Revolutionary Architecture Change**

**From**: Linear single execution (Email → Data → JSON → API → Complete)  
**To**: Daily cyclic processing with individual PO status tracking

#### **🚀 Key Transformation Benefits:**
- **Daily Scheduled Execution**: Runs automatically every day at 8 AM
- **Incremental Processing**: Each PO advances gradually through pipeline over multiple days
- **Individual Status Tracking**: Every PO maintains its own processing status in JSON files
- **Backlog Management**: Processes pending POs from previous executions alongside new emails
- **Resilient Processing**: Individual PO failures don't affect other POs in the batch
- **Smart Routing**: Each PO gets routed to exactly the processing step it needs

### 🏗️ Architecture

#### **Workflow Type**: Agno Workflows 2.0 - Daily Scheduled Architecture
Built using **daily cyclic execution** with status-based PO processing and specialized agents:

```python
Workflow(
    name="processamento_faturas",
    description="Daily scheduled CTE invoice processing with individual PO status-based routing",
    steps=[
        Step("daily_initialization", executor=execute_daily_initialization_step),
        Step("json_analysis", executor=execute_json_analysis_step),
        Step("status_based_routing", executor=execute_status_based_routing_step), 
        Step("individual_po_processing", executor=execute_individual_po_processing_step),
        Step("daily_completion", executor=execute_daily_completion_step)
    ],
    storage=PostgresStorage(auto_upgrade_schema=True)
)
```

#### **🔄 Daily Processing Cycle Example:**
```
Day 1 (8 AM): Email scan → 3 new POs (PENDING) → invoiceGen → 3 POs (WAITING_MONITORING)
Day 2 (8 AM): JSON analysis → 3 POs (WAITING_MONITORING) → invoiceMonitor → 3 POs (MONITORED)
Day 3 (8 AM): JSON analysis → 3 POs (MONITORED) → individual downloads → 3 POs (DOWNLOADED)
Day 4 (8 AM): JSON analysis → 3 POs (DOWNLOADED) → individual uploads → 3 POs (UPLOADED) ✅
```

#### **5 Specialized Agents - Enhanced for Daily Processing**
Each step utilizes dedicated agents with specific daily processing expertise:

- **📧 EmailProcessor** - Gmail OAuth2 + existing JSON file scanning, morning email processing
- **📊 DataExtractor** - JSON file analysis, individual PO status extraction, categorization
- **🏗️ JSONGenerator** - Status-based routing logic, processing queue organization  
- **🔗 APIOrchestrator** - Individual PO API calls, batch vs individual processing modes
- **📁 FileManager** - JSON file updates, status persistence, next execution scheduling

#### **🎯 Status-Based Processing Logic:**
```
PENDING POs        → invoiceGen API (batch processing)    → WAITING_MONITORING
WAITING_MONITORING → invoiceMonitor API (batch)          → MONITORED  
MONITORED POs      → download API (individual per PO)    → DOWNLOADED
DOWNLOADED POs     → upload API (individual per PO)      → UPLOADED ✅
UPLOADED POs       → Skip (already completed)            → No action
FAILED_* POs       → Error handling and retry logic      → Status-specific recovery
```

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
        "NF/CTE": "96765", 
        "valor CHAVE": 1644.67,
        "Empresa Origem": "CLARO MOVEL ENG",
        "CNPJ Fornecedor": "9351138000100",
        "Competência": "45778"
      }
    ],
    "total_value": 1644.67,
    "cte_count": 1,
    "status": "PENDING"
  }
}
```

#### **Output**: Daily Status-Tracked JSON Structure
```json
{
  "batch_id": "daily_20250113_080012",
  "source_file": "faturas_janeiro_2025.xlsx",
  "processing_timestamp": "2025-01-13T08:00:12Z",
  "last_daily_update": "2025-01-13T08:15:32Z",
  "total_ctes": 15,
  "total_pos": 8,
  "total_value": 45230.89,
  "client_data": ["CLARO MOVEL ENG", 9351138000100],
  "type": "CTE",
  "orders": [
    {
      "po_number": "600708542",
      "cte_entries": [...],
      "total_value": 1644.67,
      "status": "WAITING_MONITORING",  // Individual PO status tracking
      "last_updated": "2025-01-13T08:15:32Z",
      "processing_history": [
        {"status": "PENDING", "timestamp": "2025-01-12T08:00:00Z"},
        {"status": "WAITING_MONITORING", "timestamp": "2025-01-13T08:15:32Z"}
      ]
    },
    {
      "po_number": "600708543", 
      "cte_entries": [...],
      "total_value": 2189.45,
      "status": "DOWNLOADED",  // Different POs can be in different stages
      "last_updated": "2025-01-12T08:20:15Z",
      "download_path": "mctech/downloads/fatura_600708543.pdf"
    }
  ]
}
```

### 🔗 Browser API Integration

#### **Status-Based API Orchestration**
The daily workflow integrates with Browser API through status-driven flow execution using a **single endpoint**:

**🎯 Unified Endpoint**: `POST /execute_flow`

All API calls use the same endpoint with different `flow_name` parameters:

1. **`invoiceGen`** - **Batch processing** for PENDING POs (multiple POs per call)
2. **`invoiceMonitor`** - **Batch processing** for WAITING_MONITORING POs  
3. **`main-download-invoice`** - **Individual processing** for MONITORED POs (one API call per PO)
4. **`invoiceUpload`** - **Individual processing** for DOWNLOADED POs (one API call per PO)

#### **📋 API Call Structure**
```http
POST http://localhost:8088/execute_flow
Content-Type: application/json

{
  "flow_name": "invoiceGen",
  "parameters": {
    "orders": ["600708542", "600708543"],
    "headless": true
  },
  "headless": true
}
```

#### **🔄 Daily API Call Distribution:**
```
Single Daily Execution Processes:
├── 5 PENDING POs      → 1 batch invoiceGen call    → 5 WAITING_MONITORING POs
├── 3 MONITORING POs   → 1 batch invoiceMonitor call → 3 MONITORED POs  
├── 2 MONITORED POs    → 2 individual download calls → 2 DOWNLOADED POs
└── 4 DOWNLOADED POs   → 4 individual upload calls  → 4 UPLOADED POs ✅

Total API calls: 8 calls processing 14 POs in various stages
```

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

### 💾 State Management - Daily Persistence Architecture

#### **Enhanced PostgreSQL Persistence**
- **Daily Session State**: Cross-step data sharing with daily execution context
- **Individual PO Status**: Persistent status tracking per PO across multiple days
- **JSON File State**: Real-time status updates written back to JSON files
- **Backlog Management**: Automatic identification and processing of pending POs
- **Error Recovery**: Individual PO failure isolation with status-specific recovery
- **Daily Metrics**: Performance tracking across multiple daily executions

#### **Daily Status Transition Flow**
```
🔄 DAILY EXECUTION CYCLE:

Day N-2: PENDING → invoiceGen (batch) → WAITING_MONITORING
Day N-1: WAITING_MONITORING → invoiceMonitor (batch) → MONITORED  
Day N:   MONITORED → download (individual) → DOWNLOADED
Day N+1: DOWNLOADED → upload (individual) → UPLOADED ✅

📊 PARALLEL PROCESSING:
- Multiple POs can be in different stages simultaneously
- Each PO progresses independently based on its individual status
- Failed POs don't block progression of successful POs
- New POs from emails get added to PENDING queue daily

❌ ERROR HANDLING:
FAILED_EXTRACTION   → Retry email/Excel processing (next day)
FAILED_GENERATION   → Retry invoiceGen API call
FAILED_MONITORING   → Retry invoiceMonitor API call  
FAILED_DOWNLOAD     → Retry individual download
FAILED_UPLOAD       → Retry individual upload
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

### ⚡ Performance Targets - Daily Execution Optimized

- **Daily Initialization**: <10s for email scan + JSON file analysis
- **JSON Analysis**: <5s per existing JSON file analyzed
- **Status-Based Routing**: <3s for processing queue organization
- **Batch API Operations**: <15s per batch call (invoiceGen, invoiceMonitor)
- **Individual API Operations**: <8s per individual call (download, upload)
- **Daily Completion**: <5s for JSON file updates and scheduling
- **Total Daily Execution**: <2 minutes for typical mixed workload

#### **📊 Daily Processing Capacity:**
```
Typical Daily Workload:
├── New emails: 0-3 (morning only, <12PM)
├── Existing POs to process: 10-50 across various stages
├── Batch API calls: 0-2 (invoiceGen + invoiceMonitor)
├── Individual API calls: 5-25 (downloads + uploads)
└── JSON files updated: 3-8 consolidated files

Performance: Processes 50+ POs across multiple stages in under 2 minutes
```

### 🔧 Configuration

#### **Environment Setup**
```bash
# Required environment variables (.env)
GMAIL_CLIENT_ID=your_gmail_oauth_client_id
GMAIL_CLIENT_SECRET=your_gmail_oauth_secret

# Database connection (automatically configured with make agent)
DATABASE_URL="postgresql://localhost:35532/hive_agent"

# Browser API Configuration
BROWSER_API_BASE_URL="http://localhost:8088"
BROWSER_API_TIMEOUT="900"
BROWSER_API_MAX_RETRIES="3"
```

#### **📋 Browser API Server Requirements**
The workflow requires a **running Browser API server** at `http://localhost:8088`:

```bash
# Browser API must be running and responding to:
curl -X POST http://localhost:8088/execute_flow \
  -H "Content-Type: application/json" \
  -d '{"flow_name": "test", "parameters": {}}'

# Health check (if available):
curl http://localhost:8088/health
```

**⚠️ Important**: The workflow will **fail immediately** if the Browser API is not available. Ensure the server is running before executing the workflow.

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

### 🚀 Deployment - Daily Scheduled Execution

#### **Local Development**
```bash
# Start workflow service
uv run python api/main.py

# Access playground for manual testing
open http://localhost:8000

# Test daily workflow execution
cd ai/workflows/processamento-faturas/
uv run python workflow.py
```

#### **Production Deployment with Daily Scheduling**
```bash
# Docker deployment
docker build -t hive-workflows .
docker run -p 8000:8000 hive-workflows

# Cron job setup for daily execution at 8 AM
crontab -e
# Add: 0 8 * * * cd /project && uv run python -c "
import asyncio
from ai.workflows.processamento_faturas.workflow import get_processamento_faturas_workflow

async def daily_run():
    workflow = get_processamento_faturas_workflow()
    await workflow.arun('Execute daily CTE processing')

asyncio.run(daily_run())
"
```

#### **⚡ Quick Execution**
```bash
# 1. Ensure Browser API is running
curl http://localhost:8088/health  # Should return 200

# 2. Start agent services
make agent

# 3. Run workflow via API Playground
uv run python api/main.py
# Access: http://localhost:8000
# Select: processamento_faturas workflow -> Run
```

#### **🕰️ Scheduling Options:**
```bash
# Option 1: Cron Job (Linux/Mac) - with API check
#!/bin/bash
# daily-workflow-runner.sh
if curl -sf http://localhost:8088/health > /dev/null; then
  cd /project && uv run python api/main.py --execute processamento_faturas
else
  echo "Browser API not available - workflow skipped" >&2
  exit 1
fi

# Cron: 0 8 * * * /path/to/daily-workflow-runner.sh

# Option 2: Docker Compose with Scheduler
services:
  browser-api:
    image: browser-api:latest
    ports: ["8088:8088"]
  
  hive-scheduler:
    build: .
    command: python daily_scheduler.py
    environment:
      - SCHEDULE_TIME=08:00
      - WORKFLOW_NAME=processamento_faturas
      - BROWSER_API_BASE_URL=http://browser-api:8088
    depends_on: [browser-api]

# Option 3: MCP automagik-hive scheduled execution
mcp__automagik_hive__schedule_workflow(
    workflow_id="processamento_faturas",
    schedule="0 8 * * *",  # Daily at 8 AM
    input_data={"mode": "daily_processing"}
)
```

### 📊 Monitoring & Metrics

#### **Daily Workflow Metrics**
- **Daily Execution Time**: Complete daily cycle duration (<2 minutes target)
- **PO Processing Volume**: Total POs processed across all stages per day
- **Status Progression Rate**: POs advancing from one status to next per day
- **API Success Rate**: Browser API call success percentage by call type
- **Backlog Reduction**: Rate of PO completion (UPLOADED status) per day
- **New vs Existing Ratio**: New emails processed vs existing PO backlog handled

#### **Individual PO Tracking**
- **Status Duration**: Time spent in each processing stage
- **End-to-End Latency**: Days from PENDING to UPLOADED per PO
- **Error Recovery Time**: Time to recover from individual PO failures
- **Batch vs Individual Performance**: Efficiency comparison of processing modes

#### **📈 Daily Dashboard Metrics:**
```
Daily Execution Summary (2025-01-13):
├── Total POs Found: 23
├── New POs Added: 3 (from morning emails)
├── POs Processed: 18
│   ├── Batch Operations: 8 POs (2 API calls)
│   └── Individual Operations: 10 POs (10 API calls)
├── POs Completed: 6 (reached UPLOADED status)
├── POs Remaining: 5 (various stages)
└── Next Execution: 2025-01-14 08:00:00
```

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
