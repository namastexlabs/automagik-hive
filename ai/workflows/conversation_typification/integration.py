"""
Integration module for connecting typification workflow with Ana team router
Handles post-conversation typification and agent routing based on results
"""

from typing import Dict, Optional, Any
from lib.logging import logger

from .workflow import get_conversation_typification_workflow, ConversationTypificationWorkflow

class TypificationIntegration:
    """Integration layer for typification workflow with Ana team"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.workflow: Optional[ConversationTypificationWorkflow] = None
        self._initialize_workflow()
    
    def _initialize_workflow(self):
        """Initialize the typification workflow"""
        try:
            self.workflow = get_conversation_typification_workflow(debug_mode=self.debug_mode)
            logger.info("🔄 Typification workflow initialized successfully")
        except Exception as e:
            logger.error(f"🔄 Failed to initialize typification workflow: {e}")
            raise
    
    def run_post_conversation_typification(
        self,
        session_id: str,
        conversation_history: str,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run typification workflow after conversation completion
        
        Args:
            session_id: Unique session identifier
            conversation_history: Complete conversation text
            customer_id: Customer identifier if available
            metadata: Additional conversation metadata
            
        Returns:
            Typification result or None if failed
        """
        
        if not self.workflow:
            logger.error("🔄 Typification workflow not initialized")
            return None
        
        try:
            logger.info(f"🔄 Starting post-conversation typification for session {session_id}")
            
            # Run the workflow
            results = list(self.workflow.run(
                session_id=session_id,
                conversation_history=conversation_history,
                customer_id=customer_id,
                metadata=metadata
            ))
            
            if not results:
                logger.warning(f"🔄 No results from typification workflow for session {session_id}")
                return None
            
            # Get the last result (should be RunResponse with workflow_completed event)
            result = results[-1]
            
            if hasattr(result, 'content') and result.content.get('status') == 'completed':
                logger.info(f"🔄 Typification completed successfully: {result.content['hierarchy_path']}")
                return result.content
            else:
                logger.error(f"🔄 Typification failed: {result.content}")
                return None
                
        except Exception as e:
            logger.error(f"🔄 Error in post-conversation typification: {e}")
            return None
    
    def get_agent_routing_suggestions(
        self, 
        typification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get agent routing suggestions based on typification results
        
        Args:
            typification_result: Result from typification workflow
            
        Returns:
            Routing suggestions with team and priority
        """
        
        if not typification_result or 'typification' not in typification_result:
            return {
                'suggested_team': 'general_support',
                'priority': 'medium',
                'routing_reason': 'No typification data available'
            }
        
        typification = typification_result['typification']
        business_unit = typification.get('unidade_negocio', '')
        product = typification.get('produto', '')
        motive = typification.get('motivo', '')
        
        # Business unit to team mapping
        team_mapping = {
            'Adquirência Web': 'adquirencia_team',
            'Adquirência Web / Adquirência Presencial': 'adquirencia_team',
            'Emissão': 'emissao_team',
            'PagBank': 'pagbank_team'
        }
        
        # Priority mapping based on motive keywords
        high_priority_keywords = ['bloqueio', 'fraude', 'perda', 'roubo', 'urgente']
        medium_priority_keywords = ['dúvida', 'orientação', 'informação']
        
        # Determine team
        suggested_team = team_mapping.get(business_unit, 'general_support')
        
        # Determine priority
        priority = 'low'
        motive_lower = motive.lower()
        
        if any(keyword in motive_lower for keyword in high_priority_keywords):
            priority = 'high'
        elif any(keyword in motive_lower for keyword in medium_priority_keywords):
            priority = 'medium'
        
        # Special cases for specific products
        if product == 'Pix' and 'problema' in motive_lower:
            priority = 'high'
        elif product.startswith('Cartão') and 'bloqueio' in motive_lower:
            priority = 'high'
        
        return {
            'suggested_team': suggested_team,
            'priority': priority,
            'routing_reason': f"Based on {business_unit} → {product} → {motive}",
            'confidence_scores': typification_result.get('confidence_scores', {}),
            'hierarchy_path': typification_result.get('hierarchy_path', '')
        }
    
    def create_escalation_context(
        self,
        typification_result: Dict[str, Any],
        conversation_history: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Create escalation context for human handoff
        
        Args:
            typification_result: Result from typification workflow
            conversation_history: Original conversation
            session_id: Session identifier
            
        Returns:
            Context for human agent escalation
        """
        
        if not typification_result or 'typification' not in typification_result:
            return {
                'escalation_reason': 'Typification failed',
                'session_id': session_id,
                'conversation_history': conversation_history,
                'suggested_actions': ['Manual review required']
            }
        
        typification = typification_result['typification']
        
        # Extract key information
        business_unit = typification.get('unidade_negocio', 'Unknown')
        product = typification.get('produto', 'Unknown')
        motive = typification.get('motivo', 'Unknown')
        submotive = typification.get('submotivo', 'Unknown')
        
        # Generate context
        context = {
            'escalation_reason': 'Automatic typification completed',
            'session_id': session_id,
            'business_unit': business_unit,
            'product': product,
            'motive': motive,
            'submotive': submotive,
            'hierarchy_path': typification_result.get('hierarchy_path', ''),
            'confidence_scores': typification_result.get('confidence_scores', {}),
            'resolution_time': typification_result.get('resolution_time_minutes', 0),
            'ticket_id': typification_result.get('ticket', {}).get('ticket_id', ''),
            'conversation_summary': self._extract_conversation_summary(conversation_history),
            'suggested_actions': self._generate_suggested_actions(typification),
            'conversation_history': conversation_history
        }
        
        return context
    
    def _extract_conversation_summary(self, conversation_history: str) -> str:
        """Extract a brief summary from conversation history"""
        lines = conversation_history.split('\n')
        relevant_lines = [line for line in lines if line.strip()]
        
        if len(relevant_lines) <= 3:
            return ' '.join(relevant_lines)
        
        # Get first and last few lines
        summary_lines = relevant_lines[:2] + ['...'] + relevant_lines[-2:]
        return ' '.join(summary_lines)
    
    def _generate_suggested_actions(self, typification: Dict[str, Any]) -> list:
        """Generate suggested actions based on typification"""
        
        actions = []
        
        business_unit = typification.get('unidade_negocio', '')
        product = typification.get('produto', '')
        motive = typification.get('motivo', '')
        
        # General actions
        actions.append(f"Review {business_unit} procedures")
        actions.append(f"Check {product} specific guidelines")
        
        # Specific actions based on motive
        if 'dúvida' in motive.lower():
            actions.append("Provide detailed explanation")
            actions.append("Share relevant documentation")
        elif 'problema' in motive.lower():
            actions.append("Investigate technical issue")
            actions.append("Escalate to technical support if needed")
        elif 'bloqueio' in motive.lower():
            actions.append("Check security protocols")
            actions.append("Verify customer identity")
        
        return actions
    
    def validate_typification_quality(
        self, 
        typification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate the quality of typification results
        
        Args:
            typification_result: Result from typification workflow
            
        Returns:
            Quality assessment with recommendations
        """
        
        quality_issues = []
        recommendations = []
        
        if not typification_result:
            return {
                'quality_score': 0.0,
                'issues': ['No typification result available'],
                'recommendations': ['Retry typification process']
            }
        
        # Check confidence scores
        confidence_scores = typification_result.get('confidence_scores', {})
        
        low_confidence_threshold = 0.7
        low_confidence_levels = [
            level for level, score in confidence_scores.items() 
            if score < low_confidence_threshold
        ]
        
        if low_confidence_levels:
            quality_issues.append(f"Low confidence in: {', '.join(low_confidence_levels)}")
            recommendations.append("Consider manual review for low confidence classifications")
        
        # Check for missing data
        required_fields = ['typification', 'hierarchy_path', 'confidence_scores']
        missing_fields = [field for field in required_fields if field not in typification_result]
        
        if missing_fields:
            quality_issues.append(f"Missing required fields: {', '.join(missing_fields)}")
            recommendations.append("Ensure all workflow steps complete successfully")
        
        # Check resolution time
        resolution_time = typification_result.get('resolution_time_minutes', 0)
        if resolution_time > 5:  # 5 minutes threshold
            quality_issues.append(f"High resolution time: {resolution_time:.1f} minutes")
            recommendations.append("Optimize workflow performance")
        
        # Calculate overall quality score
        base_score = 1.0
        
        # Deduct for issues
        confidence_penalty = len(low_confidence_levels) * 0.1
        missing_data_penalty = len(missing_fields) * 0.2
        time_penalty = max(0, (resolution_time - 5) * 0.05)
        
        quality_score = max(0.0, base_score - confidence_penalty - missing_data_penalty - time_penalty)
        
        return {
            'quality_score': round(quality_score, 2),
            'issues': quality_issues,
            'recommendations': recommendations,
            'confidence_scores': confidence_scores,
            'resolution_time_minutes': resolution_time
        }

# Global integration instance
_integration_instance: Optional[TypificationIntegration] = None

def get_typification_integration(debug_mode: bool = False) -> TypificationIntegration:
    """Get or create typification integration instance"""
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = TypificationIntegration(debug_mode=debug_mode)
    
    return _integration_instance

def run_post_conversation_typification(
    session_id: str,
    conversation_history: str,
    customer_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Convenience function for running post-conversation typification
    
    Args:
        session_id: Session identifier
        conversation_history: Complete conversation text
        customer_id: Customer identifier if available
        metadata: Additional conversation metadata
        
    Returns:
        Typification result or None if failed
    """
    
    integration = get_typification_integration()
    return integration.run_post_conversation_typification(
        session_id=session_id,
        conversation_history=conversation_history,
        customer_id=customer_id,
        metadata=metadata
    )