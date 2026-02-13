# System Health Endpoint

Retrieve overall system health status from the monitoring API.

## 🔧 Endpoint

```
GET /health
```

## 📥 Request

This endpoint does not require a request body.

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "status": "string",
    "components": {
      "event_bridge": "string",
      "learning_processor": "string",
      "sentinel": "string",
      "orchestrator": "string",
      "ceo": "string"
    },
    "timestamp": "2026-02-12T10:30:15Z"
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to retrieve health status",
    "details": {}
  }
}
```

## 📝 Example Request

```bash
curl -X GET http://localhost:9997/health
```

## 📝 Example Response

### Healthy System
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

### Degraded System
```json
{
  "status": "success",
  "data": {
    "status": "degraded",
    "components": {
      "event_bridge": "healthy",
      "learning_processor": "healthy",
      "sentinel": "degraded",
      "orchestrator": "healthy",
      "ceo": "healthy"
    },
    "timestamp": "2026-02-12T10:30:15Z"
  }
}
```

### Unhealthy System
```json
{
  "status": "success",
  "data": {
    "status": "unhealthy",
    "components": {
      "event_bridge": "healthy",
      "learning_processor": "unhealthy",
      "sentinel": "degraded",
      "orchestrator": "healthy",
      "ceo": "healthy"
    },
    "timestamp": "2026-02-12T10:30:15Z"
  }
}
```

## 🐍 Python Example

```python
import requests
import json
from datetime import datetime

def get_system_health():
    """Get overall system health status."""
    url = "http://localhost:9997/health"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting system health: {e}")
        return None

def display_health_status():
    """Display formatted system health status."""
    print("=" * 50)
    print("            System Health Status")
    print("=" * 50)
    
    health = get_system_health()
    
    if not health or health.get("status") != "success":
        print("Failed to retrieve health status")
        if health and "error" in health:
            print(f"Error: {health['error'].get('message', 'Unknown error')}")
        return
    
    data = health["data"]
    
    # Overall system status
    overall_status = data.get("status", "unknown")
    status_icons = {
        "healthy": "🟢",
        "degraded": "🟡",
        "unhealthy": "🔴",
        "unknown": "❓"
    }
    status_icon = status_icons.get(overall_status, "❓")
    print(f"Overall Status:  {status_icon} {overall_status.upper()}")
    print(f"Checked At:      {data.get('timestamp', 'Unknown')}")
    
    print("-" * 50)
    
    # Component statuses
    print("Component Statuses:")
    components = data.get("components", {})
    
    component_names = {
        "event_bridge": "EventBridge",
        "learning_processor": "Learning Processor",
        "sentinel": "Sentinel (Level 1)",
        "orchestrator": "Orchestrator (Level 2)",
        "ceo": "CEO (Level 3)"
    }
    
    for component_key, status in components.items():
        component_name = component_names.get(component_key, component_key)
        component_icon = status_icons.get(status, "❓")
        print(f"  {component_icon} {component_name:<25} {status.upper()}")
    
    print("=" * 50)

def is_system_healthy():
    """Check if the system is healthy."""
    health = get_system_health()
    
    if not health or health.get("status") != "success":
        return False, "Unable to retrieve health status"
    
    data = health["data"]
    overall_status = data.get("status", "unknown")
    
    if overall_status == "healthy":
        return True, "System is healthy"
    elif overall_status == "degraded":
        return False, "System is degraded"
    elif overall_status == "unhealthy":
        return False, "System is unhealthy"
    else:
        return False, "Unknown system status"

def get_unhealthy_components():
    """Get a list of unhealthy components."""
    health = get_system_health()
    
    if not health or health.get("status") != "success":
        return None
    
    data = health["data"]
    components = data.get("components", {})
    
    unhealthy = []
    for component, status in components.items():
        if status != "healthy":
            unhealthy.append({
                "component": component,
                "status": status
            })
    
    return unhealthy

def generate_health_report():
    """Generate a comprehensive health report."""
    print("=" * 60)
    print("                   ELF Health Report")
    print("=" * 60)
    
    # Overall health
    is_healthy, health_message = is_system_healthy()
    health_icon = "✅" if is_healthy else "⚠️"
    print(f"{health_icon} {health_message}")
    
    # Timestamp
    health = get_system_health()
    if health and health.get("status") == "success":
        timestamp = health["data"].get("timestamp", "Unknown")
        print(f"Report Generated: {timestamp}")
    
    print("-" * 60)
    
    # Component details
    display_health_status()
    
    # Unhealthy components
    unhealthy = get_unhealthy_components()
    if unhealthy:
        print("\n⚠️  Issues Detected:")
        for issue in unhealthy:
            print(f"  - {issue['component']} is {issue['status']}")
    
    print("=" * 60)

def monitor_health_continuously(interval=30):
    """Monitor system health continuously."""
    import time
    
    print("Starting continuous health monitoring...")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        while True:
            health = get_system_health()
            
            if health and health.get("status") == "success":
                data = health["data"]
                overall_status = data.get("status", "unknown")
                status_icons = {
                    "healthy": "🟢",
                    "degraded": "🟡",
                    "unhealthy": "🔴"
                }
                status_icon = status_icons.get(overall_status, "❓")
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {status_icon} System is {overall_status}")
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ❓ Unable to retrieve health status")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping health monitoring...")

# Example usage
if __name__ == "__main__":
    # Generate health report
    generate_health_report()
    
    # Check if system is healthy
    print("\nHealth Check:")
    is_healthy, message = is_system_healthy()
    health_icon = "✅" if is_healthy else "⚠️"
    print(f"{health_icon} {message}")
    
    # Get unhealthy components
    unhealthy = get_unhealthy_components()
    if unhealthy:
        print("\nUnhealthy Components:")
        for component in unhealthy:
            print(f"  - {component['component']}: {component['status']}")
    
    # Uncomment the following line to start continuous monitoring
    # monitor_health_continuously(10)  # Check every 10 seconds
```

## 📄 JavaScript Example

```javascript
async function getSystemHealth() {
    const url = 'http://localhost:9997/health';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting system health:', error);
        throw error;
    }
}

async function displayHealthStatus() {
    console.log("=".repeat(50));
    console.log("            System Health Status");
    console.log("=".repeat(50));
    
    try {
        const health = await getSystemHealth();
        
        if (!health || health.status !== "success") {
            console.log("Failed to retrieve health status");
            if (health && health.error) {
                console.log(`Error: ${health.error.message || 'Unknown error'}`);
            }
            return;
        }
        
        const data = health.data;
        
        // Overall system status
        const overallStatus = data.status || "unknown";
        const statusIcons = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴",
            "unknown": "❓"
        };
        const statusIcon = statusIcons[overallStatus] || "❓";
        console.log(`Overall Status:  ${statusIcon} ${overallStatus.toUpperCase()}`);
        console.log(`Checked At:      ${data.timestamp || 'Unknown'}`);
        
        console.log("-".repeat(50));
        
        // Component statuses
        console.log("Component Statuses:");
        const components = data.components || {};
        
        const componentNames = {
            "event_bridge": "EventBridge",
            "learning_processor": "Learning Processor",
            "sentinel": "Sentinel (Level 1)",
            "orchestrator": "Orchestrator (Level 2)",
            "ceo": "CEO (Level 3)"
        };
        
        for (const [componentKey, status] of Object.entries(components)) {
            const componentName = componentNames[componentKey] || componentKey;
            const componentIcon = statusIcons[status] || "❓";
            console.log(`  ${componentIcon} ${componentName.padEnd(25)} ${status.toUpperCase()}`);
        }
        
        console.log("=".repeat(50));
    } catch (error) {
        console.error("Error displaying health status:", error);
    }
}

async function isSystemHealthy() {
    try {
        const health = await getSystemHealth();
        
        if (!health || health.status !== "success") {
            return [false, "Unable to retrieve health status"];
        }
        
        const data = health.data;
        const overallStatus = data.status || "unknown";
        
        if (overallStatus === "healthy") {
            return [true, "System is healthy"];
        } else if (overallStatus === "degraded") {
            return [false, "System is degraded"];
        } else if (overallStatus === "unhealthy") {
            return [false, "System is unhealthy"];
        } else {
            return [false, "Unknown system status"];
        }
    } catch (error) {
        return [false, `Error checking health: ${error.message}`];
    }
}

async function getUnhealthyComponents() {
    try {
        const health = await getSystemHealth();
        
        if (!health || health.status !== "success") {
            return null;
        }
        
        const data = health.data;
        const components = data.components || {};
        
        const unhealthy = [];
        for (const [component, status] of Object.entries(components)) {
            if (status !== "healthy") {
                unhealthy.push({
                    component: component,
                    status: status
                });
            }
        }
        
        return unhealthy;
    } catch (error) {
        console.error('Error getting unhealthy components:', error);
        return null;
    }
}

async function generateHealthReport() {
    console.log("=".repeat(60));
    console.log("                   ELF Health Report");
    console.log("=".repeat(60));
    
    try {
        // Overall health
        const [isHealthy, healthMessage] = await isSystemHealthy();
        const healthIcon = isHealthy ? "✅" : "⚠️";
        console.log(`${healthIcon} ${healthMessage}`);
        
        // Timestamp
        const health = await getSystemHealth();
        if (health && health.status === "success") {
            const timestamp = health.data.timestamp || "Unknown";
            console.log(`Report Generated: ${timestamp}`);
        }
        
        console.log("-".repeat(60));
        
        // Component details
        await displayHealthStatus();
        
        // Unhealthy components
        const unhealthy = await getUnhealthyComponents();
        if (unhealthy && unhealthy.length > 0) {
            console.log("\n⚠️  Issues Detected:");
            for (const issue of unhealthy) {
                console.log(`  - ${issue.component} is ${issue.status}`);
            }
        }
        
        console.log("=".repeat(60));
    } catch (error) {
        console.error("Error generating health report:", error);
    }
}

// Example usage
(async () => {
    try {
        // Generate health report
        await generateHealthReport();
        
        // Check if system is healthy
        console.log("\nHealth Check:");
        const [isHealthy, message] = await isSystemHealthy();
        const healthIcon = isHealthy ? "✅" : "⚠️";
        console.log(`${healthIcon} ${message}`);
        
        // Get unhealthy components
        const unhealthy = await getUnhealthyComponents();
        if (unhealthy && unhealthy.length > 0) {
            console.log("\nUnhealthy Components:");
            for (const component of unhealthy) {
                console.log(`  - ${component.component}: ${component.status}`);
            }
        }
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Health Status Values

| Status | Description |
|--------|-------------|
| `healthy` | Component/system is functioning normally |
| `degraded` | Component/system has minor issues but is still operational |
| `unhealthy` | Component/system has major issues and may not be functional |

## 📋 Response Fields

### Main Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Overall system health status |
| `components` | object | Individual component health statuses |
| `timestamp` | string | Timestamp of health check (ISO 8601) |

### Components Object
| Field | Type | Description |
|-------|------|-------------|
| `event_bridge` | string | EventBridge health status |
| `learning_processor` | string | Learning processor health status |
| `sentinel` | string | Sentinel agent health status |
| `orchestrator` | string | Orchestrator health status |
| `ceo` | string | CEO agent health status |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 Related Endpoints

- [Monitoring Summary](summary.md)
- [Detailed Statistics](statistics.md)
- [Component Health](../../eventbridge/health.md)

## 📖 Further Reading

- [Monitoring API Overview](README.md)
- [OpenAPI Specification](../../openapi/monitoring.yaml)
- [Monitoring Implementation](../../../core/monitoring_api.py)
- [Schema Definitions](../../schemas/responses.md)