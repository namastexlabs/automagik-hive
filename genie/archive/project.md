# Development Orchestrator Instructions - PagBank Multi-Agent System

## Project Overview

You are tasked with orchestrating the development of a multi-agent customer support system for PagBank, a Brazilian digital bank. This system must handle diverse customer inquiries with intelligence, empathy, and efficiency.

## Core Requirements

1. **Framework**: Agno (latest version)
2. **LLM Model**: Claude-4-Sonnet for all agents
3. **Architecture**: Hierarchical routing system with specialized teams
4. **Key Features**: Memory persistence, knowledge base with filters, frustration detection, human escalation

## Project Documentation

Read and understand these documents in the project folder:

1. **@pagbank/genie/archive/pagbank_session_state.md** - Defines the shared session state structure that maintains context across all agents
2. **@pagbank/genie/archive/pagbank_agents_detailed.md** - Complete specification of all agents, their roles, prompts, and configurations
3. **@pagbank/genie/archive/pagbank_demo_interaction.md** - Six demonstration cases showing different system capabilities (the human will simulate these users during the demo, this is just for context)
4. **@pagbank/genie/archive/pagbank_knowledge_structure.md** - CSV schema and metadata structure for the knowledge base
5. **@pagbank/genie/archive/pagbank_strategic_recommendations.md** - Technical implementation tasks and configuration details



## Development Sub-Agents Structure

### 1. Knowledge Base Agent (`todo_knowledge_base.md`)
**Responsibilities:**
- Convert PagBank documentation into structured CSV (refer to @pagbank_knowledge_structure.md)
- Implement CSVKnowledgeBase with PgVector (server already preconfigured in the default postgresql+psycopg://ai:ai@localhost:5532/ai)
- Configure metadata columns and embedding strategy
- Test agentic knowledge filters for each team
- Validate search functionality with different filter combinations
- the knowledge raw data is present at @pagbank/knowledge.md

**Key References:**
- CSV schema in @pagbank/pagbank_knowledge_structure.md
- Filter configurations in @pagbank/pagbank_agents_detailed.md
- Research Agno docs: knowledge base setup, agentic filters, vector databases

### 2. Memory System Agent (`todo_memory_system.md`)
**Responsibilities:**
- Implement SqliteMemoryDb 
- Configure Memory object with enable_agentic_memory=True
- Set up user memories and session summaries
- Implement pattern detection for recurring issues
- Create memory persistence across sessions

**Key References:**
- Memory configuration in @pagbank/pagbank_agents_detailed.md
- Session state structure in @pagbank/pagbank_session_state.md
- Research Agno docs: memory.v2, storage drivers, session management

### 3. Main Orchestrator Agent (`todo_main_orchestrator.md`)
**Responsibilities:**
- Create the main routing Team with mode="route"
- Implement integrated clarification logic (no separate clarification agent)
- Build frustration detection system with keyword analysis
- Implement interaction counter for escalation
- Create message normalization for common Portuguese errors

**Key References:**
- Orchestrator specifications in @pagbank/pagbank_agents_detailed.md
- Frustration detection logic in demonstration cases @pagbank/pagbank_demo_interaction.md
- Research Agno docs: Team routing mode, team_session_state

### 4. Specialist Teams Agent (`todo_specialist_teams.md`)
**Responsibilities:**
- Implement 5 specialist teams (Cards, Digital Account, Investments, Credit, Insurance)
- Configure knowledge filters for each team
- Create specialized prompts with proper language adaptation
- Implement compliance warnings for investment team
- Add fraud detection for credit team

**Key References:**
- Team specifications in @pagbank/pagbank_agents_detailed.md
- Knowledge filters per team in @pagbank_strategic_recommendations.md
- Research Agno docs: Team coordination mode, agent tools

### 5. Action Agents Developer (`todo_action_agents.md`)
**Responsibilities:**
- Implement Technical Escalation Agent with ticket creation
- Create Feedback Collector Agent with categorization
- Build Human Agent (mock) for demo purposes
- Implement support tools (create_support_ticket, normalize_text)
- Configure memory for pattern learning

**Key References:**
- Action agents specs in @pagbank/pagbank_agents_detailed.md
- Mock human transfer in @pagbank/pagbank_demo_interaction.md
- Research Agno docs: custom tools, agent functions


## Technical Specifications

### Core Configurations
```python
# All agents use these base settings
model = Claude-4-Sonnet
temperature = 0.1
max_tokens = 2048
markdown = True
show_tool_calls = True  # For demo
```

### Required Integrations
1. **Database**: SQLite
2. **Vector DB**: PgVector
3. **Memory**: SqliteMemoryDb with persistent storage
4. **Knowledge**: CSVKnowledgeBase with metadata filters

## Implementation Priorities

1. **Phase 1 - Core System**
   - Main orchestrator with routing
   - Memory and storage setup
   - Basic knowledge base

2. **Phase 2 - Specialists**
   - Two specialist teams (Cards and Digital Account)
   - Knowledge filters implementation
   - Basic frustration detection

3. **Phase 3 - Complete System**
   - All specialist teams
   - Action agents
   - Human escalation mock

4. **Phase 4 - Demo Ready**
   - Playground (if __name__ == "__main__":
    playground_app.serve("playground:app"))

## Quality Checks

Before marking any task complete, ensure:

1. **Functionality**: Agent responds correctly to expected inputs
2. **Language**: Adapts to customer education level (see @pagbank_demo_interaction.md cases)
3. **Memory**: Patterns are captured and stored
4. **Knowledge**: Filters work correctly for each team
5. **Escalation**: Frustration detection triggers at right threshold
6. **Demo**: Each case runs smoothly without errors

## Special Considerations

1. **Portuguese Language**: System must handle common spelling errors and informal language
2. **Fraud Protection**: Credit team must detect payment advance scams
3. **Compliance**: Investment team must include disclaimers
4. **Empathy**: Language must be warm and patient, especially for elderly/low-education customers
5. **Efficiency**: Multi-routing for business customers (see Amanda Chen case)

## Final Deliverables

1. Working multi-agent system with all teams
2. Populated knowledge base with PagBank information
3. Demo environment with 6 scripted scenarios
4. Simple dashboard showing agent routing
5. Documentation for running demos

## Research Priority

Focus your Agno documentation research on:
1. Team routing vs coordination modes
2. Agentic knowledge filters
3. Memory v2 implementation
4. Session state persistence
5. Custom tool creation
6. Streaming responses for demos

Remember: This is a POC to demonstrate PagBank how AI can revolutionize their customer service. Focus on showcasing intelligence, empathy, and efficiency in every interaction.

