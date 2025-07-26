"""
Template Example Agent - YAML Templating Demonstration

This agent demonstrates the full capabilities of the YAML templating system
including context injection, conditional logic, and personalized configuration.
"""

from lib.utils.version_factory import create_agent


async def get_template_example_agent(**kwargs):
    """
    Create template example agent with dynamic configuration.

    This factory function demonstrates how agents can be created with
    context-aware templating that personalizes the agent based on:

    - User context (name, permissions, subscription)
    - Session context (channel, metadata)
    - System context (environment, debug mode)
    - Tenant context (features, branding)

    Args:
        **kwargs: Context parameters for template rendering including:
            - user_id: User identifier for context loading
            - user_name: Display name for personalization
            - email: User email address
            - phone_number: Contact phone (formatted in templates)
            - permissions: List of user permissions
            - subscription_type: User subscription level (basic, pro, enterprise)
            - is_vip: VIP status flag
            - session_id: Session identifier
            - channel: Communication channel (whatsapp, web, api)
            - debug_mode: Enable debug features
            - tenant_id: Tenant/organization identifier
            - custom_context: Additional template variables

    Returns:
        Agent instance with rendered configuration based on provided context

    Example Usage:
        # Basic usage
        agent = get_template_example_agent(
            user_name="João Silva",
            user_id="user_123",
            subscription_type="pro"
        )

        # Advanced usage with full context
        agent = get_template_example_agent(
            user_name="Maria Santos",
            user_id="user_456",
            email="maria@example.com",
            phone_number="5511999887766",
            permissions=["read", "write", "admin"],
            subscription_type="enterprise",
            is_vip=True,
            session_id="sess_789",
            channel="whatsapp",
            debug_mode=True,
            tenant_id="company_abc",
            custom_context={
                "company_name": "Empresa XYZ",
                "support_level": "premium"
            }
        )
    """
    return await create_agent("template_example", **kwargs)
