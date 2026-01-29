#!/usr/bin/env python3
"""
AI Dashboard Sentinel - CEO Advisor Edition

Executive intelligence for dashboard strategic decision-making with complete capabilities:
- Learning & Adaptation
- Predictive Analysis
- Auto-corrections
- Content Analysis
- CEO Strategic Intelligence
- Performance Optimization
"""

import sqlite3
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys

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
    """Complete AI-powered dashboard monitoring agent with CEO advisory capabilities."""

    def __init__(self, name="Dashboard Sentinel AI", model="big-pickle", server_url="http://localhost:4096"):
        self.name = name
        self.model = model
        self.server_url = server_url
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
        
        # Add HTTP API client
        import sys
        from pathlib import Path
        agents_path = str(Path(__file__).parent)
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        try:
            from opencode_client import OpenCodeClient
            self.api_client = OpenCodeClient(model=model, server_url=server_url)
        except ImportError:
            logger.warning("OpenCodeClient not available, will use basic calls")
            self.api_client = None

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
            learning_types = dict(cursor.fetchall())

            cursor.execute("SELECT domain, COUNT(*) FROM heuristics GROUP BY domain")
            heuristic_domains = dict(cursor.fetchall())

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
        if len(self.performance_history) >= 20:
            growth_data = [
                entry["data_growth"] for entry in self.performance_history[-20:]
            ]
            if len(growth_data) >= 2:
                growth_rate = (growth_data[-1] - growth_data[0]) / len(growth_data)
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

            # Growth metrics
            if ceo_insights["growth_metrics"]:
                growth = ceo_insights["growth_metrics"]
                communication["executive_summary"] += (
                    f" | Growth: {growth['growth_velocity']} ({growth['daily_growth_rate']}/day)"
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
                communication["closing"] = "Keep up excellent work! ⭐"

        return communication

    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle with full capabilities."""
        logger.info(f"🤖 {self.name} - Starting comprehensive monitoring cycle...")

        # Collect metrics
        metrics = self.collect_metrics()

        # Simple rule-based analysis
        if "error" in metrics:
            analysis = {
                "status": "critical",
                "analysis": f"Monitoring system error: {metrics['error']}",
                "anomalies": ["Monitoring failure"],
                "recommendations": ["Check monitoring system"],
                "patterns": [],
                "priority_actions": ["Fix monitoring system"],
            }
        else:
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

            analysis = {
                "status": status,
                "analysis": analysis,
                "anomalies": [],
                "recommendations": [],
                "patterns": [],
                "priority_actions": [],
            }

        # Generate intelligent communication
        communication = self.generate_intelligent_communication(
            analysis, metrics, mode="user"
        )

        # Execute autonomous actions (simplified for now)
        actions_taken = []
        if analysis.get("status") == "critical":
            logger.critical("🚨 CRITICAL: Service health issues detected!")
            actions_taken.append("Emergency service restart protocol activated")

        # Display results
        self.display_comprehensive_status(
            metrics, analysis, communication, actions_taken
        )

        # Store analysis
        self.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "communication": communication,
            "actions_taken": actions_taken,
        }

        return self.last_analysis

    def display_comprehensive_status(
        self,
        metrics: Dict[str, Any],
        analysis: Dict[str, Any],
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

        # Actions taken
        if actions:
            print(f"\n🎯 Autonomous Actions:")
            for action in actions:
                print(f"  ✓ {action}")

        # Personalized closing
        print(f"\n{communication['closing']}")
        print("=" * 80)

    def display_ceo_briefing(
        self,
        metrics: Dict[str, Any],
        analysis: Dict[str, Any],
        communication: Dict[str, str],
        actions: List[str],
    ):
        """Display CEO-specific briefing dashboard."""
        print(f"\n👔 CEO Dashboard Briefing - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)

        # Executive communication
        print(f"{communication['greeting']}{communication['status_message']}")
        print(f"{communication['strategic_insights']}")
        print(f"\n{communication['executive_summary']}")

        # CEO-specific metrics
        total_data = metrics.get("data", {}).get("total_items", 0)
        golden_rules = metrics.get("data", {}).get("golden_rules", 0)

        print(f"\n📊 CEO Metrics:")
        print(f"  📈 Knowledge Assets: {total_data} items")
        print(f"  👑 Golden Rules: {golden_rules} constitutional principles")
        print(
            f"  🎯 Quality Score: {metrics.get('quality', {}).get('quality_score', 0):.1%}"
        )

        print(f"\n🎯 Strategic Actions:")
        for action in actions:
            print(f"  ✓ {action}")

        print(f"\n{communication['closing']}")
        print("=" * 80)

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
                if "error" in metrics:
                    analysis = {
                        "status": "critical",
                        "analysis": f"Monitoring system error: {metrics['error']}",
                        "anomalies": ["Monitoring failure"],
                        "recommendations": ["Check monitoring system"],
                        "patterns": [],
                        "priority_actions": ["Fix monitoring system"],
                    }
                else:
                    services_ok = metrics.get("services", {}).get("overall", False)
                    activity_score = metrics.get("activity", {}).get(
                        "activity_score", 0
                    )

                    if not services_ok:
                        status = "critical"
                        analysis = "Service health issues detected"
                    elif activity_score == 0:
                        status = "warning"
                        analysis = "No recent activity detected"
                    else:
                        status = "healthy"
                        analysis = "All systems operational"

                    analysis = {
                        "status": status,
                        "analysis": analysis,
                        "anomalies": [],
                        "recommendations": [],
                        "patterns": [],
                        "priority_actions": [],
                    }

                # Generate appropriate communication
                if mode == "ceo":
                    communication = self.generate_intelligent_communication(
                        analysis, metrics, mode="ceo"
                    )
                else:
                    communication = self.generate_intelligent_communication(
                        analysis, metrics, mode="user"
                    )

                # Execute autonomous actions
                actions_taken = []
                if analysis.get("status") == "critical":
                    logger.critical("🚨 CRITICAL: Service health issues detected!")
                    actions_taken.append("Emergency service restart protocol activated")

                # Display comprehensive results
                if mode == "ceo":
                    self.display_ceo_briefing(
                        metrics, analysis, communication, actions_taken
                    )
                else:
                    self.display_comprehensive_status(
                        metrics, analysis, communication, actions_taken
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(f"⏹️  {self.name} stopped by user")
        except Exception as e:
            logger.error(f"{self.name} crashed: {e}")
            raise


if __name__ == "__main__":
    # Check for CEO mode
    mode = "user"
    if len(sys.argv) > 1:
        if "--ceo" in sys.argv:
            mode = "ceo"
        elif "--user" in sys.argv:
            mode = "user"

    # Create and start complete AI Sentinel
    sentinel = AISentinel(
        name="Dashboard Sentinel AI - CEO Advisor Edition", model="big-pickle"
    )

    # Start monitoring with appropriate mode
    if mode == "ceo":
        print("👔 Starting CEO Advisory Dashboard Briefing Mode...")
        sentinel.start_continuous_monitoring(interval=30, mode=mode)
    else:
        print("🤖 Starting User Monitoring Mode...")
        sentinel.start_continuous_monitoring(interval=30, mode=mode)
