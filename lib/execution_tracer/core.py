"""
Core execution tracing system

Clean observer pattern implementation for universal AI execution visibility.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Set


class ExecutionEventType(Enum):
    """Types of execution events that can be traced"""
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"
    STEP_START = "step_start"
    STEP_END = "step_end"
    TOOL_CALL = "tool_call"
    KNOWLEDGE_SEARCH = "knowledge_search"
    CONTEXT_SHARING = "context_sharing"
    ROUTING_DECISION = "routing_decision"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class ExecutionEvent:
    """Event data structure for execution tracing"""
    event_type: ExecutionEventType
    execution_id: str
    component_type: str  # "team", "agent", "workflow"
    component_id: str
    timestamp: float
    data: Dict[str, Any]
    parent_execution_id: Optional[str] = None
    step_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TraceLevel(Enum):
    """Levels of tracing detail"""
    DISABLED = "disabled"
    BASIC = "basic"          # Start/end events only
    DETAILED = "detailed"    # Include routing decisions, tool calls
    VERBOSE = "verbose"      # All events including internal steps


@dataclass
class TraceConfig:
    """Configuration for execution tracing"""
    enabled: bool = False
    level: TraceLevel = TraceLevel.BASIC
    component_filters: Optional[Set[str]] = None  # {"team", "agent", "workflow"}
    id_filters: Optional[Set[str]] = None         # {"ana-team", "specialist-agent"}
    
    def should_trace(self, event: ExecutionEvent) -> bool:
        """Determine if an event should be traced based on configuration"""
        if not self.enabled:
            return False
        
        # Filter by component type
        if self.component_filters and event.component_type not in self.component_filters:
            return False
        
        # Filter by component ID
        if self.id_filters and event.component_id not in self.id_filters:
            return False
        
        # Filter by event type based on level
        if self.level == TraceLevel.BASIC:
            return event.event_type in {
                ExecutionEventType.EXECUTION_START,
                ExecutionEventType.EXECUTION_END,
                ExecutionEventType.ERROR_OCCURRED
            }
        elif self.level == TraceLevel.DETAILED:
            return event.event_type not in {
                ExecutionEventType.STEP_START,
                ExecutionEventType.STEP_END
            }
        
        return True  # VERBOSE shows all events


class ExecutionObserver(ABC):
    """Abstract base class for execution event observers"""
    
    @abstractmethod
    def on_event(self, event: ExecutionEvent):
        """Handle an execution event"""
        pass


class ExecutionTracer:
    """Main execution tracing system"""
    
    def __init__(self):
        self._observers: List[ExecutionObserver] = []
        self._config = TraceConfig()
        self._enabled = False
    
    def add_observer(self, observer: ExecutionObserver):
        """Add an observer to receive execution events"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: ExecutionObserver):
        """Remove an observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def emit_event(self, event: ExecutionEvent):
        """Emit an execution event to all observers"""
        if not self._enabled or not self._config.should_trace(event):
            return
        
        for observer in self._observers:
            try:
                observer.on_event(event)
            except Exception as e:
                # Don't let observer errors crash the system
                pass
    
    def enable(self):
        """Enable execution tracing"""
        self._enabled = True
    
    def disable(self):
        """Disable execution tracing"""
        self._enabled = False
    
    def configure(self, config: TraceConfig):
        """Update tracing configuration"""
        self._config = config
        self._enabled = config.enabled
    
    @property
    def enabled(self) -> bool:
        """Check if tracing is enabled"""
        return self._enabled
    
    @property
    def config(self) -> TraceConfig:
        """Get current configuration"""
        return self._config


# Global tracer instance
tracer = ExecutionTracer()


def load_trace_config() -> TraceConfig:
    """Load tracing configuration from environment variables"""
    
    # Check if any tracing is enabled
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    execution_tracing = os.getenv("EXECUTION_TRACING", "false").lower() == "true"
    
    if not (demo_mode or execution_tracing):
        return TraceConfig(enabled=False)
    
    # Parse trace level
    level_str = os.getenv("TRACE_LEVEL", "basic").lower()
    try:
        level = TraceLevel(level_str)
    except ValueError:
        level = TraceLevel.BASIC
    
    # Parse component filters
    component_filters = None
    if filters_str := os.getenv("TRACE_COMPONENTS"):
        component_filters = set(filters_str.split(","))
    
    # Parse ID filters
    id_filters = None
    if ids_str := os.getenv("TRACE_IDS"):
        id_filters = set(ids_str.split(","))
    
    return TraceConfig(
        enabled=True,
        level=level,
        component_filters=component_filters,
        id_filters=id_filters
    )