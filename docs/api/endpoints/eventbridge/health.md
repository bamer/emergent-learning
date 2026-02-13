# EventBridge Health Endpoints

Retrieve health status information for the EventBridge system and its components.

## 🔧 Endpoints

### Overall System Health
```
GET /api/v1/health
```

### Component Health
```
GET /api/v1/health/{component}
```

## 📥 Request

These endpoints do not require a request body.

### Path Parameters

For component health:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `component` | string | Yes | Component to check health for |

### Supported Components

| Component | Description |
|-----------|-------------|
| `event_bridge` | EventBridge core system |
| `mission_bridge` | Mission processing system |
| `sentinel_monitor` | Monitoring system |

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "status": "string",
    "service": "string",
    "running": true,
    "events": 0,
    "timestamp": "2026-02-12T10:30:15Z"
  }
}
```

Or for specific components:

```json
{
  "status": "success",
  "data": {
    "status": "string",
    "service": "string",
    "running": true,
    "hooks_executed": 0,
    "last_heartbeat": "2026-02-12T10:30:15Z"
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Component not found",
    "details": {}
  }
}
```

## 📝 Example Requests

### Overall Health
```bash
curl -X GET http://localhost:9998/api/v1/health
```

### EventBridge Component Health
```bash
curl -X GET http://localhost:9998/api/v1/health/event_bridge
```

### Mission Bridge Component Health
```bash
curl -X GET http://localhost:9998/api/v1/health/mission_bridge
```

### Sentinel Monitor Component Health
```bash
curl -X GET http://localhost:9998/api/v1/health/sentinel_monitor
```

## 📝 Example Responses

### Overall Health
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "service": "event_bridge",
    "running": true,
    "events": 1247,
    "timestamp": "2026-02-12T10:30:15Z"
  }
}
```

### Mission Bridge Health
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "service": "mission_bridge",
    "running": true,
    "hooks_executed": 63345,
    "last_heartbeat": "2026-02-12T10:30:15Z"
  }
}
```

### Sentinel Monitor Health
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "service": "sentinel_monitor",
    "running": true,
    "events_monitored": 28311,
    "last_check": "2026-02-12T10:30:15Z"
  }
}
```

## 🐍 Python Example

```python
import requests
import json
from datetime import datetime

def get_overall_health():
    """Get overall system health."""
    url = "http://localhost:9998/api/v1/health"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting overall health: {e}")
        return None

def get_component_health(component):
    """Get health status for a specific component."""
    url = f"http://localhost:9998/api/v1/health/{component}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting {component} health: {e}")
        return None

def get_all_health_status():
    """Get health status for all components."""
    components = ["event_bridge", "mission_bridge", "sentinel_monitor"]
    results = {}
    
    # Get overall health
    overall = get_overall_health()
    results["overall"] = overall
    
    # Get component health
    for component in components:
        health = get_component_health(component)
        results[component] = health
    
    return results

def health_check_summary():
    """Display a summary of system health."""
    print("=" * 50)
    print("           System Health Summary")
    print("=" * 50)
    
    # Overall health
    overall = get_overall_health()
    if overall and overall.get("status") == "success":
        data = overall["data"]
        status_icon = "🟢" if data.get("status") == "healthy" else "🔴"
        print(f"Overall:     {status_icon} {data.get('status', 'unknown').title()}")
        print(f"Service:     {data.get('service', 'unknown')}")
        print(f"Running:     {'Yes' if data.get('running') else 'No'}")
        print(f"Events:      {data.get('events', 0):,}")
        print(f"Timestamp:   {data.get('timestamp', 'unknown')}")
    else:
        print("Overall:     ❓ Unknown (failed to retrieve)")
    
    print("-" * 50)
    
    # Component health
    components = ["event_bridge", "mission_bridge", "sentinel_monitor"]
    for component in components:
        health = get_component_health(component)
        if health and health.get("status") == "success":
            data = health["data"]
            status_icon = "🟢" if data.get("status") == "healthy" else "🔴"
            print(f"{component.replace('_', ' ').title()}:")
            print(f"  Status:    {status_icon} {data.get('status', 'unknown').title()}")
            if "hooks_executed" in data:
                print(f"  Hooks:     {data.get('hooks_executed', 0):,}")
            if "events_monitored" in data:
                print(f"  Events:    {data.get('events_monitored', 0):,}")
            if "last_heartbeat" in data:
                print(f"  Heartbeat: {data.get('last_heartbeat', 'unknown')}")
            if "last_check" in data:
                print(f"  Check:     {data.get('last_check', 'unknown')}")
        else:
            print(f"{component.replace('_', ' ').title()}: ❓ Unknown (failed to retrieve)")
        print()
    
    print("=" * 50)

def is_system_healthy():
    """Check if the entire system is healthy."""
    results = get_all_health_status()
    
    # Check overall health
    overall_healthy = False
    if results["overall"] and results["overall"].get("status") == "success":
        overall_healthy = results["overall"]["data"].get("status") == "healthy"
    
    # Check component health
    components_healthy = True
    components = ["event_bridge", "mission_bridge", "sentinel_monitor"]
    for component in components:
        if results[component] and results[component].get("status") == "success":
            if results[component]["data"].get("status") != "healthy":
                components_healthy = False
                break
        else:
            components_healthy = False
            break
    
    return overall_healthy and components_healthy

# Example usage
if __name__ == "__main__":
    # Display health summary
    health_check_summary()
    
    # Check if system is healthy
    print("System Health Check:")
    healthy = is_system_healthy()
    print(f"System is {'🟢 Healthy' if healthy else '🔴 Unhealthy'}")
```

## 📄 JavaScript Example

```javascript
async function getOverallHealth() {
    const url = 'http://localhost:9998/api/v1/health';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting overall health:', error);
        throw error;
    }
}

async function getComponentHealth(component) {
    const url = `http://localhost:9998/api/v1/health/${component}`;
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error getting ${component} health:`, error);
        throw error;
    }
}

async function getAllHealthStatus() {
    const components = ["event_bridge", "mission_bridge", "sentinel_monitor"];
    const results = {};
    
    // Get overall health
    try {
        results.overall = await getOverallHealth();
    } catch (error) {
        results.overall = null;
    }
    
    // Get component health
    for (const component of components) {
        try {
            results[component] = await getComponentHealth(component);
        } catch (error) {
            results[component] = null;
        }
    }
    
    return results;
}

async function healthCheckSummary() {
    console.log("=".repeat(50));
    console.log("           System Health Summary");
    console.log("=".repeat(50));
    
    // Overall health
    try {
        const overall = await getOverallHealth();
        if (overall.status === "success") {
            const data = overall.data;
            const statusIcon = data.status === "healthy" ? "🟢" : "🔴";
            console.log(`Overall:     ${statusIcon} ${data.status.charAt(0).toUpperCase() + data.status.slice(1)}`);
            console.log(`Service:     ${data.service}`);
            console.log(`Running:     ${data.running ? 'Yes' : 'No'}`);
            console.log(`Events:      ${data.events?.toLocaleString() || 0}`);
            console.log(`Timestamp:   ${data.timestamp}`);
        } else {
            console.log("Overall:     ❓ Unknown (failed to retrieve)");
        }
    } catch (error) {
        console.log("Overall:     ❓ Unknown (failed to retrieve)");
    }
    
    console.log("-".repeat(50));
    
    // Component health
    const components = ["event_bridge", "mission_bridge", "sentinel_monitor"];
    for (const component of components) {
        try {
            const health = await getComponentHealth(component);
            if (health.status === "success") {
                const data = health.data;
                const statusIcon = data.status === "healthy" ? "🟢" : "🔴";
                console.log(`${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:`);
                console.log(`  Status:    ${statusIcon} ${data.status.charAt(0).toUpperCase() + data.status.slice(1)}`);
                if ("hooks_executed" in data) {
                    console.log(`  Hooks:     ${data.hooks_executed?.toLocaleString() || 0}`);
                }
                if ("events_monitored" in data) {
                    console.log(`  Events:    ${data.events_monitored?.toLocaleString() || 0}`);
                }
                if ("last_heartbeat" in data) {
                    console.log(`  Heartbeat: ${data.last_heartbeat}`);
                }
                if ("last_check" in data) {
                    console.log(`  Check:     ${data.last_check}`);
                }
            } else {
                console.log(`${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ❓ Unknown (failed to retrieve)`);
            }
        } catch (error) {
            console.log(`${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ❓ Unknown (failed to retrieve)`);
        }
        console.log();
    }
    
    console.log("=".repeat(50));
}

async function isSystemHealthy() {
    try {
        const results = await getAllHealthStatus();
        
        // Check overall health
        let overallHealthy = false;
        if (results.overall && results.overall.status === "success") {
            overallHealthy = results.overall.data.status === "healthy";
        }
        
        // Check component health
        let componentsHealthy = true;
        const components = ["event_bridge", "mission_bridge", "sentinel_monitor"];
        for (const component of components) {
            if (results[component] && results[component].status === "success") {
                if (results[component].data.status !== "healthy") {
                    componentsHealthy = false;
                    break;
                }
            } else {
                componentsHealthy = false;
                break;
            }
        }
        
        return overallHealthy && componentsHealthy;
    } catch (error) {
        console.error("Error checking system health:", error);
        return false;
    }
}

// Example usage
(async () => {
    try {
        // Display health summary
        await healthCheckSummary();
        
        // Check if system is healthy
        console.log("System Health Check:");
        const healthy = await isSystemHealthy();
        console.log(`System is ${healthy ? '🟢 Healthy' : '🔴 Unhealthy'}`);
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Health Status Values

| Status | Description |
|--------|-------------|
| `healthy` | Component is functioning normally |
| `degraded` | Component has minor issues but is still operational |
| `unhealthy` | Component has major issues and may not be functional |

## 📋 Response Fields

### Overall Health
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status |
| `service` | string | Service name |
| `running` | boolean | Whether service is running |
| `events` | integer | Number of events processed |
| `timestamp` | string | Timestamp of health check (ISO 8601) |

### Component Health
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Component health status |
| `service` | string | Service name |
| `running` | boolean | Whether component is running |
| `hooks_executed` | integer | Number of hooks executed (mission_bridge) |
| `events_monitored` | integer | Number of events monitored (sentinel_monitor) |
| `last_heartbeat` | string | Last heartbeat timestamp (ISO 8601) |
| `last_check` | string | Last check timestamp (ISO 8601) |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Component not found |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 Related Endpoints

- [EventBridge Status](status.md)
- [Monitoring Health](../../monitoring/health.md)

## 📖 Further Reading

- [EventBridge API Overview](README.md)
- [OpenAPI Specification](../../openapi/eventbridge.yaml)
- [EventBridge Architecture](../../../ARCHITECTURE-EventBridge.md)
- [Schema Definitions](../../schemas/responses.md)