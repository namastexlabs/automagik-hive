# TODO: Knowledge Base Agent

## Objective
Convert PagBank documentation into a structured CSV knowledge base with metadata columns, implement CSVKnowledgeBase with PgVector for semantic search, and configure agentic knowledge filters for each specialist team.

## Technical Requirements
- [ ] Parse raw knowledge from @pagbank/knowledge.md into structured CSV format
- [ ] Implement CSV schema with required metadata columns:
  - conteudo (main content)
  - area (cartoes, conta_digital, investimentos, credito, seguros)
  - tipo_produto (specific product types)
  - tipo_informacao (como_solicitar, taxas, beneficios, requisitos, prazos, limites, problemas_comuns)
  - nivel_complexidade (basico, intermediario, avancado)
  - publico_alvo (pessoa_fisica, pessoa_juridica, aposentado, menor_idade, trabalhador_clt, todos)
  - palavras_chave (space-separated keywords)
  - atualizado_em (YYYY-MM format)
- [ ] Configure PgVector database connection (postgresql+psycopg://ai:ai@localhost:5532/ai)
- [ ] Implement CSVKnowledgeBase with vector embeddings
- [ ] Configure metadata columns for filtering
- [ ] Test agentic knowledge filters for each team:
  - Cards team: area="cartoes"
  - Digital Account team: area="conta_digital"
  - Investments team: area="investimentos"
  - Credit team: area="credito"
  - Insurance team: area="seguros"
- [ ] Validate search functionality with different filter combinations
- [ ] Implement search performance optimization (<2 seconds response time)
- [ ] Create knowledge base loader script with recreate option
- [ ] Add fraud/scam alerts in credit area with high priority

## Code Structure
```python
pagbank/  # Root project directory (clean structure)
  knowledge/
    pagbank_knowledge.csv          # Generated CSV file ✅ COMPLETED
    csv_knowledge_base.py          # CSVKnowledgeBase implementation ✅ COMPLETED
    agentic_filters.py            # Team filter configurations ✅ COMPLETED
    validation_tests.py           # Test search and filters ✅ COMPLETED
  config/
    database.py                   # Database configuration ✅ AVAILABLE
    models.py                     # Model configuration ✅ AVAILABLE
```

## Research Required
- Agno CSVKnowledgeBase documentation
- PgVector setup and optimization
- Agentic knowledge filters configuration
- Embedding strategies for Portuguese content
- Metadata-based filtering best practices

## Integration Points
- Input from: Raw knowledge documentation (pagbank/knowledge.md)
- Output to: All specialist teams (filtered knowledge access)
- Shared with: Main orchestrator (for routing decisions)

## Testing Checklist
- [ ] Unit tests for CSV conversion accuracy
- [ ] Integration test with PgVector connection
- [ ] Filter validation for each specialist team
- [ ] Search relevance testing with sample queries
- [ ] Performance test: 100 concurrent searches <2s
- [ ] Test Portuguese language tokenization
- [ ] Validate fraud alert prioritization
- [ ] Test knowledge updates without downtime

## Deliverables
1. `pagbank_knowledge.csv` - Complete structured knowledge base
2. Knowledge base initialization scripts
3. Filter configuration for all 5 teams
4. Search performance metrics report
5. Knowledge validation test results

## Implementation Example
```python
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector

# Configure vector database
vector_db = PgVector(
    table_name="pagbank_documents",
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    embedding_model="text-embedding-3-small"
)

# Initialize knowledge base
knowledge_base = CSVKnowledgeBase(
    path="pagbank/knowledge/pagbank_knowledge.csv",
    vector_db=vector_db,
    columns_to_embed=["conteudo", "palavras_chave"],
    metadata_columns=[
        "area", "tipo_produto", "tipo_informacao",
        "nivel_complexidade", "publico_alvo", "atualizado_em"
    ]
)

# Load and index
knowledge_base.load(recreate=True)

# Example search with filters
results = knowledge_base.search(
    "como aumentar limite cartão",
    filters={
        "area": "cartoes",
        "tipo_produto": ["cartao_credito", "limite_credito"]
    },
    limit=5
)
```

## Priority Items
1. Fraud/scam alerts must be easily searchable
2. Common problems should have quick resolution paths
3. Compliance text for investments must be included
4. Language should be simplified for basic complexity items
5. Ensure all products have "como_solicitar" entries