# Detailed Statistics Endpoint

Retrieve detailed system statistics from the monitoring API.

## 🔧 Endpoint

```
GET /stats
```

## 📥 Request

This endpoint does not require a request body.

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "timestamp": "2026-02-12T10:30:15Z",
    "uptime_seconds": 3600,
    "architecture": {
      "event_bridge": {
        "name": "EventBridge v2.0",
        "port": 9998,
        "status": "running",
        "endpoint": "/status"
      },
      "learning_processor": {
        "name": "Learning Processor",
        "status": "running",
        "functions": [
          "pre_tool_process",
          "post_tool_process",
          "decay_trails",
          "get_hot_spots"
        ]
      },
      "agents": {
        "sentinel": {
          "name": "Sentinel (Level 1)",
          "status": "running"
        },
        "orchestrator": {
          "name": "Orchestrator (Level 2)",
          "status": "running"
        },
        "ceo": {
          "name": "CEO (Level 3)",
          "status": "running"
        }
      }
    },
    "database": {
      "path": "/home/bamer/.opencode/emergent-learning/memory/index.db",
      "size_kb": 2560
    },
    "events": {
      "per_minute": 15.5,
      "recent": [
        {
          "event_type": "tool",
          "count": 234,
          "last_seen": "2026-02-12T10:30:15Z"
        }
      ]
    },
    "learning": {
      "heuristics": 247,
      "golden_rules": 12,
      "trails": 1542,
      "pheromone_trails": 89,
      "learnings": 67
    },
    "tools": {
      "tools_detected": 234
    },
    "system": {
      "status": "healthy",
      "components_healthy": 5,
      "total_components": 5,
      "last_activity": "2026-02-12T10:30:15Z"
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
    "message": "Failed to retrieve statistics",
    "details": {}
  }
}
```

## 📝 Example Request

```bash
curl -X GET http://localhost:9997/stats
```

## 📝 Example Response

```json
{
  "status": "success",
  "data": {
    "timestamp": "2026-02-12T10:30:15Z",
    "uptime_seconds": 3600,
    "architecture": {
      "event_bridge": {
        "name": "EventBridge v2.0",
        "port": 9998,
        "status": "running",
        "endpoint": "/status"
      },
      "learning_processor": {
        "name": "Learning Processor",
        "status": "running",
        "functions": [
          "pre_tool_process",
          "post_tool_process",
          "decay_trails",
          "get_hot_spots"
        ]
      },
      "agents": {
        "sentinel": {
          "name": "Sentinel (Level 1)",
          "status": "running"
        },
        "orchestrator": {
          "name": "Orchestrator (Level 2)",
          "status": "running"
        },
        "ceo": {
          "name": "CEO (Level 3)",
          "status": "running"
        }
      }
    },
    "database": {
      "path": "/home/bamer/.opencode/emergent-learning/memory/index.db",
      "size_kb": 2560
    },
    "events": {
      "per_minute": 15.5,
      "recent": [
        {
          "event_type": "tool",
          "count": 234,
          "last_seen": "2026-02-12T10:30:10Z"
        },
        {
          "event_type": "message.part.updated",
          "count": 15059,
          "last_seen": "2026-02-12T10:30:15Z"
        },
        {
          "event_type": "message",
          "count": 115,
          "last_seen": "2026-02-12T10:29:45Z"
        }
      ]
    },
    "learning": {
      "heuristics": 247,
      "golden_rules": 12,
      "trails": 1542,
      "pheromone_trails": 89,
      "learnings": 67
    },
    "tools": {
      "tools_detected": 234
    },
    "system": {
      "status": "healthy",
      "components_healthy": 5,
      "total_components": 5,
      "last_activity": "2026-02-12T10:30:15Z"
    }
  }
}
```

## 🐍 Python Example

```python
import requests
import json
from datetime import datetime

def get_detailed_statistics():
    """Get detailed system statistics."""
    url = "http://localhost:9997/stats"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting detailed statistics: {e}")
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

def display_architecture_info(stats_data):
    """Display architecture information."""
    if not stats_data or "architecture" not in stats_data:
        return
    
    arch = stats_data["architecture"]
    print("Architecture:")
    print("  Components:")
    
    # Event Bridge
    if "event_bridge" in arch:
        eb = arch["event_bridge"]
        status_icon = "🟢" if eb.get("status") == "running" else "🔴"
        print(f"    {status_icon} {eb.get('name', 'Unknown')} (Port {eb.get('port', 'N/A')})")
    
    # Learning Processor
    if "learning_processor" in arch:
        lp = arch["learning_processor"]
        status_icon = "🟢" if lp.get("status") == "running" else "🔴"
        print(f"    {status_icon} {lp.get('name', 'Unknown')}")
    
    # Agents
    if "agents" in arch:
        print("  Agents:")
        agents = arch["agents"]
        for agent_name, agent_info in agents.items():
            status_icon = "🟢" if agent_info.get("status") == "running" else "🔴"
            print(f"    {status_icon} {agent_info.get('name', 'Unknown')}")

def display_learning_metrics(stats_data):
    """Display learning metrics."""
    if not stats_data or "learning" not in stats_data:
        return
    
    learning = stats_data["learning"]
    print("\nLearning Metrics:")
    print(f"  Heuristics:      {learning.get('heuristics', 0):>8,}")
    print(f"  Golden Rules:    {learning.get('golden_rules', 0):>8,}")
    print(f"  Trails:          {learning.get('trails', 0):>8,}")
    print(f"  Pheromone Trails:{learning.get('pheromone_trails', 0):>8,}")
    print(f"  Learnings:       {learning.get('learnings', 0):>8,}")

def display_event_statistics(stats_data):
    """Display event statistics."""
    if not stats_data or "events" not in stats_data:
        return
    
    events = stats_data["events"]
    print(f"\nEvent Processing:")
    print(f"  Events/Minute:   {events.get('per_minute', 0.0):>8.1f}")
    
    recent_events = events.get("recent", [])
    if recent_events:
        print("  Recent Events:")
        for event in recent_events[:5]:  # Show top 5
            print(f"    {event.get('event_type', 'unknown'):<20} {event.get('count', 0):>6,}")

def generate_system_report():
    """Generate a comprehensive system report."""
    print("=" * 70)
    print("                       ELF System Report")
    print("=" * 70)
    
    stats = get_detailed_statistics()
    
    if not stats or stats.get("status") != "success":
        print("Failed to retrieve system statistics")
        if stats and "error" in stats:
            print(f"Error: {stats['error'].get('message', 'Unknown error')}")
        return
    
    data = stats["data"]
    
    # System Overview
    print(f"Report Time:     {data.get('timestamp', 'Unknown')}")
    print(f"Uptime:          {parse_uptime(data.get('uptime_seconds', 0))}")
    print(f"Database Size:   {data.get('database', {}).get('size_kb', 0):,} KB")
    print(f"Last Activity:   {data.get('system', {}).get('last_activity', 'Unknown')}")
    
    print("-" * 70)
    
    # Architecture
    display_architecture_info(data)
    
    print("-" * 70)
    
    # Learning Metrics
    display_learning_metrics(data)
    
    print("-" * 70)
    
    # Event Statistics
    display_event_statistics(data)
    
    print("-" * 70)
    
    # System Health
    system = data.get("system", {})
    health_status = system.get("status", "unknown")
    status_icon = "🟢" if health_status == "healthy" else "🔴" if health_status == "unhealthy" else "🟡"
    print(f"System Health:   {status_icon} {health_status.title()}")
    print(f"Components:      {system.get('components_healthy', 0)}/{system.get('total_components', 0)} healthy")
    
    print("=" * 70)

def get_performance_trends():
    """Get performance trends by comparing current stats with previous data."""
    # In a real implementation, you would store historical data
    # For this example, we'll just return current stats with some analysis
    stats = get_detailed_statistics()
    
    if not stats or stats.get("status") != "success":
        return None
    
    data = stats["data"]
    
    # Simple trend analysis
    events_pm = data.get("events", {}).get("per_minute", 0)
    tools_detected = data.get("tools", {}).get("tools_detected", 0)
    heuristics = data.get("learning", {}).get("heuristics", 0)
    
    trend_analysis = {
        "events_trend": "normal",
        "tools_trend": "normal",
        "learning_trend": "normal"
    }
    
    # Simple threshold-based analysis
    if events_pm > 100:
        trend_analysis["events_trend"] = "high"
    elif events_pm < 1:
        trend_analysis["events_trend"] = "low"
    
    if tools_detected > 1000:
        trend_analysis["tools_trend"] = "high"
    elif tools_detected < 10:
        trend_analysis["tools_trend"] = "low"
    
    if heuristics > 500:
        trend_analysis["learning_trend"] = "high"
    elif heuristics < 10:
        trend_analysis["learning_trend"] = "low"
    
    return {
        "current_stats": data,
        "trend_analysis": trend_analysis
    }

# Example usage
if __name__ == "__main__":
    # Generate system report
    generate_system_report()
    
    # Get performance trends
    print("\nPerformance Trends:")
    trends = get_performance_trends()
    if trends:
        analysis = trends["trend_analysis"]
        print(f"  Events Trend:    {analysis['events_trend']}")
        print(f"  Tools Trend:     {analysis['tools_trend']}")
        print(f"  Learning Trend:  {analysis['learning_trend']}")
```

## 📄 JavaScript Example

```javascript
async function getDetailedStatistics() {
    const url = 'http://localhost:9997/stats';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting detailed statistics:', error);
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

function displayArchitectureInfo(statsData) {
    if (!statsData || !statsData.architecture) return;
    
    const arch = statsData.architecture;
    console.log("Architecture:");
    console.log("  Components:");
    
    // Event Bridge
    if (arch.event_bridge) {
        const eb = arch.event_bridge;
        const statusIcon = eb.status === "running" ? "🟢" : "🔴";
        console.log(`    ${statusIcon} ${eb.name || 'Unknown'} (Port ${eb.port || 'N/A'})`);
    }
    
    // Learning Processor
    if (arch.learning_processor) {
        const lp = arch.learning_processor;
        const statusIcon = lp.status === "running" ? "🟢" : "🔴";
        console.log(`    ${statusIcon} ${lp.name || 'Unknown'}`);
    }
    
    // Agents
    if (arch.agents) {
        console.log("  Agents:");
        for (const [agentName, agentInfo] of Object.entries(arch.agents)) {
            const statusIcon = agentInfo.status === "running" ? "🟢" : "🔴";
            console.log(`    ${statusIcon} ${agentInfo.name || 'Unknown'}`);
        }
    }
}

function displayLearningMetrics(statsData) {
    if (!statsData || !statsData.learning) return;
    
    const learning = statsData.learning;
    console.log("\nLearning Metrics:");
    console.log(`  Heuristics:      ${learning.heuristics?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
    console.log(`  Golden Rules:    ${learning.golden_rules?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
    console.log(`  Trails:          ${learning.trails?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
    console.log(`  Pheromone Trails:${learning.pheromone_trails?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
    console.log(`  Learnings:       ${learning.learnings?.toLocaleString().padStart(8) || '0'.padStart(8)}`);
}

function displayEventStatistics(statsData) {
    if (!statsData || !statsData.events) return;
    
    const events = statsData.events;
    console.log(`\nEvent Processing:`);
    console.log(`  Events/Minute:   ${events.per_minute?.toFixed(1).padStart(8) || '0.0'.padStart(8)}`);
    
    const recentEvents = events.recent || [];
    if (recentEvents.length > 0) {
        console.log("  Recent Events:");
        recentEvents.slice(0, 5).forEach(event => { // Show top 5
            console.log(`    ${event.event_type?.padEnd(20) || 'unknown'.padEnd(20)} ${event.count?.toLocaleString().padStart(6) || '0'.padStart(6)}`);
        });
    }
}

async function generateSystemReport() {
    console.log("=".repeat(70));
    console.log("                       ELF System Report");
    console.log("=".repeat(70));
    
    try {
        const stats = await getDetailedStatistics();
        
        if (!stats || stats.status !== "success") {
            console.log("Failed to retrieve system statistics");
            if (stats && stats.error) {
                console.log(`Error: ${stats.error.message || 'Unknown error'}`);
            }
            return;
        }
        
        const data = stats.data;
        
        // System Overview
        console.log(`Report Time:     ${data.timestamp || 'Unknown'}`);
        console.log(`Uptime:          ${parseUptime(data.uptime_seconds || 0)}`);
        console.log(`Database Size:   ${(data.database?.size_kb || 0).toLocaleString()} KB`);
        console.log(`Last Activity:   ${data.system?.last_activity || 'Unknown'}`);
        
        console.log("-".repeat(70));
        
        // Architecture
        displayArchitectureInfo(data);
        
        console.log("-".repeat(70));
        
        // Learning Metrics
        displayLearningMetrics(data);
        
        console.log("-".repeat(70));
        
        // Event Statistics
        displayEventStatistics(data);
        
        console.log("-".repeat(70));
        
        // System Health
        const system = data.system || {};
        const healthStatus = system.status || "unknown";
        const statusIcon = healthStatus === "healthy" ? "🟢" : healthStatus === "unhealthy" ? "🔴" : "🟡";
        console.log(`System Health:   ${statusIcon} ${healthStatus.charAt(0).toUpperCase() + healthStatus.slice(1)}`);
        console.log(`Components:      ${system.components_healthy || 0}/${system.total_components || 0} healthy`);
        
        console.log("=".repeat(70));
    } catch (error) {
        console.error("Error generating system report:", error);
    }
}

async function getPerformanceTrends() {
    try {
        // In a real implementation, you would store historical data
        // For this example, we'll just return current stats with some analysis
        const stats = await getDetailedStatistics();
        
        if (!stats || stats.status !== "success") {
            return null;
        }
        
        const data = stats.data;
        
        // Simple trend analysis
        const eventsPm = data.events?.per_minute || 0;
        const toolsDetected = data.tools?.tools_detected || 0;
        const heuristics = data.learning?.heuristics || 0;
        
        const trendAnalysis = {
            events_trend: "normal",
            tools_trend: "normal",
            learning_trend: "normal"
        };
        
        // Simple threshold-based analysis
        if (eventsPm > 100) {
            trendAnalysis.events_trend = "high";
        } else if (eventsPm < 1) {
            trendAnalysis.events_trend = "low";
        }
        
        if (toolsDetected > 1000) {
            trendAnalysis.tools_trend = "high";
        } else if (toolsDetected < 10) {
            trendAnalysis.tools_trend = "low";
        }
        
        if (heuristics > 500) {
            trendAnalysis.learning_trend = "high";
        } else if (heuristics < 10) {
            trendAnalysis.learning_trend = "low";
        }
        
        return {
            current_stats: data,
            trend_analysis: trendAnalysis
        };
    } catch (error) {
        console.error('Error getting performance trends:', error);
        return null;
    }
}

// Example usage
(async () => {
    try {
        // Generate system report
        await generateSystemReport();
        
        // Get performance trends
        console.log("\nPerformance Trends:");
        const trends = await getPerformanceTrends();
        if (trends) {
            const analysis = trends.trend_analysis;
            console.log(`  Events Trend:    ${analysis.events_trend}`);
            console.log(`  Tools Trend:     ${analysis.tools_trend}`);
            console.log(`  Learning Trend:  ${analysis.learning_trend}`);
        }
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Response Fields

### Main Object
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | Timestamp of statistics (ISO 8601) |
| `uptime_seconds` | integer | System uptime in seconds |
| `architecture` | object | Architecture information |
| `database` | object | Database information |
| `events` | object | Event statistics |
| `learning` | object | Learning statistics |
| `tools` | object | Tool detection statistics |
| `system` | object | System information |

### Architecture Object
| Field | Type | Description |
|-------|------|-------------|
| `event_bridge` | object | EventBridge information |
| `learning_processor` | object | Learning processor information |
| `agents` | object | Agent information |

### Database Object
| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Database file path |
| `size_kb` | integer | Database size in KB |

### Events Object
| Field | Type | Description |
|-------|------|-------------|
| `per_minute` | number | Events per minute |
| `recent` | array | Recent event statistics |

### Learning Object
| Field | Type | Description |
|-------|------|-------------|
| `heuristics` | integer | Number of heuristics |
| `golden_rules` | integer | Number of golden rules |
| `trails` | integer | Number of trails |
| `pheromone_trails` | integer | Number of pheromone trails |
| `learnings` | integer | Number of learnings |

### Tools Object
| Field | Type | Description |
|-------|------|-------------|
| `tools_detected` | integer | Number of tools detected |

### System Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | System status |
| `components_healthy` | integer | Number of healthy components |
| `total_components` | integer | Total number of components |
| `last_activity` | string | Timestamp of last activity (ISO 8601) |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 Related Endpoints

- [Monitoring Summary](summary.md)
- [System Health](health.md)
- [Learning Statistics](learning.md)

## 📖 Further Reading

- [Monitoring API Overview](README.md)
- [OpenAPI Specification](../../openapi/monitoring.yaml)
- [Monitoring Implementation](../../../core/monitoring_api.py)
- [Schema Definitions](../../schemas/responses.md)