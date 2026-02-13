# Component Health Endpoint

Retrieve health status for a specific component in the ELF system.

## 🔧 Endpoint

```
GET /api/v1/health/{component}
```

## 📥 Request

This endpoint does not require a request body.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `component` | string | Yes | Component to check health for |

### Supported Components

| Component | Description |
|-----------|-------------|
| `event_bridge` | Event processing system |
| `orchestrator` | Service management system |
| `dashboard` | Web interface |
| `learning_processor` | AI learning system |

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "component": "string",
    "status": "string",
    "details": {},
    "confidence": 0.0,
    "recommendation": "string"
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

### Check EventBridge Health
```bash
curl -X GET http://localhost:9998/api/v1/health/event_bridge
```

### Check Orchestrator Health
```bash
curl -X GET http://localhost:9998/api/v1/health/orchestrator
```

## 📝 Example Responses

### Healthy Component
```json
{
  "status": "success",
  "data": {
    "component": "event_bridge",
    "status": "healthy",
    "details": {
      "events_processed": 1247,
      "uptime_seconds": 3600,
      "last_event_time": "2026-02-12T10:30:15Z"
    },
    "confidence": 0.95,
    "recommendation": "continue"
  }
}
```

### Degraded Component
```json
{
  "status": "success",
  "data": {
    "component": "orchestrator",
    "status": "degraded",
    "details": {
      "services_healthy": 2,
      "total_services": 3,
      "issues": ["sentinel service down"]
    },
    "confidence": 0.85,
    "recommendation": "restart_sentinel"
  }
}
```

### Component Not Found
```json
{
  "status": "error",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Component 'unknown_component' not found",
    "details": {
      "requested_component": "unknown_component",
      "supported_components": ["event_bridge", "orchestrator", "dashboard", "learning_processor"]
    }
  }
}
```

## 🐍 Python Example

```python
import requests
import json

def check_component_health(component):
    """Check the health of a specific component."""
    url = f"http://localhost:9998/api/v1/health/{component}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking {component} health: {e}")
        return None

def check_all_components():
    """Check health of all supported components."""
    components = ["event_bridge", "orchestrator", "dashboard", "learning_processor"]
    results = {}
    
    for component in components:
        result = check_component_health(component)
        results[component] = result
        
        if result and result.get("status") == "success":
            health_status = result["data"]["status"]
            print(f"{component}: {health_status}")
        else:
            print(f"{component}: ERROR - {result.get('error', {}).get('message', 'Unknown error')}")
    
    return results

def get_system_health_summary():
    """Get a summary of overall system health."""
    components = ["event_bridge", "orchestrator", "dashboard", "learning_processor"]
    health_statuses = []
    
    for component in components:
        result = check_component_health(component)
        if result and result.get("status") == "success":
            health_statuses.append(result["data"]["status"])
        else:
            health_statuses.append("unknown")
    
    # Determine overall system health
    if all(status == "healthy" for status in health_statuses if status != "unknown"):
        overall_health = "healthy"
    elif any(status == "unhealthy" for status in health_statuses if status != "unknown"):
        overall_health = "unhealthy"
    else:
        overall_health = "degraded"
    
    return {
        "overall_health": overall_health,
        "component_health": dict(zip(components, health_statuses))
    }

# Example usage
if __name__ == "__main__":
    # Check individual component health
    print("Checking EventBridge health:")
    result = check_component_health("event_bridge")
    if result:
        print(json.dumps(result, indent=2))
    
    print("\nChecking all components:")
    check_all_components()
    
    print("\nSystem health summary:")
    summary = get_system_health_summary()
    print(json.dumps(summary, indent=2))
```

## 📄 JavaScript Example

```javascript
async function checkComponentHealth(component) {
    const url = `http://localhost:9998/api/v1/health/${component}`;
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error checking ${component} health:`, error);
        throw error;
    }
}

async function checkAllComponents() {
    const components = ["event_bridge", "orchestrator", "dashboard", "learning_processor"];
    const results = {};
    
    for (const component of components) {
        try {
            const result = await checkComponentHealth(component);
            results[component] = result;
            
            if (result.status === "success") {
                const healthStatus = result.data.status;
                console.log(`${component}: ${healthStatus}`);
            } else {
                console.log(`${component}: ERROR - ${result.error?.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error(`${component}: Failed to check health`);
            results[component] = { error: error.message };
        }
    }
    
    return results;
}

function getSystemHealthSummary(componentResults) {
    const components = ["event_bridge", "orchestrator", "dashboard", "learning_processor"];
    const healthStatuses = components.map(component => {
        const result = componentResults[component];
        if (result && result.status === "success") {
            return result.data.status;
        }
        return "unknown";
    });
    
    // Determine overall system health
    const knownStatuses = healthStatuses.filter(status => status !== "unknown");
    let overallHealth;
    
    if (knownStatuses.every(status => status === "healthy")) {
        overallHealth = "healthy";
    } else if (knownStatuses.some(status => status === "unhealthy")) {
        overallHealth = "unhealthy";
    } else {
        overallHealth = "degraded";
    }
    
    return {
        overall_health: overallHealth,
        component_health: Object.fromEntries(components.map((comp, i) => [comp, healthStatuses[i]]))
    };
}

// Example usage
(async () => {
    try {
        // Check individual component health
        console.log("Checking EventBridge health:");
        const result = await checkComponentHealth("event_bridge");
        console.log(JSON.stringify(result, null, 2));
        
        console.log("\nChecking all components:");
        const allResults = await checkAllComponents();
        
        console.log("\nSystem health summary:");
        const summary = getSystemHealthSummary(allResults);
        console.log(JSON.stringify(summary, null, 2));
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
| `unknown` | Unable to determine component health |

## 📋 Response Fields

### Main Object
| Field | Type | Description |
|-------|------|-------------|
| `component` | string | Component name |
| `status` | string | Health status |
| `details` | object | Additional health details |
| `confidence` | number | Confidence level in health assessment (0.0-1.0) |
| `recommendation` | string | Recommended action |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Component not found |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## 📚 Related Endpoints

- [System Health](../../endpoints/monitoring/health.md)
- [Orchestrator Status](status.md)

## 📖 Further Reading

- [Orchestrator API Overview](README.md)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/responses.md)