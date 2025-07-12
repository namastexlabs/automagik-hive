# CSV Typification Analysis - PagBank Knowledge Base

**Navigation**: [← YAML Configuration](./yaml-configuration.md) | [THIS FILE] | [Context Search Tools →](./context-search-tools.md)

## Overview

Found one main CSV file containing typification/classification data:
- **Location**: `/home/namastex/workspace/pagbank-multiagents/context/knowledge/knowledge_rag.csv`
- **Structure**: Contains customer service knowledge with hierarchical typification

## CSV Structure

The CSV has 4 main columns:
1. **problem**: Customer query/issue description
2. **solution**: Detailed response/solution
3. **typification**: Hierarchical classification (multi-line format)
4. **business_unit**: Business unit assignment

## Typification Hierarchy

The typification follows a consistent 5-level hierarchy:

```
Unidade de negócio (Business Unit)
└── Produto (Product)
    └── Motivo (Reason/Motive)
        └── Submotivo (Sub-reason)
            └── Conclusão (Conclusion)
```

### Hierarchy Levels

1. **Unidade de negócio** (4 unique values):
   - Adquirência Web
   - Adquirência Web / Adquirência Presencial
   - Emissão
   - PagBank

2. **Produto** (20+ unique values):
   - Antecipação de Vendas (Sales Anticipation)
   - Various Card Products (Pré-Pago, Débito, Crédito, Múltiplo)
   - Pix
   - TED
   - Folha de Pagamento (Payroll)
   - Conta PagBank (PagBank Account)
   - Aplicativo PagBank (PagBank App)
   - And others...

3. **Motivo** (40+ unique values):
   - Various customer intents and issues
   - Questions about features
   - Transaction problems
   - Account management
   - Technical issues

4. **Submotivo** (53+ unique values):
   - Specific resolution actions
   - Detailed problem descriptions
   - Customer guidance provided

5. **Conclusão** (1 unique value):
   - Always "Orientação" (Guidance/Orientation)

## Example Entry

```csv
"problem": "Cliente deseja entender o que é e como funciona a antecipação de vendas."
"solution": "No PagBank o vendedor consegue antecipar os valores..."
"typification": "Unidade de negócio: Adquirência Web
Produto: Antecipação de Vendas
Motivo: Dúvidas sobre a Antecipação de Vendas
Submotivo: Cliente orientado sobre a Antecipação de Vendas
Conclusão: Orientação"
"business_unit": "Adquirência Web"
```

## Key Insights

1. **Hierarchical Classification**: Each knowledge entry has a 5-level classification hierarchy
2. **Consistent Structure**: All entries follow the same typification pattern
3. **Business Unit Alignment**: The typification's business unit matches the separate business_unit column
4. **Portuguese Language**: All content is in Portuguese, targeting Brazilian customers
5. **Service-Oriented**: All entries conclude with "Orientação" indicating customer guidance focus

## Usage in System

This CSV appears to be used for:
- Knowledge base queries
- Agent routing decisions
- Customer query classification
- Response generation templates
- Business unit assignment

Co-Authored-By: Automagik Genie <genie@namastex.ai>