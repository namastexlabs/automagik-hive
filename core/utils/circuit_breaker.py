"""
Circuit Breaker Pattern Implementation

Provides fault tolerance for external service calls with automatic recovery.
Used by MCP connection pooling to handle server failures gracefully.
"""

import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests due to failures
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5      # Number of failures before opening
    recovery_timeout: float = 60.0  # Seconds to wait before trying recovery
    success_threshold: int = 2      # Successes needed to close from half-open
    timeout: float = 30.0           # Request timeout


class CircuitBreaker:
    """
    Circuit breaker for handling external service failures.
    
    Implements the circuit breaker pattern to prevent cascading failures
    and provide automatic recovery for external services.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 success_threshold: int = 2, timeout: float = 30.0):
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout
        )
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: Original exception from function call
        """
        if self.is_open():
            raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute an async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: Original exception from function call
        """
        if self.is_open():
            raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
    
    def record_success(self):
        """Record a successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
    
    def record_failure(self):
        """Record a failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._open()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Return to open state on failure during recovery
            self._open()
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if self._should_attempt_reset():
                self._half_open()
                return False
            return True
        return False
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed"""
        return self.state == CircuitBreakerState.CLOSED
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half open"""
        return self.state == CircuitBreakerState.HALF_OPEN
    
    def force_open(self):
        """Force circuit breaker to open state"""
        self._open()
        logger.warning("Circuit breaker forced to open state")
    
    def force_close(self):
        """Force circuit breaker to closed state"""
        self._close()
        logger.info("Circuit breaker forced to closed state")
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        logger.info("Circuit breaker reset to initial state")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _open(self):
        """Transition to open state"""
        if self.state != CircuitBreakerState.OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.last_state_change = time.time()
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _close(self):
        """Transition to closed state"""
        if self.state != CircuitBreakerState.CLOSED:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_state_change = time.time()
            logger.info("Circuit breaker closed - service recovered")
    
    def _half_open(self):
        """Transition to half-open state"""
        if self.state != CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.HALF_OPEN
            self.success_count = 0
            self.last_state_change = time.time()
            logger.info("Circuit breaker half-open - testing service recovery")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'last_state_change': self.last_state_change,
            'time_since_last_failure': time.time() - self.last_failure_time if self.last_failure_time else None,
            'time_in_current_state': time.time() - self.last_state_change,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout
            }
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Useful for managing circuit breakers for different services
    or resources with shared configuration.
    """
    
    def __init__(self, default_config: CircuitBreakerConfig = None):
        self.default_config = default_config or CircuitBreakerConfig()
        self.breakers: dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker by name"""
        if name not in self.breakers:
            breaker_config = config or self.default_config
            self.breakers[name] = CircuitBreaker(
                failure_threshold=breaker_config.failure_threshold,
                recovery_timeout=breaker_config.recovery_timeout,
                success_threshold=breaker_config.success_threshold,
                timeout=breaker_config.timeout
            )
        
        return self.breakers[name]
    
    def remove_breaker(self, name: str):
        """Remove a circuit breaker"""
        if name in self.breakers:
            del self.breakers[name]
    
    def get_all_stats(self) -> dict:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
    
    def list_breakers(self) -> list[str]:
        """List all circuit breaker names"""
        return list(self.breakers.keys())