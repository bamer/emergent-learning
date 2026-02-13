#!/usr/bin/env python3
"""
ELF System Monitoring & Alerting Service

Monitors the ELF learning capture system and provides alerts:
- High failure embedding rate
- Database growth anomalies
- Learning capture health
- System performance issues

Usage:
    python elf_monitor.py start  # Run as daemon
    python elf_monitor.py once   # Run single check
"""

import json
import sqlite3
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_DIR / "memory" / "index.db"
ALERT_LOG = ELF_DIR / ".coordination" / "monitoring_alerts.log"
ESCALATION_DIR = ELF_DIR / ".coordination" / "escalations"

# Thresholds
MAX_FAILURES_PER_HOUR = 50
MAX_FAILURES_PER_24H = 200
EMBEDDING_RATE_THRESHOLD = 100  # embeddings/hour
DATABASE_SIZE_THRESHOLD_MB = 1000

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(ALERT_LOG), logging.StreamHandler()],
)
logger = logging.getLogger("ELFMonitor")


class ELFMonitor:
    """ELF system health monitoring and alerting."""

    def __init__(self):
        self.alerts_sent = []
        self.check_interval = 300  # 5 minutes
        self.max_alert_frequency = 3600  # Don't alert same issue within 1 hour

    def get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None

    def check_failure_rate(self) -> Optional[Dict]:
        """Check if failure embedding rate is too high."""
        conn = self.get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # Check failures in last hour
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM embeddings
                WHERE source_type = 'failure'
                AND created_at > datetime('now', '-1 hour')
            """)
            last_hour = cursor.fetchone()["count"]

            # Check failures in last 24 hours
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM embeddings
                WHERE source_type = 'failure'
                AND created_at > datetime('now', '-24 hours')
            """)
            last_24h = cursor.fetchone()["count"]

            # Get failure rate trend
            cursor.execute("""
                SELECT
                    substr(created_at, 1, 13) as hour_bucket,
                    COUNT(*) as count
                FROM embeddings
                WHERE source_type = 'failure'
                AND created_at > datetime('now', '-24 hours')
                GROUP BY hour_bucket
                ORDER BY hour_bucket
            """)
            trend = [
                {"hour": row["hour_bucket"], "count": row["count"]}
                for row in cursor.fetchall()
            ]

            conn.close()

            # Check thresholds
            if last_hour > MAX_FAILURES_PER_HOUR:
                return {
                    "alert_type": "HIGH_FAILURE_RATE_1H",
                    "severity": "CRITICAL",
                    "message": f"High failure rate: {last_hour} failures in last hour (threshold: {MAX_FAILURES_PER_HOUR}/hour)",
                    "metrics": {
                        "last_hour": last_hour,
                        "last_24h": last_24h,
                        "trend": trend,
                    },
                }
            elif last_24h > MAX_FAILURES_PER_24H:
                return {
                    "alert_type": "HIGH_FAILURE_RATE_24H",
                    "severity": "WARNING",
                    "message": f"High failure rate: {last_24h} failures in last 24h (threshold: {MAX_FAILURES_PER_24H}/24h)",
                    "metrics": {
                        "last_hour": last_hour,
                        "last_24h": last_24h,
                        "trend": trend,
                    },
                }

            return None

        except Exception as e:
            logger.error(f"Failure rate check error: {e}")
            conn.close()
            return None

    def check_embedding_rate(self) -> Optional[Dict]:
        """Check for abnormally high embedding rate (possible loop)."""
        conn = self.get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # Get embeddings per hour in last 4 hours
            cursor.execute("""
                SELECT
                    substr(created_at, 1, 13) as hour_bucket,
                    COUNT(*) as count,
                    source_type
                FROM embeddings
                WHERE created_at > datetime('now', '-4 hours')
                GROUP BY hour_bucket, source_type
                ORDER BY hour_bucket DESC, source_type
            """)
            results = cursor.fetchall()
            conn.close()

            # Check for hour with >100 embeddings
            for row in results:
                if row["count"] > EMBEDDING_RATE_THRESHOLD:
                    return {
                        "alert_type": "HIGH_EMBEDDING_RATE",
                        "severity": "WARNING",
                        "message": f"High embedding rate: {row['count']} embeddings in {row['hour_bucket']} (source: {row['source_type']})",
                        "metrics": {
                            "hour": row["hour_bucket"],
                            "count": row["count"],
                            "source_type": row["source_type"],
                        },
                    }

            return None

        except Exception as e:
            logger.error(f"Embedding rate check error: {e}")
            conn.close()
            return None

    def check_database_size(self) -> Optional[Dict]:
        """Check database size against threshold."""
        try:
            size_bytes = DB_PATH.stat().st_size
            size_mb = size_bytes / (1024 * 1024)

            if size_mb > DATABASE_SIZE_THRESHOLD_MB:
                return {
                    "alert_type": "DATABASE_SIZE_WARNING",
                    "severity": "INFO",
                    "message": f"Database size: {size_mb:.1f} MB (threshold: {DATABASE_SIZE_THRESHOLD_MB} MB)",
                    "metrics": {"size_mb": size_mb, "size_bytes": size_bytes},
                }

            return None

        except Exception as e:
            logger.error(f"Database size check error: {e}")
            return None

    def check_learning_capture_health(self) -> Optional[Dict]:
        """Check if learning capture is active and processing events."""
        try:
            # Check for recent embeddings (last 30 minutes)
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM embeddings
                WHERE created_at > datetime('now', '-30 minutes')
            """)
            recent_embeddings = cursor.fetchone()[0]

            conn.close()

            # If system is active but no recent embeddings, might be stalled
            # (This is a soft check - system might just be idle)
            return {
                "alert_type": "LEARNING_CAPTURE_HEALTH",
                "severity": "INFO",
                "message": f"Learning capture active: {recent_embeddings} embeddings in last 30 minutes",
                "metrics": {"recent_embeddings": recent_embeddings},
            }

        except Exception as e:
            logger.error(f"Learning capture health check error: {e}")
            return None

    def create_escalation(self, alert: Dict) -> str:
        """Create escalation markdown file for the alert."""
        escalation_id = (
            f"MONITOR_{alert['alert_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        escalation_file = ESCALATION_DIR / f"monitor_{escalation_id}.md"

        content = f"""# Monitoring Alert: {alert["alert_type"]}

## Alert Details
- **Type**: {alert["alert_type"]}
- **Severity**: {alert["severity"]}
- **Time**: {datetime.now().isoformat()}
- **Escalation ID**: {escalation_id}

## Message
{alert["message"]}

## Metrics
```json
{json.dumps(alert.get("metrics", {}), indent=2)}
```

## Recommended Actions
- Review the metrics above
- Investigate root cause
- Take corrective action if needed
- Monitor for resolution

## Context
This is an automated alert from the ELF monitoring service.

---
*Generated by ELF Monitor at {datetime.now().isoformat()}*
"""

        try:
            escalation_file.write_text(content)
            logger.info(f"✅ Escalation created: {escalation_file}")
            return str(escalation_file)
        except Exception as e:
            logger.error(f"Failed to create escalation: {e}")
            return ""

    def should_send_alert(self, alert_type: str) -> bool:
        """Check if alert should be sent (frequency limiting)."""
        now = datetime.now()

        # Remove old alert records (>1 hour)
        self.alerts_sent = [
            (alert_t, alert_type)
            for alert_t, alert_type in self.alerts_sent
            if now - alert_t < timedelta(seconds=self.max_alert_frequency)
        ]

        # Check if this alert type was sent recently
        for alert_t, a_type in self.alerts_sent:
            if a_type == alert_type:
                return False

        return True

    def send_alert(self, alert: Dict):
        """Send alert via multiple channels."""
        if not self.should_send_alert(alert["alert_type"]):
            logger.info(f"⏭️  Alert skipped (rate limited): {alert['alert_type']}")
            return

        # Log alert
        logger.warning(f"🚨 [{alert['severity']}] {alert['message']}")

        # Create escalation
        escalation_path = self.create_escalation(alert)

        # Record that we sent this alert
        self.alerts_sent.append((datetime.now(), alert["alert_type"]))

        # TODO: Add more notification channels (webhook, email, etc.)
        # For now, just logging and escalation file

    def run_checks(self):
        """Run all monitoring checks."""
        logger.info("🔍 Running ELF monitoring checks...")

        checks = [
            ("Failure Rate", self.check_failure_rate),
            ("Embedding Rate", self.check_embedding_rate),
            ("Database Size", self.check_database_size),
            ("Learning Capture Health", self.check_learning_capture_health),
        ]

        alerts_triggered = []

        for check_name, check_func in checks:
            try:
                alert = check_func()
                if alert:
                    logger.warning(f"⚠️  {check_name}: {alert['message']}")
                    self.send_alert(alert)
                    alerts_triggered.append(check_name)
                else:
                    logger.info(f"✅ {check_name}: Normal")
            except Exception as e:
                logger.error(f"❌ {check_name} check failed: {e}")

        if alerts_triggered:
            logger.warning(f"🚨 Alerts triggered: {', '.join(alerts_triggered)}")
        else:
            logger.info("✅ All checks passed - system healthy")

    def start(self):
        """Start continuous monitoring."""
        logger.info("=" * 60)
        logger.info("🚀 ELF Monitoring Service Starting")
        logger.info(f"   Check Interval: {self.check_interval}s")
        logger.info("=" * 60)

        try:
            while True:
                self.run_checks()
                logger.info(f"💤 Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down ELF Monitor...")
        finally:
            logger.info("✅ ELF Monitor stopped")

    def run_once(self):
        """Run single check cycle and exit."""
        logger.info("🎯 Running single monitoring cycle...")
        self.run_checks()
        logger.info("✅ Cycle complete")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ELF System Monitor")
    parser.add_argument(
        "command",
        choices=["start", "once"],
        help="start: Run as daemon, once: Run single cycle",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=300,
        help="Seconds between checks (default: 300)",
    )

    args = parser.parse_args()

    monitor = ELFMonitor()
    monitor.check_interval = args.check_interval

    if args.command == "start":
        monitor.start()
    else:
        monitor.run_once()


if __name__ == "__main__":
    main()
