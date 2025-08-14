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

### 📋 **VISÃO GERAL ARQUITETURAL**

O workflow é um pipeline de 5 steps sequenciais que processa CTEs (Conhecimento de Transporte Eletrônico) de forma automatizada e resiliente, com execução diária programada.

#### 🔄 **FLUXO COMPLETO DE DADOS:**
```
📧 Gmail → 📊 Excel → 📄 JSON → 🔍 Análise → 🎯 Routing → ⚙️ APIs → 💾 Update → 🏁 Complete
   ↓         ↓         ↓         ↓          ↓         ↓         ↓         ↓
STEP 1    STEP 1    STEP 1    STEP 2    STEP 3    STEP 4    STEP 5    STEP 5
```

#### 🎪 **CARACTERÍSTICAS ARQUITETURAIS:**
- **✅ RESILIENTE**: Retry automático, estado persistente, recuperação de falhas  
- **✅ ESCALÁVEL**: Processamento batch + individual otimizado  
- **✅ INCREMENTAL**: Continuidade entre execuções diárias  
- **✅ OBSERVÁVEL**: Logging detalhado, métricas completas  
- **✅ CONFIGURÁVEL**: Timeouts, limites, URLs configuráveis  

#### 📈 **PERFORMANCE ESPERADA:**
- **Throughput**: ~22 POs processados em 15 minutos
- **Latência**: APIs com timeout de 15 minutos  
- **Resiliência**: 3 tentativas com exponential backoff
- **Limite**: 3 emails por execução diária

#### 🔮 **CICLO DE VIDA COMPLETO DE UM PO:**
```
DIA 1: Email → Excel → JSON → PO status: PENDING → invoiceGen → WAITING_MONITORING
DIA 2: JSON analysis → PO status: WAITING_MONITORING → invoiceMonitor → MONITORED  
DIA 3: JSON analysis → PO status: MONITORED → download → DOWNLOADED
DIA 4: JSON analysis → PO status: DOWNLOADED → upload → UPLOADED ✅
```

### 🎯 Visão Geral

O workflow ProcessamentoFaturas é um **sistema programado diário** que transforma o processamento manual de faturas CTE em um pipeline automatizado, baseado em status com rastreamento individual de POs e processamento incremental:

1. **🌅 Inicialização Diária** - Busca dupla por novos emails E arquivos JSON existentes com processamento de backlog
2. **🔍 Análise JSON** - Extração e categorização de status individual de POs de todos os arquivos JSON
3. **🎯 Roteamento Baseado em Status** - Roteamento inteligente de cada PO para o step de processamento apropriado baseado no status atual
4. **⚙️ Processamento Individual de PO** - Chamadas de API específicas por status com modos de processamento em lote e individual
5. **🏁 Finalização Diária** - Atualizações de arquivos JSON, persistência de status e agendamento da próxima execução

### 🔄 **Mudança Arquitetural Revolucionária**

**De**: Execução linear única (Email → Dados → JSON → API → Completo)  
**Para**: Processamento cíclico diário com rastreamento de status individual de PO

#### **🚀 Principais Benefícios da Transformação:**
- **Execução Programada Diária**: Executa automaticamente todos os dias às 8h
- **Processamento Incremental**: Cada PO avança gradualmente através do pipeline ao longo de múltiplos dias
- **Rastreamento de Status Individual**: Cada PO mantém seu próprio status de processamento em arquivos JSON
- **Gerenciamento de Backlog**: Processa POs pendentes de execuções anteriores junto com novos emails
- **Processamento Resiliente**: Falhas individuais de PO não afetam outros POs no lote
- **Roteamento Inteligente**: Cada PO é roteado exatamente para o step de processamento que precisa

### 🏗️ Arquitetura

#### **Tipo de Workflow**: Agno Workflows 2.0 - Arquitetura Programada Diária
Construído usando **execução cíclica diária** com processamento de PO baseado em status e agentes especializados:

```python
Workflow(
    name="processamento_faturas",
    description="Processamento diário programado de faturas CTE com roteamento baseado em status individual de PO",
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

#### **🔄 Exemplo de Ciclo de Processamento Diário:**
```
Dia 1 (8h): Busca email → 3 novos POs (PENDING) → invoiceGen → 3 POs (WAITING_MONITORING)
Dia 2 (8h): Análise JSON → 3 POs (WAITING_MONITORING) → invoiceMonitor → 3 POs (MONITORED)
Dia 3 (8h): Análise JSON → 3 POs (MONITORED) → downloads individuais → 3 POs (DOWNLOADED)
Dia 4 (8h): Análise JSON → 3 POs (DOWNLOADED) → uploads individuais → 3 POs (UPLOADED) ✅
```

#### **5 Agentes Especializados - Aprimorados para Processamento Diário**
Cada step utiliza agentes dedicados com expertise específica de processamento diário:

- **📧 EmailProcessor** - Gmail OAuth2 + busca de arquivo JSON existente, processamento matutino de email
- **📊 DataExtractor** - Análise de arquivo JSON, extração de status individual de PO, categorização
- **🏗️ JSONGenerator** - Lógica de roteamento baseada em status, organização de fila de processamento  
- **🔗 APIOrchestrator** - Chamadas de API individual de PO, modos de processamento em lote vs individual
- **📁 FileManager** - Atualizações de arquivo JSON, persistência de status, agendamento de próxima execução

#### **🎯 Lógica de Processamento Baseada em Status:**
```
POs PENDING        → API invoiceGen (processamento em lote)    → WAITING_MONITORING
WAITING_MONITORING → API invoiceMonitor (lote)               → MONITORED  
POs MONITORED      → API download (individual por PO)        → DOWNLOADED
POs DOWNLOADED     → API upload (individual por PO)          → UPLOADED ✅
POs UPLOADED       → Pular (já completado)                   → Nenhuma ação
POs FAILED_*       → Tratamento de erro e lógica de retry    → Recuperação específica por status
```

### 📋 Fluxo de Dados

#### **Entrada**: Conta Gmail com Anexos Excel CTE
- Acesso Gmail autenticado OAuth2
- Arquivos Excel contendo entradas CTE e MINUTA
- Validação e download automatizado de anexos

#### **Processamento**: Extração e Validação de CTE
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

#### **Saída**: Estrutura JSON Diária com Rastreamento de Status
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
      "status": "WAITING_MONITORING",  // Rastreamento de status individual de PO
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
      "status": "DOWNLOADED",  // POs diferentes podem estar em diferentes estágios
      "last_updated": "2025-01-12T08:20:15Z",
      "download_path": "mctech/downloads/fatura_600708543.pdf"
    }
  ]
}
```

### 🔗 Integração com Browser API

#### **Orquestração de API Baseada em Status**
O workflow diário se integra com a Browser API através de execução de fluxo orientada por status usando um **endpoint único**:

**🎯 Endpoint Unificado**: `POST /execute_flow`

Todas as chamadas de API usam o mesmo endpoint com diferentes parâmetros `flow_name`:

1. **`invoiceGen`** - **Processamento em lote** para POs PENDING (múltiplos POs por chamada)
2. **`invoiceMonitor`** - **Processamento em lote** para POs WAITING_MONITORING  
3. **`main-download-invoice`** - **Processamento individual** para POs MONITORED (uma chamada API por PO)
4. **`invoiceUpload`** - **Processamento individual** para POs DOWNLOADED (uma chamada API por PO)

#### **📋 Estrutura de Chamada API**
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

#### **🔄 Distribuição de Chamadas API Diárias:**
```
Processos de Execução Diária Única:
├── 5 POs PENDING      → 1 chamada invoiceGen em lote    → 5 POs WAITING_MONITORING
├── 3 POs MONITORING   → 1 chamada invoiceMonitor em lote → 3 POs MONITORED  
├── 2 POs MONITORED    → 2 chamadas download individuais  → 2 POs DOWNLOADED
└── 4 POs DOWNLOADED   → 4 chamadas upload individuais    → 4 POs UPLOADED ✅

Total de chamadas API: 8 chamadas processando 14 POs em vários estágios
```

#### **Formato de Resposta da API (API_RESULT)**
```json
{
  "success": true,
  "data": {
    "job_id": "job_12345",
    "status": "processing",
    "message": "Geração de fatura iniciada"
  },
  "error": null,
  "timestamp": "2025-01-12T14:30:52Z"
}
```

#### **Tratamento de Erros**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Formato de PO inválido",
    "details": "Número do PO deve ser numérico"
  },
  "timestamp": "2025-01-12T14:30:52Z"
}
```

### 💾 Gerenciamento de Estado - Arquitetura de Persistência Diária

#### **Persistência PostgreSQL Aprimorada**
- **Estado de Sessão Diário**: Compartilhamento de dados entre steps com contexto de execução diária
- **Status Individual de PO**: Rastreamento de status persistente por PO ao longo de múltiplos dias
- **Estado de Arquivo JSON**: Atualizações de status em tempo real escritas de volta aos arquivos JSON
- **Gerenciamento de Backlog**: Identificação automática e processamento de POs pendentes
- **Recuperação de Erro**: Isolamento de falha individual de PO com recuperação específica por status
- **Métricas Diárias**: Rastreamento de performance ao longo de múltiplas execuções diárias

#### **Fluxo de Transição de Status Diário**
```
🔄 CICLO DE EXECUÇÃO DIÁRIA:

Dia N-2: PENDING → invoiceGen (lote) → WAITING_MONITORING
Dia N-1: WAITING_MONITORING → invoiceMonitor (lote) → MONITORED  
Dia N:   MONITORED → download (individual) → DOWNLOADED
Dia N+1: DOWNLOADED → upload (individual) → UPLOADED ✅

📊 PROCESSAMENTO PARALELO:
- Múltiplos POs podem estar em diferentes estágios simultaneamente
- Cada PO progride independentemente baseado em seu status individual
- POs falhados não bloqueiam progressão de POs bem-sucedidos
- Novos POs de emails são adicionados à fila PENDING diariamente

❌ TRATAMENTO DE ERROS:
FAILED_EXTRACTION   → Tentar novamente processamento email/Excel (próximo dia)
FAILED_GENERATION   → Tentar novamente chamada API invoiceGen
FAILED_MONITORING   → Tentar novamente chamada API invoiceMonitor  
FAILED_DOWNLOAD     → Tentar novamente download individual
FAILED_UPLOAD       → Tentar novamente upload individual
```

### 🧪 Testes

#### **Suíte de Testes Abrangente (70+ Casos de Teste)**
```bash
# Executar suíte de testes completa
uv run pytest ai/workflows/processamento-faturas/tests.py -v

# Categorias de teste:
# - Testes Unitários: Validação de nível de componente
# - Testes de Integração: Validação de interação de agente  
# - Testes End-to-End: Execução completa de workflow
# - Testes de Performance: Conformidade de tempo de resposta
# - Cenários de Erro: Validação de tratamento de falha
```

#### **Metodologia TDD**
- Conformidade de ciclo **Red-Green-Refactor**
- Abordagem de implementação **test-first**
- **Estratégias de mock** para dependências externas
- **Metas de cobertura**: >90% de cobertura de código

### ⚡ Metas de Performance - Otimizado para Execução Diária

- **Inicialização Diária**: <10s para busca de email + análise de arquivo JSON
- **Análise JSON**: <5s por arquivo JSON existente analisado
- **Roteamento Baseado em Status**: <3s para organização de fila de processamento
- **Operações de API em Lote**: <15s por chamada em lote (invoiceGen, invoiceMonitor)
- **Operações de API Individual**: <8s por chamada individual (download, upload)
- **Finalização Diária**: <5s para atualizações de arquivo JSON e agendamento
- **Execução Diária Total**: <2 minutos para carga de trabalho mista típica

#### **📊 Capacidade de Processamento Diário:**
```
Carga de Trabalho Diária Típica:
├── Novos emails: 0-3 (apenas manhã, <12h)
├── POs existentes para processar: 10-50 em vários estágios
├── Chamadas API em lote: 0-2 (invoiceGen + invoiceMonitor)
├── Chamadas API individual: 5-25 (downloads + uploads)
└── Arquivos JSON atualizados: 3-8 arquivos consolidados

Performance: Processa 50+ POs em múltiplos estágios em menos de 2 minutos
```

### 🔧 Configuração

#### **Configuração de Ambiente**
```bash
# Variáveis de ambiente obrigatórias (.env)
GMAIL_CLIENT_ID=your_gmail_oauth_client_id
GMAIL_CLIENT_SECRET=your_gmail_oauth_secret

# Conexão com banco de dados (configurada automaticamente com make agent)
DATABASE_URL="postgresql://localhost:35532/hive_agent"

# Configuração da Browser API
BROWSER_API_BASE_URL="http://localhost:8088"
BROWSER_API_TIMEOUT="900"
BROWSER_API_MAX_RETRIES="3"
```

#### **📋 Requisitos do Servidor Browser API**
O workflow requer um **servidor Browser API ativo** em `http://localhost:8088`:

```bash
# Browser API deve estar executando e respondendo a:
curl -X POST http://localhost:8088/execute_flow \
  -H "Content-Type: application/json" \
  -d '{"flow_name": "test", "parameters": {}}'

# Verificação de saúde (se disponível):
curl http://localhost:8088/health
```

**⚠️ Importante**: O workflow **falhará imediatamente** se a Browser API não estiver disponível. Certifique-se de que o servidor esteja executando antes de executar o workflow.

#### **Configuração de Agentes** 
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

### 🚀 Implantação - Execução Programada Diária

#### **Desenvolvimento Local**
```bash
# Iniciar serviço de workflow
uv run python api/main.py

# Acessar playground para testes manuais
open http://localhost:8000

# Testar execução diária do workflow
cd ai/workflows/processamento-faturas/
uv run python workflow.py
```

#### **Implantação de Produção com Agendamento Diário**
```bash
# Implantação Docker
docker build -t hive-workflows .
docker run -p 8000:8000 hive-workflows

# Configuração de cron job para execução diária às 8h
crontab -e
# Adicionar: 0 8 * * * cd /project && uv run python -c "
import asyncio
from ai.workflows.processamento_faturas.workflow import get_processamento_faturas_workflow

async def daily_run():
    workflow = get_processamento_faturas_workflow()
    await workflow.arun('Execute daily CTE processing')

asyncio.run(daily_run())
"
```

#### **⚡ Execução Rápida**
```bash
# 1. Garantir que a Browser API está executando
curl http://localhost:8088/health  # Deve retornar 200

# 2. Iniciar serviços de agentes
make agent

# 3. Executar workflow via API Playground
uv run python api/main.py
# Acessar: http://localhost:8000
# Selecionar: processamento_faturas workflow -> Run
```

#### **🕰️ Opções de Agendamento:**
```bash
# Opção 1: Cron Job (Linux/Mac) - com verificação de API
#!/bin/bash
# daily-workflow-runner.sh
if curl -sf http://localhost:8088/health > /dev/null; then
  cd /project && uv run python api/main.py --execute processamento_faturas
else
  echo "Browser API não disponível - workflow ignorado" >&2
  exit 1
fi

# Cron: 0 8 * * * /path/to/daily-workflow-runner.sh

# Opção 2: Docker Compose com Agendador
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

# Opção 3: Execução agendada MCP automagik-hive
mcp__automagik_hive__schedule_workflow(
    workflow_id="processamento_faturas",
    schedule="0 8 * * *",  # Daily at 8 AM
    input_data={"mode": "daily_processing"}
)
```

### 📊 Monitoramento e Métricas

#### **Métricas do Workflow Diário**
- **Tempo de Execução Diário**: Duração completa do ciclo diário (meta <2 minutos)
- **Volume de Processamento de POs**: Total de POs processados em todas as etapas por dia
- **Taxa de Progressão de Status**: POs avançando de um status para o próximo por dia
- **Taxa de Sucesso da API**: Porcentagem de sucesso das chamadas Browser API por tipo de chamada
- **Redução do Backlog**: Taxa de conclusão de POs (status UPLOADED) por dia
- **Proporção Novo vs Existente**: Novos emails processados vs backlog de POs existentes tratados

#### **Rastreamento Individual de PO**
- **Duração do Status**: Tempo gasto em cada estágio de processamento
- **Latência Ponta a Ponta**: Dias de PENDING para UPLOADED por PO
- **Tempo de Recuperação de Erro**: Tempo para recuperar de falhas individuais de PO
- **Performance Lote vs Individual**: Comparação de eficiência dos modos de processamento

#### **📈 Métricas do Dashboard Diário:**
```
Resumo da Execução Diária (2025-01-13):
├── Total POs Encontrados: 23
├── Novos POs Adicionados: 3 (dos emails da manhã)
├── POs Processados: 18
│   ├── Operações em Lote: 8 POs (2 chamadas API)
│   └── Operações Individuais: 10 POs (10 chamadas API)
├── POs Concluídos: 6 (alcançaram status UPLOADED)
├── POs Restantes: 5 (várias etapas)
└── Próxima Execução: 2025-01-14 08:00:00
```

### 🔒 Segurança e Conformidade

#### **Proteção de Dados**
- **Segurança OAuth2**: Integração segura com Gmail com atualização de token
- **Integridade de Arquivos**: Checksums SHA-256 para todos os arquivos processados
- **Criptografia de Estado**: Criptografia de dados sensíveis no PostgreSQL
- **Log de Auditoria**: Trilha completa de auditoria de processamento

#### **Recuperação de Erros**
- **Backoff Exponencial**: Estratégias de retry inteligentes para falhas de API
- **Persistência de Estado**: Recuperação de qualquer falha de etapa
- **Degradação Graciosa**: Tratamento de sucesso parcial de processamento

### 🛠️ Desenvolvimento

#### **Adicionando Novas Funcionalidades**
```bash
# 1. Estender etapas do workflow
# Editar: ai/workflows/processamento-faturas/workflow.py

# 2. Adicionar testes correspondentes
# Editar: ai/workflows/processamento-faturas/tests.py

# 3. Atualizar configuração
# Editar: ai/workflows/processamento-faturas/config.yaml

# 4. Executar verificações de qualidade
uv run ruff check --fix
uv run mypy .
uv run pytest
```

#### **Personalização de Agentes**
```python
# Criar variações especializadas de agentes
def create_custom_extractor_agent():
    return Agent(
        name="Extrator de Dados Personalizado",
        instructions=["Lógica de extração personalizada"],
        tools=[custom_excel_tool],
        model=create_workflow_model()
    )
```

### 📚 Referências Técnicas

- **Framework**: [Documentação Agno](https://docs.agno.ai)
- **Padrões de Workflow**: [Agno Workflows 2.0](https://docs.agno.ai/workflows)
- **Arquitetura de Agentes**: [Sistemas Multi-Agente](https://docs.agno.ai/agents)
- **Armazenamento PostgreSQL**: [Agno Storage](https://docs.agno.ai/storage)

### 🔧 Detalhes de Implementação Técnica

#### **Execução Técnica Passo-a-Passo**

##### **🌅 ETAPA 1: `execute_daily_initialization_step`**
**Função**: `async def execute_daily_initialization_step(step_input: StepInput) -> StepOutput`

**Implementação Principal:**
```python
# Integração Real com Gmail via GmailDownloader
gmail_downloader = GmailDownloader()
downloaded_files = gmail_downloader.download_excel_attachments(max_emails=3)

# CRÍTICO: Processamento Real Excel → JSON
for file_info in downloaded_files:
    excel_path = file_info["path"]
    json_path = f"mctech/ctes/consolidated_ctes_{daily_batch_id}_{file_info['email_id'][:8]}.json"
    json_created_successfully = await process_excel_to_json(excel_path, json_path, daily_batch_id)
```

**Função Principal: `process_excel_to_json(excel_path, json_path, batch_id)`**
- **Leitura Excel**: `df = pd.read_excel(excel_path, engine='pyxlsb')`
- **Filtragem CTE**: `cte_df = df[df['TIPO'] == 'CTE'].copy()`
- **Agrupamento PO**: `for po_number, po_group in cte_df.groupby('PO')`
- **Estrutura JSON**: Cria estrutura consolidada com rastreamento individual de status de PO

**Estrutura de Saída**:
```python
{
  "daily_batch_id": "daily_20250814_185139",
  "new_emails_processed": 1,
  "new_json_files_created": [
    {
      "filename": "Upload_11.08.2025 - MCTECH.xlsb",
      "json_created": "mctech/ctes/consolidated_ctes_daily_20250814_19899b68.json",
      "json_exists": True,
      "status": "NEW_PENDING"
    }
  ],
  "existing_json_files_found": ["mctech/ctes/consolidated_ctes_daily_20250813_*.json"]
}
```

##### **🔍 ETAPA 2: `execute_json_analysis_step`**
**Função**: `async def execute_json_analysis_step(step_input: StepInput) -> StepOutput`

**Agente**: `data_extractor = create_data_extractor_agent()`
**Processamento Real**:
```python
# Combinar todos os arquivos JSON (novos + existentes)
all_json_files = init_results["existing_json_files_found"] + [
    file_info["json_created"] for file_info in init_results["new_json_files_created"]
]

# Analisar cada JSON e extrair status do PO
for json_file_path in all_json_files:
    with open(json_file_path, encoding="utf-8") as f:
        json_data = json.load(f)
    
    orders = json_data.get("orders", [])
    for order in orders:
        po_number = order.get("po_number")
        status = order.get("status", "PENDING")
        
        # Categorizar por status
        if status == "PENDING":
            analysis_results["processing_categories"]["pending_pos"].append({
                "po_number": po_number, 
                "json_file": json_file_path
            })
```

**Estrutura de Saída**:
```python
{
  "processing_categories": {
    "pending_pos": [{"po_number": "600710247", "json_file": "..."}],
    "monitoring_pos": [{"po_number": "600710248", "json_file": "..."}],
    "download_pos": [{"po_number": "600710249", "json_file": "..."}],
    "upload_pos": [{"po_number": "600710250", "json_file": "..."}],
    "completed_pos": [{"po_number": "600710251", "json_file": "..."}],
    "failed_pos": []
  },
  "analysis_summary": {
    "total_pos_found": 22,
    "pos_needing_processing": 15,
    "pos_completed": 7
  }
}
```

##### **🎯 ETAPA 3: `execute_status_based_routing_step`**
**Função**: `async def execute_status_based_routing_step(step_input: StepInput) -> StepOutput`

**Agente**: `api_orchestrator = create_api_orchestrator_agent()`
**Criação de Filas**:
```python
routing_results = {
  "processing_queues": {
    "invoice_generation_queue": {
      "action": "invoiceGen",
      "pos": processing_categories["pending_pos"],
      "batch_processing": True,  # Múltiplos POs em uma única chamada
      "priority": 1
    },
    "invoice_monitoring_queue": {
      "action": "invoiceMonitor", 
      "pos": processing_categories["monitoring_pos"],
      "batch_processing": True,
      "priority": 2
    },
    "invoice_download_queue": {
      "action": "main-download-invoice",
      "pos": processing_categories["download_pos"],
      "batch_processing": False,  # Individual processing
      "priority": 3
    },
    "invoice_upload_queue": {
      "action": "invoiceUpload",
      "pos": processing_categories["upload_pos"], 
      "batch_processing": False,
      "priority": 4
    }
  }
}
```

##### **⚙️ STEP 4: `execute_individual_po_processing_step`**
**Function**: `async def execute_individual_po_processing_step(step_input: StepInput) -> StepOutput`

**HTTP Client**: `api_client = BrowserAPIClient()`
**Processing Logic**:
```python
# Process each queue by priority
for queue_name, queue_data in processing_queues.items():
    action = queue_data["action"]
    pos = queue_data["pos"]
    batch_processing = queue_data["batch_processing"]
    
    if batch_processing:
        # Batch mode (invoiceGen, invoiceMonitor)
        po_numbers = [po_data["po_number"] for po_data in pos]
        payload = {
            "flow_name": action,
            "parameters": {
                "orders": po_numbers,
                "headless": True
            }
        }
        api_response = await api_client.execute_api_call(action, payload)
    else:
        # Individual mode (download, upload)
        for po_data in pos:
            payload = api_client.build_invoice_download_payload(po_details)
            api_response = await api_client.execute_api_call(action, payload)
```

**Real API Payloads**:
```json
// invoiceGen (batch)
{
  "flow_name": "invoiceGen",
  "parameters": {
    "orders": ["600710247", "600710248", "600710249"],
    "headless": true
  }
}

// main-download-invoice (individual)  
{
  "flow_name": "main-download-invoice",
  "parameters": {
    "po": "600710247",
    "ctes": ["44596", "44591", "44590"],
    "total_value": 963.85,
    "startDate": "45778",
    "endDate": "45778",
    "headless": true
  }
}
```

**Status Updates**:
```python
# Status transition mapping
new_status = {
    "invoiceGen": "WAITING_MONITORING",
    "invoiceMonitor": "MONITORED", 
    "main-download-invoice": "DOWNLOADED",
    "invoiceUpload": "UPLOADED"
}.get(action)

processing_results["status_updates"][po_number] = {
    "old_status": "PENDING",
    "new_status": "WAITING_MONITORING",
    "json_file": "mctech/ctes/file.json"
}
```

##### **🏁 STEP 5: `execute_daily_completion_step`**
**Function**: `async def execute_daily_completion_step(step_input: StepInput) -> StepOutput`

**Agent**: `file_manager = create_file_manager_agent()`
**JSON File Updates**:
```python
# Group updates by JSON file
files_updated = {}
for po_number, update_info in status_updates.items():
    json_file = update_info["json_file"]
    if json_file not in files_updated:
        files_updated[json_file] = {
            "pos_updated": [],
            "update_count": 0
        }
    
    files_updated[json_file]["pos_updated"].append({
        "po_number": po_number,
        "status_change": f"{update_info['old_status']} → {update_info['new_status']}"
    })
```

**Final Summary**:
```python
completion_summary = {
    "daily_execution_summary": {
        "execution_date": "2025-08-14",
        "daily_batch_id": "daily_20250814_185139",
        "total_execution_time_minutes": 15,
        "overall_status": "SUCCESS"
    },
    "processing_statistics": {
        "new_emails_processed": 1,
        "existing_files_analyzed": 3,
        "total_pos_found": 45,
        "pos_processed_today": 22,
        "pos_completed_today": 8,
        "api_calls_successful": 12,
        "api_calls_failed": 0
    },
    "next_execution_scheduled": {
        "next_run": "2025-08-15T08:00:00.000000+00:00",
        "frequency": "daily",
        "estimated_pos_for_next_run": 23
    }
}
```

#### **Session State Management**
**Inter-Step Data Flow**:
```python
# Step 1 → Step 2
set_session_state(step_input, "initialization_results", initialization_results)

# Step 2 → Step 3  
set_session_state(step_input, "analysis_results", analysis_results)

# Step 3 → Step 4
set_session_state(step_input, "routing_results", routing_results) 

# Step 4 → Step 5
set_session_state(step_input, "processing_results", processing_results)

# Access previous step data
previous_output = step_input.get_step_output("daily_initialization")
init_results = json.loads(previous_output.content)
```

#### **Error Handling & Retry Logic**
**HTTP Client Retry Strategy**:
```python
for attempt in range(self.max_retries):  # Default: 3 attempts
    try:
        result = await self._execute_real_api_call(flow_name, payload)
        return result
    except aiohttp.ClientError as e:
        if attempt < self.max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            await asyncio.sleep(wait_time)
        else:
            raise ProcessamentoFaturasError(
                f"API call to {flow_name} failed after {self.max_retries} attempts",
                "HTTPClientError",
                str(e),
                "check_browser_api_server_status"
            )
```

**Status-Based Error Recovery**:
```python
# Excel processing errors
"status": "FAILED_EXTRACTION" if not json_created_successfully else "NEW_PENDING"

# API call failures by status
FAILED_GENERATION   → Retry invoiceGen API call
FAILED_MONITORING   → Retry invoiceMonitor API call  
FAILED_DOWNLOAD     → Retry individual download
FAILED_UPLOAD       → Retry individual upload
```

#### **Real JSON Consolidated Structure**
**Complete Example from Production**:
```json
{
  "batch_info": {
    "batch_id": "daily_20250814_185139",
    "source_file": "mctech/sheets/Upload_11.08.2025 - MCTECH.xlsb",
    "processing_timestamp": "2025-08-14T18:55:21.474957+00:00",
    "total_ctes": 45,
    "total_minutas_excluded": 82
  },
  "orders": [
    {
      "po_number": "600710247",
      "status": "PENDING",
      "ctes": [
        {
          "NF/CTE": "44596",
          "valor_chave": "372.27",
          "empresa_origem": "EMBRATEL",
          "cnpj_fornecedor": "9351138000100",
          "competencia": "45778"
        }
      ],
      "cte_count": 3,
      "po_total_value": 963.85,
      "start_date": "45778",
      "end_date": "45778",
      "created_at": "2025-08-14T18:55:21.475548+00:00",
      "last_updated": "2025-08-14T18:55:21.475553+00:00"
    }
  ],
  "summary": {
    "total_orders": 22,
    "total_ctes": 45,
    "total_value": 86159.77
  }
}
```

### 🔍 **ANÁLISE DETALHADA DOS STEPS**

---

#### **🌅 STEP 1: `daily_initialization`**

**🎯 OBJETIVO DO STEP 1:**
Inicializar o ciclo diário combinando **novos emails** com **trabalho pendente** de execuções anteriores.

**🔧 OPERAÇÕES DETALHADAS:**

**📊 1.1 - Geração de Batch ID:**
```python
daily_batch_id = f"daily_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
# Exemplo: "daily_20250814_185139"
```

**📧 1.2 - Processamento de Emails Novos:**
```python
gmail_downloader = GmailDownloader()
downloaded_files = gmail_downloader.download_excel_attachments(max_emails=3)
```
- **Conecta** no Gmail via OAuth2
- **Busca** emails com label "MC Tech/Não Processado"  
- **Filtra** anexos Excel (.xlsx, .xlsb, .xls)
- **Baixa** até 3 arquivos Excel por execução
- **Move** emails processados para "MC Tech/Processado"

**🔄 1.3 - Conversão Excel → JSON (NOVA IMPLEMENTAÇÃO):**
```python
for file_info in downloaded_files:
    excel_path = file_info["path"]
    json_path = f"mctech/ctes/consolidated_ctes_{daily_batch_id}_{file_info['email_id'][:8]}.json"
    json_created_successfully = await process_excel_to_json(excel_path, json_path, daily_batch_id)
```

**Detalhes da conversão:**
- **Lê Excel** com pandas + pyxlsb engine
- **Filtra CTEs**: `df[df['TIPO'] == 'CTE']` (exclui MINUTAS)  
- **Agrupa por PO**: Purchase Orders individuais
- **Cria estrutura JSON**:
  ```json
  {
    "batch_info": { "batch_id": "...", "total_ctes": 45 },
    "orders": [
      {
        "po_number": "600710247",
        "status": "PENDING",
        "ctes": [...],
        "po_total_value": 963.85
      }
    ]
  }
  ```

**📁 1.4 - Scan de JSONs Existentes:**
```python
json_pattern = "mctech/ctes/consolidated_ctes_*.json"
existing_json_files = glob.glob(json_pattern)
```
- **Encontra** todos os JSONs de execuções anteriores
- **Lista** caminhos completos dos arquivos

**📤 1.5 - Output do Step:**
```python
{
  "daily_batch_id": "daily_20250814_185139",
  "new_emails_processed": 1,
  "new_json_files_created": [...],  # JSONs criados hoje
  "existing_json_files_found": [...], # JSONs de dias anteriores  
  "total_files_to_analyze": 5
}
```

---

#### **🔍 STEP 2: `json_analysis`**

**🎯 OBJETIVO DO STEP 2:**
Analisar **TODOS** os JSONs (novos + existentes) e extrair o status individual de cada PO para determinar próximas ações necessárias.

**🔧 OPERAÇÕES DETALHADAS:**

**🤖 2.1 - Agent de Análise:**
```python
data_extractor = create_data_extractor_agent()
response = data_extractor.run(analysis_context)
```
- **Agent** especializado em análise de dados estruturados
- **Contextualiza** a análise com instruções específicas

**📋 2.2 - Coleta de Arquivos:**
```python
all_json_files = init_results["existing_json_files_found"] + [
    file_info["json_created"] for file_info in init_results["new_json_files_created"]
]
```
- **Combina** JSONs existentes + JSONs recém-criados
- **Lista única** de todos os arquivos para análise

**🔍 2.3 - Análise de Cada JSON:**
```python
for json_file_path in all_json_files:
    with open(json_file_path, encoding="utf-8") as f:
        json_data = json.load(f)
    
    orders = json_data.get("orders", [])
    for order in orders:
        po_number = order.get("po_number")
        status = order.get("status", "PENDING")
```

**📊 2.4 - Categorização por Status:**
Cada PO é categorizado conforme seu status atual:
- **`PENDING`** → `pending_pos[]` → Pronto para invoiceGen API  
- **`WAITING_MONITORING`** → `monitoring_pos[]` → Pronto para invoiceMonitor API
- **`MONITORED`** → `download_pos[]` → Pronto para download API
- **`DOWNLOADED`** → `upload_pos[]` → Pronto para upload API
- **`UPLOADED`** → `completed_pos[]` → Completado (skip)
- **`FAILED_*`** → `failed_pos[]` → Precisa retry/correção

**📤 2.5 - Output do Step:**
```python
{
  "processing_categories": {
    "pending_pos": [{"po_number": "600710247", "json_file": "..."}],
    "monitoring_pos": [...],
    "download_pos": [...],
    "upload_pos": [...],
    "completed_pos": [...],
    "failed_pos": [...]
  },
  "analysis_summary": {
    "total_pos_found": 22,
    "pos_needing_processing": 15,
    "pos_completed": 7
  }
}
```

---

#### **🎯 STEP 3: `status_based_routing`**

**🎯 OBJETIVO DO STEP 3:**
Organizar POs em **filas de processamento** otimizadas por tipo de operação e prioridade, preparando a execução eficiente das APIs.

**🔧 OPERAÇÕES DETALHADAS:**

**🤖 3.1 - Agent de Orquestração:**
```python
api_orchestrator = create_api_orchestrator_agent()
response = api_orchestrator.run(routing_context)
```
- **Agent** especializado em coordenação de APIs
- **Planeja** sequência otimizada de execução

**📋 3.2 - Criação de Filas Priorizadas:**

**🥇 FILA 1 - invoice_generation_queue (Prioridade 1):**
```python
{
  "action": "invoiceGen",
  "pos": processing_categories["pending_pos"],
  "batch_processing": True,  # Múltiplos POs em 1 call
  "priority": 1
}
```
- **Input**: POs com status `PENDING`
- **Ação**: Gerar faturas via Browser API
- **Output**: Status → `WAITING_MONITORING`

**🥈 FILA 2 - invoice_monitoring_queue (Prioridade 2):**
```python
{
  "action": "invoiceMonitor", 
  "pos": processing_categories["monitoring_pos"],
  "batch_processing": True,  # Múltiplos POs em 1 call
  "priority": 2
}
```
- **Input**: POs com status `WAITING_MONITORING`
- **Ação**: Monitorar conclusão da geração
- **Output**: Status → `MONITORED`

**🥉 FILA 3 - invoice_download_queue (Prioridade 3):**
```python
{
  "action": "main-download-invoice",
  "pos": processing_categories["download_pos"], 
  "batch_processing": False,  # Individual por PO
  "priority": 3
}
```
- **Input**: POs com status `MONITORED`
- **Ação**: Download individual de cada fatura
- **Output**: Status → `DOWNLOADED`

**🏅 FILA 4 - invoice_upload_queue (Prioridade 4):**
```python
{
  "action": "invoiceUpload",
  "pos": processing_categories["upload_pos"],
  "batch_processing": False,  # Individual por PO  
  "priority": 4
}
```
- **Input**: POs com status `DOWNLOADED`
- **Ação**: Upload individual de cada fatura
- **Output**: Status → `UPLOADED`

**📊 3.3 - Plano de Execução:**
```python
"execution_plan": {
  "total_actions": 22,
  "batch_actions": 2,        # invoiceGen + invoiceMonitor
  "individual_actions": 15,  # downloads + uploads individuais
  "estimated_execution_time_minutes": 15
}
```

**📤 3.4 - Output do Step:**
Filas organizadas e prontas para execução sequencial por prioridade.

---

#### **⚙️ STEP 4: `individual_po_processing`**

**🎯 OBJETIVO DO STEP 4:**
Executar as **APIs do Browser** em sequência otimizada, processando cada fila conforme sua prioridade e modo (batch vs individual).

**🔧 OPERAÇÕES DETALHADAS:**

**🌐 4.1 - Cliente HTTP:**
```python
api_client = BrowserAPIClient()
# URL: http://localhost:8088 (configurável)
# Timeout: 900s, Max retries: 3
```

**🔄 4.2 - Processamento por Prioridade:**
```python
for queue_name, queue_data in processing_queues.items():
    action = queue_data["action"]
    pos = queue_data["pos"]  
    batch_processing = queue_data["batch_processing"]
```

**📦 4.3 - Modo BATCH (Filas 1-2):**
```python
if batch_processing:  # invoiceGen, invoiceMonitor
    po_numbers = [po_data["po_number"] for po_data in pos]
    payload = {
        "flow_name": action,
        "parameters": {
            "orders": po_numbers,  # ["600710247", "600710248", ...]
            "headless": True
        }
    }
    api_response = await api_client.execute_api_call(action, payload)
```

**Exemplo payload invoiceGen:**
```json
{
  "flow_name": "invoiceGen",
  "parameters": {
    "orders": ["600710247", "600710248", "600710249"],
    "headless": true
  }
}
```

**⚡ Atualização de Status em Batch:**
```python
if api_response["success"]:
    new_status = {
        "invoiceGen": "WAITING_MONITORING", 
        "invoiceMonitor": "MONITORED"
    }.get(action)
    
    for po_data in pos:
        status_updates[po_number] = {
            "old_status": "PENDING",
            "new_status": "WAITING_MONITORING",
            "json_file": "mctech/ctes/file.json"
        }
```

**🔄 4.4 - Modo INDIVIDUAL (Filas 3-4):**
```python
else:  # main-download-invoice, invoiceUpload
    for po_data in pos:
        po_details = load_po_from_json(po_data["json_file"])
        
        if action == "main-download-invoice":
            payload = api_client.build_invoice_download_payload(po_details)
        elif action == "invoiceUpload":  
            payload = api_client.build_invoice_upload_payload(po_details, file_path)
            
        api_response = await api_client.execute_api_call(action, payload)
```

**Exemplo payload download:**
```json
{
  "flow_name": "main-download-invoice",
  "parameters": {
    "po": "600710247",
    "ctes": ["44596", "44591", "44590"],
    "total_value": 963.85,
    "startDate": "45778",
    "endDate": "45778", 
    "headless": true
  }
}
```

**🔄 4.5 - Sistema de Retry com Exponential Backoff:**
```python
for attempt in range(self.max_retries):  # 3 tentativas
    try:
        result = await self._execute_real_api_call(flow_name, payload)
        return result
    except Exception as e:
        if attempt < self.max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait_time)
```

**📊 4.6 - Tracking de Execuções:**
```python
processing_results = {
    "api_executions": {
        "invoice_generation_queue": {
            "action": "invoiceGen",
            "pos_processed": ["600710247", "600710248"],
            "batch_mode": True,
            "success": True,
            "execution_time_ms": 15000
        }
    },
    "status_updates": {
        "600710247": {
            "old_status": "PENDING",
            "new_status": "WAITING_MONITORING",
            "json_file": "mctech/ctes/file.json"
        }
    },
    "execution_summary": {
        "successful_actions": 4,
        "failed_actions": 0,
        "pos_updated": 22
    }
}
```

---

#### **🏁 STEP 5: `daily_completion`**

**🎯 OBJETIVO DO STEP 5:**
Finalizar o ciclo diário atualizando os JSONs com novos status, gerando relatório completo e agendando próxima execução.

**🔧 OPERAÇÕES DETALHADAS:**

**🤖 5.1 - Agent de Gerenciamento:**
```python
file_manager = create_file_manager_agent()
response = file_manager.run(completion_context)
```
- **Agent** especializado em operações de arquivo
- **Coordena** atualizações de estado

**💾 5.2 - Atualização de JSONs:**
```python
files_updated = {}
for po_number, update_info in status_updates.items():
    json_file = update_info["json_file"]
    files_updated[json_file]["pos_updated"].append({
        "po_number": po_number,
        "status_change": f"PENDING → WAITING_MONITORING"
    })
```
- **Agrupa** atualizações por arquivo JSON
- **Preserva** estrutura original dos JSONs
- **Atualiza** apenas campos de status e timestamp

**📊 5.3 - Consolidação de Estatísticas:**
```python
completion_summary = {
    "daily_execution_summary": {
        "execution_date": "2025-08-14",
        "daily_batch_id": "daily_20250814_185139", 
        "total_execution_time_minutes": 15,
        "overall_status": "SUCCESS"
    },
    "processing_statistics": {
        "new_emails_processed": 1,
        "existing_files_analyzed": 3,
        "total_pos_found": 45,
        "pos_processed_today": 22,
        "pos_completed_today": 8,  # Reached UPLOADED
        "api_calls_successful": 12,
        "api_calls_failed": 0
    }
}
```

**⏰ 5.4 - Agendamento da Próxima Execução:**
```python
"next_execution_scheduled": {
    "next_run": "2025-08-15T08:00:00.000000+00:00",
    "frequency": "daily",
    "estimated_pos_for_next_run": 23  # POs ainda pendentes
}
```

**📋 5.5 - Rastreamento de Transições:**
```python
"status_transitions_applied": {
    "600710247": {
        "old_status": "PENDING",
        "new_status": "WAITING_MONITORING", 
        "json_file": "mctech/ctes/consolidated_ctes_daily_20250814_19899b68.json"
    },
    "600710248": {
        "old_status": "WAITING_MONITORING",
        "new_status": "MONITORED",
        "json_file": "mctech/ctes/consolidated_ctes_daily_20250813_ab123cd4.json" 
    }
}
```

### 🎯 **RESUMO EXECUTIVO DO WORKFLOW**

Este workflow é uma **obra-prima de automação robusta e inteligente!** 🚀 Combina processamento em tempo real, persistência de estado, orquestração de APIs e recuperação automática em um sistema altamente eficiente para processamento de CTEs.


Co-Authored-By: Automagik Genie <genie@namastex.ai>
