"""
Instrumentation decorators for execution tracing

Provides clean @trace_execution decorator for universal AI component tracing.
"""

import asyncio
import time
import uuid
from functools import wraps
from typing import Any, Callable, Optional

from .core import tracer, ExecutionEvent, ExecutionEventType


def trace_execution(component_type: str, component_id: Optional[str] = None):
    """
    Decorator to trace execution of AI components (teams, agents, workflows).
    
    Args:
        component_type: Type of component ("team", "agent", "workflow")
        component_id: Optional component ID (will try to infer from instance)
    
    Usage:
        @trace_execution(component_type="team")
        async def run(self, query: str):
            # Component logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Generate unique execution ID
            execution_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Get component_id from instance if not provided
            comp_id = component_id
            if comp_id is None and len(args) > 0:
                instance = args[0]
                if hasattr(instance, 'team_id'):
                    comp_id = instance.team_id
                elif hasattr(instance, 'agent_id'):
                    comp_id = instance.agent_id
                elif hasattr(instance, 'workflow_id'):
                    comp_id = instance.workflow_id
                elif hasattr(instance, 'name'):
                    comp_id = instance.name
                else:
                    comp_id = f"{component_type}-{id(instance)}"
            else:
                comp_id = comp_id or "unknown"
            
            # Store execution_id in instance for child events
            if len(args) > 0 and hasattr(args[0], '__dict__'):
                args[0]._current_execution_id = execution_id
            
            # Emit start event
            tracer.emit_event(ExecutionEvent(
                event_type=ExecutionEventType.EXECUTION_START,
                execution_id=execution_id,
                component_type=component_type,
                component_id=comp_id,
                timestamp=start_time,
                data={
                    "function": func.__name__,
                    "args": _safe_serialize(args[1:]),  # Skip self
                    "kwargs": _safe_serialize(kwargs)
                }
            ))
            
            try:
                result = await func(*args, **kwargs)
                
                # Emit success event
                tracer.emit_event(ExecutionEvent(
                    event_type=ExecutionEventType.EXECUTION_END,
                    execution_id=execution_id,
                    component_type=component_type,
                    component_id=comp_id,
                    timestamp=time.time(),
                    data={
                        "status": "success",
                        "duration": time.time() - start_time,
                        "result_length": len(str(result)) if result else 0
                    }
                ))
                
                return result
                
            except Exception as e:
                # Emit error event
                tracer.emit_event(ExecutionEvent(
                    event_type=ExecutionEventType.ERROR_OCCURRED,
                    execution_id=execution_id,
                    component_type=component_type,
                    component_id=comp_id,
                    timestamp=time.time(),
                    data={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration": time.time() - start_time
                    }
                ))
                raise
            
            finally:
                # Clean up execution_id from instance
                if len(args) > 0 and hasattr(args[0], '_current_execution_id'):
                    delattr(args[0], '_current_execution_id')
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Generate unique execution ID
            execution_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Get component_id from instance if not provided
            comp_id = component_id
            if comp_id is None and len(args) > 0:
                instance = args[0]
                if hasattr(instance, 'team_id'):
                    comp_id = instance.team_id
                elif hasattr(instance, 'agent_id'):
                    comp_id = instance.agent_id
                elif hasattr(instance, 'workflow_id'):
                    comp_id = instance.workflow_id
                elif hasattr(instance, 'name'):
                    comp_id = instance.name
                else:
                    comp_id = f"{component_type}-{id(instance)}"
            else:
                comp_id = comp_id or "unknown"
            
            # Store execution_id in instance for child events
            if len(args) > 0 and hasattr(args[0], '__dict__'):
                args[0]._current_execution_id = execution_id
            
            # Emit start event
            tracer.emit_event(ExecutionEvent(
                event_type=ExecutionEventType.EXECUTION_START,
                execution_id=execution_id,
                component_type=component_type,
                component_id=comp_id,
                timestamp=start_time,
                data={
                    "function": func.__name__,
                    "args": _safe_serialize(args[1:]),  # Skip self
                    "kwargs": _safe_serialize(kwargs)
                }
            ))
            
            try:
                result = func(*args, **kwargs)
                
                # Emit success event
                tracer.emit_event(ExecutionEvent(
                    event_type=ExecutionEventType.EXECUTION_END,
                    execution_id=execution_id,
                    component_type=component_type,
                    component_id=comp_id,
                    timestamp=time.time(),
                    data={
                        "status": "success",
                        "duration": time.time() - start_time,
                        "result_length": len(str(result)) if result else 0
                    }
                ))
                
                return result
                
            except Exception as e:
                # Emit error event
                tracer.emit_event(ExecutionEvent(
                    event_type=ExecutionEventType.ERROR_OCCURRED,
                    execution_id=execution_id,
                    component_type=component_type,
                    component_id=comp_id,
                    timestamp=time.time(),
                    data={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration": time.time() - start_time
                    }
                ))
                raise
            
            finally:
                # Clean up execution_id from instance
                if len(args) > 0 and hasattr(args[0], '_current_execution_id'):
                    delattr(args[0], '_current_execution_id')
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def emit_routing_decision(instance: Any, data: dict):
    """
    Emit a routing decision event.
    
    Args:
        instance: Component instance (team, agent, workflow)
        data: Routing decision data
    """
    if not hasattr(instance, '_current_execution_id'):
        return
    
    tracer.emit_event(ExecutionEvent(
        event_type=ExecutionEventType.ROUTING_DECISION,
        execution_id=instance._current_execution_id,
        component_type=_get_component_type(instance),
        component_id=_get_component_id(instance),
        timestamp=time.time(),
        data=data
    ))


def emit_tool_call(instance: Any, data: dict):
    """
    Emit a tool call event.
    
    Args:
        instance: Component instance (team, agent, workflow)
        data: Tool call data
    """
    if not hasattr(instance, '_current_execution_id'):
        return
    
    tracer.emit_event(ExecutionEvent(
        event_type=ExecutionEventType.TOOL_CALL,
        execution_id=instance._current_execution_id,
        component_type=_get_component_type(instance),
        component_id=_get_component_id(instance),
        timestamp=time.time(),
        data=data
    ))


def emit_knowledge_search(instance: Any, data: dict):
    """
    Emit a knowledge search event.
    
    Args:
        instance: Component instance (team, agent, workflow)
        data: Knowledge search data
    """
    if not hasattr(instance, '_current_execution_id'):
        return
    
    tracer.emit_event(ExecutionEvent(
        event_type=ExecutionEventType.KNOWLEDGE_SEARCH,
        execution_id=instance._current_execution_id,
        component_type=_get_component_type(instance),
        component_id=_get_component_id(instance),
        timestamp=time.time(),
        data=data
    ))


def _get_component_type(instance: Any) -> str:
    """Get component type from instance"""
    if hasattr(instance, 'team_id'):
        return "team"
    elif hasattr(instance, 'agent_id'):
        return "agent"
    elif hasattr(instance, 'workflow_id'):
        return "workflow"
    else:
        return "unknown"


def _get_component_id(instance: Any) -> str:
    """Get component ID from instance"""
    if hasattr(instance, 'team_id'):
        return instance.team_id
    elif hasattr(instance, 'agent_id'):
        return instance.agent_id
    elif hasattr(instance, 'workflow_id'):
        return instance.workflow_id
    elif hasattr(instance, 'name'):
        return instance.name
    else:
        return f"unknown-{id(instance)}"


def _safe_serialize(obj: Any, max_length: int = 200) -> str:
    """Safely serialize object to string with length limit"""
    try:
        result = str(obj)
        if len(result) > max_length:
            return result[:max_length - 3] + "..."
        return result
    except:
        return "<unserializable>"