# 📋 PLANEJAMENTO: CHECK_ORDER_STATUS para Workflow de Minutas

**Data**: 2025-10-18
**Objetivo**: Adicionar validação de liberação entre PENDING e CLARO_GENERATED
**Estimativa**: ~1h 30min

---

## 🎯 FLUXO DESEJADO

```
PENDING
   ↓ [minutGen API call]
CHECK_ORDER_STATUS
   ↓ [claroCheck API call para cada PO]
   ├─ Se LIBERADO para emissão → CLARO_GENERATED (multi-hop pipeline)
   └─ Se NÃO LIBERADO → CHECK_ORDER_STATUS (permanece, retry próxima run)
```

---

## 🔍 LÓGICA DE LIBERAÇÃO (claroCheck)

### **Resposta do Browser API:**
```json
{
  "raw_response": {
    "output": {
      "status": "Autorizada Emissão Nota Fiscal"  // ou outras opções
    }
  }
}
```

### **Mapeamento de Status:**

| Status Retornado | Significa | Próximo Status | Ação |
|-----------------|-----------|----------------|------|
| `"Autorizada Emissão Nota Fiscal"` | ✅ LIBERADO | `CLARO_GENERATED` | Avança para multi-hop |
| `"Agendamento Pendente"` | ✅ LIBERADO | `CLARO_GENERATED` | Avança para multi-hop |
| `"Aguardando Liberação"` | ❌ NÃO LIBERADO | `CHECK_ORDER_STATUS` | Permanece, retry amanhã |
| Outros/Vazio | ❌ ERRO | `FAILED_GENERATION` | Intervenção manual |

**Regra Simples**:
- ✅ **Liberado** = Status contém "Autorizada" ou "Agendamento Pendente"
- ❌ **Não Liberado** = "Aguardando Liberação"

---

## 🏗️ IMPLEMENTAÇÃO

### **1. Atualizar Enum** (workflow.py:77)
```python
class MinutaProcessingStatus(str, Enum):
    PENDING = "PENDING"
    CHECK_ORDER_STATUS = "CHECK_ORDER_STATUS"  # ← NOVO
    CLARO_GENERATED = "CLARO_GENERATED"
    # ... resto
```

### **2. Adicionar Parser MINUTA-Specific** (BrowserAPIClient)
```python
def parse_claro_check_response_for_minuta(self, api_response: dict) -> tuple[bool, str, str]:
    """Parse claroCheck: retorna CLARO_GENERATED APENAS se liberado"""
    output_status = api_response.get("raw_response", {}).get("output", {}).get("status", "")

    # LIBERADO → CLARO_GENERATED
    if output_status in ["Autorizada Emissão Nota Fiscal", "Agendamento Pendente"]:
        return True, "CLARO_GENERATED", "Order approved - ready for pipeline"

    # NÃO LIBERADO → CHECK_ORDER_STATUS (permanece)
    if output_status == "Aguardando Liberação":
        return True, "CHECK_ORDER_STATUS", "Order not released yet - retry next run"

    # ERRO
    return False, "FAILED_GENERATION", f"Unknown status: {output_status}"
```

### **3. Modificar minutGen** (transição)
```python
async def execute_minutgen_only(entry, api_client):
    # ... executa minutGen ...

    if success:
        # ANTES: → CLARO_GENERATED
        # AGORA: → CHECK_ORDER_STATUS
        next_status = "CHECK_ORDER_STATUS"
        await update_cnpj_status_in_json(..., new_status=next_status)
```

### **4. Adicionar Detecção** (json_analysis)
```python
# workflow.py:3859
processing_categories = {
    "pending_cnpjs": [],
    "check_order_cnpjs": [],  # ← NOVO
    "claro_generated_cnpjs": [],
    # ...
}

for group in cnpj_groups:
    if status == "CHECK_ORDER_STATUS":
        processing_categories["check_order_cnpjs"].append({
            "cnpj": group["cnpj_claro"],
            "json_file": json_file_path,
            "pending_pos": extract_pending_pos(group)
        })
```

### **5. Criar Queue** (status_routing)
```python
# workflow.py:4065
if check_order_cnpjs:
    processing_queues["order_validation_queue"] = {
        "action": "claroCheck",
        "cnpjs": check_order_cnpjs
    }
```

### **6. Implementar Validação** (NOVA FUNÇÃO)
```python
async def execute_claro_check_for_minuta(entry, api_client):
    """
    Valida cada PO via claroCheck.

    - Se TODOS liberados → CLARO_GENERATED
    - Se ALGUM não liberado → CHECK_ORDER_STATUS (permanece)
    """
    cnpj = entry["cnpj"]
    json_file = entry["json_file"]
    pending_pos = entry["pending_pos"]

    pos_approved = []
    pos_still_pending = []

    # Valida cada PO individualmente
    for po_number in pending_pos:
        payload = api_client.build_claro_check_payload(po_number)
        api_response = await api_client.execute_api_call("claroCheck", payload)

        if api_response["success"]:
            # Parse response
            success, new_status, msg = api_client.parse_claro_check_response_for_minuta(
                api_response.get("api_result", {})
            )

            if new_status == "CLARO_GENERATED":
                pos_approved.append(po_number)
                logger.info(f"✅ PO {po_number} LIBERADO")
            elif new_status == "CHECK_ORDER_STATUS":
                pos_still_pending.append(po_number)
                logger.info(f"⏳ PO {po_number} NÃO LIBERADO")

    # Decisão CNPJ-level
    if pos_approved and not pos_still_pending:
        # TODOS liberados → CLARO_GENERATED
        final_status = "CLARO_GENERATED"
        logger.info(f"🎉 CNPJ {cnpj}: TODOS POs liberados → CLARO_GENERATED")
    else:
        # ALGUM não liberado → permanece CHECK_ORDER_STATUS
        final_status = "CHECK_ORDER_STATUS"
        logger.info(f"⏳ CNPJ {cnpj}: Ainda aguardando liberação → CHECK_ORDER_STATUS")

    # Atualiza JSON
    await update_cnpj_status_in_json(
        json_file_path=json_file,
        cnpj_claro=cnpj,
        new_status=final_status,
        pending_pos=pos_still_pending if pos_still_pending else pos_approved
    )

    return {"success": True, "status": final_status}
```

### **7. Integrar Branch** (cnpj_processing)
```python
# workflow.py:4158

# Branch 1: minutGen (PENDING → CHECK_ORDER_STATUS)
if "minuta_generation_queue" in processing_queues:
    for entry in cnpjs:
        await execute_minutgen_only(entry, api_client)

# Branch 2: claroCheck (CHECK_ORDER_STATUS → CLARO_GENERATED ou permanece) ← NOVO
if "order_validation_queue" in processing_queues:
    for entry in cnpjs:
        result = await execute_claro_check_for_minuta(entry, api_client)

        if result["status"] == "CLARO_GENERATED":
            logger.info(f"✅ {entry['cnpj']} aprovado → multi-hop ready")
        else:
            logger.info(f"⏳ {entry['cnpj']} ainda pendente → retry next run")

# Branch 3: Multi-hop (CLARO_GENERATED → UPLOADED)
if "multi_hop_pipeline_queue" in processing_queues:
    # ... existing logic ...
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] 1. Adicionar `CHECK_ORDER_STATUS` ao enum `MinutaProcessingStatus`
- [ ] 2. Criar método `parse_claro_check_response_for_minuta` no `BrowserAPIClient`
- [ ] 3. Modificar `execute_minutgen_only`: next_status = `CHECK_ORDER_STATUS`
- [ ] 4. Adicionar `check_order_cnpjs` categoria no `minuta_json_analysis`
- [ ] 5. Criar `order_validation_queue` no `minuta_status_routing`
- [ ] 6. Implementar função `execute_claro_check_for_minuta`
- [ ] 7. Adicionar Branch 2 no `minuta_cnpj_processing`
- [ ] 8. Testar fluxo completo

---

## 🧪 CENÁRIOS DE TESTE

### **Cenário 1: Liberação Imediata**
```
PENDING → minutGen → CHECK_ORDER_STATUS
Next run: claroCheck → "Autorizada Emissão" → CLARO_GENERATED → multi-hop
```

### **Cenário 2: Aguardando Liberação**
```
PENDING → minutGen → CHECK_ORDER_STATUS
Run 1: claroCheck → "Aguardando Liberação" → CHECK_ORDER_STATUS (permanece)
Run 2: claroCheck → "Aguardando Liberação" → CHECK_ORDER_STATUS (permanece)
Run 3: claroCheck → "Autorizada Emissão" → CLARO_GENERATED → multi-hop
```

### **Cenário 3: Liberação Parcial**
```
CNPJ com 3 POs: PO1, PO2, PO3
- PO1: "Autorizada" → aprovado
- PO2: "Aguardando" → pendente
- PO3: "Autorizada" → aprovado

Resultado: CNPJ permanece CHECK_ORDER_STATUS (porque PO2 ainda pendente)
```

---

## 🎯 DEFINIÇÃO DE SUCESSO

✅ **Implementação completa quando:**

1. minutGen transiciona para `CHECK_ORDER_STATUS` (não mais `CLARO_GENERATED`)
2. CNPJs em `CHECK_ORDER_STATUS` são validados via claroCheck
3. **APENAS** quando claroCheck retorna liberação → `CLARO_GENERATED`
4. Quando claroCheck retorna "Aguardando" → permanece `CHECK_ORDER_STATUS`
5. Multi-hop pipeline só executa para CNPJs em `CLARO_GENERATED`
6. Retry automático na próxima run para CNPJs ainda em `CHECK_ORDER_STATUS`

---

**Próximo Passo**: Iniciar implementação seguindo checklist
