#!/usr/bin/env python3
"""
ELF Service Manager - Unified Service Management with Auto-Recovery

This module provides:
1. Service lifecycle management (start, stop, restart)
2. Health monitoring with configurable intervals
3. Auto-recovery on failures
4. Dependency management (start services in correct order)
5. Dead letter queue for failed operations
6. Graceful degradation when services are unavailable

Usage:
    from core.service_manager import ServiceManager, get_service_manager
    
    manager = get_service_manager()
    manager.start_all_services()
    
    # Check service health
    health = manager.get_all_health()
    
    # Auto-recover failed services
    manager.auto_recover()
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import requests

# Setup logging
logger = logging.getLogger("service_manager")

# Try to import circuit breaker
try:
    from core.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    logger.warning("Circuit breaker not available")


class ServiceStatus(Enum):
    """Service status enumeration."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"
    DISABLED = "disabled"


class ServicePriority(Enum):
    """Service startup priority (lower = higher priority)."""
    CRITICAL = 0    # Must start first (OpenCode, Database)
    HIGH = 1        # Core services (EventBridge, Semantic)
    NORMAL = 2      # Standard services (Orchestrator, Sentinel)
    LOW = 3         # Optional services (Dashboard, CEO Monitor)


@dataclass
class ServiceConfig:
    """Configuration for a managed service."""
    name: str
    command: List[str]
    working_dir: Optional[Path] = None
    priority: ServicePriority = ServicePriority.NORMAL
    health_check_url: Optional[str] = None
    health_check_command: Optional[List[str]] = None
    health_check_interval: float = 30.0
    startup_timeout: float = 30.0
    restart_on_failure: bool = True
    max_restarts: int = 5
    restart_delay: float = 5.0
    restart_backoff: float = 2.0
    dependencies: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    log_file: Optional[Path] = None
    pid_file: Optional[Path] = None
    port: Optional[int] = None
    process_pattern: Optional[str] = None  # For pgrep-based detection


@dataclass
class ServiceState:
    """Runtime state of a service."""
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.UNKNOWN
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    last_health_status: Optional[bool] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    last_error: Optional[str] = None
    circuit_breaker: Optional[Any] = None


class ServiceManager:
    """
    Unified service manager with auto-recovery capabilities.
    
    Features:
    - Start/stop services in dependency order
    - Health monitoring with circuit breakers
    - Auto-recovery with exponential backoff
    - Dead letter queue for failed operations
    - Graceful degradation
    """
    
    # Default ELF services configuration
    DEFAULT_SERVICES = {
        "opencode": ServiceConfig(
            name="opencode",
            command=["opencode", "serve", "--port", "4096", "--hostname", "127.0.0.1"],
            priority=ServicePriority.CRITICAL,
            health_check_url="http://localhost:4096/global/health",
            health_check_interval=60.0,
            startup_timeout=30.0,
            restart_on_failure=True,
            max_restarts=3,
            process_pattern="opencode serve",
            port=4096
        ),
        "event_bridge": ServiceConfig(
            name="event_bridge",
            command=["python3", "event_bridge_v2.py", "start"],
            working_dir=Path("/home/bamer/.opencode/emergent-learning/core"),
            priority=ServicePriority.HIGH,
            health_check_url="http://localhost:9998/status",
            health_check_interval=30.0,
            startup_timeout=20.0,
            restart_on_failure=True,
            max_restarts=5,
            process_pattern="event_bridge_v2.py",
            port=9998,
            dependencies=["opencode"],
            pid_file=Path("/home/bamer/.opencode/emergent-learning/.coordination/event_bridge_v2.pid")
        ),
        "semantic_daemon": ServiceConfig(
            name="semantic_daemon",
            command=["python3", "daemon.py", "--port", "5001"],
            working_dir=Path("/home/bamer/.opencode/emergent-learning/semantic"),
            priority=ServicePriority.HIGH,
            health_check_url="http://localhost:5001/health",
            health_check_interval=60.0,
            startup_timeout=15.0,
            restart_on_failure=True,
            max_restarts=5,
            process_pattern="daemon.py.*5001",
            port=5001
        ),
        "orchestrator": ServiceConfig(
            name="orchestrator",
            command=["python3", "unified_orchestrator.py", "start"],
            working_dir=Path("/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator"),
            priority=ServicePriority.NORMAL,
            health_check_url="http://localhost:9998/status",  # Same as EventBridge
            health_check_interval=30.0,
            startup_timeout=20.0,
            restart_on_failure=True,
            max_restarts=5,
            process_pattern="unified_orchestrator.py",
            dependencies=["event_bridge", "semantic_daemon"]
        ),
        "sentinel": ServiceConfig(
            name="sentinel",
            command=["python3", "sentinel.py"],
            working_dir=Path("/home/bamer/.opencode/emergent-learning/core"),
            priority=ServicePriority.NORMAL,
            health_check_command=["pgrep", "-f", "core/sentinel.py"],
            health_check_interval=60.0,
            startup_timeout=10.0,
            restart_on_failure=True,
            max_restarts=5,
            process_pattern="core/sentinel.py",
            dependencies=["event_bridge"]
        ),
        "learning_capture": ServiceConfig(
            name="learning_capture",
            command=["python3", "background-learning-capture.py"],
            working_dir=Path("/home/bamer/.opencode/emergent-learning/scripts"),
            priority=ServicePriority.LOW,
            health_check_command=["pgrep", "-f", "background-learning-capture.py"],
            health_check_interval=120.0,
            startup_timeout=10.0,
            restart_on_failure=True,
            max_restarts=3,
            process_pattern="background-learning-capture.py",
            dependencies=["semantic_daemon"]
        ),
        "ceo_monitor": ServiceConfig(
            name="ceo_monitor",
            command=["python3", "ceo_inbox_monitor.py", "start"],
            working_dir=Path("/home/bamer/.opencode/emergent-learning/Open_ELF/agents"),
            priority=ServicePriority.LOW,
            health_check_command=["pgrep", "-f", "ceo_inbox_monitor.py"],
            health_check_interval=120.0,
            startup_timeout=10.0,
            restart_on_failure=False,  # Optional service
            max_restarts=2,
            process_pattern="ceo_inbox_monitor.py"
        )
    }
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, services: Optional[Dict[str, ServiceConfig]] = None):
        """Initialize service manager."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.services: Dict[str, ServiceState] = {}
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._dead_letter_queue: List[Dict[str, Any]] = []
        self._max_dead_letter_size = 1000
        
        # Load services
        services = services or self.DEFAULT_SERVICES
        for name, config in services.items():
            self.services[name] = ServiceState(config=config)
            
            # Create circuit breaker if available
            if CIRCUIT_BREAKER_AVAILABLE and config.health_check_url:
                self.services[name].circuit_breaker = CircuitBreaker(
                    name=f"{name}_service",
                    failure_threshold=config.max_restarts,
                    recovery_timeout=config.restart_delay * 10
                )
        
        self._initialized = True
        logger.info(f"ServiceManager initialized with {len(self.services)} services")
    
    @classmethod
    def get_instance(cls) -> 'ServiceManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def start_service(self, name: str, force: bool = False) -> bool:
        """
        Start a specific service.
        
        Args:
            name: Service name
            force: Force start even if dependencies are not met
            
        Returns:
            True if started successfully
        """
        if name not in self.services:
            logger.error(f"Unknown service: {name}")
            return False
        
        state = self.services[name]
        config = state.config
        
        # Check if already running
        if state.status == ServiceStatus.RUNNING and not force:
            logger.info(f"Service {name} already running")
            return True
        
        # Check dependencies
        if not force:
            for dep in config.dependencies:
                if dep in self.services:
                    dep_state = self.services[dep]
                    if dep_state.status != ServiceStatus.RUNNING:
                        logger.warning(
                            f"Cannot start {name}: dependency {dep} not running "
                            f"(status: {dep_state.status})"
                        )
                        return False
        
        logger.info(f"Starting service: {name}")
        state.status = ServiceStatus.STARTING
        
        try:
            # Kill any existing process first (cleanup stale processes)
            self._kill_existing_process(config)
            time.sleep(1)  # Wait for port to be released
            
            # Prepare environment
            env = os.environ.copy()
            env.update(config.env)
            
            # Start the process
            work_dir = str(config.working_dir) if config.working_dir else None
            
            log_file = None
            if config.log_file:
                config.log_file.parent.mkdir(parents=True, exist_ok=True)
                log_file = open(config.log_file, 'a')
            
            process = subprocess.Popen(
                config.command,
                cwd=work_dir,
                env=env,
                stdout=log_file if log_file else subprocess.PIPE,
                stderr=log_file if log_file else subprocess.PIPE,
                start_new_session=True
            )
            
            state.pid = process.pid
            state.started_at = datetime.now()
            
            # Wait for service to be ready
            if self._wait_for_service(name, config.startup_timeout):
                state.status = ServiceStatus.RUNNING
                state.last_error = None
                logger.info(f"✅ Service {name} started (PID: {state.pid})")
                return True
            else:
                state.status = ServiceStatus.FAILED
                state.last_error = "Startup timeout"
                logger.error(f"❌ Service {name} failed to start within timeout")
                return False
                
        except Exception as e:
            state.status = ServiceStatus.FAILED
            state.last_error = str(e)
            logger.error(f"❌ Failed to start service {name}: {e}")
            return False
    
    def _kill_existing_process(self, config: ServiceConfig):
        """Kill any existing process for the service."""
        # Try to kill by PID file
        if config.pid_file and config.pid_file.exists():
            try:
                pid = int(config.pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
                config.pid_file.unlink()
            except (ValueError, ProcessLookupError, FileNotFoundError):
                pass
        
        # Try to kill by process pattern
        if config.process_pattern:
            try:
                subprocess.run(
                    ["pkill", "-f", config.process_pattern],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
        
        # Try to kill by port
        if config.port:
            try:
                result = subprocess.run(
                    ["lsof", "-ti", str(config.port)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.stdout.strip():
                    for pid_str in result.stdout.strip().split('\n'):
                        try:
                            os.kill(int(pid_str), signal.SIGKILL)
                        except:
                            pass
            except:
                pass
    
    def _wait_for_service(self, name: str, timeout: float) -> bool:
        """Wait for service to become healthy."""
        state = self.services[name]
        config = state.config
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_health(name, quick=True):
                return True
            time.sleep(0.5)
        
        return False
    
    def stop_service(self, name: str) -> bool:
        """Stop a specific service."""
        if name not in self.services:
            return False
        
        state = self.services[name]
        config = state.config
        
        logger.info(f"Stopping service: {name}")
        
        try:
            # Try graceful shutdown first
            if state.pid:
                try:
                    os.kill(state.pid, signal.SIGTERM)
                    time.sleep(2)
                    
                    # Check if still running
                    try:
                        os.kill(state.pid, 0)  # Signal 0 = check existence
                        # Still running, force kill
                        os.kill(state.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Already stopped
                except ProcessLookupError:
                    pass  # Already stopped
            
            # Also try pattern-based kill
            self._kill_existing_process(config)
            
            state.status = ServiceStatus.STOPPED
            state.pid = None
            logger.info(f"✅ Service {name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop service {name}: {e}")
            return False
    
    def restart_service(self, name: str) -> bool:
        """Restart a service."""
        logger.info(f"Restarting service: {name}")
        
        state = self.services[name]
        state.restart_count += 1
        state.last_restart = datetime.now()
        
        # Stop then start
        if not self.stop_service(name):
            # Force stop if graceful stop failed
            self._kill_existing_process(state.config)
        
        time.sleep(state.config.restart_delay)
        return self.start_service(name, force=True)
    
    def _check_health(self, name: str, quick: bool = False) -> bool:
        """
        Check health of a service.
        
        Args:
            name: Service name
            quick: If True, only check if process is running
            
        Returns:
            True if healthy
        """
        state = self.services[name]
        config = state.config
        
        # Quick check: is process running?
        if state.pid:
            try:
                os.kill(state.pid, 0)
            except ProcessLookupError:
                state.status = ServiceStatus.STOPPED
                state.pid = None
        
        # Full health check - always check actual service status
        healthy = False
        
        # Try URL-based health check FIRST (most reliable)
        if config.health_check_url:
            try:
                response = requests.get(
                    config.health_check_url,
                    timeout=5
                )
                healthy = response.status_code < 500
                if healthy:
                    state.status = ServiceStatus.RUNNING
            except:
                healthy = False
        
        # Try command-based health check
        if not healthy and config.health_check_command:
            try:
                result = subprocess.run(
                    config.health_check_command,
                    capture_output=True,
                    timeout=5
                )
                healthy = result.returncode == 0
                if healthy:
                    state.status = ServiceStatus.RUNNING
            except:
                healthy = False
        
        # Try process pattern check
        if not healthy and config.process_pattern:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", config.process_pattern],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                healthy = result.returncode == 0
                if healthy and result.stdout.strip():
                    state.pid = int(result.stdout.strip().split('\n')[0])
                    state.status = ServiceStatus.RUNNING
            except:
                healthy = False
        
        # Update status if not healthy
        if not healthy and state.status == ServiceStatus.UNKNOWN:
            state.status = ServiceStatus.STOPPED
        
        state.last_health_check = datetime.now()
        state.last_health_status = healthy
        
        # Update circuit breaker
        if state.circuit_breaker:
            if healthy:
                state.circuit_breaker.record_success()
            else:
                state.circuit_breaker.record_failure(Exception("Health check failed"))
        
        return healthy
    
    def get_service_health(self, name: str) -> Dict[str, Any]:
        """Get detailed health status for a service."""
        if name not in self.services:
            return {"error": f"Unknown service: {name}"}
        
        state = self.services[name]
        config = state.config
        
        health = {
            "name": name,
            "status": state.status.value,
            "pid": state.pid,
            "uptime_seconds": (
                (datetime.now() - state.started_at).total_seconds()
                if state.started_at else 0
            ),
            "restart_count": state.restart_count,
            "last_health_check": (
                state.last_health_check.isoformat()
                if state.last_health_check else None
            ),
            "last_health_status": state.last_health_status,
            "last_error": state.last_error,
            "port": config.port
        }
        
        if state.circuit_breaker:
            health["circuit_breaker"] = state.circuit_breaker.get_stats()
        
        return health
    
    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all services."""
        return {
            name: self.get_service_health(name)
            for name in self.services
        }
    
    def start_all_services(self) -> Dict[str, bool]:
        """
        Start all services in dependency order.
        
        Returns:
            Dict mapping service name to start success
        """
        logger.info("Starting all services...")
        results = {}
        
        # Sort by priority
        sorted_services = sorted(
            self.services.items(),
            key=lambda x: x[1].config.priority.value
        )
        
        for name, state in sorted_services:
            results[name] = self.start_service(name)
            if not results[name]:
                logger.warning(f"Failed to start {name}, continuing...")
        
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """Stop all services in reverse dependency order."""
        logger.info("Stopping all services...")
        results = {}
        
        # Sort by priority (reverse)
        sorted_services = sorted(
            self.services.items(),
            key=lambda x: x[1].config.priority.value,
            reverse=True
        )
        
        for name, state in sorted_services:
            results[name] = self.stop_service(name)
        
        return results
    
    def auto_recover(self) -> Dict[str, bool]:
        """
        Automatically recover failed services.
        
        Returns:
            Dict mapping service name to recovery success
        """
        logger.info("Running auto-recovery check...")
        results = {}
        
        for name, state in self.services.items():
            config = state.config
            
            # Skip disabled services
            if state.status == ServiceStatus.DISABLED:
                continue
            
            # Check health
            healthy = self._check_health(name)
            
            if not healthy:
                logger.warning(f"Service {name} is unhealthy (status: {state.status})")
                
                # Check if auto-restart is enabled
                if not config.restart_on_failure:
                    logger.info(f"Auto-restart disabled for {name}")
                    continue
                
                # Check restart limit
                if state.restart_count >= config.max_restarts:
                    logger.error(
                        f"Service {name} exceeded max restarts "
                        f"({state.restart_count}/{config.max_restarts})"
                    )
                    self._add_to_dead_letter(name, "exceeded_max_restarts")
                    continue
                
                # Check circuit breaker
                if state.circuit_breaker and state.circuit_breaker.is_open:
                    logger.warning(
                        f"Service {name} circuit breaker is OPEN, "
                        f"waiting for recovery timeout"
                    )
                    continue
                
                # Calculate backoff delay
                delay = config.restart_delay * (
                    config.restart_backoff ** state.restart_count
                )
                delay = min(delay, 300)  # Max 5 minutes
                
                logger.info(
                    f"Attempting to recover {name} "
                    f"(attempt {state.restart_count + 1}/{config.max_restarts}, "
                    f"delay: {delay:.1f}s)"
                )
                
                time.sleep(delay)
                results[name] = self.restart_service(name)
            else:
                # Reset restart count on healthy check
                if state.restart_count > 0:
                    state.restart_count = 0
                results[name] = True
        
        return results
    
    def _add_to_dead_letter(self, service_name: str, reason: str):
        """Add failed service to dead letter queue."""
        entry = {
            "service": service_name,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "state": self.get_service_health(service_name)
        }
        
        self._dead_letter_queue.append(entry)
        
        # Trim queue if too large
        if len(self._dead_letter_queue) > self._max_dead_letter_size:
            self._dead_letter_queue = self._dead_letter_queue[-self._max_dead_letter_size:]
        
        logger.error(f"Added to dead letter queue: {service_name} - {reason}")
    
    def get_dead_letter_queue(self) -> List[Dict[str, Any]]:
        """Get dead letter queue contents."""
        return self._dead_letter_queue.copy()
    
    def start_monitoring(self, interval: float = 30.0):
        """
        Start background health monitoring.
        
        Args:
            interval: Seconds between health checks
        """
        if self._running:
            logger.warning("Monitoring already running")
            return
        
        self._running = True
        
        def monitor_loop():
            while self._running:
                try:
                    self.auto_recover()
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                
                time.sleep(interval)
        
        self._monitor_thread = threading.Thread(
            target=monitor_loop,
            daemon=True,
            name="ServiceMonitor"
        )
        self._monitor_thread.start()
        logger.info(f"Started service monitoring (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
        logger.info("Stopped service monitoring")
    
    def get_service_status_summary(self) -> Dict[str, Any]:
        """Get summary of all service statuses."""
        statuses = {}
        for name, state in self.services.items():
            statuses[name] = {
                "status": state.status.value,
                "healthy": state.last_health_status
            }
        
        return {
            "services": statuses,
            "running_count": sum(
                1 for s in self.services.values()
                if s.status == ServiceStatus.RUNNING
            ),
            "total_count": len(self.services),
            "dead_letter_count": len(self._dead_letter_queue),
            "monitoring_active": self._running
        }


# Global accessor
def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    return ServiceManager.get_instance()


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ELF Service Manager")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status", "health", "recover", "monitor"],
        help="Action to perform"
    )
    parser.add_argument(
        "--service", "-s",
        help="Specific service to act on"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Act on all services"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=30.0,
        help="Monitoring interval in seconds"
    )
    
    args = parser.parse_args()
    
    manager = get_service_manager()
    
    if args.action == "status":
        summary = manager.get_service_status_summary()
        print(json.dumps(summary, indent=2))
    
    elif args.action == "health":
        if args.service:
            health = manager.get_service_health(args.service)
        else:
            health = manager.get_all_health()
        print(json.dumps(health, indent=2))
    
    elif args.action == "start":
        if args.service:
            result = manager.start_service(args.service)
        elif args.all:
            result = manager.start_all_services()
        else:
            print("Specify --service or --all")
            sys.exit(1)
        print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
    
    elif args.action == "stop":
        if args.service:
            result = manager.stop_service(args.service)
        elif args.all:
            result = manager.stop_all_services()
        else:
            print("Specify --service or --all")
            sys.exit(1)
        print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
    
    elif args.action == "restart":
        if args.service:
            result = manager.restart_service(args.service)
            print(result)
        else:
            print("Specify --service")
            sys.exit(1)
    
    elif args.action == "recover":
        result = manager.auto_recover()
        print(json.dumps(result, indent=2))
    
    elif args.action == "monitor":
        print("Starting service monitoring...")
        manager.start_monitoring(args.interval)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            manager.stop_monitoring()