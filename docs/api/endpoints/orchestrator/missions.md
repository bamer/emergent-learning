# List Missions Endpoint

Retrieve a list of currently active missions in the ELF system.

## 🔧 Endpoint

```
GET /api/v1/missions
```

## 📥 Request

This endpoint does not require a request body.

### Query Parameters

Currently, this endpoint does not support query parameters.

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "missions": [
      {
        "mission_id": "string",
        "agent_type": "string",
        "mission": "string",
        "status": "string",
        "created_at": "2026-02-12T10:30:15Z",
        "updated_at": "2026-02-12T10:30:15Z",
        "progress": 0.0
      }
    ],
    "total": 0,
    "active": 0
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to retrieve missions",
    "details": {}
  }
}
```

## 📝 Example Request

```bash
curl -X GET http://localhost:9998/api/v1/missions
```

## 📝 Example Response

```json
{
  "status": "success",
  "data": {
    "missions": [
      {
        "mission_id": "mission_20260212_103015_12345",
        "agent_type": "researcher",
        "mission": "Research the latest developments in artificial intelligence",
        "status": "running",
        "created_at": "2026-02-12T10:30:15Z",
        "updated_at": "2026-02-12T10:32:45Z",
        "progress": 25.0
      },
      {
        "mission_id": "mission_20260212_091522_67890",
        "agent_type": "writer",
        "mission": "Write a summary of quantum computing advances",
        "status": "completed",
        "created_at": "2026-02-12T09:15:22Z",
        "updated_at": "2026-02-12T09:45:30Z",
        "progress": 100.0
      }
    ],
    "total": 2,
    "active": 1
  }
}
```

## 🐍 Python Example

```python
import requests
import json

def list_missions():
    """Get a list of all missions."""
    url = "http://localhost:9998/api/v1/missions"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving missions: {e}")
        return None

def list_active_missions():
    """Get a list of only active missions."""
    result = list_missions()
    
    if result and result.get("status") == "success":
        all_missions = result["data"]["missions"]
        active_missions = [m for m in all_missions if m["status"] in ["submitted", "running"]]
        return {
            "status": "success",
            "data": {
                "missions": active_missions,
                "total": len(active_missions),
                "active": len(active_missions)
            }
        }
    return result

# Example usage
if __name__ == "__main__":
    # List all missions
    result = list_missions()
    
    if result and result["status"] == "success":
        missions_data = result["data"]
        print(f"Total missions: {missions_data['total']}")
        print(f"Active missions: {missions_data['active']}")
        
        for mission in missions_data["missions"]:
            print(f"- {mission['mission_id']}: {mission['mission']} ({mission['status']})")
        
        # List only active missions
        active_result = list_active_missions()
        if active_result and active_result["status"] == "success":
            print("\nActive missions only:")
            for mission in active_result["data"]["missions"]:
                print(f"- {mission['mission_id']}: {mission['mission']} ({mission['status']})")
```

## 📄 JavaScript Example

```javascript
async function listMissions() {
    const url = 'http://localhost:9998/api/v1/missions';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error retrieving missions:', error);
        throw error;
    }
}

async function listActiveMissions() {
    try {
        const result = await listMissions();
        
        if (result.status === "success") {
            const allMissions = result.data.missions;
            const activeMissions = allMissions.filter(m => 
                m.status === "submitted" || m.status === "running"
            );
            
            return {
                status: "success",
                data: {
                    missions: activeMissions,
                    total: activeMissions.length,
                    active: activeMissions.length
                }
            };
        }
        return result;
    } catch (error) {
        console.error('Error listing active missions:', error);
        throw error;
    }
}

// Example usage
(async () => {
    try {
        // List all missions
        const result = await listMissions();
        
        if (result.status === "success") {
            const missionsData = result.data;
            console.log(`Total missions: ${missionsData.total}`);
            console.log(`Active missions: ${missionsData.active}`);
            
            missionsData.missions.forEach(mission => {
                console.log(`- ${mission.mission_id}: ${mission.mission} (${mission.status})`);
            });
            
            // List only active missions
            const activeResult = await listActiveMissions();
            if (activeResult.status === "success") {
                console.log("\nActive missions only:");
                activeResult.data.missions.forEach(mission => {
                    console.log(`- ${mission.mission_id}: ${mission.mission} (${mission.status})`);
                });
            }
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
| `missions` | array | Array of mission objects |
| `total` | integer | Total number of missions |
| `active` | integer | Number of active missions |

### Mission Object
| Field | Type | Description |
|-------|------|-------------|
| `mission_id` | string | Unique mission identifier |
| `agent_type` | string | Type of agent executing the mission |
| `mission` | string | Mission description |
| `status` | string | Current mission status |
| `created_at` | string | When mission was created (ISO 8601) |
| `updated_at` | string | When mission was last updated (ISO 8601) |
| `progress` | number | Mission progress percentage (0-100) |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 Related Endpoints

- [Submit Mission](mission.md)
- [Get Mission Details](mission.md)
- [Update Mission Status](mission.md)

## 📖 Further Reading

- [Orchestrator API Overview](README.md)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/responses.md)