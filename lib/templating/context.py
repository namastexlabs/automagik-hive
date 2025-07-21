"""
Context Provider System for YAML Templating

Provides runtime context assembly for dynamic agent configuration including:
- User context (profile, preferences, permissions)
- Session context (current session data)
- Tenant context (organization settings)
- System context (environment, debug info)
"""

import os
import socket
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

try:
    from lib.logging import logger
except ImportError:
    try:
        from agno.utils.log import logger
    except ImportError:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """User-specific context data for template rendering."""
    user_id: str
    user_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    cpf: str | None = None
    permissions: list[str] | None = None
    preferences: dict[str, Any] | None = None
    subscription_type: str | None = None
    is_vip: bool = False
    language: str = "pt-BR"
    timezone: str = "America/Sao_Paulo"


@dataclass
class SessionContext:
    """Session-specific context data for template rendering."""
    session_id: str
    agent_id: str | None = None
    channel: str | None = None  # whatsapp, web, api
    started_at: datetime | None = None
    last_activity: datetime | None = None
    interaction_count: int = 0
    metadata: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class TenantContext:
    """Tenant/organization context data for template rendering."""
    tenant_id: str
    tenant_name: str | None = None
    business_units: list[str] | None = None
    enabled_features: list[str] | None = None
    subscription_type: str | None = None
    custom_settings: dict[str, Any] | None = None
    branding: dict[str, str] | None = None
    locale: str = "pt-BR"


@dataclass
class SystemContext:
    """System-level context data for template rendering."""
    environment: str
    debug_mode: bool
    hostname: str
    timestamp: datetime
    app_version: str | None = None
    feature_flags: dict[str, bool] | None = None
    region: str = "brazil-south"


class ContextProvider:
    """
    Provides runtime context assembly for template rendering.
    
    Builds comprehensive context dictionaries from various data sources
    including user profiles, session data, tenant settings, and system info.
    """

    def __init__(self):
        self.logger = logger

    def build_context(self, **kwargs) -> dict[str, Any]:
        """
        Build complete context dictionary for template rendering.
        
        Args:
            **kwargs: Context parameters including user_id, session_id, etc.
            
        Returns:
            Complete context dictionary with user, session, tenant, and system contexts
        """
        try:
            context = {
                "user_context": self._build_user_context(kwargs),
                "session_context": self._build_session_context(kwargs),
                "tenant_context": self._build_tenant_context(kwargs),
                "system_context": self._build_system_context(kwargs)
            }

            # Add any additional custom context
            custom_context = kwargs.get("custom_context", {})
            if custom_context:
                context["custom_context"] = custom_context

            self.logger.debug(f"🎯 Built context for user: {kwargs.get('user_id', 'unknown')}")
            return context

        except Exception as e:
            self.logger.error(f"🚨 Context building failed: {e!s}")
            return self._build_minimal_context(kwargs)

    def _build_user_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build user context from provided parameters and data sources."""
        user_id = kwargs.get("user_id")
        if not user_id:
            return {}

        # Build from kwargs first (for immediate usage)
        user_context = UserContext(
            user_id=user_id,
            user_name=kwargs.get("user_name"),
            email=kwargs.get("email"),
            phone_number=kwargs.get("phone_number"),
            cpf=kwargs.get("cpf"),
            permissions=kwargs.get("permissions", []),
            preferences=kwargs.get("preferences", {}),
            subscription_type=kwargs.get("subscription_type", "basic"),
            is_vip=kwargs.get("is_vip", False),
            language=kwargs.get("language", "pt-BR"),
            timezone=kwargs.get("timezone", "America/Sao_Paulo")
        )

        # TODO: Enhance with database lookup
        # user_data = self._fetch_user_from_db(user_id)
        # if user_data:
        #     user_context = self._merge_user_data(user_context, user_data)

        return asdict(user_context)

    def _build_session_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build session context from provided parameters."""
        session_id = kwargs.get("session_id", f"session_{datetime.now().timestamp()}")

        session_context = SessionContext(
            session_id=session_id,
            agent_id=kwargs.get("agent_id"),
            channel=kwargs.get("channel", "api"),
            started_at=kwargs.get("started_at", datetime.now()),
            last_activity=datetime.now(),
            interaction_count=kwargs.get("interaction_count", 0),
            metadata=kwargs.get("session_metadata", {}),
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent")
        )

        return asdict(session_context)

    def _build_tenant_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build tenant context from provided parameters."""
        tenant_id = kwargs.get("tenant_id", "default")

        tenant_context = TenantContext(
            tenant_id=tenant_id,
            tenant_name=kwargs.get("tenant_name", "Automagik Hive"),
            business_units=kwargs.get("business_units", ["customer_service"]),
            enabled_features=kwargs.get("enabled_features", ["basic_chat", "classification"]),
            subscription_type=kwargs.get("tenant_subscription", "enterprise"),
            custom_settings=kwargs.get("tenant_settings", {}),
            branding=kwargs.get("branding", {"primary_color": "#007bff"}),
            locale=kwargs.get("locale", "pt-BR")
        )

        return asdict(tenant_context)

    def _build_system_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build system context from environment and runtime info."""
        system_context = SystemContext(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug_mode=kwargs.get("debug_mode", os.getenv("DEBUG", "false").lower() == "true"),
            hostname=socket.gethostname(),
            timestamp=datetime.now(),
            app_version=kwargs.get("app_version", "1.0.0"),
            feature_flags=kwargs.get("feature_flags", {}),
            region=kwargs.get("region", "brazil-south")
        )

        return asdict(system_context)

    def _build_minimal_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build minimal fallback context when full context building fails."""
        return {
            "user_context": {"user_id": kwargs.get("user_id", "unknown")},
            "session_context": {"session_id": kwargs.get("session_id", "unknown")},
            "tenant_context": {"tenant_id": kwargs.get("tenant_id", "default")},
            "system_context": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "debug_mode": False,
                "timestamp": datetime.now().isoformat()
            }
        }

    def get_user_context(self, user_id: str, **kwargs) -> dict[str, Any]:
        """Get user context only."""
        kwargs["user_id"] = user_id
        return self._build_user_context(kwargs)

    def get_session_context(self, session_id: str, **kwargs) -> dict[str, Any]:
        """Get session context only."""
        kwargs["session_id"] = session_id
        return self._build_session_context(kwargs)

    def get_tenant_context(self, tenant_id: str, **kwargs) -> dict[str, Any]:
        """Get tenant context only."""
        kwargs["tenant_id"] = tenant_id
        return self._build_tenant_context(kwargs)

    def get_system_context(self, **kwargs) -> dict[str, Any]:
        """Get system context only."""
        return self._build_system_context(kwargs)


# Template helper functions for Jinja2
def format_phone(phone: str) -> str:
    """Format phone number for display."""
    if not phone:
        return ""

    # Remove all non-digits
    digits = "".join(filter(str.isdigit, phone))

    # Format Brazilian phone numbers
    if len(digits) == 13 and digits.startswith("55"):  # With country code: 5511999887766
        # Remove country code and format: (11) 99988-7766
        local_digits = digits[2:]
        if len(local_digits) == 11:  # Mobile
            return f"({local_digits[:2]}) {local_digits[2:7]}-{local_digits[7:]}"
        if len(local_digits) == 10:  # Landline
            return f"({local_digits[:2]}) {local_digits[2:6]}-{local_digits[6:]}"
    elif len(digits) == 11:  # Mobile without country code: (11) 99999-9999
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:  # Landline without country code: (11) 9999-9999
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"

    return phone  # Return original if unknown format


def format_cpf(cpf: str) -> str:
    """Format CPF for display."""
    if not cpf:
        return ""

    # Remove all non-digits
    digits = "".join(filter(str.isdigit, cpf))

    # Format CPF: 123.456.789-01
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return cpf  # Return original if invalid


def mask_sensitive(value: str, mask_char: str = "*", visible_chars: int = 3) -> str:
    """Mask sensitive information."""
    if not value or len(value) <= visible_chars:
        return value

    return value[:visible_chars] + mask_char * (len(value) - visible_chars)


# Export template helper functions for use in Jinja2
TEMPLATE_HELPERS = {
    "format_phone": format_phone,
    "format_cpf": format_cpf,
    "mask_sensitive": mask_sensitive,
}
