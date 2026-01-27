#!/usr/bin/env python3
"""
AI Dashboard Sentinel - Intelligent monitoring agent with Claude Haiku model

This agent uses Claude Haiku for intelligent analysis of dashboard health,
pattern recognition, and autonomous decision-making.
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

# Add Claude Code integration
try:
    from task import Task
except ImportError:
    print("Warning: Task tool not available, falling back to simple monitoring")
    Task = None

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
    """AI-powered dashboard monitoring agent with adaptive learning capabilities."""

    def __init__(self, name="Dashboard Sentinel AI", model="big-pickle"):
        self.name = name
        self.model = model
        self.db_path = "/home/bamer/.claude/emergent-learning/memory/index.db"
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8888"
        self.conversation_history = []
        self.last_analysis = None
        self.pattern_memory = []
        self.user_preferences = {}
        self.learned_patterns = {}
        self.performance_history = []
        self.adaptation_count = 0

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
            }

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def analyze_with_ai(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Use Claude Haiku for intelligent analysis of metrics."""
        if not Task:
            return self.fallback_analysis(metrics)

        try:
            # Prepare analysis prompt for Claude Haiku
            prompt = f"""
You are the Dashboard Sentinel AI, monitoring the Emergent Learning Framework dashboard.

Current metrics:
{json.dumps(metrics, indent=2)}

Your tasks:
1. Analyze the health and patterns in this data
2. Identify any anomalies or concerns
3. Suggest improvements or actions
4. Detect patterns in the activity
5. Provide a concise status assessment

Respond with JSON format:
{{
    "status": "healthy|warning|critical",
    "analysis": "brief analysis of current state",
    "anomalies": ["list of detected anomalies"],
    "recommendations": ["list of suggestions"],
    "patterns": ["observed patterns"],
    "priority_actions": ["most important actions to take"]
}}
"""

            # Use Task tool with Claude Haiku
            task_result = Task(
                description="Analyze dashboard metrics",
                prompt=prompt,
                subagent_type="general-purpose",
                session_id="sentinel_analysis",
            )

            # Parse AI response
            if hasattr(task_result, "result"):
                analysis = json.loads(task_result.result)
                return analysis
            else:
                return self.fallback_analysis(metrics)

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self.fallback_analysis(metrics)

    def fallback_analysis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI is not available."""
        if "error" in metrics:
            return {
                "status": "critical",
                "analysis": f"Monitoring system error: {metrics['error']}",
                "anomalies": ["Monitoring failure"],
                "recommendations": ["Check monitoring system"],
                "patterns": [],
                "priority_actions": ["Fix monitoring system"],
            }

        # Simple rule-based analysis
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
            'timestamp': datetime.now().isoformat(),
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'activity_level': metrics.get('activity', {}).get('activity_score', 0),
            'data_growth': metrics.get('data', {}).get('total_items', 0),
            'service_health': metrics.get('services', {}).get('overall', False)
        }
        
        # Store learning data
        self.performance_history.append(learning_data)
        
        # Keep last 100 entries for learning
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Learn patterns if we have enough data
        if len(self.performance_history) >= 10:
            return self.analyze_learning_patterns()
        
        return {'status': 'learning', 'patterns_detected': 0}
    
    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """Analyze learned patterns and adapt behavior."""
        patterns = {}
        
        # Learn peak activity hours
        hourly_activity = {}
        for entry in self.performance_history:
            hour = entry['hour']
            activity = entry['activity_level']
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
        patterns['peak_activity_hours'] = peak_hours[:3]
        
        # Learn service reliability patterns
        service_reliability = {}
        for entry in self.performance_history:
            day = entry['day_of_week']
            health = entry['service_health']
            if day not in service_reliability:
                service_reliability[day] = {'healthy': 0, 'unhealthy': 0}
            if health:
                service_reliability[day]['healthy'] += 1
            else:
                service_reliability[day]['unhealthy'] += 1
        
        # Find least reliable day
        unreliable_days = []
        for day, stats in service_reliability.items():
            total = stats['healthy'] + stats['unhealthy']
            if total > 0:
                reliability = stats['healthy'] / total
                if reliability < 0.8:  # Less than 80% reliable
                    unreliable_days.append((day, reliability))
        
        patterns['unreliable_days'] = unreliable_days
        
        # Learn data growth patterns
        data_growth = [entry['data_growth'] for entry in self.performance_history]
        if len(data_growth) >= 2:
            growth_rate = (data_growth[-1] - data_growth[0]) / len(data_growth)
            patterns['data_growth_rate'] = growth_rate
            
            # Predict future data size
            future_size = data_growth[-1] + (growth_rate * 24)  # Next 24 hours
            patterns['predicted_size_24h'] = int(future_size)
        
        return patterns
    
    def adapt_behavior(self, patterns: Dict[str, Any]) -> List[str]:
        """Adapt behavior based on learned patterns."""
        adaptations = []
        
        # Adapt monitoring frequency based on peak hours
        current_hour = datetime.now().hour
        peak_hours = [hour for hour, _ in patterns.get('peak_activity_hours', [])]
        
        if current_hour in peak_hours:
            adaptations.append("Increased monitoring frequency during peak hours")
            # Could dynamically adjust monitoring interval here
        
        # Adapt alerting based on unreliable days
        current_day = datetime.now().weekday()
        unreliable_days = [day for day, _ in patterns.get('unreliable_days', [])]
        
        if current_day in unreliable_days:
            adaptations.append("Enhanced service monitoring on historically unreliable day")
        
        # Adapt resource management based on growth predictions
        growth_rate = patterns.get('data_growth_rate', 0)
        if growth_rate > 5:  # High growth rate
            adaptations.append("Proactive resource scaling due to high data growth")
        
        # Store adaptations for learning
        if adaptations:
            self.adaptation_count += 1
            self.learned_patterns[f'adaptation_{self.adaptation_count}'] = {
                'timestamp': datetime.now().isoformat(),
                'patterns': patterns,
                'adaptations': adaptations
            }
        
        return adaptations
    
    def detect_patterns(self, current_metrics: Dict[str, Any]) -> List[str]:
        """Detect patterns in metrics over time with learning enhancement."""
        patterns = []
        
        # Store current metrics in pattern memory
        self.pattern_memory.append({
            'timestamp': datetime.now(),
            'metrics': current_metrics
        })
        
        # Keep only last 50 entries
        if len(self.pattern_memory) > 50:
            self.pattern_memory = self.pattern_memory[-50:]
        
        # Analyze patterns if we have enough data
        if len(self.pattern_memory) >= 5:
            # Check for declining activity
            recent_activity = [entry['metrics'].get('activity', {}).get('activity_score', 0) 
                              for entry in self.pattern_memory[-5:]]
            if all(recent_activity[i] <= recent_activity[i-1] for i in range(1, len(recent_activity))):
                patterns.append('Declining activity trend detected')
            
            # Check for service instability
            recent_services = [entry['metrics'].get('services', {}).get('overall', False) 
                               for entry in self.pattern_memory[-10:]]
            if not all(recent_services):
                patterns.append('Service instability detected')
            
            # Enhanced pattern detection with learning
            if len(self.pattern_memory) >= 20:
                # Learn cyclical patterns
                activity_cycle = self.detect_activity_cycles()
                if activity_cycle:
                    patterns.append(f'Cyclical pattern detected: {activity_cycle}')
        
        return patterns
    
    def detect_activity_cycles(self) -> Optional[str]:
        """Detect cyclical patterns in activity."""
        if len(self.pattern_memory) < 20:
            return None
        
        # Extract activity scores
        activities = [entry['metrics'].get('activity', {}).get('activity_score', 0) 
                      for entry in self.pattern_memory[-20:]]
        
        # Simple cycle detection (could be enhanced with FFT)
        # Look for repeating patterns every ~10 entries
        cycle_length = 10
        if len(activities) >= cycle_length * 2:
            first_cycle = activities[:cycle_length]
            second_cycle = activities[cycle_length:cycle_length*2]
            
            # Calculate similarity
            similarity = sum(1 for i in range(cycle_length) 
                           if abs(first_cycle[i] - second_cycle[i]) < 2) / cycle_length
            
            if similarity > 0.7:  # 70% similarity
                return f"Activity cycle of {cycle_length} intervals detected"
        
        return None

    def execute_autonomous_actions(
        self, analysis: Dict[str, Any], metrics: Dict[str, Any]
    ):
        """Execute autonomous actions based on AI analysis."""
        actions_taken = []

        # Critical status actions
        if analysis.get("status") == "critical":
            if not metrics.get("services", {}).get("overall", False):
                logger.critical("🚨 CRITICAL: Service health issues detected!")
                # Could attempt service restart here

        # Warning status actions
        elif analysis.get("status") == "warning":
            if metrics.get("activity", {}).get("activity_score", 0) == 0:
                logger.warning("⚠️  WARNING: No recent activity detected")

        # Log patterns detected
        patterns = analysis.get("patterns", [])
        if patterns:
            logger.info(f"🔍 Patterns detected: {', '.join(patterns)}")

        # Execute priority actions
        for action in analysis.get("priority_actions", []):
            logger.info(f"🎯 Priority action: {action}")
            actions_taken.append(action)

        return actions_taken

    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle."""
        logger.info(f"🤖 {self.name} - Starting monitoring cycle...")

        # Collect metrics
        metrics = self.collect_metrics()

        # AI Analysis
        analysis = self.analyze_with_ai(metrics)

        # Pattern detection
        patterns = self.detect_patterns(metrics)
        analysis["patterns"].extend(patterns)

        # Display results
        self.display_status(metrics, analysis)

        # Execute autonomous actions
        actions = self.execute_autonomous_actions(analysis, metrics)

        # Store analysis
        self.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "actions_taken": actions,
        }

        return self.last_analysis

    def display_status(self, metrics: Dict[str, Any], analysis: Dict[str, Any]):
        """Display comprehensive status dashboard."""
        print(f"\n🤖 {self.name} - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)

        # Status indicator
        status_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(
            analysis.get("status", "unknown"), "⚪"
        )

        print(f"{status_emoji} Status: {analysis.get('status', 'unknown').upper()}")
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

        # Anomalies and recommendations
        anomalies = analysis.get("anomalies", [])
        if anomalies:
            print(f"\n⚠️  Anomalies:")
            for anomaly in anomalies:
                print(f"  • {anomaly}")

        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")

        # Patterns
        patterns = analysis.get("patterns", [])
        if patterns:
            print(f"\n🔍 Patterns Detected:")
            for pattern in patterns:
                print(f"  • {pattern}")

        print("\n" + "=" * 60)

    def start_continuous_monitoring(self, interval=30):
        """Start continuous monitoring with specified interval."""
        logger.info(
            f"🚀 {self.name} starting continuous monitoring (interval: {interval}s)"
        )

        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(f"⏹️  {self.name} stopped by user")
        except Exception as e:
            logger.error(f"{self.name} crashed: {e}")
            raise


if __name__ == "__main__":
    # Create and start AI Sentinel
    sentinel = AISentinel(name="Dashboard Sentinel AI", model="haiku")

    # Start monitoring
    sentinel.start_continuous_monitoring(interval=30)
