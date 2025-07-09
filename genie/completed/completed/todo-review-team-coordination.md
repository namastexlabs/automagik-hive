# Task: Review Team Coordination Mode Usage

## Objective
Validate that Team coordination modes (coordinate vs route) are used correctly according to Agno Team patterns and best practices.

## Instructions
1. **Study Agno Team documentation** using `mcp__search-repo-docs__get-library-docs`:
   - Search for Team coordination mode examples
   - Find route mode vs coordinate mode usage patterns
   - Understand team_session_state management
   - Learn about member interaction patterns

2. **Analyze routing team implementation** in `orchestrator/main_orchestrator.py`:
   - Validate `mode="route"` usage
   - Check member configuration
   - Review routing logic implementation
   - Verify session state management

3. **Review specialist team coordination** in:
   - `teams/base_team.py` - Base coordinate mode setup
   - `teams/cards_team.py` - Cards team coordination
   - `teams/digital_account_team.py` - Digital account coordination
   - `teams/investments_team.py` - Investment team coordination
   - `teams/credit_team.py` - Credit team coordination
   - `teams/insurance_team.py` - Insurance team coordination

4. **Validate team configuration patterns**:
   - Agent member creation and roles
   - Team instruction formatting
   - Context sharing between agents
   - Response model usage (TeamResponse)
   - Error handling in coordination

5. **Check coordination vs routing logic**:
   - When to use coordinate mode vs route mode
   - Team member interaction patterns
   - Context preservation across team operations
   - Performance implications of each mode

6. **Review team session management**:
   - team_session_state usage
   - State persistence across interactions
   - Context sharing between teams
   - Session cleanup procedures

## Completion Criteria
- All team modes validated against Agno patterns
- Coordinate vs route mode usage verified as correct
- Team configuration improvements identified
- Session state management validated
- Performance optimization recommendations

## Dependencies
- Access to Agno Team documentation
- All team implementation files completed
- Understanding of Agno coordination patterns