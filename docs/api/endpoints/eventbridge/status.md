# EventBridge Status Endpoint

Retrieve the current status of the EventBridge system.

## 🔧 Endpoint

```
GET /status
```

## 📥 Request

This endpoint does not require a request body.

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "running": true,
    "events_processed": 1247,
    "opencode_server": "http://localhost:4096",
    "started_at": "2026-02-12T10:30:15",
    "uptime_seconds": 3600,
    "last_event_time": "2026-02-12T11:30:15",
    "version": "2.0",
    "event_stats": {
      "total_types": 10,
      "top_events": {
        "message.part.updated": 15059,
        "message.updated": 335
      }
    }
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to retrieve status",
    "details": {}
  }
}
```

## 📝 Example Request

```bash
curl -X GET http://localhost:9998/status
```

## 📝 Example Response

```json
{
  "status": "success",
  "data": {
    "running": true,
    "events_processed": 1247,
    "opencode_server": "http://localhost:4096",
    "started_at": "2026-02-12T10:30:15",
    "uptime_seconds": 3600,
    "last_event_time": "2026-02-12T11:30:15",
    "version": "2.0",
    "event_stats": {
      "total_types": 8,
      "top_events": {
        "message.part.updated": 892,
        "tool": 234,
        "message": 115
      },
      "last_updated": "2026-02-12T11:30:15"
    }
  }
}
```

## 🐍 Python Example

```python
import requests
import json
from datetime import datetime

def get_eventbridge_status():
    """Get the current status of the EventBridge system."""
    url = "http://localhost:9998/status"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting EventBridge status: {e}")
        return None

def parse_uptime(seconds):
    """Convert seconds to human-readable uptime format."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)

def display_status_summary():
    """Display a formatted summary of EventBridge status."""
    result = get_eventbridge_status()
    
    if result and result.get("status") == "success":
        data = result["data"]
        
        print("=" * 50)
        print("         EventBridge Status Summary")
        print("=" * 50)
        print(f"Status:        {'🟢 Running' if data['running'] else '🔴 Stopped'}")
        print(f"Version:       {data.get('version', 'Unknown')}")
        print(f"Uptime:        {parse_uptime(data.get('uptime_seconds', 0))}")
        print(f"Events:        {data.get('events_processed', 0):,}")
        print(f"OpenCode:      {data.get('opencode_server', 'Unknown')}")
        print(f"Last Event:    {data.get('last_event_time', 'Never')}")
        print("-" * 50)
        
        # Display event statistics
        event_stats = data.get("event_stats", {})
        if event_stats:
            print("Top Events:")
            top_events = event_stats.get("top_events", {})
            for event_type, count in sorted(top_events.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {event_type:<25} {count:>6,}")
        
        print("=" * 50)
        
        return data
    else:
        print("Failed to retrieve EventBridge status")
        if result and "error" in result:
            print(f"Error: {result['error'].get('message', 'Unknown error')}")
        return None

def check_eventbridge_health():
    """Simple health check for EventBridge."""
    result = get_eventbridge_status()
    
    if result and result.get("status") == "success":
        data = result["data"]
        is_healthy = (
            data.get("running", False) and
            data.get("events_processed", 0) > 0 and
            data.get("uptime_seconds", 0) > 0
        )
        
        return {
            "healthy": is_healthy,
            "details": {
                "running": data.get("running"),
                "events_processed": data.get("events_processed"),
                "uptime_seconds": data.get("uptime_seconds")
            }
        }
    else:
        return {
            "healthy": False,
            "details": {"error": "Failed to retrieve status"}
        }

# Example usage
if __name__ == "__main__":
    # Get and display status summary
    status_data = display_status_summary()
    
    # Perform health check
    print("\nHealth Check:")
    health_result = check_eventbridge_health()
    print(f"Healthy: {health_result['healthy']}")
    print(f"Details: {json.dumps(health_result['details'], indent=2)}")
```

## 📄 JavaScript Example

```javascript
async function getEventBridgeStatus() {
    const url = 'http://localhost:9998/status';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting EventBridge status:', error);
        throw error;
    }
}

function parseUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);
    
    return parts.join(' ');
}

async function displayStatusSummary() {
    try {
        const result = await getEventBridgeStatus();
        
        if (result.status === "success") {
            const data = result.data;
            
            console.log("=".repeat(50));
            console.log("         EventBridge Status Summary");
            console.log("=".repeat(50));
            console.log(`Status:        ${data.running ? '🟢 Running' : '🔴 Stopped'}`);
            console.log(`Version:       ${data.version || 'Unknown'}`);
            console.log(`Uptime:        ${parseUptime(data.uptime_seconds || 0)}`);
            console.log(`Events:        ${data.events_processed?.toLocaleString() || 0}`);
            console.log(`OpenCode:      ${data.opencode_server || 'Unknown'}`);
            console.log(`Last Event:    ${data.last_event_time || 'Never'}`);
            console.log("-".repeat(50));
            
            // Display event statistics
            const eventStats = data.event_stats || {};
            if (Object.keys(eventStats).length > 0) {
                console.log("Top Events:");
                const topEvents = eventStats.top_events || {};
                const sortedEvents = Object.entries(topEvents)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5);
                
                for (const [eventType, count] of sortedEvents) {
                    console.log(`  ${eventType.padEnd(25)} ${count.toLocaleString().padStart(6)}`);
                }
            }
            
            console.log("=".repeat(50));
            
            return data;
        } else {
            console.log("Failed to retrieve EventBridge status");
            if (result.error) {
                console.log(`Error: ${result.error.message || 'Unknown error'}`);
            }
            return null;
        }
    } catch (error) {
        console.error("Error displaying status summary:", error);
        return null;
    }
}

function checkEventBridgeHealth(statusData) {
    if (!statusData) return { healthy: false, details: { error: "No status data" } };
    
    const isHealthy = (
        statusData.running &&
        (statusData.events_processed || 0) > 0 &&
        (statusData.uptime_seconds || 0) > 0
    );
    
    return {
        healthy: isHealthy,
        details: {
            running: statusData.running,
            events_processed: statusData.events_processed,
            uptime_seconds: statusData.uptime_seconds
        }
    };
}

// Example usage
(async () => {
    try {
        // Get and display status summary
        const statusData = await displayStatusSummary();
        
        // Perform health check
        console.log("\nHealth Check:");
        const healthResult = checkEventBridgeHealth(statusData);
        console.log(`Healthy: ${healthResult.healthy}`);
        console.log(`Details: ${JSON.stringify(healthResult.details, null, 2)}`);
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Response Fields

### Main Object
| Field | Type | Description |
|-------|------|-------------|
| `running` | boolean | Whether EventBridge is running |
| `events_processed` | integer | Total number of events processed |
| `opencode_server` | string | OpenCode server URL |
| `started_at` | string | When EventBridge was started (ISO 8601) |
| `uptime_seconds` | integer | Uptime in seconds |
| `last_event_time` | string | Timestamp of last event (ISO 8601) |
| `version` | string | EventBridge version |
| `event_stats` | object | Event statistics |

### Event Stats Object
| Field | Type | Description |
|-------|------|-------------|
| `total_types` | integer | Total number of event types |
| `top_events` | object | Mapping of event types to counts |
| `last_updated` | string | When stats were last updated (ISO 8601) |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 Related Endpoints

- [System Health](health.md)
- [Monitoring API Status](../../monitoring/status.md)

## 📖 Further Reading

- [EventBridge API Overview](README.md)
- [OpenAPI Specification](../../openapi/eventbridge.yaml)
- [EventBridge Architecture](../../../ARCHITECTURE-EventBridge.md)
- [Schema Definitions](../../schemas/responses.md)