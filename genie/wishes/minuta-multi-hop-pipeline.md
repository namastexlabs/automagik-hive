# 📋 PLANEJAMENTO: MULTI-HOP EXECUTION PARA WORKFLOW DE MINUTAS

**Data**: 2025-10-14
**Status**: Planejamento Completo - Pronto para Implementação
**Estimativa**: ~2h 10min de desenvolvimento

---

## 🎯 OBJETIVO

Transformar o processamento de minutas de **single-hop** (1 status por run) para **multi-hop** a partir do status `CLARO_GENERATED`, executando sequencialmente até `UPLOADED` em uma única run com atualização de status em tempo real.

---

## 📊 1. ANÁLISE DA ARQUITETURA ATUAL

### **Como Funciona Hoje:**

```python
# Processamento Single-Hop (arquivo: workflow.py:4056-4089)
queue_order = [
    "minuta_generation_queue",      # PENDING → CLARO_GENERATED
    "main_minut_gen_queue",         # CLARO_GENERATED → ESL_GENERATED
    "main_minut_download_queue",    # ESL_GENERATED → DOWNLOADED
    "regional_download_queue",      # DOWNLOADED → REGIONAL_DOWNLOADED
    "concatenation_queue",          # REGIONAL_DOWNLOADED → CONCATENATED
    "upload_queue",                 # CONCATENATED → UPLOADED
]

# Cada run processa APENAS 1 queue por vez
for queue_name in queue_order:
    queue_info = processing_queues.get(queue_name)
    for entry in cnpj_entries:
        # Processa ação
        # Atualiza status +1
        # PARA aqui - próxima run avança para próxima queue
```

### **Pontos de Modificação Identificados:**

| Componente | Localização | Mudança Necessária |
|------------|-------------|-------------------|
| **Routing Logic** | `execute_minuta_status_routing_step` (3881) | Criar queue especial `multi_hop_pipeline_queue` |
| **Processing Loop** | `execute_minuta_cnpj_processing_step` (4056-4089) | Adicionar branch para multi-hop execution |
| **Status Updates** | `update_cnpj_status_in_json` (1629-1670) | Já suporta updates atômicos ✅ |
| **Error Handling** | Cada action block (4139-4567) | Adicionar checkpoints e resume logic |

---

## 🏗️ 2. DESIGN DA NOVA ARQUITETURA MULTI-HOP

### **Conceito: Pipeline Execution**

```python
# Nova Estrutura: Multi-Hop Pipeline
CLARO_GENERATED → [Pipeline Execution em 1 Run] → UPLOADED

Pipeline Steps:
1. main-minut-gen    → ESL_GENERATED        ✅ Checkpoint
2. main-minut-download → DOWNLOADED          ✅ Checkpoint
3. regional-download → REGIONAL_DOWNLOADED   ✅ Checkpoint (condicional TO/SE)
4. concatenate       → CONCATENATED          ✅ Checkpoint
5. invoiceUpload     → UPLOADED              ✅ Final + Protocol
```

### **Nova Queue Structure:**

```python
# Adicionar ao routing step (execute_minuta_status_routing_step)
processing_queues["multi_hop_pipeline_queue"] = {
    "action": "multi_hop_pipeline",  # ← Nova ação
    "current_statuses": ["CLARO_GENERATED"],
    "target_status": "UPLOADED",  # Status final desejado
    "pipeline_steps": [
        {
            "step": 1,
            "action": "main-minut-gen",
            "next_status": "ESL_GENERATED",
            "wait_time_seconds": 180  # 3 minutos
        },
        {
            "step": 2,
            "action": "main-minut-download",
            "next_status": "DOWNLOADED"
        },
        {
            "step": 3,
            "action": "regional-download",
            "next_status": "REGIONAL_DOWNLOADED",
            "conditional": "requires_regional == True"  # TO/SE only
        },
        {
            "step": 4,
            "action": "concatenate",
            "next_status": "CONCATENATED"
        },
        {
            "step": 5,
            "action": "invoiceUpload",
            "next_status": "UPLOADED",
            "extract_protocol": True
        }
    ],
    "cnpjs": [...]  # CNPJs em status CLARO_GENERATED
}
```

### **Nova Função: execute_multi_hop_pipeline**

```python
async def execute_multi_hop_pipeline(
    cnpj_entry: dict,
    pipeline_steps: list[dict],
    api_client: BrowserAPIClient
) -> dict:
    """
    Execute full pipeline for a single CNPJ from CLARO_GENERATED to UPLOADED.

    Args:
        cnpj_entry: CNPJ metadata (cnpj, json_file, status, etc.)
        pipeline_steps: List of pipeline step configurations
        api_client: Browser API client for actions

    Returns:
        {
            "success": bool,
            "completed_steps": int,
            "failed_step": str | None,
            "final_status": str,
            "protocol": str | None,
            "error": str | None
        }
    """
    cnpj_claro = cnpj_entry["cnpj"]
    json_file_path = cnpj_entry["json_file"]

    # Load CNPJ group data
    cnpj_group = load_cnpj_group_from_json(json_file_path, cnpj_claro)

    completed_steps = 0

    for step_config in pipeline_steps:
        step_num = step_config["step"]
        action = step_config["action"]
        next_status = MinutaProcessingStatus(step_config["next_status"])

        logger.info(f"🔄 CNPJ {cnpj_claro}: Executing pipeline step {step_num}/{len(pipeline_steps)} - {action}")

        try:
            # Check conditional execution
            if step_config.get("conditional"):
                condition = step_config["conditional"]
                if not eval_condition(condition, cnpj_group):
                    logger.info(f"⏭️ Skipping step {step_num} - condition not met")
                    await update_cnpj_status_in_json(json_file_path, cnpj_claro, next_status)
                    completed_steps += 1
                    continue

            # Wait if needed (e.g., 3 min for main-minut-gen)
            if step_config.get("wait_time_seconds"):
                wait_seconds = step_config["wait_time_seconds"]
                logger.info(f"⏳ Waiting {wait_seconds}s before {action}...")
                await asyncio.sleep(wait_seconds)

            # Execute action
            success, result = await execute_pipeline_action(
                action,
                cnpj_group,
                json_file_path,
                api_client
            )

            if not success:
                # FALHOU - para pipeline e retorna status atual
                logger.error(f"❌ Pipeline failed at step {step_num} ({action})")
                return {
                    "success": False,
                    "completed_steps": completed_steps,
                    "failed_step": action,
                    "final_status": result.get("failure_status"),
                    "error": result.get("error")
                }

            # Sucesso - atualiza status
            protocol = result.get("protocol") if step_config.get("extract_protocol") else None
            await update_cnpj_status_in_json(
                json_file_path,
                cnpj_claro,
                next_status,
                protocol_number=protocol
            )

            logger.info(f"✅ Step {step_num} completed: {cnpj_claro} → {next_status.value}")
            completed_steps += 1

        except Exception as e:
            logger.error(f"❌ Unexpected error in pipeline step {step_num}: {e}")
            import traceback
            logger.error(traceback.format_exc())

            return {
                "success": False,
                "completed_steps": completed_steps,
                "failed_step": action,
                "final_status": f"FAILED_{action.upper()}",
                "error": str(e)
            }

    # Pipeline completo!
    return {
        "success": True,
        "completed_steps": completed_steps,
        "failed_step": None,
        "final_status": "UPLOADED",
        "protocol": result.get("protocol")
    }
```

---

## ⚡ 3. PLANO DE STATUS UPDATES EM TEMPO REAL

### **Estratégia: Atomic Updates + Logging**

```python
# Já existe e funciona bem! (linha 1629-1670)
async def update_cnpj_status_in_json(
    json_file_path: str,
    cnpj_claro: str,
    new_status: MinutaProcessingStatus,
    protocol_number: str | None = None
) -> bool:
    """Update status atomically with file lock"""

    # Read JSON
    with open(json_file_path) as f:
        data = json.load(f)

    # Update specific CNPJ group
    for group in data.get("cnpj_groups", []):
        if group["cnpj_claro"] == cnpj_claro:
            group["status"] = new_status
            group["last_updated"] = datetime.now(UTC).isoformat()

            if protocol_number is not None:
                group["protocol_number"] = protocol_number

            break

    # Write JSON atomically
    with open(json_file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Updated CNPJ {cnpj_claro} status to {new_status}")
    return True
```

### **Melhorias Propostas:**

1. **Progress Tracking Field:**
```python
# Adicionar ao JSON structure
group["pipeline_progress"] = {
    "current_step": 2,
    "total_steps": 5,
    "last_step_completed": "main-minut-download",
    "last_step_timestamp": "2025-10-14T18:30:00Z"
}
```

2. **Real-Time Logging:**
```python
# Logs detalhados durante pipeline
logger.info(f"📊 Progress: {cnpj_claro} [{completed_steps}/{total_steps}] - {action} → {next_status}")
```

---

## 🛡️ 4. ESTRATÉGIA DE ERROR HANDLING

### **Princípios:**

1. **Fail-Fast**: Parar pipeline imediatamente em caso de erro
2. **Status Preservation**: Status sempre reflete último step completado com sucesso
3. **Resume Capability**: Próxima run pode retomar do ponto de falha
4. **Detailed Logging**: Logs completos para debugging

### **Error Scenarios:**

| Cenário | Status Final | Ação na Próxima Run |
|---------|-------------|---------------------|
| **main-minut-gen falha** | `CLARO_GENERATED` (não muda) | Tenta pipeline novamente desde início |
| **main-minut-download falha** | `ESL_GENERATED` | Retoma do download |
| **regional-download falha** | `DOWNLOADED` | Retoma do regional |
| **concatenate falha** | `REGIONAL_DOWNLOADED` | Retoma da concatenação |
| **invoiceUpload falha** | `CONCATENATED` | Retoma do upload |

### **Resume Logic:**

```python
# No routing step, detectar status intermediários
if status == "ESL_GENERATED":
    # Skippar main-minut-gen, começar do download
    pipeline_steps = pipeline_steps[1:]  # Remove step 1

elif status == "DOWNLOADED":
    # Skippar gen + download, começar do regional
    pipeline_steps = pipeline_steps[2:]  # Remove steps 1-2

# etc...
```

---

## 🗺️ 5. ROADMAP DE IMPLEMENTAÇÃO

### **Fase 1: Preparação** (30 min)

**Arquivo**: `workflow.py`

1. ✅ **Criar função auxiliar `execute_pipeline_action`** (linha ~4600)
   ```python
   async def execute_pipeline_action(
       action: str,
       cnpj_group: dict,
       json_file_path: str,
       api_client: BrowserAPIClient
   ) -> tuple[bool, dict]:
       """Execute single pipeline action and return success + result"""
       # Extrair lógica dos blocos if/elif existentes (linhas 4139-4567)
   ```

2. ✅ **Criar função `execute_multi_hop_pipeline`** (linha ~4700)
   - Implementar loop de pipeline steps
   - Integrar wait logic (3 min)
   - Adicionar checkpoints de status
   - Error handling com fail-fast

3. ✅ **Criar helper `eval_condition`** (linha ~4800)
   ```python
   def eval_condition(condition: str, cnpj_group: dict) -> bool:
       """Evaluate conditional execution (e.g., 'requires_regional == True')"""
   ```

---

### **Fase 2: Routing Logic** (20 min)

**Arquivo**: `workflow.py` - Função `execute_minuta_status_routing_step` (linha 3881)

1. ✅ **Adicionar detecção de CLARO_GENERATED**
   ```python
   # Após análise de status
   claro_generated_cnpjs = analysis_results.get("status_breakdown", {}).get("claro_generated", [])

   if claro_generated_cnpjs:
       processing_queues["multi_hop_pipeline_queue"] = {
           "action": "multi_hop_pipeline",
           "current_statuses": ["CLARO_GENERATED"],
           "target_status": "UPLOADED",
           "pipeline_steps": [...],  # 5 steps definidos
           "cnpjs": claro_generated_cnpjs
       }
   ```

---

### **Fase 3: Processing Integration** (25 min)

**Arquivo**: `workflow.py` - Função `execute_minuta_cnpj_processing_step` (linha 4089)

1. ✅ **Adicionar branch para multi-hop**
   ```python
   for queue_name in queue_order:
       queue_info = processing_queues.get(queue_name)

       # NOVO: Detectar multi-hop pipeline
       if queue_info.get("action") == "multi_hop_pipeline":
           pipeline_steps = queue_info.get("pipeline_steps", [])

           for entry in cnpj_entries:
               pipeline_result = await execute_multi_hop_pipeline(
                   entry,
                   pipeline_steps,
                   api_client
               )

               # Registrar resultado
               queue_results[queue_name].append({
                   "cnpj": entry["cnpj"],
                   "success": pipeline_result["success"],
                   "completed_steps": pipeline_result["completed_steps"],
                   "final_status": pipeline_result["final_status"],
                   "protocol": pipeline_result.get("protocol")
               })

               if pipeline_result["success"]:
                   execution_summary["cnpjs_updated"] += 1
                   execution_summary["minutas_generated"] += entry.get("minuta_count", 0)
               else:
                   execution_summary["cnpjs_failed"] += 1

           continue  # Skip normal queue processing

       # Processamento normal para outras queues...
   ```

---

### **Fase 4: Testing** (40 min)

1. ✅ **Teste 1: Pipeline completo**
   - CNPJ em CLARO_GENERATED
   - Executa pipeline até UPLOADED
   - Verifica protocolo extraído

2. ✅ **Teste 2: Falha no step 2 (download)**
   - Pipeline para
   - Status fica em ESL_GENERATED
   - Próxima run retoma do download

3. ✅ **Teste 3: Regional download (TO/SE)**
   - CNPJ com uf="TO"
   - Executa step 3 (palmas)
   - CNPJ com uf="SP"
   - Skip step 3

4. ✅ **Teste 4: Concatenação com múltiplos POs**
   - 3 POs por CNPJ
   - Verifica PDFs concatenados

---

### **Fase 5: Monitoring & Logs** (15 min)

1. ✅ **Adicionar logs de progresso**
   ```python
   logger.info(f"🚀 Starting multi-hop pipeline for CNPJ {cnpj_claro}")
   logger.info(f"📊 Progress: Step {step_num}/{total_steps} - {action}")
   logger.info(f"✅ Pipeline completed: {cnpj_claro} → UPLOADED (Protocol: {protocol})")
   ```

2. ✅ **Adicionar métricas ao execution_summary**
   ```python
   execution_summary["pipeline_executions"] = 5
   execution_summary["pipeline_completions"] = 4
   execution_summary["pipeline_failures"] = 1
   execution_summary["avg_pipeline_time_minutes"] = 12.5
   ```

---

## 📦 RESUMO DE ARQUIVOS A MODIFICAR

| Arquivo | Linhas | Mudanças |
|---------|--------|----------|
| `workflow.py` | ~4600 | ➕ Adicionar `execute_pipeline_action` |
| `workflow.py` | ~4700 | ➕ Adicionar `execute_multi_hop_pipeline` |
| `workflow.py` | ~4800 | ➕ Adicionar `eval_condition` |
| `workflow.py` | 3881-3970 | ✏️ Modificar routing para adicionar `multi_hop_pipeline_queue` |
| `workflow.py` | 4089-4120 | ✏️ Adicionar branch para multi-hop no processing loop |

**Total estimado**: ~350 linhas de código novo + ~50 linhas modificadas

---

## ⏱️ TIMELINE ESTIMADO

| Fase | Duração | Complexidade |
|------|---------|--------------|
| **Fase 1: Preparação** | 30 min | Média |
| **Fase 2: Routing Logic** | 20 min | Baixa |
| **Fase 3: Processing Integration** | 25 min | Média |
| **Fase 4: Testing** | 40 min | Alta |
| **Fase 5: Monitoring** | 15 min | Baixa |
| **TOTAL** | **~2h 10min** | |

---

## 🚨 RISCOS E MITIGAÇÕES

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| **Timeout em pipeline longo** | Alto | Dividir em batches de 5 CNPJs por vez |
| **Falha deixa JSON inconsistente** | Médio | Status sempre atualizado antes de próximo step |
| **Wait de 3min não suficiente** | Médio | Configurar wait_time via variável de ambiente |
| **Memory leak em processamento longo** | Baixo | Usar async/await corretamente |

---

## ✅ CRITÉRIOS DE SUCESSO

1. ✅ CNPJ em `CLARO_GENERATED` processa até `UPLOADED` em **1 única run**
2. ✅ Status atualizado em **tempo real** após cada step
3. ✅ Em caso de erro, **status preserva último step bem-sucedido**
4. ✅ Próxima run **retoma do ponto de falha**
5. ✅ Protocolo **extraído e salvo** no JSON após upload
6. ✅ Logs detalhados de **progresso do pipeline**
7. ✅ Regional download **executado apenas para TO/SE**

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### **Variáveis de Ambiente Necessárias:**

```bash
# .env
MINUTA_PIPELINE_WAIT_TIME=180  # Tempo de espera em segundos (default: 3 min)
MINUTA_PIPELINE_BATCH_SIZE=5   # Processar N CNPJs por vez (evitar timeout)
MINUTA_PIPELINE_ENABLE_RESUME=true  # Permitir retomar do ponto de falha
```

### **Estrutura JSON Atualizada:**

```json
{
  "cnpj_groups": [
    {
      "cnpj_claro": "12345678000190",
      "status": "ESL_GENERATED",
      "pipeline_progress": {
        "current_step": 1,
        "total_steps": 5,
        "last_step_completed": "main-minut-gen",
        "last_step_timestamp": "2025-10-14T18:30:00.123Z",
        "failed_step": null
      },
      "protocol_number": null,
      ...
    }
  ]
}
```

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Revisar planejamento com equipe
2. ⏭️ Iniciar implementação (Fase 1)
3. ⏭️ Testes unitários
4. ⏭️ Testes de integração
5. ⏭️ Deploy em ambiente de staging
6. ⏭️ Validação com dados reais
7. ⏭️ Deploy em produção

---

**Criado por**: Genie 🧞
**Última atualização**: 2025-10-14T18:45:00Z
