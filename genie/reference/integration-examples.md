# Integration Examples - PagBank Multi-Agent System

## Agent Integration Patterns

### 1. Knowledge Base Integration
```python
# Pattern: Agent accessing filtered knowledge
class SpecialistAgent(BaseSpecialistAgent):
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.kb.set_filter(self.business_unit)
    
    async def search_knowledge(self, query: str):
        # Knowledge automatically filtered by business unit
        results = await self.kb.search_similar(query, limit=3)
        return self._format_knowledge_response(results)
```

### 2. Memory Integration
```python
# Pattern: Storing interaction in memory
async def store_interaction(memory_manager, session_id, query, response):
    await memory_manager.add_interaction(
        session_id=session_id,
        user_message=query,
        assistant_message=response,
        metadata={
            'business_unit': self.business_unit.value,
            'confidence': response.confidence,
            'timestamp': datetime.now()
        }
    )
```

### 3. Frustration Detection Integration
```python
# Pattern: Checking frustration before response
async def check_frustration(detector, session_state):
    frustration_level = detector.analyze(
        message=session_state['last_message'],
        history=session_state.get('history', [])
    )
    
    if frustration_level >= 3:
        return BusinessUnit.HUMAN_HANDOFF
    
    return None  # Continue with normal routing
```

### 4. State Synchronization
```python
# Pattern: Synchronizing state across agents
class StateSynchronizer:
    async def sync_before_handoff(self, from_unit, to_unit, session_state):
        # Prepare context for target agent
        context = {
            'previous_unit': from_unit.value,
            'conversation_summary': self._summarize(session_state['history']),
            'escalation_reason': session_state.get('escalation_reason'),
            'customer_context': session_state.get('customer_data')
        }
        
        # Update state for target agent
        session_state['handoff_context'] = context
        return session_state
```

## WhatsApp Integration Pattern

### Human Handoff with WhatsApp
```python
# Pattern: Sending WhatsApp notification on escalation
async def escalate_to_human(session_state, reason):
    # 1. Generate ticket
    ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 2. Prepare WhatsApp message
    message = f"""
🔴 Nova Escalação - {ticket_id}

📱 Cliente: {session_state.get('customer_id', 'Não identificado')}
❗ Motivo: {reason}
🕐 Horário: {datetime.now().strftime('%H:%M')}

Contexto:
{session_state.get('conversation_summary', 'N/A')}

Por favor, assumir atendimento.
"""
    
    # 3. Send via MCP tool
    await mcp_client.call_tool(
        'evolution-api_send_message',
        {
            'instance': 'pagbank-support',
            'message': message,
            'number': SUPPORT_TEAM_NUMBER
        }
    )
    
    return ticket_id
```

## Testing Integration Patterns

### End-to-End Test Pattern
```python
# Pattern: Testing complete flow
async def test_customer_journey():
    # 1. Start conversation
    orchestrator = create_main_orchestrator()
    
    # 2. Send initial query
    response1 = await orchestrator.process("Como fazer PIX?")
    assert response1.business_unit == BusinessUnit.PAGBANK
    
    # 3. Test frustration escalation
    response2 = await orchestrator.process("Não está funcionando!")
    response3 = await orchestrator.process("PÉSSIMO ATENDIMENTO!")
    assert response3.business_unit == BusinessUnit.HUMAN_HANDOFF
    
    # 4. Verify WhatsApp notification sent
    assert mock_mcp.called_with('evolution-api_send_message')
```

### Knowledge Filtering Test
```python
# Pattern: Testing business unit filtering
def test_knowledge_filtering():
    kb = PagBankCSVKnowledgeBase()
    
    # Set filter for PagBank
    kb.set_filter(BusinessUnit.PAGBANK)
    results = kb.search("cartão")  # Card-related query
    
    # Should return no results (cards belong to Emissão)
    assert len(results) == 0
    
    # Set filter for Emissão
    kb.set_filter(BusinessUnit.EMISSAO)
    results = kb.search("cartão")
    
    # Should return card-related results
    assert len(results) > 0
    assert all(r.business_unit == 'emissao' for r in results)
```