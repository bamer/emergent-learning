#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation for ELF System

Prevents cascade failures by detecting failures and stopping calls
to failing services until they recover.

Usage:
    from core.circuit_breaker import circuit_breaker, CircuitBreaker
    
    # Decorator usage
    @circuit_breaker(name="ollama", failure_threshold=3, recovery_timeout=30)
    def call_ollama():
        ...
    
    # Direct usage
    cb = CircuitBreaker("event_bridge")
    if cb.can_execute():
        try:
            result = call_service()
            cb.record_success()
        except Exception as e:
            cb.record_failure()
            raise
"""

import time
import threading

from typing import Dict, Optional, Callable, Any
from Open_ELF.utils.elf_logging import get_logger
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from datetime import datetime
import json
from pathlib import Path

logger = get_logger("circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failing, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_circuit_opens: int = 0


class CircuitBreaker:
    """
    Circuit Breaker implementation for service resilience.
    
    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, all requests are blocked immediately
    - HALF_OPEN: Testing if service has recovered (limited requests allowed)
    
    Features:
    - Configurable failure threshold
    - Automatic recovery attempts (half-open state)
    - Exponential backoff for recovery
    - Thread-safe operations
    - Statistics tracking
    """
    
    # Class-level registry of all circuit breakers
    _instances: Dict[str, 'CircuitBreaker'] = {}
    _lock = threading.Lock()
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        exponential_backoff: bool = True,
        max_recovery_timeout: float = 300.0
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Unique name for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
            success_threshold: Successes needed to close circuit from half-open
            exponential_backoff: Whether to increase recovery timeout on repeated failures
            max_recovery_timeout: Maximum recovery timeout with exponential backoff
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.base_recovery_timeout = recovery_timeout
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.exponential_backoff = exponential_backoff
        self.max_recovery_timeout = max_recovery_timeout
        
        self._stats = CircuitStats(name=name)
        self._half_open_calls = 0
        self._consecutive_opens = 0
        
        # Register instance
        with CircuitBreaker._lock:
            CircuitBreaker._instances[name] = self
    
    @classmethod
    def get(cls, name: str) -> Optional['CircuitBreaker']:
        """Get a circuit breaker by name."""
        return cls._instances.get(name)
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict]:
        """Get statistics for all circuit breakers."""
        with cls._lock:
            return {
                name: cb.get_stats() 
                for name, cb in cls._instances.items()
            }
    
    def can_execute(self) -> bool:
        """
        Check if a request can be executed.
        
        Returns:
            True if the request should proceed, False if it should be blocked
        """
        with CircuitBreaker._lock:
            self._stats.total_requests += 1
            
            if self._stats.state == CircuitState.CLOSED:
                return True
            
            elif self._stats.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                time_since_failure = time.time() - (self._stats.last_failure_time or 0)
                
                if time_since_failure >= self.recovery_timeout:
                    # Transition to half-open
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_calls = 0
                    return True
                return False
            
            elif self._stats.state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        
        return False
    
    def record_success(self):
        """Record a successful request."""
        with CircuitBreaker._lock:
            self._stats.success_count += 1
            self._stats.total_successes += 1
            self._stats.last_success_time = time.time()
            
            if self._stats.state == CircuitState.HALF_OPEN:
                if self._stats.success_count >= self.success_threshold:
                    # Service has recovered
                    self._transition_to(CircuitState.CLOSED)
                    self._consecutive_opens = 0
                    self.recovery_timeout = self.base_recovery_timeout
                    
            elif self._stats.state == CircuitState.CLOSED:
                # Reset failure count on success
                self._stats.failure_count = 0
    
    def record_failure(self, error: Optional[Exception] = None):
        """Record a failed request."""
        with CircuitBreaker._lock:
            self._stats.failure_count += 1
            self._stats.total_failures += 1
            self._stats.last_failure_time = time.time()
            self._stats.success_count = 0  # Reset success count
            
            error_msg = str(error) if error else "Unknown error"
            logger.warning(f"Circuit '{self.name}' failure #{self._stats.failure_count}: {error_msg}")
            
            if self._stats.state == CircuitState.HALF_OPEN:
                # Service is still failing, go back to open
                self._transition_to(CircuitState.OPEN)
                self._increase_recovery_timeout()
                
            elif self._stats.state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.failure_threshold:
                    # Too many failures, open the circuit
                    self._transition_to(CircuitState.OPEN)
                    self._increase_recovery_timeout()
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._stats.state
        self._stats.state = new_state
        self._stats.last_state_change = time.time()
        
        if new_state == CircuitState.OPEN:
            self._stats.total_circuit_opens += 1
            self._consecutive_opens += 1
            logger.warning(
                f"Circuit '{self.name}' OPENED after {self._stats.failure_count} failures. "
                f"Recovery timeout: {self.recovery_timeout}s"
            )
        elif new_state == CircuitState.CLOSED:
            self._stats.failure_count = 0
            logger.info(f"Circuit '{self.name}' CLOSED - service recovered")
        elif new_state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit '{self.name}' HALF-OPEN - testing recovery")
    
    def _increase_recovery_timeout(self):
        """Increase recovery timeout with exponential backoff."""
        if self.exponential_backoff:
            self.recovery_timeout = min(
                self.recovery_timeout * 2,
                self.max_recovery_timeout
            )
    
    def force_open(self):
        """Manually open the circuit (for maintenance, etc.)."""
        with CircuitBreaker._lock:
            self._transition_to(CircuitState.OPEN)
            self._stats.last_failure_time = time.time()
    
    def force_close(self):
        """Manually close the circuit (for testing, etc.)."""
        with CircuitBreaker._lock:
            self._transition_to(CircuitState.CLOSED)
            self._stats.failure_count = 0
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            "name": self._stats.name,
            "state": self._stats.state.value,
            "failure_count": self._stats.failure_count,
            "success_count": self._stats.success_count,
            "last_failure_time": self._stats.last_failure_time,
            "last_success_time": self._stats.last_success_time,
            "last_state_change": self._stats.last_state_change,
            "total_requests": self._stats.total_requests,
            "total_failures": self._stats.total_failures,
            "total_successes": self._stats.total_successes,
            "total_circuit_opens": self._stats.total_circuit_opens,
            "recovery_timeout": self.recovery_timeout,
            "consecutive_opens": self._consecutive_opens
        }
    
    @property
    def state(self) -> CircuitState:
        """Get current state."""
        return self._stats.state
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._stats.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing requests)."""
        return self._stats.state == CircuitState.CLOSED


class CircuitOpenError(Exception):
    """Exception raised when circuit is open."""
    def __init__(self, circuit_name: str, stats: Dict):
        self.circuit_name = circuit_name
        self.stats = stats
        super().__init__(
            f"Circuit '{circuit_name}' is OPEN. "
            f"Failures: {stats['failure_count']}, "
            f"Recovery in: {stats['recovery_timeout']}s"
        )


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    fallback: Optional[Callable] = None
):
    """
    Decorator to apply circuit breaker pattern to a function.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before recovery attempt
        fallback: Optional fallback function when circuit is open
    
    Usage:
        @circuit_breaker("ollama", failure_threshold=3, fallback=lambda: None)
        def call_ollama():
            return requests.get("http://localhost:11434/api/tags")
    """
    cb = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not cb.can_execute():
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitOpenError(name, cb.get_stats())
            
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure(e)
                raise
        
        # Attach circuit breaker to function for external access
        wrapper.circuit_breaker = cb
        return wrapper
    
    return decorator


class ConnectionManager:
    """
    Manages connections with circuit breaker, retry logic, and health checks.
    
    Features:
    - Exponential backoff retries
    - Circuit breaker integration
    - Connection pooling
    - Health monitoring
    """
    
    def __init__(
        self,
        service_name: str,
        base_url: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        timeout: float = 10.0
    ):
        self.service_name = service_name
        self.base_url = base_url
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout
        
        self.circuit = CircuitBreaker(
            name=f"{service_name}_connection",
            failure_threshold=max_retries
        )
        
        self._last_health_check: Optional[float] = None
        self._health_check_interval = 30.0
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff."""
        import random
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter
    
    def call_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic and circuit breaker.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: If all retries fail
        """
        import requests
        
        if not self.circuit.can_execute():
            raise CircuitOpenError(self.circuit.name, self.circuit.get_stats())
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                self.circuit.record_success()
                return result
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ReadTimeout,
                    ConnectionRefusedError,
                    TimeoutError) as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"{self.service_name}: Connection attempt {attempt + 1}/{self.max_retries} failed. "
                        f"Retrying in {delay:.1f}s. Error: {e}"
                    )
                    time.sleep(delay)
            except Exception as e:
                # Non-retryable error
                self.circuit.record_failure(e)
                raise
        
        # All retries failed
        self.circuit.record_failure(last_error)
        raise last_error
    
    def health_check(self) -> Dict:
        """
        Perform health check on the service.
        
        Returns:
            Dict with health status
        """
        import requests
        
        health = {
            "service": self.service_name,
            "url": self.base_url,
            "healthy": False,
            "circuit_state": self.circuit.state.value,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Try a quick HEAD request or health endpoint
            health_url = f"{self.base_url.rstrip('/')}/health"
            response = requests.head(health_url, timeout=self.timeout)
            health["healthy"] = response.status_code < 500
            health["status_code"] = response.status_code
            
            if health["healthy"]:
                self.circuit.record_success()
            else:
                self.circuit.record_failure(Exception(f"HTTP {response.status_code}"))
                
        except Exception as e:
            health["error"] = str(e)
            self.circuit.record_failure(e)
        
        self._last_health_check = time.time()
        return health


# Pre-configured circuit breakers for ELF services
def get_event_bridge_circuit() -> CircuitBreaker:
    """Get circuit breaker for Event Bridge."""
    return CircuitBreaker.get("event_bridge") or CircuitBreaker(
        "event_bridge",
        failure_threshold=3,
        recovery_timeout=30.0
    )


def get_ollama_circuit() -> CircuitBreaker:
    """Get circuit breaker for Ollama embeddings."""
    return CircuitBreaker.get("ollama") or CircuitBreaker(
        "ollama",
        failure_threshold=5,
        recovery_timeout=60.0
    )


def get_opencode_circuit() -> CircuitBreaker:
    """Get circuit breaker for OpenCode server."""
    return CircuitBreaker.get("opencode") or CircuitBreaker(
        "opencode",
        failure_threshold=3,
        recovery_timeout=20.0
    )


def save_circuit_stats_to_file(filepath: Path):
    """Save all circuit breaker stats to a JSON file."""
    stats = CircuitBreaker.get_all_stats()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    # Test the circuit breaker
    print("Testing Circuit Breaker...")
    
    @circuit_breaker("test", failure_threshold=2, recovery_timeout=5.0)
    def failing_function():
        raise ConnectionError("Simulated failure")
    
    # Should fail twice, then circuit opens
    for i in range(5):
        try:
            failing_function()
        except (ConnectionError, CircuitOpenError) as e:
            print(f"Attempt {i+1}: {type(e).__name__}: {e}")
    
    # Print stats
    cb = CircuitBreaker.get("test")
    print(f"\nCircuit stats: {json.dumps(cb.get_stats(), indent=2)}")