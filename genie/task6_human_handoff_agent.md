# Task 6: Create Human Handoff Agent with WhatsApp Integration

## Objective
Create a new Human Handoff Agent that sends handover reports via WhatsApp using the Evolution API MCP server when human transfer is needed.

## Evolution API Configuration
```json
{
  "evolution-api": {
    "command": "uvx",
    "args": ["automagik-tools@latest", "tool", "evolution-api"],
    "env": {
      "EVOLUTION_API_BASE_URL": "http://192.168.112.142:8080",
      "EVOLUTION_API_API_KEY": "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF",
      "EVOLUTION_API_INSTANCE": "SofIA",
      "EVOLUTION_API_FIXED_RECIPIENT": "5511986780008@s.whatsapp.net"
    }
  }
}
```

## Implementation Plan

### Phase 1: Create Human Handoff Agent

Location: `/agents/specialists/human_handoff_agent.py`

```python
class HumanHandoffAgent(BaseSpecialistAgent):
    """
    Agent responsible for human handoffs
    Sends handover reports via WhatsApp to stakeholders
    """
    
    def __init__(self, knowledge_base, memory_manager):
        super().__init__(
            agent_name="human_handoff_specialist",
            agent_role="Especialista em Transferência Humana",
            agent_description="Responsável por transferências para atendimento humano",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "handoff"},
            tools=[self._get_whatsapp_tools()]
        )
```

### Phase 2: WhatsApp Integration Tools

Create tools for Evolution API integration:

```python
def send_whatsapp_handover(agent: Agent, summary: str, context: dict) -> str:
    """Send handover report via WhatsApp using Evolution API MCP"""
    
    # Format handover report
    report = format_handover_report(
        customer_name=context.get('customer_name'),
        session_id=context.get('session_id'),
        reason=context.get('handoff_reason'),
        conversation_summary=summary,
        last_messages=context.get('message_history')[-5:]
    )
    
    # Use Evolution API MCP tool
    # Tool name: mcp_evolution-api_send_message
    
    return "Handover report sent successfully"
```

### Phase 3: Handover Report Format

```
🚨 TRANSFERÊNCIA PARA ATENDIMENTO HUMANO

📋 Informações da Sessão:
- Cliente: {customer_name}
- Sessão: {session_id}
- Horário: {timestamp}

❗ Motivo da Transferência:
{reason}

💬 Resumo da Conversa:
{conversation_summary}

📝 Últimas Mensagens:
{last_messages}

🎯 Ação Recomendada:
{recommended_action}

---
Sistema PagBank Multi-Agente
```

### Phase 4: Integration with Orchestrator

Update main orchestrator to include human handoff agent:

```python
# In _create_specialist_agents()
human_handoff_agent = HumanHandoffAgent(knowledge_base, self.memory_manager)
agents["Human Handoff Specialist"] = human_handoff_agent.agent
```

### Phase 5: Handoff Flow

1. Frustration/human request detected
2. Route to Human Handoff Agent
3. Agent prepares handover summary
4. Send WhatsApp message via Evolution API
5. Inform customer of transfer
6. Mark session as awaiting_human

### Phase 6: MCP Tool Usage

The Evolution API MCP provides these tools:
- `send_message` - Send text message
- `send_media` - Send media files
- `get_instance_status` - Check connection

For handoff, we'll use:
```python
@tool
def send_handoff_whatsapp(report: str) -> str:
    """Send handoff report via WhatsApp"""
    # This will call the MCP tool: mcp_evolution-api_send_message
    # Fixed recipient: 5511986780008@s.whatsapp.net
```

## Testing Plan

1. Trigger human handoff scenarios:
   - User says "quero falar com humano"
   - User uses bad words
   - User writes in CAPS LOCK

2. Verify WhatsApp message:
   - Correct formatting
   - All context included
   - Sent to stakeholder number

3. Confirm customer response:
   - Polite transfer message
   - Clear next steps

## Benefits

- Real-time stakeholder notification
- Complete context for human agents
- Professional handoff process
- Demo-ready WhatsApp integration

Co-Authored-By: Automagik Genie <genie@namastex.ai>