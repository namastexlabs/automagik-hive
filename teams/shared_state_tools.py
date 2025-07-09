"""
Shared State Tools for PagBank Multi-Agent System
Tools for agents to modify team_session_state for coordination
"""

from datetime import datetime
from typing import Any, Dict, Union

from agno.agent import Agent
from agno.team import Team
from agno.tools.decorator import tool


@tool
def update_research_findings(agent: Agent, findings: Dict[str, Any]) -> str:
    """Update shared research findings
    
    Args:
        agent: Agent making the update
        findings: Research findings to add
    """
    if "research_findings" not in agent.team_session_state:
        agent.team_session_state["research_findings"] = []
    
    agent.team_session_state["research_findings"].append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent.name,
        "findings": findings
    })
    return f"Research findings updated by {agent.name}: {findings.get('summary', 'No summary provided')}"


@tool
def set_escalation_flag(agent: Agent, flag_type: str, details: str) -> str:
    """Set escalation flag in shared state
    
    Args:
        agent: Agent setting the flag
        flag_type: Type of escalation (security, technical, fraud, etc.)
        details: Details about the escalation
    """
    if "escalation_flags" not in agent.team_session_state:
        agent.team_session_state["escalation_flags"] = {}
    
    agent.team_session_state["escalation_flags"][flag_type] = {
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "agent": agent.name,
        "severity": "high" if flag_type in ["fraud", "security"] else "medium"
    }
    return f"Escalation flag '{flag_type}' set by {agent.name}: {details}"


@tool
def add_customer_insight(agent: Union[Agent, Team], insight: str, confidence: float) -> str:
    """Add customer insight to shared analysis
    
    Args:
        agent: Agent or Team adding the insight
        insight: Customer insight discovered
        confidence: Confidence level (0-1)
    """
    # Handle both Agent and Team contexts
    if isinstance(agent, Team):
        session_state = agent.team_session_state
        name = agent.name
    else:
        session_state = agent.team_session_state
        name = agent.name
    
    if "customer_analysis" not in session_state:
        session_state["customer_analysis"] = {}
    
    session_state["customer_analysis"][name] = {
        "insight": insight,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }
    return f"Customer insight added by {name} (confidence: {confidence:.2f}): {insight}"


@tool
def record_team_decision(agent: Agent, decision: str, reasoning: str) -> str:
    """Record team decision with reasoning
    
    Args:
        agent: Agent recording the decision
        decision: Decision made
        reasoning: Reasoning behind the decision
    """
    if "team_decisions" not in agent.team_session_state:
        agent.team_session_state["team_decisions"] = []
    
    agent.team_session_state["team_decisions"].append({
        "decision": decision,
        "reasoning": reasoning,
        "agent": agent.name,
        "timestamp": datetime.now().isoformat()
    })
    return f"Team decision recorded by {agent.name}: {decision}"


@tool
def share_context_with_team(agent: Agent, context_type: str, context_data: Dict[str, Any]) -> str:
    """Share context information with team
    
    Args:
        agent: Agent sharing context
        context_type: Type of context (customer_profile, transaction_history, etc.)
        context_data: Context data to share
    """
    if "context_sharing" not in agent.team_session_state:
        agent.team_session_state["context_sharing"] = {}
    
    if context_type not in agent.team_session_state["context_sharing"]:
        agent.team_session_state["context_sharing"][context_type] = []
    
    agent.team_session_state["context_sharing"][context_type].append({
        "data": context_data,
        "agent": agent.name,
        "timestamp": datetime.now().isoformat()
    })
    return f"Context '{context_type}' shared by {agent.name}"


@tool
def update_interaction_flow(agent: Agent, step: str, outcome: str) -> str:
    """Update interaction flow tracking
    
    Args:
        agent: Agent updating the flow
        step: Current step in the interaction
        outcome: Outcome of the step
    """
    if "interaction_flow" not in agent.team_session_state:
        agent.team_session_state["interaction_flow"] = []
    
    agent.team_session_state["interaction_flow"].append({
        "step": step,
        "outcome": outcome,
        "agent": agent.name,
        "timestamp": datetime.now().isoformat()
    })
    return f"Interaction flow updated by {agent.name}: {step} -> {outcome}"


@tool
def get_team_context(team: Team) -> str:
    """Get current team context summary
    
    Args:
        team: Team to get context for
    """
    state = team.team_session_state
    
    # Handle None state gracefully
    if state is None:
        state = {}
    
    research_count = len(state.get('research_findings', []))
    decisions_count = len(state.get('team_decisions', []))
    escalation_flags = list(state.get('escalation_flags', {}).keys())
    insights_count = len(state.get('customer_analysis', {}))
    context_types = list(state.get('context_sharing', {}).keys())
    flow_steps = len(state.get('interaction_flow', []))
    
    summary = f"""Team Context Summary for {team.name}:
• Research Findings: {research_count} items
• Team Decisions: {decisions_count} decisions  
• Escalation Flags: {escalation_flags if escalation_flags else 'None'}
• Customer Insights: {insights_count} insights
• Shared Context: {context_types if context_types else 'None'}
• Interaction Steps: {flow_steps} steps"""
    
    return summary


@tool
def get_escalation_status(team: Team) -> str:
    """Get current escalation status
    
    Args:
        team: Team to check escalation status for
    """
    flags = team.team_session_state.get('escalation_flags', {})
    
    if not flags:
        return "No escalation flags currently set"
    
    status = "Current Escalation Flags:\n"
    for flag_type, flag_data in flags.items():
        severity = flag_data.get('severity', 'unknown')
        agent = flag_data.get('agent', 'unknown')
        details = flag_data.get('details', 'No details')
        status += f"• {flag_type.upper()} ({severity}) by {agent}: {details}\n"
    
    return status.strip()


@tool
def clear_escalation_flag(agent: Agent, flag_type: str) -> str:
    """Clear a specific escalation flag
    
    Args:
        agent: Agent clearing the flag
        flag_type: Type of escalation flag to clear
    """
    flags = agent.team_session_state.get('escalation_flags', {})
    
    if flag_type in flags:
        del agent.team_session_state['escalation_flags'][flag_type]
        return f"Escalation flag '{flag_type}' cleared by {agent.name}"
    else:
        return f"Escalation flag '{flag_type}' not found"