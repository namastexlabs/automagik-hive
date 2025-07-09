# Estado de Sessão Compartilhado

O sistema mantém um estado persistente durante toda a conversa, permitindo que diferentes agentes acessem o contexto completo:

## Estrutura do `team_session_state`

```yaml
team_session_state:
  # Identificação do Cliente
  customer_id: "string"
  customer_name: "string"
  
  # Controle de Interações
  interaction_count: 0
  clarification_count: 0
  frustration_level: 0  # 0-3, onde 3 aciona atendimento humano
  
  # Histórico
  message_history: []  # Lista de todas as mensagens do cliente
  routing_history: []  # Lista de todos os roteamentos realizados
  
  # Estado Atual
  current_topic: "string"
  last_topic: "string"
  resolved: false
  awaiting_human: false
  
  # Tickets e Protocolos
  tickets: []
  protocols: []
  
  # Métricas de Qualidade
  satisfaction_score: null
  resolution_time: null
  
  # Contexto do Cliente
  customer_context:
    education_level: "unknown"  # baixo/médio/alto
    communication_style: "unknown"  # formal/informal
    preferred_channel: "chat"
```

## Flags de Controle

### Detecção de Frustração
- **frustration_keywords_detected**: Lista de palavras-chave de frustração encontradas
- **consecutive_failed_attempts**: Número de tentativas consecutivas sem sucesso
- **explicit_human_request**: Cliente solicitou explicitamente atendimento humano

### Qualidade da Comunicação
- **message_clarity_score**: 0-10, baseado em erros ortográficos e ambiguidade
- **requires_clarification**: Boolean indicando necessidade de esclarecimento
- **normalized_message**: Versão corrigida da mensagem original