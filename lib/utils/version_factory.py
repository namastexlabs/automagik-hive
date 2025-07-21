"""
Agno-Based Version Factory

Clean implementation using Agno storage for component versioning.
Replaces the old database-based version factory.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path
import yaml
import os
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

from lib.versioning import AgnoVersionService
# Knowledge base creation is now handled by Agno CSVKnowledgeBase + PgVector directly

from datetime import datetime
from typing import Callable


def load_global_knowledge_config():
    """Load global knowledge configuration with fallback"""
    try:
        global_config_path = Path(__file__).parent.parent / "knowledge/config.yaml"
        with open(global_config_path) as f:
            global_config = yaml.safe_load(f)
        return global_config.get("knowledge", {})
    except Exception as e:
        logger.warning("🔧 Could not load global knowledge config: %s", e)
        return {
            "csv_file_path": "knowledge_rag.csv",
            "max_results": 10,
            "enable_hot_reload": True
        }


class VersionFactory:
    """
    Clean version factory using Agno storage.
    Creates versioned components with modern patterns.
    """
    
    def __init__(self):
        """Initialize with database URL from environment."""
        self.db_url = os.getenv("HIVE_DATABASE_URL")
        if not self.db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable required")
        
        self.version_service = AgnoVersionService(self.db_url)
    
    def _create_context_functions(self, user_id: Optional[str] = None, session_id: Optional[str] = None, 
                                debug_mode: bool = False, **context_kwargs) -> Dict[str, Callable]:
        """Create AGNO native context functions to replace templating variables"""
        context = {}
        
        # User context function
        if user_id:
            def get_user_context():
                # In a real implementation, this would fetch from database/service
                return {
                    "user_name": context_kwargs.get("user_name", "User"),
                    "email": context_kwargs.get("email"),
                    "phone_number": context_kwargs.get("phone_number"),
                    "cpf": context_kwargs.get("cpf"),
                    "permissions": context_kwargs.get("permissions", []),
                    "subscription_type": context_kwargs.get("subscription_type", "basic"),
                    "language": context_kwargs.get("language", "pt-BR"),
                    "timezone": context_kwargs.get("timezone", "America/Sao_Paulo"),
                    "business_units": context_kwargs.get("business_units", []),
                    "preferences": context_kwargs.get("preferences", {}),
                    "is_vip": "vip" in context_kwargs.get("permissions", [])
                }
            context["user_data"] = get_user_context
        
        # Session context function  
        if session_id:
            def get_session_context():
                return {
                    "session_id": session_id,
                    "channel": context_kwargs.get("channel", "API"),
                    "timestamp": datetime.now().isoformat()
                }
            context["session_data"] = get_session_context
        
        # System context function
        def get_system_context():
            return {
                "environment": os.getenv("HIVE_ENVIRONMENT", "production"),
                "debug_mode": debug_mode,
                "timestamp": datetime.now().isoformat()
            }
        context["system_data"] = get_system_context
        
        # Tenant context function
        if context_kwargs.get("tenant_id"):
            def get_tenant_context():
                return {
                    "tenant_id": context_kwargs.get("tenant_id"),
                    "tenant_name": context_kwargs.get("tenant_name", "Organization"),
                    "subscription_type": context_kwargs.get("subscription_type", "basic"),
                    "enabled_features": context_kwargs.get("enabled_features", []),
                    "features": context_kwargs.get("features", [])
                }
            context["tenant_data"] = get_tenant_context
        
        return context
    
    def _build_dynamic_instructions(self, base_instructions: str, context_functions: Dict[str, Callable], 
                                   user_id: Optional[str] = None, debug_mode: bool = False) -> Callable:
        """Build dynamic instructions function that replaces templated instructions"""
        def generate_instructions():
            # Start with base instructions
            instructions = base_instructions
            
            # Add personalized greeting if user context available
            if user_id and "user_data" in context_functions:
                user_data = context_functions["user_data"]()
                user_name = user_data.get("user_name", "User")
                instructions = f"Hello {user_name}!\n\n{instructions}"
                
                # Add user-specific context
                if user_data.get("permissions"):
                    permissions = ", ".join(user_data["permissions"])
                    instructions += f"\n\nYour permissions: {permissions}"
            
            # Add debug information if debug mode
            if debug_mode:
                instructions += "\n\n🐛 DEBUG MODE ACTIVE - Enhanced logging enabled"
                
            # Add environment context
            if "system_data" in context_functions:
                system_data = context_functions["system_data"]()
                env = system_data.get("environment", "production").upper()
                instructions += f"\n\nEnvironment: {env}"
            
            return instructions
        
        return generate_instructions
    
    def create_versioned_component(
        self,
        component_id: str,
        component_type: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Union[Agent, Team, Workflow]:
        """
        Create any component type with version support.
        
        Args:
            component_id: Component identifier
            component_type: "agent", "team", or "workflow"
            version: Version number (None for active)
            session_id: Session ID for tracking
            debug_mode: Enable debug mode
            user_id: User identifier
            **kwargs: Additional parameters
            
        Returns:
            Configured component instance
        """
        
        # FIRST: Check if this is a dev version by reading YAML directly
        dev_version_record = self._check_for_dev_version(component_id, component_type)
        if dev_version_record:
            logger.info(f"🐛 DEV MODE: Loading {component_id} directly from YAML (bypassing database)")
            version_record = dev_version_record
        else:
            # Normal database lookup logic
            if version is not None:
                version_record = self.version_service.get_version(component_id, version)
                if not version_record:
                    raise ValueError(f"Version {version} not found for {component_id}")
            else:
                version_record = self.version_service.get_active_version(component_id)
                if not version_record:
                    # Fallback: Try to sync from YAML if no active version found
                    logger.warning(f"🔧 No active version found for {component_id}, attempting YAML fallback...")
                    try:
                        version_record = self._sync_from_yaml_fallback(component_id, component_type)
                        if not version_record:
                            raise ValueError(f"No active version found for {component_id} and YAML fallback failed")
                        logger.info(f"🔧 Loaded {component_id} from YAML fallback (version {version_record.version})")
                    except Exception as e:
                        raise ValueError(f"No active version found for {component_id} and YAML fallback failed: {e}")
        
        config = version_record.config
        
        # Validate component type matches
        if version_record.component_type != component_type:
            raise ValueError(f"Component {component_id} is type {version_record.component_type}, not {component_type}")
        
        # Create component based on type using appropriate Agno proxy
        if component_type == "agent":
            return self._create_agent(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                **kwargs
            )
        elif component_type == "team":
            return self._create_team(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                **kwargs
            )
        elif component_type == "workflow":
            return self._create_workflow(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported component type: {component_type}")
    
    def _create_agent(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **context_kwargs
    ) -> Agent:
        """Create versioned agent using dynamic Agno proxy for future compatibility."""
        
        # Create AGNO native context functions to replace templating
        context_functions = self._create_context_functions(
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            **context_kwargs
        )
        
        # Use the dynamic proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_proxy
        
        proxy = get_agno_proxy()
        
        # Load custom tools
        tools = self._load_agent_tools(component_id, config)
        
        # Prepare config with AGNO native context support
        enhanced_config = config.copy()
        if tools:
            enhanced_config["tools"] = tools
        
        # Add AGNO native context parameters
        enhanced_config["context"] = context_functions
        enhanced_config["add_context"] = True  # Automatically inject context into messages
        enhanced_config["resolve_context"] = True  # Resolve context functions when needed
        
        # Convert templated instructions to dynamic instructions if needed
        base_instructions = enhanced_config.get("instructions", "")
        if base_instructions and ("{{" in base_instructions or "{%" in base_instructions):
            # This config still has templating - convert to dynamic instructions
            logger.warning(f"🔧 Converting templated instructions for {component_id} to AGNO native context")
            enhanced_config["instructions"] = self._build_dynamic_instructions(
                base_instructions, context_functions, user_id, debug_mode
            )
        
        # Create agent using dynamic proxy with native context
        agent = proxy.create_agent(
            component_id=component_id,
            config=enhanced_config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url
        )
        
        logger.info(f"🤖 Agent {component_id} created with AGNO native context and {len(proxy.get_supported_parameters())} available parameters")
        
        return agent
    
    def _load_agent_tools(self, component_id: str, config: Dict[str, Any]) -> list:
        """Load custom tools for an agent from its tools.py file."""
        tools = []
        
        try:
            # Convert hyphenated agent ID to underscore for Python module path
            module_name = component_id.replace("-", "_")
            tools_module_path = f"ai.agents.{module_name}.tools"
            
            import importlib
            tools_module = importlib.import_module(tools_module_path)
            
            # Get tool names from config
            tool_names = config.get("tools", [])
            
            if tool_names:
                for tool_name in tool_names:
                    if hasattr(tools_module, tool_name):
                        tool_function = getattr(tools_module, tool_name)
                        tools.append(tool_function)
                        logger.info(f"🤖 Loaded tool '{tool_name}' for agent {component_id}")
                    else:
                        logger.warning(f"🤖 Tool '{tool_name}' not found in {tools_module_path}")
            else:
                # Fallback: load all tools from module's __all__ if no specific tools configured
                if hasattr(tools_module, '__all__'):
                    for tool_name in tools_module.__all__:
                        if hasattr(tools_module, tool_name):
                            tool_function = getattr(tools_module, tool_name)
                            tools.append(tool_function)
                            logger.info(f"🤖 Auto-loaded tool '{tool_name}' for agent {component_id}")
                            
        except ImportError:
            # No tools.py file - that's okay, just use default tools
            logger.debug(f"🤖 No custom tools found for agent {component_id}")
        except Exception as e:
            logger.error(f"🤖 Error loading tools for agent {component_id}: {e}")
        
        return tools
    
    def _create_team(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **kwargs
    ) -> Team:
        """Create team using dynamic Agno Team proxy for future compatibility."""
        
        # Use the dynamic team proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_team_proxy
        
        proxy = get_agno_team_proxy()
        
        # Create team using dynamic proxy
        team = proxy.create_team(
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            **kwargs
        )
        
        logger.info(f"🤖 Team {component_id} created with {len(proxy.get_supported_parameters())} available Agno Team parameters")
        
        return team
    
    def _create_workflow(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **kwargs
    ) -> Workflow:
        """Create workflow using dynamic Agno Workflow proxy for future compatibility."""
        
        # Use the dynamic workflow proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_workflow_proxy
        
        proxy = get_agno_workflow_proxy()
        
        # Create workflow using dynamic proxy
        workflow = proxy.create_workflow(
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            **kwargs
        )
        
        logger.info(f"🤖 Workflow {component_id} created with {len(proxy.get_supported_parameters())} available Agno Workflow parameters")
        
        return workflow
    
    def _sync_from_yaml_fallback(self, component_id: str, component_type: str):
        """Fallback: Read directly from YAML when no database version exists"""
        import yaml
        from pathlib import Path
        
        # Map component types to file patterns
        type_patterns = {
            "agent": f"ai/agents/*/config.yaml",
            "team": f"ai/teams/*/config.yaml", 
            "workflow": f"ai/workflows/*/config.yaml"
        }
        
        if component_type not in type_patterns:
            return None
            
        # Search for the component's config file
        import glob
        pattern = type_patterns[component_type]
        
        for config_file in glob.glob(pattern):
            try:
                with open(config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                
                if not yaml_config or component_type not in yaml_config:
                    continue
                
                # Check if this is the right component
                component_section = yaml_config[component_type]
                yaml_component_id = (
                    component_section.get('agent_id') or
                    component_section.get('team_id') or
                    component_section.get('workflow_id') or
                    component_section.get('component_id')
                )
                
                if yaml_component_id == component_id:
                    # Found matching component, create version record
                    from lib.versioning.agno_version_service import VersionInfo
                    
                    version = component_section.get('version', 1)
                    
                    
                    return VersionInfo(
                        component_id=component_id,
                        component_type=component_type,
                        version=version,
                        config=yaml_config,
                        created_at="yaml-fallback",
                        created_by="yaml-fallback",
                        description=f"Loaded from YAML fallback: {config_file}",
                        is_active=True
                    )
                    
            except Exception as e:
                logger.warning(f"🔧 Error reading {config_file}: {e}")
                continue
        
        return None
    
    def _check_for_dev_version(self, component_id: str, component_type: str):
        """Check if YAML has version: 'dev' and return direct YAML load"""
        import yaml
        import glob
        
        # Map component types to file patterns
        type_patterns = {
            "agent": f"ai/agents/*/config.yaml",
            "team": f"ai/teams/*/config.yaml", 
            "workflow": f"ai/workflows/*/config.yaml"
        }
        
        if component_type not in type_patterns:
            return None
            
        pattern = type_patterns[component_type]
        
        for config_file in glob.glob(pattern):
            try:
                with open(config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                
                if not yaml_config or component_type not in yaml_config:
                    continue
                
                component_section = yaml_config[component_type]
                yaml_component_id = (
                    component_section.get('agent_id') or
                    component_section.get('team_id') or
                    component_section.get('workflow_id') or
                    component_section.get('component_id')
                )
                
                if yaml_component_id == component_id:
                    version = component_section.get('version')
                    
                    # Check if version is "dev"
                    if version == "dev":
                        from lib.versioning.agno_version_service import VersionInfo
                        return VersionInfo(
                            component_id=component_id,
                            component_type=component_type,
                            version="dev",
                            config=yaml_config,
                            created_at="dev-mode",
                            created_by="dev-mode",
                            description=f"DEV MODE: Always load from YAML {config_file}",
                            is_active=True
                        )
                        
            except Exception as e:
                continue
        
        return None


# Global factory instance - lazy initialization
_version_factory = None

def get_version_factory() -> VersionFactory:
    """Get or create the global version factory instance"""
    global _version_factory
    if _version_factory is None:
        _version_factory = VersionFactory()
    return _version_factory


# Clean factory functions
def create_agent(agent_id: str, version: Optional[int] = None, **kwargs) -> Agent:
    """Create agent using factory pattern."""
    return get_version_factory().create_versioned_component(
        agent_id, "agent", version, **kwargs
    )


def create_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """Create team using factory pattern (unified with agents)."""
    return get_version_factory().create_versioned_component(
        team_id, "team", version, **kwargs
    )


def create_versioned_workflow(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
    """Create versioned workflow using Agno storage."""
    return get_version_factory().create_versioned_component(
        workflow_id, "workflow", version, **kwargs
    )