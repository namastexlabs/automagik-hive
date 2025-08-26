# Technical Specification Document: WhatsApp Processamento-Faturas Conversational Agent

## 1. OVERVIEW
**Objective**: Create a WhatsApp conversational agent system that enables natural language queries about processamento-faturas JSON data using Agno's JSONKnowledgeBase with selective vector embedding strategy
**Success Metrics**: 
- Successfully query PO status and values via WhatsApp in Portuguese
- <500ms response time for simple queries
- 95%+ accuracy for PO number and status queries
- Seamless integration with existing processamento-faturas workflow

## 2. ARCHITECTURAL VALIDATION

### 2.1 Agno Knowledge Base Architecture Analysis
**✅ JSONKnowledgeBase Capabilities Confirmed:**
- Native support for JSON document ingestion and vector embedding
- PgVector integration with full metadata filtering capabilities
- Built-in Portuguese language support through LLM embeddings
- Advanced metadata attachment and filtering at query time
- Hot reload functionality for real-time data updates
- Agentic filtering with automatic filter extraction from queries

**✅ Metadata-Based Filtering Strategy:**
```python
# VALIDATED APPROACH: Full document embedding with metadata filtering
# Entire PO JSON documents embedded for semantic search
# Metadata filtering enables selective access to po_number, status, po_total_value
knowledge_base = JSONKnowledgeBase(
    path=[
        {
            "path": "processamento_faturas_data.json", 
            "metadata": {
                "data_type": "po_orders",
                "source": "processamento_faturas_workflow",
                "updated_at": "2025-01-25T10:30:00Z"
            }
        }
    ],
    vector_db=PgVector(...),
)
```

**✅ Architecture Validation Confirmed:**
- JSONKnowledgeBase natively supports comprehensive metadata filtering
- Agentic filtering automatically extracts relevant filters from Portuguese queries
- Agent-level and query-level filtering both available
- **OPTIMAL SOLUTION**: Use native JSONKnowledgeBase with metadata filtering instead of custom preprocessing

### 2.2 WhatsApp Evolution MCP Integration Assessment
**✅ Evolution MCP Tools Available:**
- send_text_message: Core messaging capability
- send_media: Support for rich responses (images, documents)
- send_presence: Typing indicators for better UX

**⚠️ Integration Challenges Identified:**
- Evolution API instance needs to be properly configured (currently failing timeout)
- Requires Evolution API server running on specified port with valid authentication
- **SOLUTION**: Separate Evolution API setup phase required before agent deployment

### 2.3 Data Integration Strategy Validation
**✅ Processamento-Faturas JSON Structure:**
```json
{
  "orders": [
    {
      "po_number": "600714860",
      "status": "PENDING", 
      "po_total_value": 2574.15,
      "ctes": [...],
      "cte_count": 3
    }
  ]
}
```

**✅ Data Synchronization Strategy:**
- Hot reload mechanism available through CSVHotReloadManager (adaptable to JSON)
- File system monitoring for JSON updates from workflow
- Incremental loading with content hashing for performance

## 3. FUNCTIONAL REQUIREMENTS

### 3.1 Core Features
- **FR-01**: Natural language PO status queries in Portuguese
  - **Input**: "qual o status do pedido 600714860?"
  - **Output**: "O pedido 600714860 está com status PENDING."
  
- **FR-02**: PO value queries with proper Brazilian currency formatting
  - **Input**: "qual o valor do pedido 600714860?" 
  - **Output**: "O pedido 600714860 tem valor total de R$ 2.574,15."

- **FR-03**: Bulk status queries for multiple POs
  - **Input**: "quais pedidos estão pendentes?"
  - **Output**: "Os seguintes pedidos estão com status PENDING: 600714860, 600714891, 600714895..."

- **FR-04**: PO count and summary statistics
  - **Input**: "quantos pedidos temos?"
  - **Output**: "Temos 43 pedidos no total: 35 PENDING, 8 PROCESSED."

### 3.2 User Stories
- As a **operations manager**, I want to **query PO status via WhatsApp** so that **I can get real-time updates without accessing internal systems**
- As a **finance user**, I want to **check PO values quickly** so that **I can validate invoice amounts on the go**
- As a **administrator**, I want to **get batch statistics** so that **I can monitor processing pipeline health**

## 4. NON-FUNCTIONAL REQUIREMENTS

### 4.1 Performance
- **Response Time**: <500ms for simple queries (status, value lookups)
- **Throughput**: Support 50+ concurrent WhatsApp conversations
- **Scalability**: Handle up to 10,000 PO records with sub-second search

### 4.2 Security
- **Authentication**: Evolution API key validation for WhatsApp integration
- **Authorization**: WhatsApp number whitelist for access control
- **Data Protection**: No sensitive financial data logged in WhatsApp messages

### 4.3 Reliability  
- **Availability**: 99.5% uptime aligned with Evolution API availability
- **Error Handling**: Graceful fallback for API failures with user-friendly messages
- **Recovery**: Automatic reconnection to Evolution API and database

## 5. TECHNICAL ARCHITECTURE

### 5.1 System Components
- **WhatsApp Agent**: Agno Agent with Evolution MCP integration and Portuguese NLP
- **Knowledge Base**: Custom JSONKnowledgeBase with selective embedding strategy  
- **Data Sync Service**: Hot reload mechanism for processamento-faturas JSON updates
- **Response Formatter**: Brazilian Portuguese formatting for currency and lists

### 5.2 Data Models
```python
# JSONKnowledgeBase Document Structure  
class ProcessamentoFaturasDocument:
    # Full JSON document embedded with metadata filtering
    json_path: str  # Path to consolidated JSON file
    metadata: dict = {
        "data_type": "po_orders",
        "source": "processamento_faturas_workflow", 
        "batch_id": str,
        "updated_at": datetime,
        "total_pos": int
    }

# WhatsApp Response Models
class WhatsAppResponse:
    text: str
    formatting: str = "markdown"
    instance: str = "hive-production"
```

### 5.3 API Contracts
```python
# Agent Knowledge Query Interface
@endpoint("/api/po-query")
def query_po_data(
    query: str,
    filters: Optional[Dict[str, Any]] = None
) -> POQueryResponse:
    """Process natural language PO queries"""

# WhatsApp Message Handler
@webhook("/whatsapp/message")
def handle_whatsapp_message(
    message: WhatsAppMessage
) -> WhatsAppResponse:
    """Process incoming WhatsApp messages"""
```

## 6. TEST-DRIVEN DEVELOPMENT STRATEGY

### 6.1 Red-Green-Refactor Integration
- **Red Phase**: Write failing tests for Portuguese LLM query processing
  - Test agentic filtering with Portuguese queries
  - Test metadata filtering accuracy
  - Test currency formatting for Brazilian real
  
- **Green Phase**: Implement minimal JSONKnowledgeBase with agentic filtering
  - Enable agentic knowledge filters for automatic query processing
  - Basic metadata filtering integration
  - Currency formatting in agent instructions
  
- **Refactor Phase**: Optimize LLM accuracy and response quality
  - Enhanced Portuguese instructions and prompting
  - Context-aware metadata filtering
  - Performance optimization for vector search and filtering

### 6.2 Test Categories
- **Unit Tests**: Agentic filtering accuracy, metadata filtering, currency formatting
- **Integration Tests**: JSONKnowledgeBase with PgVector, Evolution MCP integration, hot reload
- **End-to-End Tests**: Complete WhatsApp conversation flows with Portuguese queries

## 7. IMPLEMENTATION PHASES

### 7.1 Phase 1: Foundation (Week 1)
- **Deliverable 1**: Evolution API setup and configuration validation
- **Deliverable 2**: JSONKnowledgeBase implementation with metadata filtering and agentic filtering
- **Deliverable 3**: Portuguese-enabled agent with LLM query processing

### 7.2 Phase 2: Core Agent (Week 2)
- **Deliverable 4**: WhatsApp Agent with Evolution MCP integration
- **Deliverable 5**: Data synchronization service for JSON hot reload
- **Deliverable 6**: Response formatting for Brazilian Portuguese

### 7.3 Phase 3: Production Integration (Week 3)
- **Deliverable 7**: Integration with processamento-faturas workflow
- **Deliverable 8**: Performance optimization and caching
- **Deliverable 9**: Production deployment and monitoring

## 8. EDGE CASES & ERROR HANDLING

### 8.1 Boundary Conditions
- **Invalid PO Numbers**: "Desculpe, não encontrei o pedido 999999999. Verifique o número e tente novamente."
- **Empty Results**: "Não foram encontrados pedidos com esse status no momento."
- **Ambiguous Queries**: "Sua consulta não foi clara. Você pode especificar o número do PO ou status desejado?"

### 8.2 Error Scenarios
- **Evolution API Down**: "Serviço temporariamente indisponível. Tente novamente em alguns minutos."
- **Database Connection Failed**: "Erro interno. Nossa equipe foi notificada e resolverá em breve."
- **Invalid WhatsApp Number**: Silent ignore with logging for security

## 9. PORTUGUESE LLM QUERY PROCESSING

### 9.1 Agentic Filtering with Portuguese Queries
```python
# Agent with agentic filtering enabled for Portuguese
agent = Agent(
    knowledge=knowledge_base,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,  # Automatically extract filters from queries
    instructions="""
    Você é um assistente especializado em consultas de pedidos (POs) do sistema processamento-faturas.
    Responda sempre em português brasileiro.
    Para consultas de status, procure informações sobre o estado atual do pedido.
    Para consultas de valor, formate valores monetários como R$ X.XXX,XX.
    """
)

# LLM automatically processes Portuguese queries and extracts relevant filters
# Examples of natural processing without regex patterns:
# "qual o status do pedido 600714860?" → Searches for PO 600714860 and returns status
# "quais pedidos estão pendentes?" → Filters by status=PENDING and lists all matches
# "valor do pedido 600714860" → Searches PO 600714860 and returns formatted value
```

### 9.2 Query-Time Filtering Examples
```python
# Status queries - LLM processes naturally
agent.print_response(
    "qual o status do pedido 600714860?",
    knowledge_filters={"po_number": "600714860"}  # Can combine with explicit filters
)

# Bulk status queries - LLM understands intent
agent.print_response(
    "quais pedidos estão com status pending?",
    knowledge_filters={"status": "PENDING"}
)

# Value queries with automatic formatting
agent.print_response(
    "qual o valor total do pedido 600714860?",
    knowledge_filters={"po_number": "600714860"}
)
```

### 9.2 Response Templates
```python
# Status responses
STATUS_RESPONSE = "O pedido {po_number} está com status {status}."

# Value responses with currency formatting
VALUE_RESPONSE = "O pedido {po_number} tem valor total de R$ {value:,.2f}."

# Bulk responses
BULK_RESPONSE = "Encontrados {count} pedidos com status {status}: {po_list}"
```

## 10. ACCEPTANCE CRITERIA

### 10.1 Definition of Done
- [ ] WhatsApp agent responds to Portuguese queries about PO status and values
- [ ] Data synchronization working with processamento-faturas JSON updates
- [ ] Response time <500ms for 90% of queries
- [ ] Brazilian Portuguese formatting for currency values
- [ ] Error handling for invalid PO numbers and API failures
- [ ] Integration tests passing for all major query types

### 10.2 Validation Steps
1. **Portuguese Query Testing**: Validate natural language processing accuracy
2. **Data Accuracy Testing**: Verify PO status and value retrieval correctness  
3. **Performance Testing**: Confirm sub-500ms response times
4. **Integration Testing**: Validate end-to-end WhatsApp conversation flows
5. **Error Handling Testing**: Verify graceful handling of edge cases

## 11. ALTERNATIVE ARCHITECTURAL APPROACHES

### 11.1 Alternative 1: Individual PO Documents (Not Recommended)
**Use Case**: If fine-grained document control needed
```python
# Create individual JSON files per PO (less efficient)
knowledge_base = JSONKnowledgeBase(
    path=[
        {
            "path": f"po_{po['po_number']}.json",
            "metadata": {
                "po_number": po["po_number"],
                "status": po["status"], 
                "po_total_value": po["po_total_value"],
                "cte_count": po["cte_count"]
            }
        }
        for po in po_data
    ],
    vector_db=PgVector(...)
)
```

### 11.2 Alternative 2: Hybrid CSV + JSON Approach
**Better for**: Leveraging existing RowBasedCSVKnowledgeBase
```python
# Convert JSON to CSV format for existing infrastructure
csv_data = convert_po_json_to_csv(po_json_data)
knowledge_base = RowBasedCSVKnowledgeBase(csv_data, vector_db)
```

## 12. RISK ANALYSIS & MITIGATION

### 12.1 High-Risk Areas
- **Evolution API Dependency**: Single point of failure for WhatsApp integration
  - **Mitigation**: Implement health checks and failover notifications
- **Agentic Filtering Accuracy**: LLM may misunderstand Portuguese queries or fail to extract correct filters
  - **Mitigation**: Extensive testing with real Portuguese query patterns and fallback to explicit filtering
- **Data Sync Delays**: Lag between workflow updates and knowledge base
  - **Mitigation**: File system monitoring with immediate reload triggers

### 12.2 Performance Risks
- **Vector Search Scaling**: Potential slowdown with large PO datasets
  - **Mitigation**: PgVector indexing optimization and connection pooling
- **WhatsApp Rate Limits**: Evolution API throttling under high load
  - **Mitigation**: Request queuing and rate limiting implementation

## 13. INTEGRATION POINTS

### 13.1 Processamento-Faturas Workflow Integration
- **Trigger Point**: JSON file creation in mctech/ctes/ directory
- **Sync Mechanism**: File system watcher with hot reload
- **Data Flow**: JSON → Document preprocessing → Vector embeddings → Knowledge base update

### 13.2 Jack-Hive Infrastructure Integration
- **Database**: Shared PgVector instance with agent environment
- **Configuration**: Unified MCP server configuration in YAML
- **Monitoring**: Integration with existing logging and metrics infrastructure

---

## 🎯 GENIE DEV-PLANNER COMPLETION SUMMARY

**Architecture Validation**: ✅ VALIDATED - JSONKnowledgeBase with custom preprocessing approach is technically sound
**Alternative Approaches**: Custom AgentKnowledge provides better control for selective embedding requirements
**Implementation Roadmap**: 3-week phased approach with clear milestones and deliverables
**Technical Specifications**: Comprehensive Portuguese NLP patterns and response templates defined
**Risk Analysis**: Key challenges identified with concrete mitigation strategies
**Integration Points**: Clear data flow from processamento-faturas workflow to WhatsApp agent

**RECOMMENDED APPROACH**: 
- Use native JSONKnowledgeBase with metadata filtering capabilities
- Enable agentic filtering for automatic Portuguese query processing via LLM
- Use Evolution MCP integration with proper error handling and fallbacks
- Deploy as dedicated Agno agent with hot reload data synchronization
- Leverage full document embedding with query-time metadata filtering

This specification provides a production-ready foundation for building a sophisticated WhatsApp conversational agent that seamlessly integrates with the existing processamento-faturas workflow while leveraging Agno's native capabilities optimally.