#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Alert Agent - Centralized error monitoring and user notification
Ensures all failures are communicated to the user appropriately.
"""

import json
import time
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_critical,
        log_error,
        log_warning,
        log_info,
    )

    logger = get_logger("alert_agent")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("alert_agent")

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
ALERT_CONFIG = ELF_DIR / ".coordination" / "alert_config.json"

# Alert levels
ALERT_CRITICAL = 1  # Notify immediately via dashboard + desktop notification
ALERT_WARNING = 2  # Log and show in dashboard
ALERT_INFO = 3  # Just log


class AlertAgent:
    def __init__(self):
        self.alert_history = []
        self.last_notification = {}
        log_info("alert_agent", "🚀 Alert Agent initialized")

    def check_database_health(self):
        """Check all databases are accessible and non-empty"""
        issues = []
        memory_dir = ELF_DIR / "memory"

        critical_dbs = ["building.db", "conductor.db", "learning_database.db"]

        for db_name in critical_dbs:
            db_path = memory_dir / db_name
            if not db_path.exists():
                issues.append(
                    {
                        "level": ALERT_CRITICAL,
                        "source": "database",
                        "message": f"Critical database missing: {db_name}",
                        "action_required": f"Rebuild {db_name} immediately",
                    }
                )
            elif os.path.getsize(db_path) == 0:
                issues.append(
                    {
                        "level": ALERT_CRITICAL,
                        "source": "database",
                        "message": f"Critical database is empty: {db_name}",
                        "action_required": f"Restore or rebuild {db_name}",
                    }
                )

        return issues

    def check_agent_health(self):
        """Verify all required agents are running"""
        issues = []
        registry_path = ELF_DIR / ".coordination" / "agent_registry.json"

        try:
            with open(registry_path) as f:
                registry = json.load(f)

            registered = registry.get("registered_agents", {})

            required_agents = ["sentinel", "event_bridge", "learning_capture"]

            for agent in required_agents:
                if agent not in registered:
                    issues.append(
                        {
                            "level": ALERT_CRITICAL,
                            "source": "agent",
                            "message": f"Required agent not registered: {agent}",
                            "action_required": f"Register {agent} in agent_registry.json",
                        }
                    )
                else:
                    status = registered[agent].get("status", "unknown")
                    if status not in ["running", "ready"]:
                        issues.append(
                            {
                                "level": ALERT_WARNING,
                                "source": "agent",
                                "message": f"Agent {agent} status: {status}",
                                "action_required": f"Restart {agent} service",
                            }
                        )
        except Exception as e:
            issues.append(
                {
                    "level": ALERT_CRITICAL,
                    "source": "agent_registry",
                    "message": f"Cannot read agent registry: {e}",
                    "action_required": "Check agent_registry.json file",
                }
            )

        return issues

    def check_service_health(self):
        """Verify critical services are responding"""
        issues = []

        # Check dashboard endpoints
        try:
            import requests

            r = requests.get("http://localhost:8888/", timeout=5)
            if r.status_code != 200:
                issues.append(
                    {
                        "level": ALERT_WARNING,
                        "source": "service",
                        "message": f"Dashboard backend returning {r.status_code}",
                        "action_required": "Check uvicorn backend service",
                    }
                )
        except:
            issues.append(
                {
                    "level": ALERT_CRITICAL,
                    "source": "service",
                    "message": "Dashboard backend not responding on port 8888",
                    "action_required": "Start backend service: uvicorn main:app --port 8888",
                }
            )

        return issues

    def should_notify_user(self, issue):
        """Determine if this issue requires user notification"""
        source = issue["source"]
        level = issue["level"]
        current_time = datetime.now()

        # Critical issues: notify once per hour
        if level == ALERT_CRITICAL:
            if (
                source not in self.last_notification
                or (current_time - self.last_notification[source]).total_seconds()
                > 3600
            ):
                self.last_notification[source] = current_time
                return True

        # Warning issues: notify once per day
        if level == ALERT_WARNING:
            if (
                source not in self.last_notification
                or (current_time - self.last_notification[source]).total_seconds()
                > 86400
            ):
                self.last_notification[source] = current_time
                return True

        return False

    def send_notification(self, issues):
        """Send alert notifications to user"""
        critical_issues = [i for i in issues if i["level"] == ALERT_CRITICAL]
        warning_issues = [i for i in issues if i["level"] == ALERT_WARNING]

        if not critical_issues and not warning_issues:
            return

        # Format notification
        notification = {
            "timestamp": datetime.now().isoformat(),
            "critical_count": len(critical_issues),
            "warning_count": len(warning_issues),
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "requires_action": len(critical_issues) > 0,
        }

        # Log the notification
        self.logger.warning(
            f"🚨 ALERT: {len(critical_issues)} critical, {len(warning_issues)} warning issues detected"
        )

        # Save to alert history
        self.alert_history.append(notification)

        # Write to notification file for dashboard
        notification_file = ELF_DIR / ".coordination" / "pending_alerts.json"
        with open(notification_file, "w") as f:
            json.dump(notification, f, indent=2)

        # TODO: Add user notification channels:
        # - Desktop notification (if running GUI)
        # - Email notification
        # - Slack/Discord webhook
        # - SMS for critical issues

    def run_health_check(self):
        """Run comprehensive health check"""
        self.logger.info("🔍 Running system health check...")

        all_issues = []

        # Check databases
        all_issues.extend(self.check_database_health())

        # Check agents
        all_issues.extend(self.check_agent_health())

        # Check services
        all_issues.extend(self.check_service_health())

        # Send notifications for new issues
        if all_issues:
            self.send_notification(all_issues)
        else:
            # Clear alerts if system is healthy
            notification_file = ELF_DIR / ".coordination" / "pending_alerts.json"
            if notification_file.exists():
                os.remove(notification_file)
            self.logger.info("✅ System healthy - no alerts")

        return all_issues


if __name__ == "__main__":
    agent = AlertAgent()

    # Run initial health check
    issues = agent.run_health_check()

    if issues:
        log_warning("alert_agent", f"⚠️  Found {len(issues)} issues requiring attention")
        for issue in issues:
            log_warning(
                "alert_agent",
                f"  [{issue['level']}] {issue['source']}: {issue['message']}",
            )
    else:
        log_info("alert_agent", "✅ System is healthy")
