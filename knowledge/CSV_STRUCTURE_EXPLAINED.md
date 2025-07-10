# PagBank CSV Knowledge Base Structure Explained

## 📊 **Overview**
The PagBank knowledge base uses a structured CSV with 8 columns to enable intelligent multi-agent routing and filtering. Each row represents a specific piece of customer service knowledge.

**File**: `pagbank_knowledge.csv`  
**Total Entries**: 651 documents  
**Structure**: 8 columns with specific purposes

---

## 🏗️ **Column-by-Column Breakdown**

### 1. `conteudo` (Content) - **PRIMARY CONTENT**
- **Purpose**: Main document content that gets embedded and searched
- **Usage**: What customers and agents actually read
- **Type**: Long text (avg 318 characters)
- **Examples**:
  - PIX instructions
  - Credit card benefit explanations  
  - Insurance coverage details
- **In RAG**: This content gets vectorized for similarity search

### 2. `area` (Business Area) - **TEAM ROUTING**
- **Purpose**: Routes queries to the correct specialist agent
- **Values**: 5 main business areas
  - `conta_digital` (212 entries) → Digital Account Agent
  - `cartoes` (153 entries) → Cards Agent  
  - `seguros` (121 entries) → Insurance Agent
  - `credito` (91 entries) → Credit Agent
  - `investimentos` (71 entries) → Investments Agent
- **In RAG**: Primary filter for team-based knowledge retrieval

### 3. `tipo_produto` (Product Type) - **FINE-GRAINED FILTERING**
- **Purpose**: Specific product/service within each business area
- **Examples by Area**:
  - **Cartões**: `cartao_credito`, `limite_credito`, `cartao_prepago_visa`
  - **Conta Digital**: `conta_rendeira`, `pix`, `recarga_celular`
  - **Crédito**: `fgts`, `antecipacao_vendas`, `consignado_inss`
  - **Investimentos**: `cdb`, `renda_variavel`, `fundos`
  - **Seguros**: `seguro_vida`, `saude`, `seguro_conta`
- **In RAG**: Secondary filter for precise product matching

### 4. `tipo_informacao` (Information Type) - **CONTENT CATEGORIZATION**
- **Purpose**: What kind of information is provided
- **Values** (7 types):
  - `beneficios` (286 entries) - Product benefits/advantages
  - `taxas` (153 entries) - Fees and pricing
  - `como_solicitar` (78 entries) - How to request/apply
  - `limites` (52 entries) - Limits and restrictions
  - `problemas_comuns` (43 entries) - Common issues/troubleshooting
  - `prazos` (27 entries) - Timeframes and deadlines
  - `requisitos` (9 entries) - Requirements and eligibility
- **In RAG**: Helps agents find specific types of answers

### 5. `nivel_complexidade` (Complexity Level) - **RESPONSE SOPHISTICATION**
- **Purpose**: Determines appropriate detail level for responses
- **Values** (3 levels):
  - `intermediario` (435 entries) - Standard explanations
  - `basico` (175 entries) - Simple, basic explanations
  - `avancado` (38 entries) - Detailed, technical explanations
- **In RAG**: Agents can match response complexity to customer sophistication

### 6. `publico_alvo` (Target Audience) - **CUSTOMER SEGMENTATION**
- **Purpose**: Filters content based on customer type
- **Values** (5 audience types):
  - `pessoa_fisica` (546 entries) - Individual customers
  - `pessoa_juridica` (67 entries) - Business customers
  - `aposentado` (21 entries) - Retirees
  - `menor_idade` (7 entries) - Minors
  - `trabalhador_clt` (7 entries) - Formal workers
- **In RAG**: Ensures responses are relevant to customer profile

### 7. `palavras_chave` (Keywords) - **EXCLUDED FROM METADATA**
- **Purpose**: Supplementary search terms
- **Usage**: NOT used as metadata filters (excluded in Enhanced CSV Reader)
- **Why Excluded**: Would create too many filter combinations; used for content enrichment only
- **Content**: Space-separated keywords related to the content

### 8. `atualizado_em` (Updated Date) - **EXCLUDED FROM METADATA**
- **Purpose**: Content versioning and tracking
- **Usage**: NOT used as metadata filters (excluded in Enhanced CSV Reader)
- **Why Excluded**: Not relevant for customer queries; used for management tracking only
- **Content**: Currently all entries show `2024-01`

---

## 🎯 **How Columns Enable Multi-Agent Intelligence**

### **Agent Routing Flow**:
1. **Query Reception**: "Como fazer PIX?"
2. **Intent Detection**: Main Orchestrator identifies this as digital account query
3. **Agent Selection**: Routes to Digital Account Agent
4. **Knowledge Filtering**: Agent searches with `area='conta_digital'`
5. **Results**: Gets only digital account knowledge (212 entries instead of 651)
6. **Response Generation**: Agent provides contextually appropriate answer

### **Practical Examples**:

**Example 1: PIX Question**
```python
# Customer: "Como fazer PIX?"
# Digital Account Agent searches:
kb.search_with_filters('como fazer pix', team='conta_digital')

# Results: Only conta_digital documents
# Sample result metadata:
{
    'area': 'conta_digital',
    'tipo_produto': 'conta_rendeira', 
    'tipo_informacao': 'como_solicitar',
    'nivel_complexidade': 'basico',
    'publico_alvo': 'pessoa_fisica'
}
```

**Example 2: Credit Card Limit**
```python
# Customer: "Qual meu limite do cartão?"
# Cards Agent searches:
kb.search_with_filters('limite cartao', team='cartoes')

# Results: Only cartoes documents
# Sample result metadata:
{
    'area': 'cartoes',
    'tipo_produto': 'limite_credito',
    'tipo_informacao': 'beneficios', 
    'nivel_complexidade': 'intermediario',
    'publico_alvo': 'pessoa_fisica'
}
```

---

## 🔧 **Technical Implementation**

### **Enhanced CSV Reader Configuration**:
```python
EnhancedCSVReader(
    content_column="conteudo",           # Main content for embedding
    metadata_columns=[                   # Used as search filters
        "area",                          # Team routing
        "tipo_produto",                  # Product filtering  
        "tipo_informacao",               # Info type filtering
        "nivel_complexidade",            # Complexity filtering
        "publico_alvo"                   # Audience filtering
    ],
    exclude_columns=[                    # NOT used as metadata
        "palavras_chave",               # Too granular for filtering
        "atualizado_em"                 # Not relevant for queries
    ]
)
```

### **Before vs After Fix**:

**Before (Broken)**: Documents only had chunking metadata
```python
metadata = {'chunk': 13, 'chunk_size': 4999}
# Result: 0 documents found for team filters
```

**After (Fixed)**: Documents have CSV column metadata  
```python
metadata = {
    'area': 'conta_digital',
    'tipo_produto': 'pix',
    'tipo_informacao': 'como_solicitar',
    'nivel_complexidade': 'basico', 
    'publico_alvo': 'pessoa_fisica'
}
# Result: 5 documents found for team filters
```

---

## 📈 **Data Distribution Summary**

| Business Area | Documents | Top Products | Use Case |
|---------------|-----------|--------------|----------|
| Conta Digital | 212 (32.6%) | conta_rendeira, pix, recarga | Digital banking, transfers, payments |
| Cartões | 153 (23.5%) | cartao_credito, limite_credito | Credit/debit cards, limits |
| Seguros | 121 (18.6%) | seguro_vida, saude | Insurance products, coverage |
| Crédito | 91 (14.0%) | fgts, antecipacao_vendas | Loans, credit products |
| Investimentos | 71 (10.9%) | cdb, renda_variavel | Investment products, returns |

**Information Types**: 44% benefits, 24% fees, 12% how-to guides  
**Complexity**: 67% intermediate, 27% basic, 6% advanced  
**Audience**: 84% individual customers, 10% business customers

---

## 🎯 **Key Benefits of This Structure**

1. **🎯 Precise Routing**: Each agent only searches relevant knowledge subset
2. **⚡ Performance**: Filtering 651 docs → ~150 relevant docs per team  
3. **🧠 Context Awareness**: Agents can adjust complexity and audience appropriateness
4. **🔍 Granular Filtering**: Can combine multiple metadata filters for specific scenarios
5. **📊 Analytics**: Track which content types are most requested by area
6. **🔄 Scalability**: Easy to add new areas, products, or information types

This structure transforms a simple CSV into an intelligent knowledge base that powers sophisticated multi-agent customer service interactions.