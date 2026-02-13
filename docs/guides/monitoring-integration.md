# ELF Monitoring Integration Guide

This guide explains how to integrate with and utilize the ELF monitoring system to track system performance, health, and learning metrics.

## 🎯 Understanding ELF Monitoring

The ELF monitoring system provides comprehensive visibility into the framework through multiple layers:

### Monitoring Components
1. **EventBridge Monitoring** (Port 9998) - Core event processing metrics
2. **System Monitoring** (Port 9997) - Overall system health and performance
3. **Dashboard Monitoring** (Port 8888) - Web interface metrics
4. **Learning Processor Monitoring** - AI learning and heuristic generation metrics

### Key Metrics Tracked
- **Event Processing**: Events per minute, event types, processing latency
- **System Health**: Component status, uptime, resource utilization
- **Learning Metrics**: Heuristics generated, golden rules, trails created
- **Agent Performance**: Mission completion rates, execution times
- **Tool Usage**: Tool detection and execution frequency

## 🚀 Monitoring API Overview

### Base URLs
```
EventBridge Monitoring: http://localhost:9998
System Monitoring: http://localhost:9997
Dashboard Monitoring: http://localhost:8888
```

### Authentication
Currently no authentication required for local development.

### Common Headers
```
Content-Type: application/json
Accept: application/json
```

## 📋 Key Monitoring Endpoints

### System Monitoring (Port 9997)
- `GET /` - Quick monitoring summary
- `GET /stats` - Detailed system statistics
- `GET /health` - Overall system health
- `GET /api/v1/summary` - API summary
- `GET /api/v1/architecture` - Architecture information
- `GET /api/v1/learning` - Learning statistics
- `GET /api/v1/events` - Event statistics

### EventBridge Monitoring (Port 9998)
- `GET /status` - EventBridge status
- `GET /api/v1/health` - Overall health
- `GET /api/v1/health/{component}` - Component health

## 🎯 Practical Monitoring Examples

### 1. Get System Health Overview

```bash
# Get overall system health
curl -X GET http://localhost:9997/health
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "components": {
      "event_bridge": "healthy",
      "learning_processor": "healthy",
      "sentinel": "healthy",
      "orchestrator": "healthy",
      "ceo": "healthy"
    },
    "timestamp": "2026-02-12T10:30:15Z"
  }
}
```

### 2. Get Detailed System Statistics

```bash
# Get detailed system statistics
curl -X GET http://localhost:9997/stats
```

### 3. Monitor Event Processing

```bash
# Get event processing statistics
curl -X GET http://localhost:9997/api/v1/events
```

### 4. Check Learning Metrics

```bash
# Get learning system statistics
curl -X GET http://localhost:9997/api/v1/learning
```

## 🐍 Python Monitoring Integration

```python
import requests
import json
import time
from datetime import datetime, timedelta

class ELFMonitor:
    def __init__(self, system_url="http://localhost:9997", 
                 eventbridge_url="http://localhost:9998"):
        self.system_url = system_url
        self.eventbridge_url = eventbridge_url
    
    def get_system_health(self):
        """Get overall system health status."""
        try:
            response = requests.get(f"{self.system_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting system health: {e}")
            return None
    
    def get_detailed_stats(self):
        """Get detailed system statistics."""
        try:
            response = requests.get(f"{self.system_url}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting detailed stats: {e}")
            return None
    
    def get_eventbridge_status(self):
        """Get EventBridge status."""
        try:
            response = requests.get(f"{self.eventbridge_url}/status", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting EventBridge status: {e}")
            return None
    
    def get_component_health(self, component):
        """Get health status for a specific component."""
        try:
            response = requests.get(
                f"{self.eventbridge_url}/api/v1/health/{component}", 
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting {component} health: {e}")
            return None
    
    def generate_health_report(self):
        """Generate a comprehensive health report."""
        print("=" * 60)
        print("                    ELF Health Report")
        print("=" * 60)
        
        # System Health
        health = self.get_system_health()
        if health and health.get("status") == "success":
            data = health["data"]
            status_icons = {
                "healthy": "🟢",
                "degraded": "🟡",
                "unhealthy": "🔴"
            }
            status_icon = status_icons.get(data["status"], "❓")
            print(f"Overall Status:  {status_icon} {data['status'].upper()}")
            print(f"Report Time:     {data['timestamp']}")
        else:
            print("Overall Status:  ❓ UNKNOWN")
        
        print("-" * 60)
        
        # Component Health
        components = ["event_bridge", "mission_bridge", "sentinel_monitor"]
        print("Component Health:")
        for component in components:
            comp_health = self.get_component_health(component)
            if comp_health and comp_health.get("status") == "success":
                comp_data = comp_health["data"]
                comp_icon = status_icons.get(comp_data["status"], "❓")
                print(f"  {comp_icon} {component.replace('_', ' ').title()}: {comp_data['status'].upper()}")
            else:
                print(f"  ❓ {component.replace('_', ' ').title()}: UNKNOWN")
        
        print("-" * 60)
        
        # EventBridge Status
        eb_status = self.get_eventbridge_status()
        if eb_status and eb_status.get("status") == "success":
            eb_data = eb_status["data"]
            eb_icon = "🟢" if eb_data["running"] else "🔴"
            print(f"EventBridge:     {eb_icon} {'RUNNING' if eb_data['running'] else 'STOPPED'}")
            print(f"Events Processed: {eb_data.get('events_processed', 0):,}")
            print(f"Uptime:          {eb_data.get('uptime_seconds', 0)} seconds")
        else:
            print("EventBridge:     ❓ UNKNOWN")
        
        print("=" * 60)
    
    def monitor_continuously(self, interval=60):
        """Continuously monitor system health."""
        print(f"Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        try:
            while True:
                # Get health status
                health = self.get_system_health()
                eb_status = self.get_eventbridge_status()
                
                if health and health.get("status") == "success":
                    overall_status = health["data"]["status"]
                    status_icons = {
                        "healthy": "🟢",
                        "degraded": "🟡",
                        "unhealthy": "🔴"
                    }
                    status_icon = status_icons.get(overall_status, "❓")
                    
                    # Get events processed
                    events_processed = 0
                    if eb_status and eb_status.get("status") == "success":
                        events_processed = eb_status["data"].get("events_processed", 0)
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {status_icon} {overall_status.upper()} | "
                          f"Events: {events_processed:,}")
                else:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] ❓ UNKNOWN")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
    
    def get_performance_metrics(self):
        """Get key performance metrics."""
        stats = self.get_detailed_stats()
        
        if not stats or stats.get("status") != "success":
            return None
        
        data = stats["data"]
        
        # Extract key metrics
        metrics = {
            "timestamp": data.get("timestamp"),
            "uptime": data.get("uptime_seconds", 0),
            "events_per_minute": data.get("events", {}).get("per_minute", 0),
            "heuristics": data.get("learning", {}).get("heuristics", 0),
            "golden_rules": data.get("learning", {}).get("golden_rules", 0),
            "trails": data.get("learning", {}).get("trails", 0),
            "tools_detected": data.get("tools", {}).get("tools_detected", 0),
            "database_size_kb": data.get("database", {}).get("size_kb", 0)
        }
        
        return metrics
    
    def alert_on_anomalies(self, metrics):
        """Check for anomalous conditions and alert."""
        alerts = []
        
        # High event rate
        if metrics["events_per_minute"] > 1000:
            alerts.append(f"⚠️  High event rate: {metrics['events_per_minute']:.1f}/min")
        
        # Low learning activity
        if metrics["heuristics"] < 10 and metrics["uptime"] > 3600:  # 1 hour
            alerts.append(f"⚠️  Low learning activity: {metrics['heuristics']} heuristics")
        
        # Large database
        if metrics["database_size_kb"] > 100000:  # 100MB
            alerts.append(f"⚠️  Large database: {metrics['database_size_kb']:,} KB")
        
        return alerts
    
    def generate_performance_report(self):
        """Generate a performance report."""
        print("=" * 70)
        print("                   ELF Performance Report")
        print("=" * 70)
        
        metrics = self.get_performance_metrics()
        if not metrics:
            print("❌ Failed to retrieve performance metrics")
            return
        
        # Basic metrics
        uptime_hours = metrics["uptime"] / 3600
        print(f"Report Time:     {metrics['timestamp']}")
        print(f"Uptime:          {uptime_hours:.1f} hours")
        print(f"Database Size:   {metrics['database_size_kb']:,} KB")
        
        print("-" * 70)
        
        # Event processing
        print("Event Processing:")
        print(f"  Events/Minute:   {metrics['events_per_minute']:.1f}")
        print(f"  Tools Detected:  {metrics['tools_detected']:,}")
        
        print("-" * 70)
        
        # Learning metrics
        print("Learning Metrics:")
        print(f"  Heuristics:      {metrics['heuristics']:,}")
        print(f"  Golden Rules:    {metrics['golden_rules']:,}")
        print(f"  Trails:          {metrics['trails']:,}")
        
        print("-" * 70)
        
        # Anomaly detection
        alerts = self.alert_on_anomalies(metrics)
        if alerts:
            print("⚠️  Alerts:")
            for alert in alerts:
                print(f"  {alert}")
        else:
            print("✅ No anomalies detected")
        
        print("=" * 70)

# Usage example
if __name__ == "__main__":
    monitor = ELFMonitor()
    
    # Generate health report
    monitor.generate_health_report()
    
    print("\n")
    
    # Generate performance report
    monitor.generate_performance_report()
    
    # Uncomment to start continuous monitoring
    # monitor.monitor_continuously(30)  # Check every 30 seconds
```

## 📄 JavaScript Monitoring Integration

```javascript
class ELFMonitor {
    constructor(systemUrl = 'http://localhost:9997', 
                eventbridgeUrl = 'http://localhost:9998') {
        this.systemUrl = systemUrl;
        this.eventbridgeUrl = eventbridgeUrl;
    }
    
    async getSystemHealth() {
        try {
            const response = await fetch(`${this.systemUrl}/health`, { timeout: 10000 });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting system health:', error);
            return null;
        }
    }
    
    async getDetailedStats() {
        try {
            const response = await fetch(`${this.systemUrl}/stats`, { timeout: 10000 });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting detailed stats:', error);
            return null;
        }
    }
    
    async getEventBridgeStatus() {
        try {
            const response = await fetch(`${this.eventbridgeUrl}/status`, { timeout: 10000 });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting EventBridge status:', error);
            return null;
        }
    }
    
    async getComponentHealth(component) {
        try {
            const response = await fetch(
                `${this.eventbridgeUrl}/api/v1/health/${component}`, 
                { timeout: 10000 }
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error getting ${component} health:`, error);
            return null;
        }
    }
    
    async generateHealthReport() {
        console.log("=".repeat(60));
        console.log("                    ELF Health Report");
        console.log("=".repeat(60));
        
        // System Health
        const health = await this.getSystemHealth();
        if (health && health.status === "success") {
            const data = health.data;
            const statusIcons = {
                "healthy": "🟢",
                "degraded": "🟡",
                "unhealthy": "🔴"
            };
            const statusIcon = statusIcons[data.status] || "❓";
            console.log(`Overall Status:  ${statusIcon} ${data.status.toUpperCase()}`);
            console.log(`Report Time:     ${data.timestamp}`);
        } else {
            console.log("Overall Status:  ❓ UNKNOWN");
        }
        
        console.log("-".repeat(60));
        
        // Component Health
        const components = ["event_bridge", "mission_bridge", "sentinel_monitor"];
        console.log("Component Health:");
        for (const component of components) {
            const compHealth = await this.getComponentHealth(component);
            if (compHealth && compHealth.status === "success") {
                const compData = compHealth.data;
                const compIcon = statusIcons[compData.status] || "❓";
                console.log(`  ${compIcon} ${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${compData.status.toUpperCase()}`);
            } else {
                console.log(`  ❓ ${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: UNKNOWN`);
            }
        }
        
        console.log("-".repeat(60));
        
        // EventBridge Status
        const ebStatus = await this.getEventBridgeStatus();
        if (ebStatus && ebStatus.status === "success") {
            const ebData = ebStatus.data;
            const ebIcon = ebData.running ? "🟢" : "🔴";
            console.log(`EventBridge:     ${ebIcon} ${ebData.running ? 'RUNNING' : 'STOPPED'}`);
            console.log(`Events Processed: ${ebData.events_processed?.toLocaleString() || 0}`);
            console.log(`Uptime:          ${ebData.uptime_seconds || 0} seconds`);
        } else {
            console.log("EventBridge:     ❓ UNKNOWN");
        }
        
        console.log("=".repeat(60));
    }
    
    async monitorContinuously(interval = 60000) {
        console.log(`Starting continuous monitoring (interval: ${interval/1000}s)`);
        console.log("Press Ctrl+C to stop");
        console.log("-".repeat(60));
        
        const monitorLoop = async () => {
            try {
                // Get health status
                const health = await this.getSystemHealth();
                const ebStatus = await this.getEventBridgeStatus();
                
                if (health && health.status === "success") {
                    const overallStatus = health.data.status;
                    const statusIcons = {
                        "healthy": "🟢",
                        "degraded": "🟡",
                        "unhealthy": "🔴"
                    };
                    const statusIcon = statusIcons[overallStatus] || "❓";
                    
                    // Get events processed
                    let eventsProcessed = 0;
                    if (ebStatus && ebStatus.status === "success") {
                        eventsProcessed = ebStatus.data.events_processed || 0;
                    }
                    
                    const timestamp = new Date().toLocaleTimeString();
                    console.log(`[${timestamp}] ${statusIcon} ${overallStatus.toUpperCase()} | Events: ${eventsProcessed.toLocaleString()}`);
                } else {
                    const timestamp = new Date().toLocaleTimeString();
                    console.log(`[${timestamp}] ❓ UNKNOWN`);
                }
            } catch (error) {
                console.error('Monitoring error:', error);
            }
        };
        
        // Run immediately
        await monitorLoop();
        
        // Set up interval
        const intervalId = setInterval(monitorLoop, interval);
        
        // Handle graceful shutdown
        process.on('SIGINT', () => {
            console.log('\nStopping monitoring...');
            clearInterval(intervalId);
            process.exit(0);
        });
    }
    
    async getPerformanceMetrics() {
        const stats = await this.getDetailedStats();
        
        if (!stats || stats.status !== "success") {
            return null;
        }
        
        const data = stats.data;
        
        // Extract key metrics
        return {
            timestamp: data.timestamp,
            uptime: data.uptime_seconds || 0,
            eventsPerMinute: data.events?.per_minute || 0,
            heuristics: data.learning?.heuristics || 0,
            goldenRules: data.learning?.golden_rules || 0,
            trails: data.learning?.trails || 0,
            toolsDetected: data.tools?.tools_detected || 0,
            databaseSizeKb: data.database?.size_kb || 0
        };
    }
    
    alertOnAnomalies(metrics) {
        const alerts = [];
        
        // High event rate
        if (metrics.eventsPerMinute > 1000) {
            alerts.push(`⚠️  High event rate: ${metrics.eventsPerMinute.toFixed(1)}/min`);
        }
        
        // Low learning activity
        if (metrics.heuristics < 10 && metrics.uptime > 3600) { // 1 hour
            alerts.push(`⚠️  Low learning activity: ${metrics.heuristics} heuristics`);
        }
        
        // Large database
        if (metrics.databaseSizeKb > 100000) { // 100MB
            alerts.push(`⚠️  Large database: ${metrics.databaseSizeKb.toLocaleString()} KB`);
        }
        
        return alerts;
    }
    
    async generatePerformanceReport() {
        console.log("=".repeat(70));
        console.log("                   ELF Performance Report");
        console.log("=".repeat(70));
        
        const metrics = await this.getPerformanceMetrics();
        if (!metrics) {
            console.log("❌ Failed to retrieve performance metrics");
            return;
        }
        
        // Basic metrics
        const uptimeHours = metrics.uptime / 3600;
        console.log(`Report Time:     ${metrics.timestamp}`);
        console.log(`Uptime:          ${uptimeHours.toFixed(1)} hours`);
        console.log(`Database Size:   ${metrics.databaseSizeKb.toLocaleString()} KB`);
        
        console.log("-".repeat(70));
        
        // Event processing
        console.log("Event Processing:");
        console.log(`  Events/Minute:   ${metrics.eventsPerMinute.toFixed(1)}`);
        console.log(`  Tools Detected:  ${metrics.toolsDetected.toLocaleString()}`);
        
        console.log("-".repeat(70));
        
        // Learning metrics
        console.log("Learning Metrics:");
        console.log(`  Heuristics:      ${metrics.heuristics.toLocaleString()}`);
        console.log(`  Golden Rules:    ${metrics.goldenRules.toLocaleString()}`);
        console.log(`  Trails:          ${metrics.trails.toLocaleString()}`);
        
        console.log("-".repeat(70));
        
        // Anomaly detection
        const alerts = this.alertOnAnomalies(metrics);
        if (alerts.length > 0) {
            console.log("⚠️  Alerts:");
            alerts.forEach(alert => console.log(`  ${alert}`));
        } else {
            console.log("✅ No anomalies detected");
        }
        
        console.log("=".repeat(70));
    }
}

// Usage example
(async () => {
    const monitor = new ELFMonitor();
    
    // Generate health report
    await monitor.generateHealthReport();
    
    console.log("\n");
    
    // Generate performance report
    await monitor.generatePerformanceReport();
    
    // Uncomment to start continuous monitoring
    // await monitor.monitorContinuously(30000); // Check every 30 seconds
})();
```

## 🎯 Advanced Monitoring Patterns

### 1. Custom Metric Collection

```python
class CustomMetricCollector:
    def __init__(self, monitor):
        self.monitor = monitor
        self.custom_metrics = {}
    
    def record_custom_metric(self, name, value, tags=None):
        """Record a custom metric."""
        if name not in self.custom_metrics:
            self.custom_metrics[name] = []
        
        self.custom_metrics[name].append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or {}
        })
    
    def get_metric_statistics(self, name):
        """Get statistics for a custom metric."""
        if name not in self.custom_metrics:
            return None
        
        values = [m["value"] for m in self.custom_metrics[name]]
        if not values:
            return None
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }
    
    def export_metrics(self, format="json"):
        """Export metrics in specified format."""
        if format == "json":
            return json.dumps(self.custom_metrics, indent=2)
        elif format == "csv":
            # Convert to CSV format
            csv_lines = ["metric,timestamp,value,tags"]
            for metric_name, measurements in self.custom_metrics.items():
                for measurement in measurements:
                    tags_str = ",".join([f"{k}:{v}" for k, v in measurement["tags"].items()])
                    csv_lines.append(
                        f"{metric_name},{measurement['timestamp']},"
                        f"{measurement['value']},{tags_str}"
                    )
            return "\n".join(csv_lines)
```

### 2. Alerting System

```python
class AlertingSystem:
    def __init__(self, monitor):
        self.monitor = monitor
        self.alert_rules = []
        self.alert_history = []
    
    def add_alert_rule(self, name, condition, severity="medium"):
        """Add an alert rule."""
        self.alert_rules.append({
            "name": name,
            "condition": condition,
            "severity": severity,
            "enabled": True
        })
    
    def evaluate_alerts(self):
        """Evaluate all alert rules."""
        active_alerts = []
        
        for rule in self.alert_rules:
            if not rule["enabled"]:
                continue
            
            try:
                if rule["condition"]():
                    alert = {
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "timestamp": datetime.now().isoformat(),
                        "triggered": True
                    }
                    active_alerts.append(alert)
                    self.alert_history.append(alert)
            except Exception as e:
                print(f"Error evaluating alert rule '{rule['name']}': {e}")
        
        return active_alerts
    
    def get_recent_alerts(self, hours=24):
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]
        return recent_alerts
```

## 📊 Dashboard Integration

### 1. HTML Dashboard Generator

```python
def generate_monitoring_dashboard(output_file="elf_dashboard.html"):
    """Generate an HTML dashboard for monitoring."""
    
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>ELF Monitoring Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #333; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-card h3 {{ margin-top: 0; color: #333; }}
        .metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .status-indicator {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .status-healthy {{ background: #4CAF50; }}
        .status-warning {{ background: #FFC107; }}
        .status-error {{ background: #F44336; }}
        .chart-container {{ height: 200px; margin-top: 20px; }}
        .refresh-info {{ text-align: center; margin-top: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ELF Monitoring Dashboard</h1>
            <p>Real-time system monitoring and performance metrics</p>
        </div>
        
        <div class="metrics-grid">
            {metric_cards}
        </div>
        
        <div class="refresh-info">
            <p>Last updated: {timestamp}</p>
            <p>This dashboard auto-refreshes every 60 seconds</p>
        </div>
    </div>
    
    <script>
        setTimeout(function(){{ location.reload(); }}, 60000);
    </script>
</body>
</html>
"""
    
    # Generate metric cards
    metric_cards = ""
    
    # In a real implementation, you would fetch actual data
    sample_data = {
        "system_health": {"status": "healthy", "value": "Healthy"},
        "events_processed": {"status": "normal", "value": "1,247"},
        "heuristics_generated": {"status": "normal", "value": "247"},
        "uptime": {"status": "normal", "value": "1h 30m"},
        "tools_detected": {"status": "normal", "value": "234"},
        "database_size": {"status": "normal", "value": "2.5 MB"}
    }
    
    status_classes = {
        "healthy": "status-healthy",
        "normal": "status-healthy",
        "warning": "status-warning",
        "error": "status-error"
    }
    
    for metric_name, metric_data in sample_data.items():
        status_class = status_classes.get(metric_data["status"], "status-healthy")
        card = f"""
        <div class="metric-card">
            <h3>{metric_name.replace('_', ' ').title()}</h3>
            <div><span class="status-indicator {status_class}"></span> {metric_data['status'].title()}</div>
            <div class="metric-value">{metric_data['value']}</div>
        </div>
        """
        metric_cards += card
    
    # Generate complete HTML
    html_content = html_template.format(
        metric_cards=metric_cards,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Write to file
    try:
        with open(output_file, 'w') as f:
            f.write(html_content)
        print(f"✅ Monitoring dashboard generated: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to generate dashboard: {e}")
        return False
```

## 📚 Related Documentation

- [API Quick Start Guide](quickstart.md)
- [Orchestration Guide](orchestration-guide.md)
- [Monitoring API Documentation](../api/endpoints/monitoring/)
- [EventBridge API Documentation](../api/endpoints/eventbridge/)
- [System Health Monitoring](../api/endpoints/monitoring/health.md)

## 📖 Further Reading

- [ELF Architecture Overview](../api/overview.md)
- [API Design Principles](../architecture/api-design.md)
- [Error Handling Best Practices](../api/error-handling.md)
- [Performance Monitoring](https://prometheus.io/docs/introduction/overview/)