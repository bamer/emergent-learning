#!/usr/bin/env python3
"""
ELF System - Unified Entry Point with Auto-Recovery

This is the main entry point for the ELF system, providing:
1. Unified service management
2. Auto-recovery on failures
3. Health monitoring
4. Graceful shutdown

Usage:
    python elf_system.py start          # Start all services
    python elf_system.py stop           # Stop all services
    python elf_system.py status         # Show status
    python elf_system.py monitor        # Start with auto-recovery monitoring
    python elf_system.py recover        # Run auto-recovery once
"""

import argparse
import json

import os
import signal
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from Open_ELF.utils.elf_logging import get_logger
from typing import Dict, Any, Optional

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger("elf_system")

# Try to import components
try:
    from core.circuit_breaker import CircuitBreaker, save_circuit_stats_to_file
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    logger.warning("Circuit breaker not available")

try:
    from core.service_manager import ServiceManager, ServiceStatus, get_service_manager
    SERVICE_MANAGER_AVAILABLE = True
except ImportError as e:
    SERVICE_MANAGER_AVAILABLE = False
    logger.error(f"Service manager not available: {e}")


class ELFSystem:
    """
    Unified ELF System with auto-recovery capabilities.
    
    This class provides the main entry point for managing the ELF system,
    including service lifecycle, health monitoring, and auto-recovery.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the ELF system."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.running = False
        self.service_manager: Optional[ServiceManager] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._shutdown_requested = False
        self._coordination_dir = ELF_DIR / ".coordination"
        self._status_file = self._coordination_dir / "elf_system_status.json"
        
        # Initialize service manager if available
        if SERVICE_MANAGER_AVAILABLE:
            self.service_manager = get_service_manager()
        else:
            logger.error("Service manager not available - limited functionality")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self._initialized = True
        logger.info("ELF System initialized")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True
        self.stop()
        sys.exit(0)
    
    def start(self, services: Optional[list] = None) -> Dict[str, bool]:
        """
        Start the ELF system.
        
        Args:
            services: Optional list of specific services to start.
                     If None, starts all services.
        
        Returns:
            Dict mapping service name to start success
        """
        logger.info("=" * 60)
        logger.info("🚀 Starting ELF System")
        logger.info("=" * 60)
        
        if not self.service_manager:
            logger.error("Service manager not available")
            return {"error": "Service manager not available"}
        
        self.running = True
        self._update_status_file("starting")
        
        results = {}
        
        if services:
            # Start specific services
            for service in services:
                results[service] = self.service_manager.start_service(service)
        else:
            # Start all services in dependency order
            results = self.service_manager.start_all_services()
        
        # Update status
        self._update_status_file("running")
        
        # Print summary
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        logger.info("=" * 60)
        logger.info(f"✅ Started {success_count}/{total_count} services")
        logger.info("=" * 60)
        
        return results
    
    def stop(self) -> Dict[str, bool]:
        """
        Stop the ELF system.
        
        Returns:
            Dict mapping service name to stop success
        """
        logger.info("=" * 60)
        logger.info("🛑 Stopping ELF System")
        logger.info("=" * 60)
        
        self.running = False
        self._update_status_file("stopping")
        
        if not self.service_manager:
            return {"error": "Service manager not available"}
        
        # Stop monitoring first
        self.service_manager.stop_monitoring()
        
        # Stop all services
        results = self.service_manager.stop_all_services()
        
        self._update_status_file("stopped")
        
        logger.info("✅ ELF System stopped")
        return results
    
    def restart(self, services: Optional[list] = None) -> Dict[str, bool]:
        """
        Restart the ELF system or specific services.
        
        Args:
            services: Optional list of specific services to restart.
        
        Returns:
            Dict mapping service name to restart success
        """
        logger.info("🔄 Restarting ELF System...")
        
        self.stop()
        time.sleep(2)
        return self.start(services)
    
    def status(self) -> Dict[str, Any]:
        """
        Get system status.
        
        Returns:
            Dict with system status information
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "running": self.running,
            "shutdown_requested": self._shutdown_requested,
        }
        
        if self.service_manager:
            status["services"] = self.service_manager.get_all_health()
            status["summary"] = self.service_manager.get_service_status_summary()
        
        if CIRCUIT_BREAKER_AVAILABLE:
            status["circuit_breakers"] = CircuitBreaker.get_all_stats()
        
        return status
    
    def health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Dict with health information
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "healthy": True,
            "issues": [],
            "services": {}
        }
        
        if not self.service_manager:
            health["healthy"] = False
            health["issues"].append("Service manager not available")
            return health
        
        # Check each service with actual health checks
        for name, state in self.service_manager.services.items():
            # Perform actual health check
            is_healthy = self.service_manager._check_health(name)
            
            service_health = self.service_manager.get_service_health(name)
            health["services"][name] = {
                "healthy": is_healthy,
                "status": service_health.get("status"),
                "last_health_status": service_health.get("last_health_status"),
                "pid": service_health.get("pid")
            }
            
            if not is_healthy:
                health["healthy"] = False
                health["issues"].append(f"Service {name} is not healthy (status: {service_health.get('status')})")
        
        return health
    
    def recover(self) -> Dict[str, bool]:
        """
        Run auto-recovery for failed services.
        
        Returns:
            Dict mapping service name to recovery success
        """
        logger.info("🔧 Running auto-recovery...")
        
        if not self.service_manager:
            return {"error": "Service manager not available"}
        
        return self.service_manager.auto_recover()
    
    def monitor(self, interval: float = 30.0):
        """
        Start monitoring with auto-recovery.
        
        Args:
            interval: Seconds between health checks
        """
        logger.info(f"📊 Starting monitoring (interval: {interval}s)")
        
        if not self.service_manager:
            logger.error("Service manager not available")
            return
        
        self.running = True
        self._update_status_file("monitoring")
        
        # Start service manager monitoring
        self.service_manager.start_monitoring(interval)
        
        # Main monitoring loop
        try:
            while self.running and not self._shutdown_requested:
                # Periodic status update
                self._update_status_file("monitoring")
                
                # Save circuit breaker stats
                if CIRCUIT_BREAKER_AVAILABLE:
                    stats_file = self._coordination_dir / "circuit_breaker_stats.json"
                    save_circuit_stats_to_file(stats_file)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        finally:
            self.service_manager.stop_monitoring()
            self._update_status_file("stopped")
    
    def _update_status_file(self, state: str):
        """Update the status file for external monitoring."""
        try:
            self._coordination_dir.mkdir(parents=True, exist_ok=True)
            
            status = {
                "state": state,
                "timestamp": datetime.now().isoformat(),
                "pid": os.getpid(),
                "running": self.running
            }
            
            if self.service_manager:
                status["services"] = self.service_manager.get_service_status_summary()
            
            with open(self._status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update status file: {e}")


def get_elf_system() -> ELFSystem:
    """Get the global ELF system instance."""
    return ELFSystem()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ELF System - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python elf_system.py start              # Start all services
    python elf_system.py start -s sentinel  # Start specific service
    python elf_system.py stop               # Stop all services
    python elf_system.py status             # Show system status
    python elf_system.py health             # Health check
    python elf_system.py monitor            # Start with monitoring
    python elf_system.py recover            # Run auto-recovery
        """
    )
    
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status", "health", "monitor", "recover"],
        help="Action to perform"
    )
    
    parser.add_argument(
        "--service", "-s",
        action="append",
        help="Specific service(s) to act on (can be used multiple times)"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=30.0,
        help="Monitoring interval in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output in JSON format"
    )
    
    args = parser.parse_args()
    
    # Create ELF system instance
    elf = get_elf_system()
    
    # Execute action
    if args.action == "start":
        result = elf.start(args.service)
        if args.json:
            print(json.dumps(result, indent=2))
    
    elif args.action == "stop":
        result = elf.stop()
        if args.json:
            print(json.dumps(result, indent=2))
    
    elif args.action == "restart":
        result = elf.restart(args.service)
        if args.json:
            print(json.dumps(result, indent=2))
    
    elif args.action == "status":
        result = elf.status()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n" + "=" * 60)
            print("ELF System Status")
            print("=" * 60)
            
            summary = result.get("summary", {})
            print(f"\nRunning: {result.get('running', False)}")
            print(f"Services: {summary.get('running_count', 0)}/{summary.get('total_count', 0)}")
            
            services = result.get("services", {})
            for name, info in services.items():
                status = info.get("status", "unknown")
                emoji = "🟢" if status == "running" else "🔴" if status == "stopped" else "🟡"
                print(f"  {emoji} {name}: {status}")
            
            print()
    
    elif args.action == "health":
        result = elf.health()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            emoji = "✅" if result["healthy"] else "❌"
            print(f"\n{emoji} System Health: {'Healthy' if result['healthy'] else 'Unhealthy'}")
            
            if result["issues"]:
                print("\nIssues:")
                for issue in result["issues"]:
                    print(f"  ⚠️ {issue}")
            
            print()
    
    elif args.action == "monitor":
        print("Starting ELF System with monitoring...")
        print("Press Ctrl+C to stop\n")
        
        # Start services first
        elf.start(args.service)
        
        # Then monitor
        elf.monitor(args.interval)
    
    elif args.action == "recover":
        result = elf.recover()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\nAuto-Recovery Results:")
            for service, success in result.items():
                emoji = "✅" if success else "❌"
                print(f"  {emoji} {service}: {'Recovered' if success else 'Failed'}")
            print()


if __name__ == "__main__":
    main()