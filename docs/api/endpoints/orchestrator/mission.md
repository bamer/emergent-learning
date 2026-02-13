# Mission Endpoints

Manage missions in the ELF system. Missions represent tasks or jobs that agents execute.

## 🔧 Endpoints

### Submit Mission
```
POST /api/v1/mission
```

### Get Mission Details
```
GET /api/v1/mission/{mission_id}
```

### Update Mission Status
```
POST /api/v1/mission/{mission_id}/status
```

## 📥 Submit Mission Request Body

```json
{
  "agent_type": "string",
  "mission": "string",
  "task_id": "string",
  "source": "string"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_type` | string | Yes | Type of agent to execute the mission |
| `mission` | string | Yes | Mission description |
| `task_id` | string | No | Optional task identifier |
| `source` | string | No | Source of the mission request (default: "dashboard") |

## 📤 Submit Mission Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "mission_id": "string",
    "status": "string",
    "estimated_time": 0,
    "priority": 0,
    "confidence": 0.0
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid mission parameters",
    "details": {}
  }
}
```

## 📥 Update Mission Status Request Body

```json
{
  "status": "string",
  "progress": 0.0,
  "details": {}
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New mission status (submitted, running, completed, failed, cancelled) |
| `progress` | number | No | Mission progress percentage (0-100) |
| `details` | object | No | Additional status details |

## 📤 Update Mission Status Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "mission_id": "string",
    "status": "string",
    "estimated_time": 0,
    "priority": 0,
    "confidence": 0.0
  }
}
```

## 📝 Example Requests

### Submit Mission
```bash
curl -X POST http://localhost:9998/api/v1/mission \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "mission": "Research the latest developments in artificial intelligence",
    "source": "dashboard"
  }'
```

### Get Mission Details
```bash
curl -X GET http://localhost:9998/api/v1/mission/mission_20260212_103015_12345
```

### Update Mission Status
```bash
curl -X POST http://localhost:9998/api/v1/mission/mission_20260212_103015_12345/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running",
    "progress": 25.0
  }'
```

## 📝 Example Responses

### Submit Mission Success
```json
{
  "status": "success",
  "data": {
    "mission_id": "mission_20260212_103015_12345",
    "status": "submitted",
    "estimated_time": 300,
    "priority": 3,
    "confidence": 0.95
  }
}
```

### Get Mission Details
```json
{
  "status": "success",
  "data": {
    "mission_id": "mission_20260212_103015_12345",
    "agent_type": "researcher",
    "mission": "Research the latest developments in artificial intelligence",
    "status": "running",
    "created_at": "2026-02-12T10:30:15Z",
    "updated_at": "2026-02-12T10:32:45Z",
    "progress": 25.0
  }
}
```

### Update Mission Status Success
```json
{
  "status": "success",
  "data": {
    "mission_id": "mission_20260212_103015_12345",
    "status": "running",
    "estimated_time": 225,
    "priority": 3,
    "confidence": 0.9
  }
}
```

## 🐍 Python Examples

```python
import requests
import json
from datetime import datetime

def submit_mission(agent_type, mission, task_id=None, source="dashboard"):
    """Submit a new mission to the orchestrator."""
    url = "http://localhost:9998/api/v1/mission"
    
    payload = {
        "agent_type": agent_type,
        "mission": mission,
        "source": source
    }
    
    if task_id:
        payload["task_id"] = task_id
    
    response = requests.post(url, json=payload)
    return response.json()

def get_mission(mission_id):
    """Get details for a specific mission."""
    url = f"http://localhost:9998/api/v1/mission/{mission_id}"
    
    response = requests.get(url)
    return response.json()

def update_mission_status(mission_id, status, progress=None, details=None):
    """Update the status of a mission."""
    url = f"http://localhost:9998/api/v1/mission/{mission_id}/status"
    
    payload = {"status": status}
    
    if progress is not None:
        payload["progress"] = progress
    
    if details:
        payload["details"] = details
    
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Submit a mission
    result = submit_mission(
        agent_type="researcher",
        mission="Research the latest developments in artificial intelligence"
    )
    
    if result["status"] == "success":
        mission_id = result["data"]["mission_id"]
        print(f"Mission submitted: {mission_id}")
        
        # Get mission details
        mission_details = get_mission(mission_id)
        print(f"Mission details: {json.dumps(mission_details, indent=2)}")
        
        # Update mission status
        update_result = update_mission_status(
            mission_id=mission_id,
            status="running",
            progress=25.0
        )
        print(f"Status updated: {json.dumps(update_result, indent=2)}")
```

## 📄 JavaScript Examples

```javascript
async function submitMission(agentType, mission, taskId = null, source = "dashboard") {
    const url = 'http://localhost:9998/api/v1/mission';
    
    const payload = {
        agent_type: agentType,
        mission: mission,
        source: source
    };
    
    if (taskId) {
        payload.task_id = taskId;
    }
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error submitting mission:', error);
        throw error;
    }
}

async function getMission(missionId) {
    const url = `http://localhost:9998/api/v1/mission/${missionId}`;
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error getting mission:', error);
        throw error;
    }
}

async function updateMissionStatus(missionId, status, progress = null, details = null) {
    const url = `http://localhost:9998/api/v1/mission/${missionId}/status`;
    
    const payload = { status: status };
    
    if (progress !== null) {
        payload.progress = progress;
    }
    
    if (details) {
        payload.details = details;
    }
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error updating mission status:', error);
        throw error;
    }
}

// Example usage
(async () => {
    try {
        // Submit a mission
        const result = await submitMission(
            "researcher",
            "Research the latest developments in artificial intelligence"
        );
        
        if (result.status === "success") {
            const missionId = result.data.mission_id;
            console.log(`Mission submitted: ${missionId}`);
            
            // Get mission details
            const missionDetails = await getMission(missionId);
            console.log("Mission details:", JSON.stringify(missionDetails, null, 2));
            
            // Update mission status
            const updateResult = await updateMissionStatus(
                missionId,
                "running",
                25.0
            );
            console.log("Status updated:", JSON.stringify(updateResult, null, 2));
        }
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Mission Status Values

| Status | Description |
|--------|-------------|
| `submitted` | Mission has been submitted but not yet started |
| `running` | Mission is currently being executed |
| `completed` | Mission has finished successfully |
| `failed` | Mission encountered an error and failed |
| `cancelled` | Mission was cancelled before completion |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BAD_REQUEST` | 400 | Invalid mission parameters |
| `INVALID_INPUT` | 400 | Malformed request body |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing |
| `RESOURCE_NOT_FOUND` | 404 | Mission not found |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## 📚 Related Endpoints

- [List Missions](missions.md)
- [Ask Orchestrator](ask.md)
- [Agent Management](agents.md)

## 📖 Further Reading

- [Orchestrator API Overview](README.md)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/requests.md)