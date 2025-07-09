# Feedback Collection and Human Agent Mock System

Sistema avançado de coleta de feedback e simulação de agentes humanos para o PagBank Multi-Agent System.

## 🎯 Visão Geral

Este módulo implementa um sistema completo de feedback e atendimento humano simulado, incluindo:

- **Feedback Collector**: Coleta, categoriza e analisa feedback de clientes
- **Human Agent Mock**: Simula agentes humanos com comportamento realista
- **Conversation Manager**: Gerencia histórico e continuidade de conversas
- **Feedback Analyzer**: Gera insights e identifica oportunidades de melhoria

## 🚀 Funcionalidades Principais

### 📋 Feedback Collector
- Categorização automática (sugestão, reclamação, elogio, dúvida)
- Análise de sentimento (positivo, neutro, negativo)
- Priorização inteligente (baixa, média, alta, crítica)
- Respostas empáticas personalizadas
- Detecção de padrões recorrentes
- Geração de relatórios detalhados

### 👤 Human Agent Mock
- Simulação realista de agentes humanos
- Múltiplos perfis com especialidades diferentes
- Tempo de digitação variável baseado no perfil
- Elementos conversacionais naturais
- Protocolo de handoff entre agentes
- Resumos automáticos de conversas

### 💬 Conversation Manager
- Gerenciamento de múltiplas conversas simultâneas
- Suporte a diferentes canais (web, mobile, WhatsApp)
- Estados de conversa (ativa, pausada, completada, abandonada)
- Métricas em tempo real
- Histórico completo de interações
- Detecção de abandono e recuperação

### 📊 Feedback Analyzer
- Análise de tendências temporais
- Segmentação automática de clientes
- Identificação de oportunidades de melhoria
- Cálculo de ROI estimado
- Insights acionáveis
- Relatórios executivos

## 🛠️ Instalação

```bash
# Clone o repositório
git clone [repository-url]

# Navegue até o diretório
cd feedback_human_systems

# Instale as dependências usando UV
uv add agno openai pydantic

# Para testes
uv add pytest pytest-asyncio
```

## 📖 Uso Básico

### Coleta de Feedback

```python
from feedback_collector import FeedbackCollector

# Inicializar coletor
collector = FeedbackCollector(model_id="claude-opus-4-20250514")

# Coletar feedback
feedback = collector.collect_feedback(
    customer_id="CLT_001",
    feedback_content="O novo sistema de PIX está excelente!",
    context={"feature": "pix", "version": "4.0"}
)

# Gerar resposta empática
response = collector.get_feedback_response(feedback)
print(response)

# Analisar padrões
patterns = collector.analyze_patterns(time_window_days=30)
```

### Simulação de Agente Humano

```python
from human_agent_mock import HumanAgentMock

# Inicializar agente
agent = HumanAgentMock(model_id="claude-opus-4-20250514")

# Gerar resposta humana
response, metadata = await agent.generate_human_response(
    customer_id="CLT_002",
    message="Preciso de ajuda com meu cartão bloqueado",
    conversation_context={"urgency": "alta"}
)

print(f"{metadata['agent_name']}: {response}")
```

### Gerenciamento de Conversas

```python
from conversation_manager import ConversationManager

# Inicializar gerenciador
manager = ConversationManager(model_id="claude-opus-4-20250514")

# Iniciar conversa
context = manager.start_conversation(
    customer_id="CLT_003",
    channel="whatsapp",
    initial_message="Olá, preciso de suporte"
)

# Adicionar mensagens
manager.add_message(
    context.conversation_id,
    "agent",
    "Ana Silva",
    "Olá! Como posso ajudar você hoje?"
)

# Obter métricas
metrics = manager.calculate_metrics(context.conversation_id)
```

### Análise de Feedback

```python
from feedback_analyzer import FeedbackAnalyzer

# Inicializar analisador
analyzer = FeedbackAnalyzer(model_id="claude-opus-4-20250514")

# Analisar tendências
trends = analyzer.analyze_trends(feedbacks, period_days=30)

# Segmentar clientes
segments = analyzer.segment_customers(feedbacks)

# Gerar relatório
report = analyzer.generate_analytics_report(
    feedbacks,
    period_start=datetime.now() - timedelta(days=30),
    period_end=datetime.now()
)
```

## 🧪 Testes

Execute os testes usando UV:

```bash
# Executar todos os testes
uv run python tests/test_feedback_human.py

# Executar com pytest
uv run -m pytest tests/ -v
```

## 🎮 Demonstração

Execute a demonstração completa:

```bash
uv run python demo.py
```

A demonstração mostra:
1. Coleta e categorização de feedback
2. Interação com agente humano simulado
3. Transferência entre agentes (handoff)
4. Gerenciamento de múltiplas conversas
5. Análise e geração de insights

## 🏗️ Arquitetura

```
feedback_human_systems/
├── feedback_collector.py    # Coleta e processa feedback
├── human_agent_mock.py      # Simula agentes humanos
├── conversation_manager.py  # Gerencia conversas
├── feedback_analyzer.py     # Analisa e gera insights
├── demo.py                 # Demonstração do sistema
└── tests/                  # Testes unitários e integração
```

### Modelos de Dados

- **FeedbackEntry**: Entrada individual de feedback
- **FeedbackPattern**: Padrão identificado em feedbacks
- **ConversationContext**: Contexto de uma conversa
- **HumanAgentProfile**: Perfil de agente humano
- **HandoffProtocol**: Protocolo de transferência
- **AnalyticsReport**: Relatório analítico completo

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Modelo padrão (Claude Opus 4)
export MODEL_ID="claude-opus-4-20250514"

# Caminho do banco de dados
export DB_PATH="tmp/pagbank_feedback.db"
```

### Personalização

Você pode personalizar:
- Categorias de feedback
- Perfis de agentes
- Limiares de análise
- Templates de resposta
- Métricas calculadas

## 📊 Métricas e KPIs

O sistema rastreia:
- Taxa de satisfação do cliente
- Tempo médio de resposta
- Taxa de resolução
- Tendências de feedback
- Padrões emergentes
- ROI de melhorias

## 🤝 Integração

Este módulo integra com:
- Sistema de memória Agno
- Main Orchestrator (Phase 2)
- Sistema de escalação
- Analytics dashboard

## 📝 Notas Importantes

1. **Modelo**: Usa Claude Opus 4 (claude-opus-4-20250514) por padrão
2. **Idioma**: Todas as interações em português brasileiro
3. **Empatia**: Foco em respostas empáticas e humanizadas
4. **Performance**: Otimizado para múltiplas conversas simultâneas
5. **Segurança**: Dados sensíveis são anonimizados

## 🐛 Troubleshooting

### Problema: Erro de modelo não encontrado
```bash
# Solução: Verificar configuração do modelo
export MODEL_ID="gpt-4o"  # Usar GPT-4 como fallback
```

### Problema: Banco de dados não criado
```bash
# Solução: Criar diretório tmp
mkdir -p tmp/
```

## 📚 Documentação Adicional

- [Agno Framework Docs](https://docs.agno.com)
- [PagBank API Reference](https://dev.pagbank.com.br)
- [Claude API Documentation](https://docs.anthropic.com)

## 🎯 Roadmap

- [ ] Integração com WhatsApp Business API
- [ ] Dashboard de visualização em tempo real
- [ ] ML para previsão de churn
- [ ] Automação de respostas frequentes
- [ ] Export de relatórios em PDF

## 👥 Contribuindo

Para contribuir:
1. Faça fork do projeto
2. Crie sua feature branch
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é parte do PagBank Multi-Agent System.

---

**Desenvolvido com ❤️ usando Agno Framework e Claude Opus 4**