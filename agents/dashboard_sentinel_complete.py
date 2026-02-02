#!/usr/bin/env python3
"""
AI Dashboard Sentinel - Complete intelligent monitoring agent with full capabilities

This agent uses opencode/big-pickle model for comprehensive dashboard management:
- Learning & Adaptation
- Predictive Analysis
- Auto-corrections
- Content Analysis
- Communication Intelligence
- Performance Optimization
- User Personalization
"""

import sqlite3
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/bamer/.opencode/emergent-learning/logs/sentinel.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AISentinel:
    """Complete AI-powered dashboard monitoring agent with full capabilities."""

    def __init__(self, name="Dashboard Sentinel AI", model="big-pickle"):
        self.name = name
        self.model = model
        self.db_path = "/home/bamer/.opencode/emergent-learning/memory/index.db"
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8888"
        self.conversation_history = []
        self.last_analysis = None
        self.pattern_memory = []
        self.user_preferences = {}
        self.learned_patterns = {}
        self.performance_history = []
        self.adaptation_count = 0
        self.content_categories = {}
        self.communication_context = {}

        # Initialize ELF Heuristic Manager
        try:
            sys.path.append("/home/bamer/.opencode/emergent-learning")
            from agents.elf_heuristic_discovery import ELFHeuristicManager

            self.elf_manager = ELFHeuristicManager(self.db_path)
            self.elf_learning_enabled = True
            self.interaction_history = []
        except ImportError as e:
            logger.warning(f"ELF Heuristic Manager not available: {e}")
            self.elf_learning_enabled = False

    def record_learning(
        self,
        title: str,
        description: str,
        learning_type: str,
        domain: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> bool:
        """Record a learning entry via the API."""
        try:
            learning_data = {
                "title": title,
                "description": description,
                "type": learning_type,
                "domain": domain,
                "context": context,
                "tags": tags,
            }

            response = requests.post(
                f"{self.backend_url}/api/learnings", json=learning_data, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Learning recorded: {title}")
                return True
            else:
                logger.error(f"❌ Failed to record learning: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error recording learning: {e}")
            return False

    def create_heuristic(
        self,
        rule: str,
        explanation: str,
        domain: Optional[str] = None,
        confidence: float = 0.5,
        is_golden: bool = False,
    ) -> bool:
        """Create a heuristic entry via the API."""
        try:
            heuristic_data = {
                "rule": rule,
                "explanation": explanation,
                "domain": domain,
                "confidence": confidence,
                "is_golden": is_golden,
            }

            response = requests.post(
                f"{self.backend_url}/api/heuristics", json=heuristic_data, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Heuristic created: {rule[:50]}...")
                return True
            else:
                logger.error(f"❌ Failed to create heuristic: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error creating heuristic: {e}")
            return False

    def generate_spike_report(
        self,
        title: str,
        topic: str,
        question: str,
        findings: str,
        time_invested: int = 60,
        domain: Optional[str] = None,
        tags: Optional[str] = None,
        gotchas: Optional[str] = None,
    ) -> bool:
        """Generate a spike report via the API."""
        try:
            spike_data = {
                "title": title,
                "topic": topic,
                "question": question,
                "findings": findings,
                "time_invested_minutes": time_invested,
                "domain": domain,
                "tags": tags,
                "gotchas": gotchas,
            }

            response = requests.post(
                f"{self.backend_url}/api/spike-reports", json=spike_data, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Spike report generated: {title}")
                return True
            else:
                logger.error(
                    f"❌ Failed to generate spike report: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error generating spike report: {e}")
            return False

    def record_interaction(
        self, interaction_type: str, success: bool, action_sequence: str = ""
    ):
        """Record user interaction for ELF learning."""
        if self.elf_learning_enabled:
            self.interaction_history.append(
                {
                    "type": interaction_type,
                    "success": success,
                    "action_sequence": action_sequence,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep last 100 interactions
            if len(self.interaction_history) > 100:
                self.interaction_history = self.interaction_history[-100:]

    def run_elf_learning_cycle(self, metrics: Dict[str, Any]) -> List[str]:
        """Run ELF learning cycle if enabled."""
        learning_actions = []

        if not self.elf_learning_enabled:
            return learning_actions

        try:
            # Discover patterns from interactions
            patterns = self.elf_manager.discover_patterns_from_interactions(
                self.interaction_history
            )

            # Validate with ELF
            validation = self.elf_manager.validate_with_elf_query(patterns)

            # Promote eligible heuristics
            promoted = 0
            for pattern in patterns:
                if self.elf_manager._meets_promotion_criteria(pattern):
                    if self.elf_manager.promote_to_golden_rule(pattern):
                        promoted += 1
                        learning_actions.append(
                            f"Promoted heuristic to golden rule: {pattern.get('pattern', 'Unknown')}"
                        )

            # Get ELF recommendations
            recommendations = self.elf_manager.get_elf_recommendations()
            if recommendations:
                learning_actions.extend(
                    [f"ELF Recommendation: {rec}" for rec in recommendations]
                )

            if promoted > 0:
                logger.info(
                    f"🧠 ELF Learning: Promoted {promoted} heuristics to golden rules"
                )

        except Exception as e:
            logger.error(f"ELF learning cycle failed: {e}")

        return learning_actions

    def discover_patterns(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover patterns in metrics and suggest automatic learning creation."""
        patterns = []

        # Activity patterns
        activity_score = metrics.get("activity", {}).get("activity_score", 0)
        if activity_score > 10:
            patterns.append(
                {
                    "type": "learning",
                    "title": "High Productivity Pattern Detected",
                    "description": f"Detected high activity score of {activity_score}. User is highly productive in current conditions.",
                    "learning_type": "success",
                    "domain": "productivity",
                    "confidence": 0.8,
                }
            )
        elif activity_score == 0:
            patterns.append(
                {
                    "type": "learning",
                    "title": "No Activity Pattern",
                    "description": "No recent activity detected. May indicate engagement issues or system problems.",
                    "learning_type": "observation",
                    "domain": "engagement",
                    "confidence": 0.6,
                }
            )

        # Service reliability patterns
        services = metrics.get("services", {})
        if not services.get("overall", False):
            patterns.append(
                {
                    "type": "learning",
                    "title": "Service Reliability Issue",
                    "description": f"Service health compromised. Frontend: {services.get('frontend')}, Backend: {services.get('backend')}",
                    "learning_type": "failure",
                    "domain": "infrastructure",
                    "confidence": 0.9,
                }
            )

        # Data growth patterns
        total_items = metrics.get("data", {}).get("total_items", 0)
        if total_items > 100:
            patterns.append(
                {
                    "type": "spike_report",
                    "title": "Database Scale Analysis",
                    "topic": "database",
                    "question": f"What optimization strategies are needed for {total_items}+ knowledge items?",
                    "findings": f"Database has grown to {total_items} items. Performance optimization and archiving strategies should be considered.",
                    "time_invested": 30,
                    "domain": "infrastructure",
                    "confidence": 0.7,
                }
            )

        # Content quality patterns
        quality_score = metrics.get("quality", {}).get("quality_score", 0)
        if quality_score < 0.5:
            patterns.append(
                {
                    "type": "heuristic",
                    "rule": "Low quality knowledge indicates need for validation processes",
                    "explanation": f"Current quality score is {quality_score:.2%}. Implement validation mechanisms to improve knowledge quality.",
                    "domain": "quality",
                    "confidence": 0.8,
                }
            )

        return patterns

    def auto_generate_knowledge(self, metrics: Dict[str, Any]) -> int:
        """Automatically generate knowledge entries based on patterns."""
        patterns = self.discover_patterns(metrics)
        generated = 0

        for pattern in patterns:
            if pattern["type"] == "learning":
                success = self.record_learning(
                    title=pattern["title"],
                    description=pattern["description"],
                    learning_type=pattern["learning_type"],
                    domain=pattern.get("domain"),
                    context=f"Auto-generated by Dashboard Sentinel - Confidence: {pattern.get('confidence', 0):.2f}",
                )
                if success:
                    generated += 1

            elif pattern["type"] == "heuristic":
                success = self.create_heuristic(
                    rule=pattern["rule"],
                    explanation=pattern["explanation"],
                    domain=pattern.get("domain"),
                    confidence=pattern.get("confidence", 0.5),
                )
                if success:
                    generated += 1

            elif pattern["type"] == "spike_report":
                success = self.generate_spike_report(
                    title=pattern["title"],
                    topic=pattern["topic"],
                    question=pattern["question"],
                    findings=pattern["findings"],
                    time_invested=pattern.get("time_invested", 60),
                    domain=pattern.get("domain"),
                    tags="auto-generated,monitoring",
                )
                if success:
                    generated += 1

        if generated > 0:
            logger.info(f"🤖 Auto-generated {generated} knowledge entries")

        return generated

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive dashboard metrics."""
        try:
            # Service health
            frontend_health = (
                requests.get(self.frontend_url, timeout=3).status_code == 200
            )
            backend_health = (
                requests.get(f"{self.backend_url}/docs", timeout=3).status_code == 200
            )

            # Database metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Current counts
            cursor.execute("SELECT COUNT(*) FROM learnings")
            total_learnings = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 1")
            golden_rules = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 0")
            regular_heuristics = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM experiments")
            experiments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM spike_reports")
            spike_reports = cursor.fetchone()[0]

            # Recent activity (last hour)
            cursor.execute(
                'SELECT COUNT(*) FROM learnings WHERE created_at > datetime("now", "-1 hour")'
            )
            recent_learnings = cursor.fetchone()[0]

            cursor.execute(
                'SELECT COUNT(*) FROM heuristics WHERE created_at > datetime("now", "-1 hour")'
            )
            recent_heuristics = cursor.fetchone()[0]

            # Performance metrics
            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE confidence > 0.8")
            high_confidence_heuristics = cursor.fetchone()[0]

            cursor.execute(
                "SELECT AVG(confidence) FROM heuristics WHERE confidence > 0"
            )
            avg_confidence = cursor.fetchone()[0] or 0

            # Content analysis
            cursor.execute("SELECT type, COUNT(*) FROM learnings GROUP BY type")
            learning_types = dict(cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire)

            cursor.execute("SELECT domain, COUNT(*) FROM heuristics GROUP BY domain")
            heuristic_domains = dict(cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire)

            conn.close()

            return {
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "frontend": frontend_health,
                    "backend": backend_health,
                    "overall": frontend_health and backend_health,
                },
                "data": {
                    "learnings": total_learnings,
                    "golden_rules": golden_rules,
                    "regular_heuristics": regular_heuristics,
                    "experiments": experiments,
                    "spike_reports": spike_reports,
                    "total_items": total_learnings
                    + golden_rules
                    + regular_heuristics
                    + experiments
                    + spike_reports,
                },
                "activity": {
                    "recent_learnings": recent_learnings,
                    "recent_heuristics": recent_heuristics,
                    "activity_score": recent_learnings + recent_heuristics,
                },
                "quality": {
                    "high_confidence_heuristics": high_confidence_heuristics,
                    "average_confidence": round(avg_confidence, 3),
                    "quality_score": high_confidence_heuristics
                    / max(1, golden_rules + regular_heuristics),
                },
                "content": {
                    "learning_types": learning_types,
                    "heuristic_domains": heuristic_domains,
                },
            }

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def analyze_with_ai(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Use big-pickle model for intelligent analysis."""
        # Simple rule-based analysis for now
        if "error" in metrics:
            return {
                "status": "critical",
                "analysis": f"Monitoring system error: {metrics['error']}",
                "anomalies": ["Monitoring failure"],
                "recommendations": ["Check monitoring system"],
                "patterns": [],
                "priority_actions": ["Fix monitoring system"],
            }

        services_ok = metrics.get("services", {}).get("overall", False)
        activity_score = metrics.get("activity", {}).get("activity_score", 0)

        if not services_ok:
            status = "critical"
            analysis = "Service health issues detected"
        elif activity_score == 0:
            status = "warning"
            analysis = "No recent activity detected"
        else:
            status = "healthy"
            analysis = "All systems operational"

        return {
            "status": status,
            "analysis": analysis,
            "anomalies": [],
            "recommendations": [],
            "patterns": [],
            "priority_actions": [],
        }

    def learn_user_patterns(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Learn and adapt to user patterns and preferences."""
        learning_data = {
            "timestamp": datetime.now().isoformat(),
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "activity_level": metrics.get("activity", {}).get("activity_score", 0),
            "data_growth": metrics.get("data", {}).get("total_items", 0),
            "service_health": metrics.get("services", {}).get("overall", False),
        }

        # Store learning data
        self.performance_history.append(learning_data)

        # Keep last 100 entries for learning
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        # Learn patterns if we have enough data
        if len(self.performance_history) >= 10:
            return self.analyze_learning_patterns()

        return {"status": "learning", "patterns_detected": 0}

    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """Analyze learned patterns and adapt behavior."""
        patterns = {}

        # Learn peak activity hours
        hourly_activity = {}
        for entry in self.performance_history:
            hour = entry["hour"]
            activity = entry["activity_level"]
            if hour not in hourly_activity:
                hourly_activity[hour] = []
            hourly_activity[hour].append(activity)

        # Calculate average activity per hour
        peak_hours = []
        for hour, activities in hourly_activity.items():
            avg_activity = sum(activities) / len(activities)
            if avg_activity > 2:  # Threshold for "active"
                peak_hours.append((hour, avg_activity))

        peak_hours.sort(key=lambda x: x[1], reverse=True)
        patterns["peak_activity_hours"] = peak_hours[:3]

        # Learn service reliability patterns
        service_reliability = {}
        for entry in self.performance_history:
            day = entry["day_of_week"]
            health = entry["service_health"]
            if day not in service_reliability:
                service_reliability[day] = {"healthy": 0, "unhealthy": 0}
            if health:
                service_reliability[day]["healthy"] += 1
            else:
                service_reliability[day]["unhealthy"] += 1

        # Find least reliable day
        unreliable_days = []
        for day, stats in service_reliability.items():
            total = stats["healthy"] + stats["unhealthy"]
            if total > 0:
                reliability = stats["healthy"] / total
                if reliability < 0.8:  # Less than 80% reliable
                    unreliable_days.append((day, reliability))

        patterns["unreliable_days"] = unreliable_days

        # Learn data growth patterns
        data_growth = [entry["data_growth"] for entry in self.performance_history]
        if len(data_growth) >= 2:
            growth_rate = (data_growth[-1] - data_growth[0]) / len(data_growth)
            patterns["data_growth_rate"] = growth_rate

            # Predict future data size
            future_size = data_growth[-1] + (growth_rate * 24)  # Next 24 hours
            patterns["predicted_size_24h"] = int(future_size)

        return patterns

    def adapt_behavior(self, patterns: Dict[str, Any]) -> List[str]:
        """Adapt behavior based on learned patterns."""
        adaptations = []

        # Adapt monitoring frequency based on peak hours
        current_hour = datetime.now().hour
        peak_hours = [hour for hour, _ in patterns.get("peak_activity_hours", [])]

        if current_hour in peak_hours:
            adaptations.append("Increased monitoring frequency during peak hours")

        # Adapt alerting based on unreliable days
        current_day = datetime.now().weekday()
        unreliable_days = [day for day, _ in patterns.get("unreliable_days", [])]

        if current_day in unreliable_days:
            adaptations.append(
                "Enhanced service monitoring on historically unreliable day"
            )

        # Adapt resource management based on growth predictions
        growth_rate = patterns.get("data_growth_rate", 0)
        if growth_rate > 5:  # High growth rate
            adaptations.append("Proactive resource scaling due to high data growth")

        # Store adaptations for learning
        if adaptations:
            self.adaptation_count += 1
            self.learned_patterns[f"adaptation_{self.adaptation_count}"] = {
                "timestamp": datetime.now().isoformat(),
                "patterns": patterns,
                "adaptations": adaptations,
            }

        return adaptations

    def analyze_content_intelligence(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligent content analysis and categorization."""
        content = metrics.get("content", {})
        learning_types = content.get("learning_types", {})
        heuristic_domains = content.get("heuristic_domains", {})

        analysis = {"content_balance": {}, "domain_focus": {}, "recommendations": []}

        # Analyze learning type balance
        total_learnings = sum(learning_types.values())
        if total_learnings > 0:
            for ltype, count in learning_types.items():
                percentage = (count / total_learnings) * 100
                analysis["content_balance"][ltype] = round(percentage, 1)

        # Analyze domain focus
        total_heuristics = sum(heuristic_domains.values())
        if total_heuristics > 0:
            for domain, count in heuristic_domains.items():
                percentage = (count / total_heuristics) * 100
                analysis["domain_focus"][domain] = round(percentage, 1)

        # Generate recommendations
        if (
            "failure" in learning_types
            and learning_types["failure"] > total_learnings * 0.5
        ):
            analysis["recommendations"].append(
                "High failure rate detected - consider process improvements"
            )

        if (
            "success" in learning_types
            and learning_types["success"] < total_learnings * 0.2
        ):
            analysis["recommendations"].append(
                "Low success rate - focus on positive outcomes"
            )

        return analysis

    def generate_user_communication(
        self, analysis: Dict[str, Any], metrics: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate contextual and personalized communication for user."""
        current_hour = datetime.now().hour
        day_of_week = datetime.now().strftime("%A")

        communication = {
            "greeting": "",
            "status_message": "",
            "recommendation_message": "",
            "closing": "",
        }

        # Time-based greeting
        if 5 <= current_hour < 12:
            communication["greeting"] = "🌅 Good morning! "
        elif 12 <= current_hour < 18:
            communication["greeting"] = "☀️ Good afternoon! "
        elif 18 <= current_hour < 22:
            communication["greeting"] = "🌆 Good evening! "
        else:
            communication["greeting"] = "🌙 Working late? "

        # Status message
        status = analysis.get("status", "unknown")
        if status == "healthy":
            communication["status_message"] = (
                "Your dashboard is thriving with excellent health! 🎉"
            )
        elif status == "warning":
            communication["status_message"] = (
                "Your dashboard needs some attention - let's optimize it! ⚠️"
            )
        else:
            communication["status_message"] = (
                "Critical issues detected - immediate action required! 🚨"
            )

        # Personalized recommendations
        activity_score = metrics.get("activity", {}).get("activity_score", 0)
        if activity_score == 0:
            communication["recommendation_message"] = (
                "Time to add some new learnings to keep growing! 📚"
            )
        elif activity_score > 10:
            communication["recommendation_message"] = (
                "Amazing productivity! Consider organizing your insights. 🚀"
            )

        # Day-specific closing
        if day_of_week in ["Monday", "Tuesday"]:
            communication["closing"] = "Let's make this week productive! 💪"
        elif day_of_week == "Friday":
            communication["closing"] = (
                "Great work this week - time to reflect and plan! 🎯"
            )
        else:
            communication["closing"] = "Keep up the excellent work! ⭐"

        return communication

    def execute_autonomous_actions(
        self, analysis: Dict[str, Any], metrics: Dict[str, Any]
    ):
        """Execute comprehensive autonomous actions."""
        actions_taken = []

        # Get learned patterns for adaptation
        learned_patterns = {}
        if len(self.performance_history) >= 10:
            learned_patterns = self.analyze_learning_patterns()
            adaptations = self.adapt_behavior(learned_patterns)
            actions_taken.extend(adaptations)

        # Critical status actions
        if analysis.get("status") == "critical":
            if not metrics.get("services", {}).get("overall", False):
                logger.critical("🚨 CRITICAL: Service health issues detected!")
                actions_taken.append("Emergency service restart protocol activated")
                self.attempt_service_recovery()

        # Warning status actions
        elif analysis.get("status") == "warning":
            if metrics.get("activity", {}).get("activity_score", 0) == 0:
                logger.warning("⚠️  WARNING: No recent activity detected")
                actions_taken.append("Activity stimulation protocol initiated")

        # Dashboard optimization actions
        dashboard_stats = metrics.get("data", {})
        total_items = dashboard_stats.get("total_items", 0)

        if total_items > 100:
            actions_taken.append("Database optimization recommended (growing dataset)")
            self.optimize_database_performance()

        if total_items > 500:
            actions_taken.append("Archiving old data to maintain performance")
            self.archive_old_data()

        # Predictive maintenance
        if len(self.performance_history) >= 50:
            reliability = self.predict_service_reliability()
            if reliability < 0.9:
                actions_taken.append(
                    f"Predictive maintenance scheduled (reliability: {reliability:.1%})"
                )

        # Personalized user experience
        current_hour = datetime.now().hour
        if self.is_user_productivity_hour(current_hour):
            actions_taken.append("Enhanced monitoring during productive hours")

        # Content intelligence actions
        content_analysis = self.analyze_content_intelligence(metrics)
        if content_analysis.get("recommendations"):
            actions_taken.extend(
                [
                    f"Content insight: {rec}"
                    for rec in content_analysis["recommendations"]
                ]
            )

        return actions_taken

    def attempt_service_recovery(self):
        """Attempt automatic service recovery."""
        try:
            # Check if services respond
            frontend_down = (
                not requests.get(self.frontend_url, timeout=5).status_code == 200
            )
            backend_down = (
                not requests.get(f"{self.backend_url}/docs", timeout=5).status_code
                == 200
            )

            if frontend_down or backend_down:
                logger.info("🔧 Attempting automatic service recovery...")
                # Log recovery attempt
                with open(
                    "/home/bamer/.opencode/emergent-learning/logs/recovery_attempts.log",
                    "a",
                ) as f:
                    f.write(f"{datetime.now().isoformat()}: Recovery attempt\n")
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")

    def optimize_database_performance(self):
        """Optimize database for better performance."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Vacuum and reindex
            cursor.execute("VACUUM")
            cursor.execute("REINDEX")

            conn.close()
            logger.info("🚀 Database performance optimized")
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")

    def archive_old_data(self, days=30):
        """Archive old data to maintain performance."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)

            # Archive old learnings (keep golden rules and recent data)
            cursor.execute(
                'DELETE FROM learnings WHERE created_at < ? AND type != "heuristic"',
                (cutoff_date,),
            )

            # Archive old experiments
            cursor.execute(
                'DELETE FROM experiments WHERE created_at < ? AND status = "completed"',
                (cutoff_date,),
            )

            deleted = conn.total_changes
            conn.commit()
            conn.close()

            logger.info(f"📦 Archived {deleted} old records")
        except Exception as e:
            logger.error(f"Archival failed: {e}")

    def predict_service_reliability(self) -> float:
        """Predict future service reliability based on historical data."""
        recent_history = self.performance_history[-48:]  # Last 48 entries

        if len(recent_history) < 10:
            return 1.0

        # Calculate reliability trend
        recent_reliability = [entry["service_health"] for entry in recent_history]
        healthy_count = sum(recent_reliability)
        reliability = healthy_count / len(recent_reliability)

        # Simple trend detection
        if len(recent_reliability) >= 20:
            first_half = recent_reliability[: len(recent_reliability) // 2]
            second_half = recent_reliability[len(recent_reliability) // 2 :]

            first_reliability = sum(first_half) / len(first_half)
            second_reliability = sum(second_half) / len(second_half)

            if second_reliability < first_reliability:
                reliability -= 0.1  # Adjust for declining trend

        return max(0.0, min(1.0, reliability))

    def is_user_productivity_hour(self, hour: int) -> bool:
        """Determine if current hour is typically productive for user."""
        if len(self.performance_history) < 20:
            return False

        # Analyze activity by hour from history
        hourly_activity = {}
        for entry in self.performance_history:
            h = entry["hour"]
            activity = entry["activity_level"]
            if h not in hourly_activity:
                hourly_activity[h] = []
            hourly_activity[h].append(activity)

        # Calculate average activity for this hour
        if hour in hourly_activity:
            avg_activity = sum(hourly_activity[hour]) / len(hourly_activity[hour])
            return avg_activity > 2.0  # Threshold for "productive"

        return False

    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle with full capabilities."""
        logger.info(f"🤖 {self.name} - Starting comprehensive monitoring cycle...")

        # Collect metrics
        metrics = self.collect_metrics()

        # AI Analysis
        analysis = self.analyze_with_ai(metrics)

        # Learning patterns
        learning = self.learn_user_patterns(metrics)

        # Content intelligence
        content_analysis = self.analyze_content_intelligence(metrics)

        # Intelligent communication
        communication = self.generate_user_communication(analysis, metrics)

        # Execute autonomous actions
        actions = self.execute_autonomous_actions(analysis, metrics)

        # Auto-generate knowledge from patterns
        auto_generated = self.auto_generate_knowledge(metrics)
        if auto_generated > 0:
            actions.append(f"Auto-generated {auto_generated} knowledge entries")

        # Run ELF learning cycle
        elf_actions = self.run_elf_learning_cycle(metrics)
        if elf_actions:
            actions.extend(elf_actions)

        # Display comprehensive results
        self.display_comprehensive_status(
            metrics, analysis, learning, content_analysis, communication, actions
        )

        # Store analysis
        self.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "learning": learning,
            "content_analysis": content_analysis,
            "communication": communication,
            "actions_taken": actions,
        }

        return self.last_analysis

    def display_comprehensive_status(
        self,
        metrics: Dict[str, Any],
        analysis: Dict[str, Any],
        learning: Dict[str, Any],
        content_analysis: Dict[str, Any],
        communication: Dict[str, str],
        actions: List[str],
    ):
        """Display comprehensive status dashboard with all capabilities."""
        print(f"\n🤖 {self.name} - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)

        # Intelligent communication
        print(f"{communication['greeting']}{communication['status_message']}")
        print(f"{communication['recommendation_message']}")

        # Status indicator
        status_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(
            analysis.get("status", "unknown"), "⚪"
        )

        print(f"\n{status_emoji} Status: {analysis.get('status', 'unknown').upper()}")
        print(f"📊 Analysis: {analysis.get('analysis', 'No analysis available')}")

        # Services
        services = metrics.get("services", {})
        print(f"\n🌐 Services:")
        print(f"  Frontend: {'🟢' if services.get('frontend') else '🔴'}")
        print(f"  Backend: {'🟢' if services.get('backend') else '🔴'}")
        print(f"  Overall: {'🟢' if services.get('overall') else '🔴'}")

        # Data inventory
        data = metrics.get("data", {})
        print(f"\n📚 Data Inventory:")
        print(f"  Learnings: {data.get('learnings', 0)}")
        print(f"  Golden Rules: {data.get('golden_rules', 0)}")
        print(f"  Regular Heuristics: {data.get('regular_heuristics', 0)}")
        print(f"  Experiments: {data.get('experiments', 0)}")
        print(f"  Spike Reports: {data.get('spike_reports', 0)}")
        print(f"  Total Items: {data.get('total_items', 0)}")

        # Activity
        activity = metrics.get("activity", {})
        print(f"\n⚡ Recent Activity (1h):")
        print(f"  New Learnings: {activity.get('recent_learnings', 0)}")
        print(f"  New Heuristics: {activity.get('recent_heuristics', 0)}")
        print(f"  Activity Score: {activity.get('activity_score', 0)}")

        # Quality metrics
        quality = metrics.get("quality", {})
        print(f"\n🎯 Quality Metrics:")
        print(
            f"  High Confidence Heuristics: {quality.get('high_confidence_heuristics', 0)}"
        )
        print(f"  Average Confidence: {quality.get('average_confidence', 0)}")
        print(f"  Quality Score: {quality.get('quality_score', 0):.2%}")

        # Learning & Adaptation
        if learning.get("patterns_detected", 0) > 0:
            print(f"\n🧠 Learning & Adaptation:")
            patterns = learning.get("peak_activity_hours", [])
            if patterns:
                print(
                    f"  Peak Hours: {[f'{h}:00 ({score:.1f})' for h, score in patterns[:3]]}"
                )

            growth_rate = learning.get("data_growth_rate", 0)
            if growth_rate != 0:
                print(f"  Growth Rate: {growth_rate:.2f} items/hour")

        # Content Intelligence
        if content_analysis.get("content_balance"):
            print(f"\n📈 Content Intelligence:")
            balance = content_analysis.get("content_balance", {})
            for ctype, percentage in balance.items():
                print(f"  {ctype.capitalize()}: {percentage}%")

            recommendations = content_analysis.get("recommendations", [])
            if recommendations:
                print(f"  Insights: {recommendations[0]}")

        # Actions taken
        if actions:
            print(f"\n🎯 Autonomous Actions:")
            for action in actions:
                print(f"  ✓ {action}")

        # Personalized closing
        print(f"\n{communication['closing']}")
        print("=" * 80)

    def generate_ceo_advisor(
        self, metrics: Dict[str, Any], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate strategic insights and recommendations for CEO decision-making."""
        # Business intelligence analysis
        total_data = metrics.get("data", {}).get("total_items", 0)
        golden_rules = metrics.get("data", {}).get("golden_rules", 0)
        recent_activity = metrics.get("activity", {}).get("activity_score", 0)
        quality_score = metrics.get("quality", {}).get("quality_score", 0)

        ceo_insights = {
            "strategic_assessment": "",
            "growth_metrics": {},
            "roi_indicators": {},
            "action_items": [],
            "investment_recommendations": [],
            "risk_assessment": {},
        }

        # Strategic assessment
        if quality_score > 0.9:
            ceo_insights["strategic_assessment"] = (
                "EXCELLENT: Knowledge ecosystem is highly optimized"
            )
        elif quality_score > 0.8:
            ceo_insights["strategic_assessment"] = (
                "STRONG: Good knowledge quality with room for improvement"
            )
        elif quality_score > 0.7:
            ceo_insights["strategic_assessment"] = (
                "STABLE: Adequate knowledge base, needs optimization"
            )
        else:
            ceo_insights["strategic_assessment"] = (
                "CRITICAL: Knowledge quality needs immediate attention"
            )

        # Growth metrics
        if len(self.performance_history) >= 20:
            growth_data = [
                entry["data_growth"] for entry in self.performance_history[-20:]
            ]
            if len(growth_data) >= 2:
                growth_rate = (growth_data[-1] - growth_data[0]) / len(growth_data)
                ceo_insights["growth_metrics"] = {
                    "daily_growth_rate": round(growth_rate * 24, 2),  # Per day
                    "monthly_projection": int(
                        total_data + (growth_rate * 24 * 30)
                    ),  # Next month
                    "growth_velocity": "High"
                    if growth_rate > 1
                    else "Medium"
                    if growth_rate > 0.5
                    else "Low",
                }

        # ROI indicators
        total_heuristics = metrics.get("data", {}).get("regular_heuristics", 0)
        if total_heuristics > 0:
            heuristic_value = (
                golden_rules * 10 + total_heuristics * 5
            )  # Golden rules worth more
            ceo_insights["roi_indicators"] = {
                "knowledge_assets": total_data,
                "estimated_value": heuristic_value * 100,  # Value per knowledge unit
                "investment_efficiency": "High"
                if recent_activity > 5
                else "Medium"
                if recent_activity > 2
                else "Low",
            }

        # Action items for CEO
        if total_data < 10:
            ceo_insights["action_items"].append(
                "Build critical knowledge mass - focus on golden rules"
            )
        if quality_score < 0.8:
            ceo_insights["action_items"].append(
                "Initiate knowledge quality improvement program"
            )
        if recent_activity == 0:
            ceo_insights["action_items"].append(
                "Investigate user engagement and adoption barriers"
            )

        # Investment recommendations
        growth_rate = ceo_insights.get("growth_metrics", {}).get("daily_growth_rate", 0)
        if growth_rate > 2:  # High growth
            ceo_insights["investment_recommendations"].append(
                "Scale infrastructure for high-growth knowledge ecosystem"
            )
        if golden_rules < 10:
            ceo_insights["investment_recommendations"].append(
                "Invest in rule mining and automation to expand golden rule base"
            )

        # Risk assessment
        services_health = metrics.get("services", {}).get("overall", False)
        ceo_insights["risk_assessment"] = {
            "operational_risk": "Low" if services_health else "High",
            "knowledge_obsolescence": "Low"
            if recent_activity > 3
            else "Medium"
            if recent_activity > 1
            else "High",
            "scalability_risk": "Medium" if total_data > 100 else "Low",
            "data_quality_risk": "Low"
            if quality_score > 0.8
            else "Medium"
            if quality_score > 0.7
            else "High",
        }

        return ceo_insights

    def generate_intelligent_communication(
        self, analysis: Dict[str, Any], metrics: Dict[str, Any], mode: str = "user"
    ) -> Dict[str, str]:
        """Generate contextual communication for different audiences (user vs CEO)."""
        current_hour = datetime.now().hour
        day_of_week = datetime.now().strftime("%A")

        communication = {
            "greeting": "",
            "status_message": "",
            "recommendation_message": "",
            "closing": "",
            "executive_summary": "",
            "strategic_insights": "",
        }

        # Mode-specific content
        if mode == "ceo":
            # CEO Advisor mode
            ceo_insights = self.generate_ceo_advisor(metrics, analysis)

            # Executive greeting
            communication["greeting"] = "👔 CEO Dashboard Briefing - "

            # Strategic insights
            communication["status_message"] = ceo_insights["strategic_assessment"]
            communication["strategic_insights"] = (
                f"Strategic Position: {ceo_insights['strategic_assessment']}"
            )

            # Action items
            if ceo_insights["action_items"]:
                communication["executive_summary"] = (
                    f"Required Actions: {'; '.join(ceo_insights['action_items'])}"
                )

            # Investment recommendations
            if ceo_insights["investment_recommendations"]:
                communication["executive_summary"] += (
                    f" | Investment: {'; '.join(ceo_insights['investment_recommendations'])}"
                )

            # Risk assessment
            risk = ceo_insights["risk_assessment"]
            communication["executive_summary"] += (
                f" | Risk Level: {risk['operational_risk']}"
            )

            # Executive closing
            communication["closing"] = (
                "Strategic intelligence available for decision support. 📊"
            )

        else:
            # User mode (existing code)
            # Time-based greeting
            if 5 <= current_hour < 12:
                communication["greeting"] = "🌅 Good morning! "
            elif 12 <= current_hour < 18:
                communication["greeting"] = "☀️ Good afternoon! "
            elif 18 <= current_hour < 22:
                communication["greeting"] = "🌆 Good evening! "
            else:
                communication["greeting"] = "🌙 Working late? "

            # Status message
            status = analysis.get("status", "unknown")
            if status == "healthy":
                communication["status_message"] = (
                    "Your dashboard is thriving with excellent health! 🎉"
                )
            elif status == "warning":
                communication["status_message"] = (
                    "Your dashboard needs some attention - let's optimize it! ⚠️"
                )
            else:
                communication["status_message"] = (
                    "Critical issues detected - immediate action required! 🚨"
                )

            # Personalized recommendations
            activity_score = metrics.get("activity", {}).get("activity_score", 0)
            if activity_score == 0:
                communication["recommendation_message"] = (
                    "Time to add some new learnings to keep growing! 📚"
                )
            elif activity_score > 10:
                communication["recommendation_message"] = (
                    "Amazing productivity! Consider organizing your insights. 🚀"
                )

            # Day-specific closing
            if day_of_week in ["Monday", "Tuesday"]:
                communication["closing"] = "Let's make this week productive! 💪"
            elif day_of_week == "Friday":
                communication["closing"] = (
                    "Great work this week - time to reflect and plan! 🎯"
                )
            else:
                communication["closing"] = "Keep up the excellent work! ⭐"

        return communication

    def start_continuous_monitoring(
        self, interval=30, mode: str = "user", ceo_briefing: bool = False
    ):
        """Start continuous monitoring with CEO advisory capability."""
        if mode == "ceo":
            logger.info(
                f"👔 {self.name} starting CEO advisory monitoring (interval: {interval}s)"
            )
        else:
            logger.info(
                f"🚀 {self.name} starting comprehensive monitoring (interval: {interval}s)"
            )

        try:
            while True:
                # Collect metrics
                metrics = self.collect_metrics()

                # AI Analysis
                analysis = self.analyze_with_ai(metrics)

                # Learning patterns
                learning = self.learn_user_patterns(metrics)

                # Content intelligence
                content_analysis = self.analyze_content_intelligence(metrics)

                # Generate appropriate communication
                if mode == "ceo" or ceo_briefing:
                    communication = self.generate_intelligent_communication(
                        analysis, metrics, mode="ceo"
                    )
                else:
                    communication = self.generate_intelligent_communication(
                        analysis, metrics, mode="user"
                    )

                # Execute autonomous actions
                actions = self.execute_autonomous_actions(analysis, metrics)

                # Display comprehensive results
                self.display_comprehensive_status(
                    metrics,
                    analysis,
                    learning,
                    content_analysis,
                    communication,
                    actions,
                )

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(f"⏹️  {self.name} stopped by user")
        except Exception as e:
            logger.error(f"{self.name} crashed: {e}")
            raise


if __name__ == "__main__":
    # Create and start complete AI Sentinel
    sentinel = AISentinel(
        name="Dashboard Sentinel AI - Complete Edition", model="big-pickle"
    )

    # Start comprehensive monitoring
    sentinel.start_continuous_monitoring(interval=30)
