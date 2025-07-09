"""
State Synchronizer for PagBank Multi-Agent System
Handles state synchronization between orchestrator and specialist teams
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


class TeamStateSynchronizer:
    """Manages state synchronization between orchestrator and teams"""
    
    def __init__(self, orchestrator):
        """Initialize state synchronizer
        
        Args:
            orchestrator: Main orchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("pagbank.state_synchronizer")
    
    def sync_team_state(self, team_name: str, team_state: Dict[str, Any]) -> bool:
        """Synchronize team state with orchestrator
        
        Args:
            team_name: Name of the team
            team_state: Current team state to sync
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            if hasattr(self.orchestrator.routing_team, 'team_session_state'):
                if "team_states" not in self.orchestrator.routing_team.team_session_state:
                    self.orchestrator.routing_team.team_session_state["team_states"] = {}
                
                self.orchestrator.routing_team.team_session_state["team_states"][team_name] = {
                    "state": team_state,
                    "last_updated": datetime.now().isoformat(),
                    "sync_version": self._get_sync_version(team_name)
                }
                
                self.logger.info(f"Successfully synced state for team: {team_name}")
                return True
            else:
                self.logger.warning("Orchestrator routing team has no team_session_state")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to sync state for team {team_name}: {str(e)}")
            return False
    
    def get_cross_team_context(self) -> Dict[str, Any]:
        """Get context from all teams
        
        Returns:
            Dictionary containing context from all teams
        """
        try:
            if hasattr(self.orchestrator.routing_team, 'team_session_state'):
                return self.orchestrator.routing_team.team_session_state.get("team_states", {})
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get cross-team context: {str(e)}")
            return {}
    
    def propagate_customer_context(self, customer_context: Dict[str, Any]) -> int:
        """Propagate customer context to all teams
        
        Args:
            customer_context: Customer context to propagate
            
        Returns:
            Number of teams that received the context
        """
        propagated_count = 0
        
        try:
            for team_name, team in self.orchestrator.specialist_teams.items():
                if hasattr(team, 'team_session_state'):
                    team.team_session_state["shared_customer_context"] = {
                        "context": customer_context,
                        "timestamp": datetime.now().isoformat(),
                        "source": "orchestrator"
                    }
                    propagated_count += 1
                    self.logger.debug(f"Propagated customer context to team: {team_name}")
            
            self.logger.info(f"Customer context propagated to {propagated_count} teams")
            return propagated_count
            
        except Exception as e:
            self.logger.error(f"Failed to propagate customer context: {str(e)}")
            return propagated_count
    
    def get_team_insights(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Get insights from a specific team
        
        Args:
            team_name: Name of the team to get insights from
            
        Returns:
            Team insights or None if not found
        """
        try:
            team_states = self.get_cross_team_context()
            if team_name in team_states:
                team_data = team_states[team_name]["state"]
                return {
                    "research_findings": team_data.get("research_findings", []),
                    "customer_analysis": team_data.get("customer_analysis", {}),
                    "escalation_flags": team_data.get("escalation_flags", {}),
                    "team_decisions": team_data.get("team_decisions", []),
                    "last_updated": team_states[team_name]["last_updated"]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get insights for team {team_name}: {str(e)}")
            return None
    
    def check_escalation_status(self) -> Dict[str, Any]:
        """Check escalation status across all teams
        
        Returns:
            Escalation status summary
        """
        escalation_summary = {
            "has_escalations": False,
            "escalation_count": 0,
            "critical_flags": [],
            "teams_with_escalations": []
        }
        
        try:
            team_states = self.get_cross_team_context()
            
            for team_name, team_data in team_states.items():
                team_state = team_data["state"]
                escalation_flags = team_state.get("escalation_flags", {})
                
                if escalation_flags:
                    escalation_summary["has_escalations"] = True
                    escalation_summary["teams_with_escalations"].append(team_name)
                    
                    for flag_type, flag_data in escalation_flags.items():
                        escalation_summary["escalation_count"] += 1
                        
                        if flag_data.get("severity") == "high":
                            escalation_summary["critical_flags"].append({
                                "team": team_name,
                                "type": flag_type,
                                "details": flag_data.get("details", ""),
                                "timestamp": flag_data.get("timestamp", "")
                            })
            
            return escalation_summary
            
        except Exception as e:
            self.logger.error(f"Failed to check escalation status: {str(e)}")
            return escalation_summary
    
    def get_customer_journey(self) -> List[Dict[str, Any]]:
        """Get complete customer interaction journey across teams
        
        Returns:
            List of interaction steps across all teams
        """
        journey = []
        
        try:
            # Get orchestrator routing history
            if hasattr(self.orchestrator.routing_team, 'team_session_state'):
                routing_decisions = self.orchestrator.routing_team.team_session_state.get("routing_decisions", [])
                for decision in routing_decisions:
                    journey.append({
                        "type": "routing",
                        "team": "orchestrator",
                        "action": "route_decision",
                        "details": decision,
                        "timestamp": decision.get("timestamp", "")
                    })
            
            # Get team interaction flows
            team_states = self.get_cross_team_context()
            for team_name, team_data in team_states.items():
                team_state = team_data["state"]
                interaction_flow = team_state.get("interaction_flow", [])
                
                for step in interaction_flow:
                    journey.append({
                        "type": "team_interaction",
                        "team": team_name,
                        "action": step.get("step", ""),
                        "outcome": step.get("outcome", ""),
                        "agent": step.get("agent", ""),
                        "timestamp": step.get("timestamp", "")
                    })
            
            # Sort by timestamp
            journey.sort(key=lambda x: x.get("timestamp", ""))
            return journey
            
        except Exception as e:
            self.logger.error(f"Failed to get customer journey: {str(e)}")
            return journey
    
    def _get_sync_version(self, team_name: str) -> int:
        """Get sync version for a team
        
        Args:
            team_name: Name of the team
            
        Returns:
            Current sync version number
        """
        try:
            team_states = self.get_cross_team_context()
            if team_name in team_states:
                return team_states[team_name].get("sync_version", 0) + 1
            return 1
        except:
            return 1
    
    def reset_team_state(self, team_name: str) -> bool:
        """Reset state for a specific team
        
        Args:
            team_name: Name of the team to reset
            
        Returns:
            True if reset successful, False otherwise
        """
        try:
            if team_name in self.orchestrator.specialist_teams:
                team = self.orchestrator.specialist_teams[team_name]
                if hasattr(team, 'team_session_state'):
                    # Reset to initial state
                    team.team_session_state.clear()
                    team.team_session_state.update({
                        "customer_analysis": {},
                        "research_findings": [],
                        "team_decisions": [],
                        "escalation_flags": {},
                        "context_sharing": {},
                        "interaction_flow": [],
                        "quality_metrics": {}
                    })
                    
                    # Update orchestrator state
                    self.sync_team_state(team_name, team.team_session_state)
                    
                    self.logger.info(f"Reset state for team: {team_name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to reset state for team {team_name}: {str(e)}")
            return False