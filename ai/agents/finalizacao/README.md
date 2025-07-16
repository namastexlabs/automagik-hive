# Finalizacao Specialist Agent

## Overview
The Finalizacao Specialist Agent handles conversation finalization in the PagBank multi-agent system. It coordinates the typification workflow, retrieves protocols, and sends personalized farewell messages to users.

## Responsibilities
- Trigger conversation typification workflow
- Retrieve protocol information from session state
- Send personalized Portuguese farewell messages
- Conclude conversations with proper protocol information

## Configuration
- **Agent ID**: `finalizacao-specialist`
- **Language**: Portuguese (pt-BR)
- **Model**: Claude Sonnet 4
- **Temperature**: 0.7 (balanced between consistency and personalization)

## Tools
- `trigger_conversation_typification_workflow`: Triggers the 5-level typification process
- `get_protocol_from_session_state`: Retrieves protocol from session state
- `send_farewell_message`: Sends personalized farewell with protocol
- `search_knowledge_base`: Access to knowledge base for context

## Integration Points
- **Ana Team**: Receives routing when conversation ends
- **Typification Workflow**: Triggers the complete typification process
- **Protocol System**: Uses shared protocol generator
- **Session State**: Accesses user context and protocol information

## Usage Flow
1. Ana team detects conversation end and routes to finalizacao-specialist
2. Agent triggers typification workflow with conversation history
3. Typification workflow generates protocol and saves to session state
4. Agent retrieves protocol and sends farewell message
5. User receives final message with protocol number

## Example Messages
- "Obrigado por entrar em contato, João! Seu atendimento foi finalizado com sucesso. Protocolo: PROTO-session-20240715123456. Tenha um ótimo dia!"
- "Fico feliz em ter ajudado! Seu protocolo de atendimento é PROTO-session-20240715123456. Agradecemos por escolher o PagBank!"

## Session State Integration
The agent automatically receives user context through session state:
- `user_context.user_name`: Customer name
- `user_context.phone_number`: Customer phone
- `user_context.cpf`: Customer CPF
- `user_context.user_id`: Customer ID

## Error Handling
- Graceful handling of protocol retrieval failures
- Fallback messages when typification fails
- Proper logging of all operations
- User-friendly error messages in Portuguese