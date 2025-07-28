"""
Coordinator Registry

Manages the registration and factory creation of all domain coordinators
in the Automagik Hive system.
"""

from typing import Dict, Type

from agno.utils.log import logger

from lib.coordination.domain_coordinator_base import DomainCoordinatorBase
from lib.utils.version_factory import create_coordinator


def _import_coordinators():
    """Import coordinator classes dynamically to handle different naming conventions."""
    coordinators = {}
    
    # Import genie-quality coordinator
    try:
        import importlib
        genie_quality_module = importlib.import_module("ai.coordinators.genie-quality.coordinator")
        coordinators["genie-quality"] = genie_quality_module.GenieQualityCoordinator
        logger.debug("Successfully imported genie-quality coordinator")
    except ImportError as e:
        logger.warning(f"Could not import genie-quality coordinator: {e}")
    
    # Import genie-testing coordinator  
    try:
        from .genie_testing.coordinator import GenieTestingCoordinator
        coordinators["genie-testing"] = GenieTestingCoordinator
        logger.debug("Successfully imported genie-testing coordinator")
    except ImportError as e:
        logger.warning(f"Could not import genie-testing coordinator: {e}")
        
    # Import genie-dev coordinator
    try:
        from .genie_dev.coordinator import GenieDevCoordinator
        coordinators["genie-dev"] = GenieDevCoordinator
        logger.debug("Successfully imported genie-dev coordinator")
    except ImportError as e:
        logger.warning(f"Could not import genie-dev coordinator: {e}")
    
    return coordinators


class CoordinatorRegistry:
    """Registry for all domain coordinators in the system."""
    
    def __init__(self):
        """Initialize the coordinator registry."""
        self._coordinators: Dict[str, Type[DomainCoordinatorBase]] = {}
        self._register_coordinators()
        
    def _register_coordinators(self):
        """Register all available coordinators."""
        # Import and register all available coordinators
        imported_coordinators = _import_coordinators()
        self._coordinators.update(imported_coordinators)
        
        logger.info(f"Coordinator registry initialized with {len(self._coordinators)} coordinators: {list(self._coordinators.keys())}")
        
    def get_coordinator_class(self, coordinator_id: str) -> Type[DomainCoordinatorBase]:
        """Get coordinator class by ID."""
        if coordinator_id not in self._coordinators:
            available = list(self._coordinators.keys())
            raise ValueError(f"Unknown coordinator '{coordinator_id}'. Available: {available}")
            
        return self._coordinators[coordinator_id]
        
    def list_coordinators(self) -> Dict[str, str]:
        """List all registered coordinators with descriptions."""
        return {
            coordinator_id: coordinator_class.__doc__ or "No description"
            for coordinator_id, coordinator_class in self._coordinators.items()
        }
        
    async def create_coordinator(
        self, 
        coordinator_id: str,
        version: int = None,
        **kwargs
    ) -> DomainCoordinatorBase:
        """Create a coordinator instance using the version factory."""
        return await create_coordinator(
            coordinator_id=coordinator_id,
            version=version,
            **kwargs
        )


# Global registry instance
_coordinator_registry = None


def get_coordinator_registry() -> CoordinatorRegistry:
    """Get or create the global coordinator registry."""
    global _coordinator_registry
    if _coordinator_registry is None:
        _coordinator_registry = CoordinatorRegistry()
    return _coordinator_registry


# Convenience functions
async def create_testing_coordinator(**kwargs) -> GenieTestingCoordinator:
    """Create a genie-testing domain coordinator."""
    registry = get_coordinator_registry()
    return await registry.create_coordinator("genie-testing", **kwargs)


async def create_quality_coordinator(**kwargs):
    """Create a genie-quality domain coordinator."""
    registry = get_coordinator_registry()
    return await registry.create_coordinator("genie-quality", **kwargs)


def list_available_coordinators() -> Dict[str, str]:
    """List all available coordinators."""
    registry = get_coordinator_registry()
    return registry.list_coordinators()
