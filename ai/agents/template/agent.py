"""
Template Agent Factory - Minimal Pattern with Custom Logic Examples
Copy this pattern for new agents and add custom logic only when needed.
"""

from lib.utils.version_factory import create_agent
from datetime import datetime


async def get_template_agent(**kwargs):
    """Template agent factory - add custom logic here if needed"""
    
    # CUSTOM LOGIC EXAMPLES (uncomment/modify as needed):
    
    # # Example 1: Subscription-based model selection  
    # if kwargs.get("user_context", {}).get("subscription") == "pro":
    #     kwargs["model_override"] = "claude-opus-3-20240229"
    
    # # Example 2: Risk-based adjustments
    # if kwargs.get("transaction_amount", 0) > 50000:
    #     kwargs["temperature_override"] = 0.01  # More conservative
    #     kwargs["instructions_append"] = "\nATENÇÃO: Alto valor - seja cauteloso"
    
    # # Example 3: Geographic compliance
    # user_state = kwargs.get("user_context", {}).get("state")
    # if user_state == "SP":
    #     kwargs["instructions_append"] = "\nAplique regras ICMS-SP"
    
    # # Example 4: Time-based behavior
    # current_hour = datetime.now().hour
    # if 18 <= current_hour or current_hour <= 6:  # After hours
    #     kwargs["temperature_override"] = 0.3
    #     kwargs["instructions_append"] = "\nHorário fora comercial - priorize urgências"
    
    # # Example 5: User experience level
    # experience = kwargs.get("user_context", {}).get("experience_level")
    # if experience == "expert":
    #     kwargs["instructions_append"] = "\nUsuário expert - seja técnico e direto"
    # elif experience == "novice":
    #     kwargs["instructions_append"] = "\nUsuário iniciante - explique termos técnicos"
    
    return await create_agent("template", **kwargs)