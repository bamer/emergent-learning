# Monitoring Summary Endpoints

Retrieve quick summaries of system monitoring data.

## 🔧 Endpoints

### Quick Summary
```
GET /
```

### API Summary
```
GET /api/v1/summary
```

## 📥 Request

These endpoints do not require a request body.

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "status": "string",
    "uptime": "string",
    "events_pm": "string",
    "heuristics": 0,
    "golden_rules": 0,
    "trails": 0,
    "pheromones": 0,
    "tools_detected": 0,
    "db_size": "string"
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to retrieve summary",
    "details": {}
  }
}
```

## 📝 Example Requests

### Quick Summary
```bash
curl -X GET http://localhost:9997/
```

### API Summary
```bash
curl -X GET http://localhost:9997/api/v1/summary
```

## 📝 Example Responses

### Success Response
```json
{
  "status": "success",
  "data": {
    "status": "🟢 Running",
    "uptime": "3600s",
    "events_pm": "15.5",
    "heuristics": 247,
    "golden_rules": 12,
    "trails": 1542,
    "pheromones": 89,
    "tools_detected": 234,
    "db_size": "2560KB"
  }
}
```

## 🐍 Python Example

```python
import requests
import json

def get_monitoring_summary():
    """Get a quick summary of system monitoring data."""
    url = "http://localhost:9997/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting monitoring summary: {e}")
        return None

def get_api_summary():
    """Get API summary information."""
    url = "http://localhost:9997/api/v1/summary"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting API summary: {e}")
        return None

def display_monitoring_dashboard():
    """Display a formatted monitoring dashboard."""
    print("=" * 60)
    print("                    ELF Monitoring Dashboard")
    print("=" * 60)
    
    # Get quick summary
    summary = get_monitoring_summary()
    if summary and summary.get("status") == "success":
        data = summary["data"]
        print(f"Status:          {data.get('status', 'Unknown')}")
        print(f"Uptime:          {data.get('uptime', '0s')}")
        print(f"Events/min:      {data.get('events_pm', '0.0')}")
        print("-" * 60)
        print("Learning Metrics:")
        print(f"  Heuristics:    {data.get('heuristics', 0):>8,}")
        print(f"  Golden Rules:  {data.get('golden_rules', 0):>8,}")
        print(f"  Trails:        {data.get('trails', 0):>8,}")
        print(f"  Pheromones:    {data.get('pheromones', 0):>8,}")
        print(f"  Tools Found:   {data.get('tools_detected', 0):>8,}")
        print("-" * 60)
        print(f"Database Size:   {data.get('db_size', '0KB')}")
    else:
        print("Failed to retrieve monitoring summary")
    
    print("=" * 60)

def get_system_performance_indicators():
    """Get key performance indicators from the monitoring summary."""
    summary = get_monitoring_summary()
    
    if summary and summary.get("status") == "success":
        data = summary["data"]
        return {
            "system_status": data.get("status", "Unknown"),
            "events_per_minute": float(data.get("events_pm", "0.0")),
            "learning_activity": {
                "heuristics": data.get("heuristics", 0),
                "golden_rules": data.get("golden_rules", 0),
                "trails": data.get("trails", 0)
            },
            "system_load": {
                "tools_detected": data.get("tools_detected", 0),
                "database_size_kb": int(data.get("db_size", "0KB").replace("KB", ""))
            }
        }
    else:
        return None

def is_system_performing_well():
    """Check if the system is performing well based on monitoring data."""
    indicators = get_system_performance_indicators()
    
    if not indicators:
        return False, "Unable to retrieve performance indicators"
    
    # Check various performance criteria
    issues = []
    
    # Events per minute should be reasonable (not too low or too high)
    events_pm = indicators["events_per_minute"]
    if events_pm < 1:
        issues.append("Low event processing rate")
    elif events_pm > 1000:
        issues.append("High event processing rate - potential overload")
    
    # Check learning activity
    learning = indicators["learning_activity"]
    if learning["heuristics"] == 0:
        issues.append("No heuristics generated")
    
    # Check system load
    load = indicators["system_load"]
    if load["database_size_kb"] > 100000:  # 100MB
        issues.append("Large database size")
    
    if issues:
        return False, "; ".join(issues)
    else:
        return True, "System performing normally"

# Example usage
if __name__ == "__main__":
    # Display monitoring dashboard
    display_monitoring_dashboard()
    
    # Get performance indicators
    print("\nPerformance Indicators:")
    indicators = get_system_performance_indicators()
    if indicators:
        print(json.dumps(indicators, indent=2))
    
    # Check system performance
    print("\nSystem Performance Check:")
    is_good, message = is_system_performing_well()
    status_icon = "✅" if is_good else "⚠️"
    print(f"{status_icon} {message}")
```

## 📄 JavaScript Example

```javascript
async function getMonitoringSummary() {
    const url = 'http://localhost:9997/';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting monitoring summary:', error);
        throw error;
    }
}

async function getApiSummary() {
    const url = 'http://localhost:9997/api/v1/summary';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting API summary:', error);
        throw error;
    }
}

async function displayMonitoringDashboard() {
    console.log("=".repeat(60));
    console.log("                    ELF Monitoring Dashboard");
    console.log("=".repeat(60));
    
    try {
        // Get quick summary
        const summary = await getMonitoringSummary();
        if (summary.status === "success") {
            const data = summary.data;
            console.log(`Status:          ${data.status || 'Unknown'}`);
            console.log(`Uptime:          ${data.uptime || '0s'}`);
            console.log(`Events/min:      ${data.events_pm || '0.0'}`);
            console.log("-".repeat(60));
            console.log("Learning Metrics:");
            console.log(`  Heuristics:    ${data.heuristics?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
            console.log(`  Golden Rules:  ${data.golden_rules?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
            console.log(`  Trails:        ${data.trails?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
            console.log(`  Pheromones:    ${data.pheromones?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
            console.log(`  Tools Found:   ${data.tools_detected?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
            console.log("-".repeat(60));
            console.log(`Database Size:   ${data.db_size || '0KB'}`);
        } else {
            console.log("Failed to retrieve monitoring summary");
        }
    } catch (error) {
        console.log("Failed to retrieve monitoring summary");
        console.error(error);
    }
    
    console.log("=".repeat(60));
}

async function getSystemPerformanceIndicators() {
    try {
        const summary = await getMonitoringSummary();
        
        if (summary.status === "success") {
            const data = summary.data;
            return {
                system_status: data.status || "Unknown",
                events_per_minute: parseFloat(data.events_pm || "0.0"),
                learning_activity: {
                    heuristics: data.heuristics || 0,
                    golden_rules: data.golden_rules || 0,
                    trails: data.trails || 0
                },
                system_load: {
                    tools_detected: data.tools_detected || 0,
                    database_size_kb: parseInt((data.db_size || "0KB").replace("KB", "")) || 0
                }
            };
        } else {
            return null;
        }
    } catch (error) {
        console.error('Error getting performance indicators:', error);
        return null;
    }
}

async function isSystemPerformingWell() {
    const indicators = await getSystemPerformanceIndicators();
    
    if (!indicators) {
        return [false, "Unable to retrieve performance indicators"];
    }
    
    // Check various performance criteria
    const issues = [];
    
    // Events per minute should be reasonable (not too low or too high)
    const eventsPm = indicators.events_per_minute;
    if (eventsPm < 1) {
        issues.push("Low event processing rate");
    } else if (eventsPm > 1000) {
        issues.push("High event processing rate - potential overload");
    }
    
    // Check learning activity
    const learning = indicators.learning_activity;
    if (learning.heuristics === 0) {
        issues.push("No heuristics generated");
    }
    
    // Check system load
    const load = indicators.system_load;
    if (load.database_size_kb > 100000) { // 100MB
        issues.push("Large database size");
    }
    
    if (issues.length > 0) {
        return [false, issues.join("; ")];
    } else {
        return [true, "System performing normally"];
    }
}

// Example usage
(async () => {
    try {
        // Display monitoring dashboard
        await displayMonitoringDashboard();
        
        // Get performance indicators
        console.log("\nPerformance Indicators:");
        const indicators = await getSystemPerformanceIndicators();
        if (indicators) {
            console.log(JSON.stringify(indicators, null, 2));
        }
        
        // Check system performance
        console.log("\nSystem Performance Check:");
        const [isGood, message] = await isSystemPerformingWell();
        const statusIcon = isGood ? "✅" : "⚠️";
        console.log(`${statusIcon} ${message}`);
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Response Fields

### Main Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | System status indicator |
| `uptime` | string | System uptime |
| `events_pm` | string | Events per minute |
| `heuristics` | integer | Number of heuristics |
| `golden_rules` | integer | Number of golden rules |
| `trails` | integer | Number of trails |
| `pheromones` | integer | Number of pheromone trails |
| `tools_detected` | integer | Number of tools detected |
| `db_size` | string | Database size |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 Related Endpoints

- [Detailed Statistics](statistics.md)
- [System Health](health.md)
- [Learning Statistics](learning.md)

## 📖 Further Reading

- [Monitoring API Overview](README.md)
- [OpenAPI Specification](../../openapi/monitoring.yaml)
- [Monitoring Implementation](../../../core/monitoring_api.py)
- [Schema Definitions](../../schemas/responses.md)