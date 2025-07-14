# Task Card: Build Typification Workflow

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### NEW: Conversation Typification Workflow (Based on CSV Hierarchy)

**CRITICAL: Typification must follow the exact 5-level hierarchy from knowledge_rag.csv**

```yaml
# workflows/conversation_typification/config.yaml
workflow:
  id: "conversation_typification"
  name: "Tipificação Automática de Atendimento"
  description: "Análise hierárquica da conversa seguindo padrão PagBank"
  
storage:
  type: "postgres"
  table_name: "conversation_typification_workflows"
  url: "${DATABASE_URL}"
  mode: "workflow"
  auto_upgrade_schema: true

agents:
  # Step 1: Identify Business Unit
  business_unit_classifier:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 200
    tools:
      - conversation_analyzer
    instructions: |
      Analise a conversa e identifique a Unidade de Negócio.
      Opções válidas APENAS (exatamente como no CSV):
      - "Adquirência Web"
      - "Adquirência Web / Adquirência Presencial"
      - "Emissão"
      - "PagBank"
      
  # Step 2: Identify Product (based on Business Unit)
  product_classifier:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 200
    instructions: |
      Baseado na Unidade de Negócio selecionada, identifique o Produto.
      Use APENAS produtos válidos para a unidade escolhida.
      
  # Step 3: Identify Motive (based on Product)
  motive_classifier:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 300
    instructions: |
      Baseado no Produto selecionado, identifique o Motivo.
      Use APENAS motivos válidos para o produto escolhido.
      
  # Step 4: Identify Submotive (based on Motive)
  submotive_classifier:
    model:
      provider: "anthropic"
      id: "claude-sonnet-4-20250514"
      max_tokens: 500
    instructions: |
      Baseado no Motivo selecionado, identifique o Submotivo.
      Use APENAS submotivos válidos para o motivo escolhido.
      
  # Step 5: Generate Ticket
  ticket_generator:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 300
    tools:
      - ticket_system_integration
    instructions: |
      Gere ticket com a tipificação completa.
      Conclusão é sempre "Orientação".

flow:
  steps:
    - business_unit_classification
    - product_classification
    - motive_classification
    - submotive_classification
    - ticket_generation
  sequential: true  # Must be sequential for hierarchy
  
settings:
  timeout: 180  # 3 minutes for all steps
  structured_outputs: true
  enable_cache: false  # Always fresh analysis
```

```python
# workflows/conversation_typification/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum

# EXACT enums from knowledge_rag.csv hierarchy
class UnidadeNegocio(str, Enum):
    """Business Unit - Level 1 of hierarchy"""
    ADQUIRENCIA_WEB = "Adquirência Web"
    ADQUIRENCIA_WEB_PRESENCIAL = "Adquirência Web / Adquirência Presencial"
    EMISSAO = "Emissão"
    PAGBANK = "PagBank"

# Product mappings per Business Unit
PRODUCTS_BY_UNIT = {
    "Adquirência Web": ["Antecipação de Vendas"],
    "Adquirência Web / Adquirência Presencial": ["Antecipação de Vendas"],
    "Emissão": [
        "Cartão Múltiplo PagBank",
        "Cartão Múltiplo PagBank (débito internacional)",
        "Cartão PagBank Mastercard",
        "Cartão PagBank Visa",
        "Cartão Pré-Pago",
        "Cartão Pré-Pago Mastercard",
        "Cartão Pré-Pago Visa",
        "Cartão da Conta (débito)",
        "Cartão da Conta PagBank (débito Visa)",
        "Cartão da Conta Visa (débito)",
        "Cartão de Crédito PagBank"
    ],
    "PagBank": [
        "Aplicativo PagBank",
        "Conta PagBank",
        "Folha de Pagamento",
        "Pix",
        "Pix (Contatos Seguros)",
        "Portabilidade de Salário",
        "Recarga de Celular",
        "TED"
    ]
}

# Motives mapped to products (would need complete mapping from CSV)
MOTIVES_BY_PRODUCT = {
    "Antecipação de Vendas": [
        "Dúvidas sobre a Antecipação de Vendas",
        "Elegibilidade da Antecipação de Vendas",
        # ... other motives
    ],
    "Folha de Pagamento": [
        "Atualização da folha",
        "Como gerar arquivo CNAB",
        "Como liberar a folha dos meus colaboradores",
        # ... 14 total motives for payroll
    ],
    # ... complete mapping needed
}

class HierarchicalTypification(BaseModel):
    """Strict hierarchical typification following CSV structure"""
    
    # Level 1: Business Unit
    unidade_negocio: UnidadeNegocio = Field(..., description="Unidade de negócio")
    
    # Level 2: Product (validated based on business unit)
    produto: str = Field(..., description="Produto relacionado")
    
    # Level 3: Motive (validated based on product)
    motivo: str = Field(..., description="Motivo do atendimento")
    
    # Level 4: Submotive (validated based on motive)
    submotivo: str = Field(..., description="Submotivo específico")
    
    # Level 5: Conclusion (always "Orientação")
    conclusao: Literal["Orientação"] = Field(default="Orientação", description="Tipo de conclusão")
    
    @validator('produto')
    def validate_produto(cls, v, values):
        """Ensure product is valid for the selected business unit"""
        if 'unidade_negocio' in values:
            unit = values['unidade_negocio'].value
            valid_products = PRODUCTS_BY_UNIT.get(unit, [])
            if v not in valid_products:
                raise ValueError(f"Produto '{v}' inválido para unidade '{unit}'")
        return v
    
    @validator('motivo')
    def validate_motivo(cls, v, values):
        """Ensure motive is valid for the selected product"""
        if 'produto' in values:
            product = values['produto']
            valid_motives = MOTIVES_BY_PRODUCT.get(product, [])
            if valid_motives and v not in valid_motives:
                raise ValueError(f"Motivo '{v}' inválido para produto '{product}'")
        return v

class ConversationTypification(BaseModel):
    """Complete conversation typification with hierarchy"""
    
    # Session identification
    session_id: str = Field(..., description="ID da sessão do atendimento")
    customer_id: Optional[str] = Field(None, description="ID do cliente")
    ticket_id: Optional[str] = Field(None, description="ID do ticket gerado")
    
    # Hierarchical classification (REQUIRED)
    typification: HierarchicalTypification = Field(..., description="Tipificação hierárquica")
    
    # Conversation analysis
    conversation_summary: str = Field(..., description="Resumo da conversa")
    resolution_provided: str = Field(..., description="Resolução fornecida")
    
    # Metrics
    conversation_turns: int = Field(..., description="Número de interações")
    resolution_time_minutes: Optional[float] = Field(None, description="Tempo de resolução")
    escalated_to_human: bool = Field(False, description="Se foi escalado para humano")

class TicketCreationResult(BaseModel):
    """Resultado da criação/atualização de ticket"""
    
    ticket_id: str = Field(..., description="ID do ticket")
    action: str = Field(..., description="created ou updated")
    status: str = Field(..., description="Status do ticket")
    assigned_team: Optional[str] = Field(None, description="Equipe atribuída")
```

```python
# workflows/conversation_typification/workflow.py
from typing import Iterator, Union
from agno.workflow import Workflow, WorkflowCompletedEvent
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from .models import ConversationTypification, TicketCreationResult

class ConversationTypificationWorkflow(Workflow):
    """Sequential workflow for hierarchical typification"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load complete hierarchy from CSV on initialization
        self.hierarchy = self._load_hierarchy_from_csv()
    
    def _load_hierarchy_from_csv(self):
        """Load complete typification hierarchy from knowledge_rag.csv"""
        import pandas as pd
        from collections import defaultdict
        
        # Parse CSV and extract hierarchy
        df = pd.read_csv("context/knowledge/knowledge_rag.csv")
        hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for _, row in df.iterrows():
            typification = row['typification']
            lines = typification.strip().split('\n')
            
            unit = lines[0].split(': ')[1]
            product = lines[1].split(': ')[1]
            motive = lines[2].split(': ')[1]
            submotive = lines[3].split(': ')[1]
            
            hierarchy[unit][product][motive].append(submotive)
        
        return dict(hierarchy)
    
    # Step 1: Business Unit Classifier
    business_unit_classifier: Agent = Agent(
        name="Business Unit Classifier",
        model=Claude(id="claude-haiku-4-20250514"),
        instructions="""
        Analise a conversa e selecione a Unidade de Negócio apropriada.
        
        Opções válidas (exatamente como aparece no CSV):
        1. "Adquirência Web" - Para antecipação de vendas online
        2. "Adquirência Web / Adquirência Presencial" - Para antecipação multi-canal
        3. "Emissão" - Para cartões (múltiplo, pré-pago, crédito, débito)
        4. "PagBank" - Para conta digital, Pix, TED, folha de pagamento, app
        
        Responda APENAS com uma das opções acima.
        """,
        response_model=BusinessUnitSelection,
        structured_outputs=True
    )
    
    # Dynamic agent creation for subsequent steps
    def create_product_classifier(self, business_unit: str) -> Agent:
        """Create product classifier with valid options for selected unit"""
        valid_products = list(self.hierarchy[business_unit].keys())
        
        return Agent(
            name="Product Classifier",
            model=Claude(id="claude-haiku-4-20250514"),
            instructions=f"""
            Baseado na Unidade de Negócio '{business_unit}', selecione o Produto.
            
            Opções válidas APENAS:
            {chr(10).join(f'- "{p}"' for p in valid_products)}
            
            Responda APENAS com uma das opções acima.
            """,
            response_model=ProductSelection,
            structured_outputs=True
        )
    
    def run(self, session_id: str, conversation_history: str) -> Iterator[WorkflowCompletedEvent]:
        """Execute hierarchical typification workflow"""
        
        # Step 1: Classify Business Unit
        unit_response = self.business_unit_classifier.run(
            f"Conversa:\n{conversation_history}"
        )
        business_unit = unit_response.content.unidade_negocio
        
        # Step 2: Classify Product (based on unit)
        product_classifier = self.create_product_classifier(business_unit)
        product_response = product_classifier.run(
            f"Unidade: {business_unit}\nConversa:\n{conversation_history}"
        )
        product = product_response.content.produto
        
        # Step 3: Classify Motive (based on product)
        motive_classifier = self.create_motive_classifier(business_unit, product)
        motive_response = motive_classifier.run(
            f"Produto: {product}\nConversa:\n{conversation_history}"
        )
        motive = motive_response.content.motivo
        
        # Step 4: Classify Submotive (based on motive)
        submotive_classifier = self.create_submotive_classifier(business_unit, product, motive)
        submotive_response = submotive_classifier.run(
            f"Motivo: {motive}\nConversa:\n{conversation_history}"
        )
        submotive = submotive_response.content.submotivo
        
        # Step 5: Generate final typification and ticket
        final_typification = HierarchicalTypification(
            unidade_negocio=business_unit,
            produto=product,
            motivo=motive,
            submotivo=submotive,
            conclusao="Orientação"
        )
        
        # Create ticket with complete typification
        ticket_result = self._create_ticket(session_id, final_typification, conversation_history)
        
        yield WorkflowCompletedEvent(
            run_id=self.run_id,
            content={
                "typification": final_typification.model_dump(),
                "ticket": ticket_result.model_dump(),
                "hierarchy_path": f"{business_unit} > {product} > {motive} > {submotive}",
                "status": "completed"
            }
        )

def get_conversation_typification_workflow(debug_mode: bool = False) -> ConversationTypificationWorkflow:
    return ConversationTypificationWorkflow(
        workflow_id="conversation-typification",
        storage=PostgresStorage(
            table_name="conversation_typification_workflows",
            db_url=db_url,
            mode="workflow",
            auto_upgrade_schema=True,
        ),
        debug_mode=debug_mode,
    )
```

## Task Details

**Priority**: HIGH - New critical functionality  
**Risk**: MEDIUM - Complex hierarchy validation

## Current State
- System routes by keywords, NOT typification
- No post-conversation analysis
- No structured ticket generation
- Typification data exists in CSV but unused

## Target State (NEW Functionality)
- Sequential workflow following CSV hierarchy
- 5-level classification: Unit → Product → Motive → Submotive → Conclusion
- Automatic ticket generation
- Based on `genie/agno-demo-app/workflows/blog_post_generator.py` pattern

## Implementation Steps

### Step 1: Extract Complete Hierarchy from CSV 
Build complete hierarchy mapping:

```python
# scripts/extract_typification_hierarchy.py
import pandas as pd
from collections import defaultdict
import json

def extract_hierarchy():
    df = pd.read_csv("context/knowledge/knowledge_rag.csv")
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    
    for _, row in df.iterrows():
        typification = row['typification']
        lines = typification.strip().split('\n')
        
        # Parse each level
        unit = lines[0].split(': ')[1]
        product = lines[1].split(': ')[1]
        motive = lines[2].split(': ')[1]
        submotive = lines[3].split(': ')[1]
        
        hierarchy[unit][product][motive].add(submotive)
    
    # Convert sets to lists for JSON
    result = {}
    for unit, products in hierarchy.items():
        result[unit] = {}
        for product, motives in products.items():
            result[unit][product] = {}
            for motive, submotives in motives.items():
                result[unit][product][motive] = sorted(list(submotives))
    
    # Save to file
    with open("workflows/conversation_typification/hierarchy.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print statistics
    print(f"Units: {len(result)}")
    print(f"Total products: {sum(len(p) for p in result.values())}")
    
    return result

hierarchy = extract_hierarchy()
```

### Step 2: Create Workflow Structure 
Based on demo app pattern:

```bash
mkdir -p workflows/conversation_typification
touch workflows/conversation_typification/__init__.py
touch workflows/conversation_typification/workflow.py
touch workflows/conversation_typification/models.py
touch workflows/conversation_typification/config.yaml
```

### Step 3: Implement Pydantic Models 
Create strict validation models:

```python
# workflows/conversation_typification/models.py
from pydantic import BaseModel, Field, validator
from typing import Literal
import json

# Load hierarchy from extracted JSON
with open("workflows/conversation_typification/hierarchy.json") as f:
    HIERARCHY = json.load(f)

class BusinessUnitSelection(BaseModel):
    unit: Literal["Adquirência Web", "Adquirência Web / Adquirência Presencial", "Emissão", "PagBank"]

class ProductSelection(BaseModel):
    product: str
    
    @validator('product')
    def validate_product(cls, v, values):
        # Validation happens in workflow context
        return v

# ... Rest of models from strategy
```

### Step 4: Build Sequential Workflow 
Following blog post generator pattern:

```python
# workflows/conversation_typification/workflow.py
from agno.workflow import Workflow, WorkflowCompletedEvent
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
import json

class ConversationTypificationWorkflow:
    """Sequential typification following exact CSV hierarchy"""
    
    description = "Classifica conversas seguindo hierarquia PagBank de 5 níveis"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load hierarchy on init
        with open("workflows/conversation_typification/hierarchy.json") as f:
            self.hierarchy = json.load(f)
    
    # Step 1: Business Unit (Static agent)
    unit_classifier: Agent = Agent(
        model=Claude(id="claude-haiku-4-20250514"),
        instructions=f"""
        Classifique a unidade de negócio.
        Opções: {', '.join(HIERARCHY.keys())}
        """,
        response_model=BusinessUnitSelection,
        structured_outputs=True
    )
    
    def create_product_classifier(self, unit: str) -> Agent:
        """Dynamic agent with unit-specific products"""
        valid_products = list(self.hierarchy[unit].keys())
        
        return Agent(
            model=Claude(id="claude-haiku-4-20250514"),
            instructions=f"""
            Unidade: {unit}
            Produtos válidos: {', '.join(valid_products)}
            Selecione o produto apropriado.
            """,
            response_model=ProductSelection,
            structured_outputs=True
        )
```

### Step 5: Test with Real Data 
Create comprehensive tests:

```python
# tests/test_typification_workflow.py
def test_hierarchy_completeness():
    """Ensure all CSV entries are in hierarchy"""
    df = pd.read_csv("context/knowledge/knowledge_rag.csv")
    hierarchy = load_hierarchy()
    
    missing = []
    for _, row in df.iterrows():
        typification = parse_typification(row['typification'])
        if not validate_path_exists(hierarchy, typification):
            missing.append(typification)
    
    assert len(missing) == 0, f"Missing paths: {missing}"

def test_sequential_classification():
    """Test full workflow with real conversation"""
    workflow = get_conversation_typification_workflow()
    
    test_conversation = """
    Cliente: Oi, quero antecipar minhas vendas
    Ana: Claro! Posso ajudar com antecipação. Qual valor?
    Cliente: Tenho 5000 reais para receber
    """
    
    result = workflow.run("test_session", test_conversation)
    
    assert result["typification"]["unidade_negocio"] == "Adquirência Web"
    assert result["typification"]["produto"] == "Antecipação de Vendas"
    assert result["typification"]["conclusao"] == "Orientação"
```

### Step 6: Integration with Ana 
Add workflow trigger at conversation end:

```python
# teams/ana/team.py 
def run_post_conversation_typification(session_id: str, history: str):
    """Run typification workflow after conversation ends"""
    workflow = get_conversation_typification_workflow()
    
    # Run asynchronously
    result = workflow.run(session_id, history)
    
    # Log result
    logger.info(f"Typification complete: {result['hierarchy_path']}")
    
    return result
```

## Hierarchy Statistics (from CSV)
```
Business Units: 4
├── Adquirência Web: 1 product
├── Adquirência Web / Adquirência Presencial: 1 product  
├── Emissão: 11 products
└── PagBank: 8 products

Total unique paths: ~200+
All conclusions: "Orientação"
```

## Validation Checklist
- [ ] Complete hierarchy extracted from CSV
- [ ] All 4 business units mapped
- [ ] All 20 products mapped to correct units
- [ ] All 40 motives mapped to correct products
- [ ] All 53 submotives mapped to correct motives
- [ ] Sequential validation works (can't skip levels)
- [ ] Invalid selections rejected with clear errors
- [ ] Workflow completes in < 30 seconds
- [ ] Results saved to database

## Dependencies
- **Prerequisite**: Database infrastructure (Phase 1)
- **Requires**: CSV hierarchy extraction complete
- **Blocks**: None - this is new functionality

## Success Metrics
- 100% of CSV paths extractable
- Zero invalid classifications
- Average classification time < 5 seconds per step
- Ticket generation success rate > 99%

Co-Authored-By: Automagik Genie <genie@namastex.ai>
