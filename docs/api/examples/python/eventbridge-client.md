# Python EventBridge Client Examples

Python examples for interacting with the ELF EventBridge API using the requests library.

## 🚀 Quick Start

### Basic Setup
```python
import requests
import json
import time
from typing import Dict, Any, Optional

# Base URL for the EventBridge
EVENTBRIDGE_URL = "http://localhost:9998"

def make_eventbridge_request(method: str, endpoint: str, 
                           data: Optional[Dict] = None) -> Dict:
    """Make a request to the EventBridge API."""
    url = f"{EVENTBRIDGE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"EventBridge request failed: {e}")
        return {"status": "error", "error": {"message": str(e)}}
```

### Check EventBridge Status
```python
def check_eventbridge_status():
    """Check the EventBridge status."""
    response = make_eventbridge_request("GET", "/status")
    
    if response["status"] == "success":
        data = response["data"]
        status_icon = "🟢" if data['running'] else "🔴"
        print(f"{status_icon} EventBridge Status")
        print(f"   Running: {data['running']}")
        print(f"   Events Processed: {data['events_processed']:,}")
        print(f"   Uptime: {data['uptime_seconds']} seconds")
        print(f"   Last Event: {data.get('last_event_time', 'Never')}")
        if 'version' in data:
            print(f"   Version: {data['version']}")
    else:
        print(f"❌ Error: {response['error']['message']}")
    
    return response

# Usage
check_eventbridge_status()
```

### Check System Health
```python
def check_system_health():
    """Check overall system health."""
    response = make_eventbridge_request("GET", "/api/v1/health")
    
    if response["status"] == "success":
        data = response["data"]
        status_icon = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴"
        }.get(data['status'], "❓")
        
        print(f"{status_icon} System Health: {data['status']}")
        print(f"   Service: {data['service']}")
        print(f"   Running: {data['running']}")
        print(f"   Events: {data['events']:,}")
        print(f"   Timestamp: {data['timestamp']}")
    else:
        print(f"❌ Error: {response['error']['message']}")
    
    return response

# Usage
check_system_health()
```

## 📋 Detailed Examples

### Check Component Health
```python
def check_component_health(component: str):
    """Check the health of a specific component."""
    response = make_eventbridge_request("GET", f"/api/v1/health/{component}")
    
    if response["status"] == "success":
        data = response["data"]
        status_icon = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴"
        }.get(data['status'], "❓")
        
        print(f"{status_icon} {component.capitalize()} Health: {data['status']}")
        
        if 'details' in data and data['details']:
            print("   Details:")
            for key, value in data['details'].items():
                print(f"     {key}: {value}")
        
        if 'confidence' in data:
            print(f"   Confidence: {data['confidence']:.2f}")
        
        if 'recommendation' in data:
            print(f"   Recommendation: {data['recommendation']}")
    else:
        error_code = response['error'].get('code', 'UNKNOWN')
        if error_code == 'RESOURCE_NOT_FOUND':
            print(f"❓ Component '{component}' not found")
        else:
            print(f"❌ Error checking {component} health: {response['error']['message']}")
    
    return response

# Usage
components = ["event_bridge", "mission_bridge", "sentinel_monitor"]
for component in components:
    check_component_health(component)
    print()
```

### Get Event Statistics
```python
def get_event_statistics():
    """Get detailed event processing statistics."""
    # First check if monitoring API is available (port 9997)
    try:
        monitoring_response = requests.get("http://localhost:9997/stats", timeout=10)
        if monitoring_response.status_code == 200:
            stats = monitoring_response.json()
            if stats["status"] == "success":
                events_data = stats["data"].get("events", {})
                print("📊 Event Processing Statistics")
                print(f"   Events per minute: {events_data.get('per_minute', 0):.1f}")
                
                recent_events = events_data.get("recent", [])
                if recent_events:
                    print("   Recent Events:")
                    for event in recent_events[:5]:  # Top 5
                        print(f"     {event['event_type']:<25} {event['count']:>6,}")
                return stats
    except requests.exceptions.RequestException:
        pass
    
    # Fallback to basic status info
    print("ℹ️  Detailed event statistics require monitoring API (port 9997)")
    response = make_eventbridge_request("GET", "/status")
    if response["status"] == "success":
        data = response["data"]
        print(f"📈 Total Events Processed: {data.get('events_processed', 0):,}")
        if 'event_stats' in data:
            event_stats = data['event_stats']
            print(f"   Event Types: {event_stats.get('total_types', 0)}")
            top_events = event_stats.get('top_events', {})
            if top_events:
                print("   Top Event Types:")
                for event_type, count in sorted(top_events.items(), 
                                              key=lambda x: x[1], reverse=True)[:5]:
                    print(f"     {event_type:<25} {count:>6,}")
    
    return response

# Usage
get_event_statistics()
```

## ⚠️ Error Handling Examples

### Robust Connection Handling
```python
import socket
from requests.exceptions import ConnectionError, Timeout

def robust_eventbridge_check(retries: int = 3, timeout: int = 10):
    """Robustly check EventBridge with retry logic."""
    for attempt in range(retries):
        try:
            # First check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 9998))
            sock.close()
            
            if result != 0:
                raise ConnectionError("EventBridge port not accessible")
            
            # Now make the actual API call
            response = requests.get(
                f"{EVENTBRIDGE_URL}/status",
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
            
        except ConnectionError as e:
            print(f"📡 Connection attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return {
                    "status": "error",
                    "error": {
                        "code": "CONNECTION_FAILED",
                        "message": f"Cannot connect to EventBridge after {retries} attempts"
                    }
                }
        
        except Timeout as e:
            print(f"⏰ Timeout on attempt {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return {
                    "status": "error",
                    "error": {
                        "code": "TIMEOUT",
                        "message": f"EventBridge timeout after {retries} attempts"
                    }
                }
        
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "UNEXPECTED_ERROR",
                    "message": str(e)
                }
            }

# Usage
response = robust_eventbridge_check(retries=3, timeout=15)
if response["status"] == "success":
    print("✅ EventBridge is responsive")
    data = response["data"]
    print(f"   Running: {data['running']}")
    print(f"   Events: {data['events_processed']:,}")
else:
    print(f"❌ EventBridge check failed: {response['error']['message']}")
```

### Handle Different Response Scenarios
```python
def comprehensive_status_check():
    """Perform a comprehensive status check with detailed error handling."""
    print("🔍 Performing comprehensive EventBridge status check...")
    print("=" * 50)
    
    # 1. Basic connectivity check
    print("1. Connectivity Check")
    try:
        response = requests.get(f"{EVENTBRIDGE_URL}/status", timeout=5)
        if response.status_code == 200:
            print("   🟢 Connection successful")
        else:
            print(f"   🔴 HTTP {response.status_code}: {response.reason}")
            return
    except requests.exceptions.RequestException as e:
        print(f"   🔴 Connection failed: {e}")
        return
    
    # 2. JSON parsing check
    print("2. Response Parsing")
    try:
        data = response.json()
        print("   🟢 JSON parsing successful")
    except json.JSONDecodeError as e:
        print(f"   🔴 JSON parsing failed: {e}")
        return
    
    # 3. Status validation
    print("3. Status Validation")
    if data["status"] == "success":
        print("   🟢 Status OK")
        bridge_data = data["data"]
        
        # 4. Data field validation
        required_fields = ["running", "events_processed", "opencode_server"]
        missing_fields = [field for field in required_fields if field not in bridge_data]
        
        if missing_fields:
            print(f"   🔴 Missing required fields: {missing_fields}")
        else:
            print("   🟢 All required fields present")
            
            # 5. Logical validation
            print("4. Logical Validation")
            if not isinstance(bridge_data["running"], bool):
                print("   🔴 'running' field should be boolean")
            elif not isinstance(bridge_data["events_processed"], int):
                print("   🔴 'events_processed' field should be integer")
            elif bridge_data["events_processed"] < 0:
                print("   🔴 'events_processed' should be non-negative")
            else:
                print("   🟢 All validations passed")
                return True
    else:
        print(f"   🔴 API returned error: {data.get('error', 'Unknown error')}")
    
    return False

# Usage
if comprehensive_status_check():
    print("\n✅ EventBridge is fully operational")
else:
    print("\n❌ EventBridge has issues that need attention")
```

## 🛠️ Advanced Examples

### Continuous Monitoring Script
```python
import csv
from datetime import datetime

class EventBridgeMonitor:
    """Continuously monitor EventBridge status and log metrics."""
    
    def __init__(self, log_file: str = "eventbridge_monitor.log",
                 csv_file: str = "eventbridge_metrics.csv"):
        self.log_file = log_file
        self.csv_file = csv_file
        self.monitoring = False
        
        # Initialize CSV file with headers if it doesn't exist
        try:
            with open(self.csv_file, 'x', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'running', 'events_processed', 'uptime_seconds',
                    'events_per_minute', 'status'
                ])
        except FileExistsError:
            pass  # File already exists
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring."""
        self.monitoring = True
        print(f"🔬 Starting EventBridge monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            while self.monitoring:
                self._collect_metrics()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            self.monitoring = False
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
    
    def _collect_metrics(self):
        """Collect and log metrics."""
        timestamp = datetime.now().isoformat()
        
        try:
            # Get EventBridge status
            response = requests.get(f"{EVENTBRIDGE_URL}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "success":
                    bridge_data = data["data"]
                    running = bridge_data.get("running", False)
                    events_processed = bridge_data.get("events_processed", 0)
                    uptime = bridge_data.get("uptime_seconds", 0)
                    
                    # Calculate events per minute (approximate)
                    events_per_minute = 0
                    if uptime > 0:
                        events_per_minute = (events_processed / uptime) * 60
                    
                    status = "healthy" if running else "unhealthy"
                    
                    # Log to file
                    self._log_to_file(timestamp, running, events_processed, 
                                    uptime, events_per_minute, status)
                    
                    # Print to console
                    status_icon = "🟢" if running else "🔴"
                    print(f"[{timestamp}] {status_icon} "
                          f"Events: {events_processed:,} | "
                          f"Uptime: {uptime}s | "
                          f"Rate: {events_per_minute:.1f}/min")
                    
                    # Check for anomalies
                    self._check_anomalies(events_per_minute, status)
                else:
                    self._log_error(timestamp, "API error", data.get("error", {}))
                    print(f"[{timestamp}] ❌ API Error: {data.get('error', 'Unknown')}")
            else:
                self._log_error(timestamp, "HTTP error", {"status_code": response.status_code})
                print(f"[{timestamp}] ❌ HTTP {response.status_code}: {response.reason}")
                
        except requests.exceptions.RequestException as e:
            self._log_error(timestamp, "Connection error", {"error": str(e)})
            print(f"[{timestamp}] ❌ Connection Error: {e}")
        except Exception as e:
            self._log_error(timestamp, "Unexpected error", {"error": str(e)})
            print(f"[{timestamp}] ❌ Unexpected Error: {e}")
    
    def _log_to_file(self, timestamp: str, running: bool, events_processed: int,
                     uptime: int, events_per_minute: float, status: str):
        """Log metrics to CSV file."""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, running, events_processed, uptime,
                    round(events_per_minute, 2), status
                ])
        except Exception as e:
            print(f"Failed to write to CSV: {e}")
    
    def _log_error(self, timestamp: str, error_type: str, details: Dict):
        """Log errors to file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] ERROR: {error_type} - {details}\n")
        except Exception as e:
            print(f"Failed to write to log: {e}")
    
    def _check_anomalies(self, events_per_minute: float, status: str):
        """Check for anomalous conditions."""
        alerts = []
        
        # High event rate
        if events_per_minute > 1000:
            alerts.append(f"⚠️  High event rate: {events_per_minute:.1f}/min")
        
        # Low event rate
        elif events_per_minute < 1 and status == "healthy":
            alerts.append(f"⚠️  Low event rate: {events_per_minute:.1f}/min")
        
        # Log alerts
        for alert in alerts:
            try:
                timestamp = datetime.now().isoformat()
                with open(self.log_file, 'a') as f:
                    f.write(f"[{timestamp}] ALERT: {alert}\n")
                print(f"   {alert}")
            except Exception as e:
                print(f"Failed to log alert: {e}")

# Usage
monitor = EventBridgeMonitor()
# monitor.start_monitoring(interval=30)  # Check every 30 seconds
```

### Health Dashboard Generator
```python
def generate_health_dashboard(output_file: str = "health_dashboard.html"):
    """Generate an HTML dashboard showing EventBridge health."""
    
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>ELF EventBridge Health Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 15px 0; border-left: 4px solid #ddd; }}
        .status-card.healthy {{ border-left-color: #28a745; }}
        .status-card.degraded {{ border-left-color: #ffc107; }}
        .status-card.unhealthy {{ border-left-color: #dc3545; }}
        .status-icon {{ font-size: 24px; margin-right: 10px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .metric:last-child {{ border-bottom: none; }}
        .refresh-info {{ text-align: center; color: #666; font-size: 14px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ELF EventBridge Health Dashboard</h1>
            <p>Generated at {timestamp}</p>
        </div>
        
        {status_section}
        
        {components_section}
        
        {metrics_section}
        
        <div class="refresh-info">
            <p>This dashboard auto-refreshes every 60 seconds</p>
        </div>
    </div>
    
    <script>
        setTimeout(function(){{ location.reload(); }}, 60000);
    </script>
</body>
</html>
"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get status information
    status_response = make_eventbridge_request("GET", "/status")
    health_response = make_eventbridge_request("GET", "/api/v1/health")
    
    # Build status section
    if status_response["status"] == "success":
        data = status_response["data"]
        running = data.get("running", False)
        status_class = "healthy" if running else "unhealthy"
        status_icon = "🟢" if running else "🔴"
        status_text = "Running" if running else "Stopped"
        
        status_section = f"""
        <div class="status-card {status_class}">
            <h2><span class="status-icon">{status_icon}</span>EventBridge Status</h2>
            <div class="metric"><span>Status:</span><strong>{status_text}</strong></div>
            <div class="metric"><span>Events Processed:</span><strong>{data.get('events_processed', 0):,}</strong></div>
            <div class="metric"><span>Uptime:</span><strong>{data.get('uptime_seconds', 0)} seconds</strong></div>
            <div class="metric"><span>Last Event:</span><strong>{data.get('last_event_time', 'Never')}</strong></div>
        </div>
        """
    else:
        status_section = """
        <div class="status-card unhealthy">
            <h2><span class="status-icon">❌</span>EventBridge Status</h2>
            <p>Unable to retrieve status information</p>
        </div>
        """
    
    # Build components section
    components = ["event_bridge", "mission_bridge", "sentinel_monitor"]
    components_html = ""
    
    for component in components:
        comp_response = make_eventbridge_request("GET", f"/api/v1/health/{component}")
        if comp_response["status"] == "success":
            comp_data = comp_response["data"]
            comp_status = comp_data.get("status", "unknown")
            status_classes = {
                "healthy": "healthy",
                "degraded": "degraded",
                "unhealthy": "unhealthy",
                "unknown": ""
            }
            status_icons = {
                "healthy": "🟢",
                "degraded": "🟡",
                "unhealthy": "🔴",
                "unknown": "❓"
            }
            
            components_html += f"""
            <div class="status-card {status_classes.get(comp_status, '')}">
                <h3><span class="status-icon">{status_icons.get(comp_status, '❓')}</span>{component.replace('_', ' ').title()}</h3>
                <div class="metric"><span>Status:</span><strong>{comp_status.title()}</strong></div>
            </div>
            """
        else:
            components_html += f"""
            <div class="status-card">
                <h3><span class="status-icon">❌</span>{component.replace('_', ' ').title()}</h3>
                <p>Unable to retrieve health information</p>
            </div>
            """
    
    components_section = f"""
    <h2>Component Health</h2>
    {components_html}
    """
    
    # Build metrics section
    try:
        monitoring_response = requests.get("http://localhost:9997/stats", timeout=10)
        if monitoring_response.status_code == 200:
            stats = monitoring_response.json()
            if stats["status"] == "success":
                stats_data = stats["data"]
                learning = stats_data.get("learning", {})
                tools = stats_data.get("tools", {})
                
                metrics_section = f"""
                <h2>System Metrics</h2>
                <div class="status-card">
                    <h3><span class="status-icon">📊</span>Learning Metrics</h3>
                    <div class="metric"><span>Heuristics:</span><strong>{learning.get('heuristics', 0):,}</strong></div>
                    <div class="metric"><span>Golden Rules:</span><strong>{learning.get('golden_rules', 0):,}</strong></div>
                    <div class="metric"><span>Trails:</span><strong>{learning.get('trails', 0):,}</strong></div>
                    <div class="metric"><span>Pheromones:</span><strong>{learning.get('pheromone_trails', 0):,}</strong></div>
                </div>
                <div class="status-card">
                    <h3><span class="status-icon">🔧</span>Tool Metrics</h3>
                    <div class="metric"><span>Tools Detected:</span><strong>{tools.get('tools_detected', 0):,}</strong></div>
                </div>
                """
            else:
                metrics_section = "<h2>System Metrics</h2><p>Unable to retrieve metrics</p>"
        else:
            metrics_section = "<h2>System Metrics</h2><p>Monitoring service not available</p>"
    except:
        metrics_section = "<h2>System Metrics</h2><p>Monitoring service not available</p>"
    
    # Generate complete HTML
    html_content = html_template.format(
        timestamp=timestamp,
        status_section=status_section,
        components_section=components_section,
        metrics_section=metrics_section
    )
    
    # Write to file
    try:
        with open(output_file, 'w') as f:
            f.write(html_content)
        print(f"✅ Health dashboard generated: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to generate dashboard: {e}")
        return False

# Usage
generate_health_dashboard("eventbridge_dashboard.html")
```

## 📚 Related Examples

- [Orchestrator Python Examples](orchestrator-client.md)
- [cURL EventBridge Examples](../../curl/eventbridge-examples.md)
- [JavaScript EventBridge Examples](../../javascript/eventbridge-client.md)

## 📖 Further Reading

- [EventBridge API Documentation](../../endpoints/eventbridge/)
- [OpenAPI Specification](../../openapi/eventbridge.yaml)
- [Schema Definitions](../../schemas/)