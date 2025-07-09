# Instructions for Processing PagBank Markdown Files to CSV

## Overview
You will process three markdown files containing PagBank customer support content and add them to an existing CSV file. Each markdown file contains multiple support scenarios separated by "---".

## Target CSV Structure
The existing `pagbank_knowledge.csv` has these columns:
- `conteudo` - Main content/text
- `area` - Business area
- `tipo_produto` - Product type
- `tipo_informacao` - Information type
- `nivel_complexidade` - Complexity level
- `publico_alvo` - Target audience
- `palavras_chave` - Keywords for search
- `atualizado_em` - Update date

## Processing Instructions

### Step 1: Read the markdown file
Open one of these files:
- `genie/missing_context/antecipacao.md` 
- `genie/missing_context/cartoes.md`
- `genie/missing_context/conta.md`

### Step 2: For each section (separated by "---"):

#### 2.1 Extract the following parts:
- **Problema a ser resolvido**: The customer's question/issue
- **Como resolver o problema**: The solution/answer
- **Como tipificar o atendimento**: Classification metadata containing:
  - Unidade de negócio
  - Produto
  - Motivo
  - Submotivo
  - Conclusão

#### 2.2 Create a CSV row with these mappings:

**conteudo**: 
- Combine "Problema a ser resolvido" + "Como resolver o problema" into one coherent text
- Remove line breaks and clean up formatting
- Keep it informative and complete

**area**:
- Map from "Unidade de negócio":
  - "Adquirência Web" → "credito"
  - "Adquirência Presencial" → "credito"
  - "Emissão" → "cartoes"
  - "PagBank" → "conta_digital"

**tipo_produto**:
- Map from "Produto":
  - "Antecipação de Vendas" → "antecipacao_vendas"
  - "Cartão Pré-Pago" → "cartao_prepago"
  - "Cartão Pré-Pago Visa" → "cartao_prepago_visa"
  - "Cartão Pré-Pago Mastercard" → "cartao_prepago_mastercard"
  - "Cartão da Conta" → "cartao_debito"
  - "Cartão Múltiplo PagBank" → "cartao_multiplo"
  - "Cartão de Crédito PagBank" → "cartao_credito"
  - "Pix" → "pix"
  - "TED" → "ted"
  - "Aplicativo PagBank" → "aplicativo"
  - "Conta PagBank" → "conta_digital"
  - "Folha de Pagamento" → "folha_pagamento"
  - "Recarga de Celular" → "recarga_celular"
  - "Portabilidade de Salário" → "portabilidade_salario"

**tipo_informacao**:
- Analyze the problem and motivo to determine:
  - If it's about how to do something → "como_solicitar"
  - If it's about fees, limits, or costs → "taxas"
  - If it's about benefits or features → "beneficios"
  - If it's about requirements or eligibility → "requisitos"
  - If it's about errors or problems → "problemas_comuns"
  - If it's about deadlines or timing → "prazos"

**nivel_complexidade**:
- Based on solution length and detail:
  - Short, simple answers (< 3 paragraphs) → "basico"
  - Medium answers with some steps → "intermediario"
  - Long, detailed answers with multiple steps → "avancado"

**publico_alvo**:
- Analyze the content to determine:
  - If mentions empresa/CNPJ/PJ → "pessoa_juridica"
  - If mentions children/teens/mesada → "menor_idade"
  - Otherwise → "pessoa_fisica"

**palavras_chave**:
- Extract key terms from the problem and solution
- Include product names, action verbs, and important concepts
- Separate with spaces, lowercase
- Example: "antecipacao vendas criterios elegibilidade maquininhas pagbank"

**atualizado_em**:
- Use "2024-01"

### Step 3: Format as CSV
Add each processed section as a new row to the CSV file, properly escaping quotes and commas.

## Example Processing

From this section in antecipacao.md:
```
## Problema a ser resolvido
Cliente deseja saber quais são os critérios para se tornar elegível à antecipação de vendas nas máquinas do PagBank.
## Como resolver o problema
Todas as contas passam por análises diárias que definem quais clientes recebem a oferta de antecipação...
## Como tipificar o atendimento
Unidade de negócio: Adquirência Web
Produto: Antecipação de Vendas
Motivo: Dúvidas sobre a Antecipação de Vendas
```

Becomes this CSV row:
```csv
"Cliente deseja saber quais são os critérios para se tornar elegível à antecipação de vendas nas máquinas do PagBank. Todas as contas passam por análises diárias que definem quais clientes recebem a oferta de antecipação...",credito,antecipacao_vendas,requisitos,intermediario,pessoa_juridica,"antecipacao vendas criterios elegibilidade analise diaria maquininhas pagbank",2024-01
```

## Important Notes
1. Process each file completely before moving to the next
2. Ensure all quotes in content are properly escaped
3. Maintain consistency in mappings
4. If a mapping doesn't exist, use the most logical alternative
5. Keep the original Portuguese language
6. Each "---" separated section becomes one CSV row
7. Skip any sections that don't have all three parts (problema, solução, tipificação)