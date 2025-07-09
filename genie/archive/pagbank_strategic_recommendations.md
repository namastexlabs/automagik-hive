# Recomendações Técnicas para Implementação - POC PagBank

## Estrutura de Knowledge Base

### Formato CSV para Importação

O conhecimento do PagBank será estruturado em CSV com as seguintes colunas de metadata:

```csv
conteudo,area,tipo_produto,tipo_informacao,nivel_complexidade,publico_alvo,palavras_chave,atualizado_em
"Para pedir o Cartão de Crédito PagBank, acesse o app, toque em Cartões e selecione Pedir Cartão Grátis",cartoes,cartao_credito,como_solicitar,basico,pessoa_fisica,"pedir cartão crédito solicitar",2024-01
"O limite do Cartão de Crédito pode ser aumentado fazendo uma reserva de saldo ou investindo em CDB",cartoes,cartao_credito,limites,intermediario,pessoa_fisica,"limite aumentar reserva cdb",2024-01
"Cartão Pré-Pago custa R$ 12,90 para emissão, sem anuidade, ideal para mesada de filhos",cartoes,cartao_prepago,taxas,basico,menor_idade,"prepago mesada filhos valor",2024-01
"Conta Rendeira rende 100% do CDI automaticamente, sem precisar fazer nada",conta_digital,conta_rendeira,beneficios,basico,pessoa_fisica,"render cdi automatico poupanca",2024-01
"PIX no PagBank é grátis e ilimitado, 24h por dia, 7 dias por semana",conta_digital,pix,beneficios,basico,pessoa_fisica,"pix gratis ilimitado transferencia",2024-01
"CDB PagBank rende até 130% do CDI e o valor investido vira limite no cartão de crédito",investimentos,cdb,beneficios,intermediario,pessoa_fisica,"cdb render limite cartao",2024-01
"Antecipação FGTS: taxas a partir de 1,24% ao mês, dinheiro em 2 minutos, até 10 parcelas",credito,fgts,taxas,basico,trabalhador_clt,"fgts antecipacao taxa rapido",2024-01
"PagBank NUNCA pede pagamento antecipado para liberar empréstimos - CUIDADO COM GOLPES",credito,todos,requisitos,basico,todos,"golpe pagamento antecipado fraude",2024-01
"PagBank Saúde: R$ 24,90/mês, sem carência, consultas com desconto, até 4 dependentes grátis",seguros,saude,precos,basico,pessoa_fisica,"saude plano consulta desconto",2024-01
```

### Configuração dos Filtros Agnósticos

Cada agente especialista terá filtros específicos:

```yaml
# Time de Cartões
knowledge_filters:
  area: "cartoes"
  tipo_produto: ["cartao_credito", "cartao_debito", "cartao_prepago"]

# Time de Conta Digital  
knowledge_filters:
  area: "conta_digital"
  tipo_produto: ["conta_rendeira", "pix", "ted", "recarga", "pagamento_contas"]

# Time de Investimentos
knowledge_filters:
  area: "investimentos"
  tipo_produto: ["cdb", "lci", "lca", "renda_variavel", "tesouro_direto", "cofrinho"]

# Time de Crédito
knowledge_filters:
  area: "credito"
  tipo_produto: ["fgts", "consignado_inss"]
  
# Time de Seguros
knowledge_filters:
  area: "seguros"
  tipo_produto: ["seguro_vida", "seguro_residencia", "seguro_conta", "saude"]
```

## Lista de Tasks para Implementação

### Configuração Base
- [ ] Configurar ambiente Agno com dependências necessárias
- [ ] Estabelecer conexão com Claude-3.5-Sonnet API
- [ ] Configurar banco de dados para memória (SqliteMemoryDb ou PostgreSQL)
- [ ] Configurar vector database para knowledge base (PgVector ou ChromaDB)

### Knowledge Base
- [ ] Converter documentação PagBank em CSV estruturado com metadados
- [ ] Implementar CSVKnowledgeBase com vector_db
- [ ] Configurar enable_agentic_knowledge_filters para todos os agentes
- [ ] Testar filtros agnósticos por área e tipo_produto
- [ ] Validar busca semântica com search_knowledge

### Sistema de Memória
- [ ] Implementar Memory com enable_agentic_memory=True
- [ ] Configurar enable_user_memories para aprendizado contínuo
- [ ] Implementar session storage para histórico persistente
- [ ] Configurar add_history_to_messages com num_history_runs=3
- [ ] Implementar detecção de padrões recorrentes

### Time Principal (Orquestrador)
- [ ] Criar agente principal com modo "route"
- [ ] Implementar lógica de clarificação integrada
- [ ] Configurar detecção de frustração baseada em keywords
- [ ] Implementar contador de interações para escalonamento
- [ ] Configurar team_session_state com estrutura completa
- [ ] Implementar normalização de texto para erros comuns

### Times Especializados
- [ ] Implementar Time de Cartões com knowledge filters
- [ ] Implementar Time de Conta Digital com knowledge filters
- [ ] Implementar Time de Investimentos com compliance alerts
- [ ] Implementar Time de Crédito com detecção de golpes
- [ ] Implementar Time de Seguros com knowledge filters

### Agentes de Ação
- [ ] Implementar Agente de Escalonamento Técnico com criação de protocolos
- [ ] Implementar Agente Coletor de Feedback com categorização
- [ ] Implementar Agente Humano (mock) para demonstração

### Ferramentas Auxiliares
- [ ] Função normalize_text para correção ortográfica
- [ ] Função detect_frustration com análise de histórico
- [ ] Função update_interaction_state para tracking
- [ ] Função create_support_ticket para protocolos
- [ ] Sistema de logging para análise posterior

### Integração e Testes
- [ ] Testar fluxo completo com diferentes personas
- [ ] Validar roteamento entre times
- [ ] Testar escalonamento automático após 3 interações
- [ ] Validar persistência de memória entre sessões
- [ ] Testar busca no knowledge base com filtros
- [ ] Simular cenários de frustração e transferência

### Preparação para Demo
- [ ] Script de demonstração com 4 atos
- [ ] Base de conhecimento populada com casos reais
- [ ] Cenários de teste para diferentes problemas
- [ ] Dashboard simples mostrando fluxo de roteamento
- [ ] Documentação de como executar a demo

## Configurações Recomendadas

### Modelos e Parâmetros
```yaml
# Todos os agentes
model: Claude-3.5-Sonnet
temperature: 0.3  # Para consistência
max_tokens: 2048

# Time Principal
show_tool_calls: True
markdown: True
debug_mode: True  # Para demo
show_members_responses: True

# Agentes Especializados
search_knowledge: True
enable_agentic_knowledge_filters: True
```

### Estado de Sessão
```yaml
team_session_state:
  customer_id: string
  customer_name: string
  interaction_count: 0
  frustration_level: 0
  message_history: []
  routing_history: []
  current_topic: string
  resolved: false
  awaiting_human: false
  tickets: []
```

## Demonstração para Stakeholders - Roteiro de 15 minutos

### Minuto 0-3: Caso Simples
- Cliente pergunta sobre cartão
- Sistema clarifica e roteia corretamente
- Resposta rápida e precisa

### Minuto 3-7: Caso com Dificuldade
- Cliente com problema de limite (Manoel)
- Sistema tenta ajudar, detecta frustração
- Mostra tentativas antes de escalar

### Minuto 7-10: Escalonamento Inteligente
- Sistema detecta necessidade de humano
- Cria resumo completo para atendente
- Transfere com contexto preservado

### Minuto 10-12: Aprendizado do Sistema
- Mostra memórias criadas
- Padrões identificados
- Sugestões capturadas

### Minuto 12-15: Potencial Futuro
- Expansão para WhatsApp
- Integração com sistemas internos
- Automação de tarefas simples