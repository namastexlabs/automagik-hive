"""
Genie Security Agent - Fortress Protection Security Scanner

This agent provides comprehensive security vulnerability scanning and remediation
through Bandit code analysis, dependency auditing, and security best practices
enforcement with enhanced memory management for persistent security context.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_security_agent(**kwargs: Any) -> Agent:
    """
    Create genie security agent with enhanced memory and state management.

    This factory function creates a specialized security agent that provides:

    - Comprehensive security vulnerability scanning using Bandit
    - Dependency vulnerability auditing with pip-audit and safety
    - Security best practices enforcement and pattern recognition
    - Enhanced memory management for persistent security analysis context
    - MCP tool integration for security task management and data storage

    Enhanced Memory Features:
    - 30 conversation history runs for security pattern recognition
    - 180-day memory retention for long-term security trend analysis
    - Agentic memory for intelligent security context management
    - Persistent storage of vulnerability remediation patterns

    Security Analysis Capabilities:
    - OWASP Top 10 vulnerability detection and remediation
    - Code vulnerability scanning with Bandit integration
    - Dependency CVE auditing and safety validation
    - Authentication and authorization security validation
    - Data protection and encryption compliance checking
    - Attack surface analysis and threat modeling

    Args:
        **kwargs: Context parameters for security agent configuration including:
            - user_id: User identifier for security context tracking
            - session_id: Session identifier for security audit continuity
            - project_context: Project-specific security requirements
            - security_level: Required security compliance level
            - audit_scope: Scope of security analysis (code, dependencies, config)
            - threat_model: Specific threat model for targeted analysis
            - compliance_requirements: Regulatory compliance needs (SOC2, HIPAA, etc.)
            - custom_context: Additional security-specific template variables

    Returns:
        Agent instance with enhanced security scanning capabilities and memory management

    Example Usage:
        # Basic security audit
        agent = await get_genie_security_agent(
            user_id="security_team",
            project_context="web_application",
            security_level="enterprise"
        )

        # Comprehensive security analysis with compliance
        agent = await get_genie_security_agent(
            user_id="compliance_officer",
            session_id="audit_2025_01",
            project_context="financial_platform",
            security_level="critical",
            audit_scope=["code", "dependencies", "infrastructure"],
            threat_model="financial_services",
            compliance_requirements=["SOC2", "PCI_DSS"],
            custom_context={
                "regulatory_framework": "financial_services",
                "data_classification": "sensitive_financial"
            }
        )

        # Vulnerability remediation tracking
        agent = await get_genie_security_agent(
            user_id="developer",
            session_id="vuln_fix_session",
            project_context="api_service",
            audit_scope=["code_vulnerabilities"],
            custom_context={
                "focus_area": "injection_prevention",
                "priority_level": "high"
            }
        )
    """
    return await create_agent("genie_security", **kwargs)