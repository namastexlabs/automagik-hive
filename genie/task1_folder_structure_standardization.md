# Task 1: Folder Structure Standardization

## Objective
Standardize the agents/teams folder structure to provide clear navigation and understanding for humans working with the codebase.

## APPROVED: OPTION A - Single Agent per Department

## Context for Implementation
This is a PagBank Multi-Agent System - a Brazilian customer service system built with Agno framework. The system needs to be restructured from complex coordinated teams to simple single agents.

### Current Working Directory
- Path: `/home/namastex/workspace/pagbank-multiagents`
- Git repo: Yes
- Main branch: master

### Key Project Files
- CLAUDE.md - Project instructions and guidelines
- Main orchestrator: `orchestrator/main_orchestrator.py`
- Teams folder: `teams/` (to be migrated)
- Empty agents folder: `agents/` (to be populated)

## Current Issues
1. Empty `/agents/` folder creates confusion about architecture
2. All implementation is in `/teams/` folder but terminology is mixed
3. Unclear whether system uses individual agents or coordinated teams
4. Folder structure doesn't reflect the actual multi-agent architecture
5. Teams use Agno Team coordination mode which is overly complex for simple Q&A

## Technical Plan

### Phase 1: Analysis (COMPLETED)
- **Current Structure**: Teams-based implementation using Agno Team coordination
- **Architectural Reality**: Main Orchestrator → Specialist Teams → Team Members (3 agents each)
- **Decision**: APPROVED - Option A: Single agent per department

### Phase 2: Approved New Structure (Option A)
```
/agents/
├── orchestrator/
│   ├── main_orchestrator.py      # Main routing agent
│   └── orchestrator_prompts.py   # Orchestrator-specific prompts
├── specialists/
│   ├── base_agent.py             # Base class for all specialist agents
│   ├── cards_agent.py            # Single cards specialist agent
│   ├── credit_agent.py           # Single credit specialist agent
│   ├── digital_account_agent.py  # Single digital account agent
│   ├── investments_agent.py      # Single investments agent
│   └── insurance_agent.py        # Single insurance agent
├── prompts/
│   ├── __init__.py
│   ├── base_prompts.py           # Shared prompt templates
│   └── specialist_prompts.py     # All specialist agent prompts
└── tools/
    ├── __init__.py
    └── agent_tools.py            # Shared tools for all agents
```

### Current Files to Migrate

**Teams folder contents:**
- `teams/base_team.py` - BaseTeam class using Agno Team coordination
- `teams/cards_team.py` - Cards team with 3 agents
- `teams/credit_team.py` - Credit team with 3 agents
- `teams/digital_account_team.py` - Digital account team with 3 agents
- `teams/investments_team.py` - Investments team with 3 agents
- `teams/insurance_team.py` - Insurance team with 3 agents
- `teams/team_config.py` - Team configurations
- `teams/team_prompts.py` - Centralized prompts (TeamPrompts class)
- `teams/team_tools.py` - Shared tools

**Other key files:**
- `orchestrator/main_orchestrator.py` - Main routing orchestrator
- `memory/` - Memory system (keep as is)
- `knowledge/` - Knowledge base (keep as is)
- `escalation_systems/` - Escalation handling (keep as is)

### Phase 3: Detailed Migration Steps

1. **Create new folder structure**
   ```bash
   # Commands to execute:
   mkdir -p agents/orchestrator
   mkdir -p agents/specialists
   mkdir -p agents/prompts
   mkdir -p agents/tools
   ```

2. **Create base files first**
   - Create `agents/specialists/base_agent.py` - Base class for all specialist agents
   - Copy and adapt from `teams/base_team.py` but simplify for single agents
   - Remove team coordination logic, keep only single agent functionality

3. **Convert each team to single agent**
   - Cards: `teams/cards_team.py` → `agents/specialists/cards_agent.py`
   - Credit: `teams/credit_team.py` → `agents/specialists/credit_agent.py`
   - Digital Account: `teams/digital_account_team.py` → `agents/specialists/digital_account_agent.py`
   - Investments: `teams/investments_team.py` → `agents/specialists/investments_agent.py`
   - Insurance: `teams/insurance_team.py` → `agents/specialists/insurance_agent.py`

4. **Move and adapt shared resources**
   - `teams/team_tools.py` → `agents/tools/agent_tools.py`
   - `teams/team_prompts.py` → `agents/prompts/specialist_prompts.py`
   - `teams/team_config.py` → Split into individual agent configs

5. **Update orchestrator**
   - Move `orchestrator/main_orchestrator.py` → `agents/orchestrator/main_orchestrator.py`
   - Update routing logic to point to single agents instead of teams
   - Change from team names to agent names in routing

6. **Update all imports** throughout the codebase
   - Search for `from teams.` and replace with `from agents.`
   - Update team references to agent references
   - Fix import paths in all Python files

7. **Clean up old structure**
   - Remove empty `/agents/` folder first (it's currently empty)
   - After verification, remove old `/teams/` folder
   - Keep backup in `legacy/teams/` temporarily

### Phase 4: Code Transformation Examples

**From Team to Agent - Example:**
```python
# OLD: teams/cards_team.py (complex)
class CardsTeam(BaseTeam):
    def __init__(self):
        members = [
            Agent(name="Cards Research Agent", ...),
            Agent(name="Cards Analysis Agent", ...),
            Agent(name="Cards Response Agent", ...)
        ]
        super().__init__(name="Time de Especialistas em Cartões", 
                         mode="coordinate", members=members)

# NEW: agents/specialists/cards_agent.py (simple)
class CardsAgent(BaseSpecialistAgent):
    def __init__(self):
        super().__init__(
            name="cards_specialist",
            tools=[search_knowledge, create_support_ticket],
            knowledge_filter={"department": "cards"}
        )
```

### Phase 5: Testing Requirements
- Run existing tests to ensure nothing breaks
- Test each specialist agent individually
- Test orchestrator routing to new agents
- Verify knowledge base access works
- Check memory persistence

### Phase 6: Documentation

## Benefits
- Clear separation of concerns
- Easy navigation for developers
- Consistent terminology
- Reflects actual architecture
- Scalable for future additions

## Risks & Mitigation
- **Risk**: Breaking existing functionality during migration
- **Mitigation**: Create comprehensive tests before migration, use git branches

## Implementation Checklist

- [ ] Create new agents folder structure
- [ ] Implement BaseSpecialistAgent class
- [ ] Convert CardsTeam to CardsAgent
- [ ] Convert CreditTeam to CreditAgent
- [ ] Convert DigitalAccountTeam to DigitalAccountAgent
- [ ] Convert InvestmentsTeam to InvestmentsAgent
- [ ] Convert InsuranceTeam to InsuranceAgent
- [ ] Update main orchestrator routing
- [ ] Move and adapt tools
- [ ] Move and adapt prompts
- [ ] Update all imports
- [ ] Test all functionality
- [ ] Remove old teams folder
- [ ] Update documentation

## Important Notes for Implementation

1. **Use UV for all Python operations** (never pip/python directly)
2. **Maintain Portuguese language support** throughout
3. **Keep fraud detection and compliance warnings**
4. **Test with existing playground.py** demo scenarios
5. **Preserve memory integration** with Agno Memory v2
6. **Keep knowledge base filtering** per specialist

## Expected Outcome

A clean, simple structure where:
- Each banking department has ONE specialist agent
- Main orchestrator routes directly to specialist agents
- No complex team coordination overhead
- Clear folder organization for humans
- Maintains all existing functionality

Co-Authored-By: Automagik Genie <genie@namastex.ai>