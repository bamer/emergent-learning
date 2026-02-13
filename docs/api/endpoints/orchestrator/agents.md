# Agent Management Endpoints

Manage and interact with agents in the ELF system. Agents are specialized components that perform specific tasks.

## 🔧 Endpoints

### List Available Agents
```
GET /api/v1/agents
```

### Run a Specific Agent
```
POST /api/v1/agents/{agent_type}/run
```

## 📥 Run Agent Request Body

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

## 📤 Response

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
    "code": "RESOURCE_NOT_FOUND",
    "message": "Agent not found",
    "details": {}
  }
}
```

## 📝 Example Requests

### List Agents
```bash
curl -X GET http://localhost:9998/api/v1/agents
```

### Run Researcher Agent
```bash
curl -X POST http://localhost:9998/api/v1/agents/researcher/run \
  -H "Content-Type: application/json" \
  -d '{
    "mission": "Research the latest developments in artificial intelligence",
    "source": "dashboard"
  }'
```

## 📝 Example Responses

### List Agents Success
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "name": "researcher",
        "type": "analysis",
        "status": "available",
        "last_seen": "2026-02-12T10:30:15Z"
      },
      {
        "name": "writer",
        "type": "content",
        "status": "busy",
        "last_seen": "2026-02-12T10:25:30Z"
      },
      {
        "name": "analyst",
        "type": "data",
        "status": "available",
        "last_seen": "2026-02-12T10:30:15Z"
      }
    ],
    "status": "success"
  }
}
```

### Run Agent Success
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

## 🐍 Python Examples

```python
import requests
import json

def list_agents():
    """Get a list of available agents."""
    url = "http://localhost:9998/api/v1/agents"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing agents: {e}")
        return None

def run_agent(agent_type, mission, task_id=None, source="dashboard"):
    """Run a specific agent with a mission."""
    url = f"http://localhost:9998/api/v1/agents/{agent_type}/run"
    
    payload = {
        "mission": mission,
        "source": source
    }
    
    if task_id:
        payload["task_id"] = task_id
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error running agent {agent_type}: {e}")
        return None

def get_available_agents():
    """Get only available agents."""
    result = list_agents()
    
    if result and result.get("status") == "success":
        all_agents = result["data"]["agents"]
        available_agents = [a for a in all_agents if a["status"] == "available"]
        return {
            "status": "success",
            "data": {
                "agents": available_agents,
                "status": "success"
            }
        }
    return result

def run_mission_with_first_available_agent(mission):
    """Run a mission with the first available agent."""
    available_agents = get_available_agents()
    
    if available_agents and available_agents["status"] == "success":
        if available_agents["data"]["agents"]:
            first_agent = available_agents["data"]["agents"][0]
            return run_agent(first_agent["name"], mission)
        else:
            print("No available agents found")
            return None
    return available_agents

# Example usage
if __name__ == "__main__":
    # List all agents
    print("Available agents:")
    agents_result = list_agents()
    
    if agents_result and agents_result["status"] == "success":
        for agent in agents_result["data"]["agents"]:
            print(f"- {agent['name']} ({agent['type']}): {agent['status']}")
    
    # Get only available agents
    print("\nAvailable agents only:")
    available_result = get_available_agents()
    
    if available_result and available_result["status"] == "success":
        for agent in available_result["data"]["agents"]:
            print(f"- {agent['name']} ({agent['type']})")
    
    # Run a mission with the researcher agent
    print("\nRunning mission with researcher agent:")
    mission_result = run_agent(
        "researcher",
        "Research the latest developments in artificial intelligence"
    )
    
    if mission_result and mission_result["status"] == "success":
        mission_id = mission_result["data"]["mission_id"]
        print(f"Mission submitted: {mission_id}")
    
    # Run a mission with the first available agent
    print("\nRunning mission with first available agent:")
    auto_result = run_mission_with_first_available_agent(
        "Analyze market trends for renewable energy"
    )
    
    if auto_result and auto_result["status"] == "success":
        mission_id = auto_result["data"]["mission_id"]
        print(f"Mission submitted: {mission_id}")
```

## 📄 JavaScript Examples

```javascript
async function listAgents() {
    const url = 'http://localhost:9998/api/v1/agents';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error listing agents:', error);
        throw error;
    }
}

async function runAgent(agentType, mission, taskId = null, source = "dashboard") {
    const url = `http://localhost:9998/api/v1/agents/${agentType}/run`;
    
    const payload = {
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
        console.error(`Error running agent ${agentType}:`, error);
        throw error;
    }
}

async function getAvailableAgents() {
    try {
        const result = await listAgents();
        
        if (result.status === "success") {
            const allAgents = result.data.agents;
            const availableAgents = allAgents.filter(a => a.status === "available");
            return {
                status: "success",
                data: {
                    agents: availableAgents,
                    status: "success"
                }
            };
        }
        return result;
    } catch (error) {
        console.error('Error getting available agents:', error);
        throw error;
    }
}

async function runMissionWithFirstAvailableAgent(mission) {
    try {
        const availableAgents = await getAvailableAgents();
        
        if (availableAgents.status === "success" && availableAgents.data.agents.length > 0) {
            const firstAgent = availableAgents.data.agents[0];
            return await runAgent(firstAgent.name, mission);
        } else {
            throw new Error("No available agents found");
        }
    } catch (error) {
        console.error('Error running mission with available agent:', error);
        throw error;
    }
}

// Example usage
(async () => {
    try {
        // List all agents
        console.log("Available agents:");
        const agentsResult = await listAgents();
        
        if (agentsResult.status === "success") {
            agentsResult.data.agents.forEach(agent => {
                console.log(`- ${agent.name} (${agent.type}): ${agent.status}`);
            });
        }
        
        // Get only available agents
        console.log("\nAvailable agents only:");
        const availableResult = await getAvailableAgents();
        
        if (availableResult.status === "success") {
            availableResult.data.agents.forEach(agent => {
                console.log(`- ${agent.name} (${agent.type})`);
            });
        }
        
        // Run a mission with the researcher agent
        console.log("\nRunning mission with researcher agent:");
        const missionResult = await runAgent(
            "researcher",
            "Research the latest developments in artificial intelligence"
        );
        
        if (missionResult.status === "success") {
            const missionId = missionResult.data.mission_id;
            console.log(`Mission submitted: ${missionId}`);
        }
        
        // Run a mission with the first available agent
        console.log("\nRunning mission with first available agent:");
        const autoResult = await runMissionWithFirstAvailableAgent(
            "Analyze market trends for renewable energy"
        );
        
        if (autoResult.status === "success") {
            const missionId = autoResult.data.mission_id;
            console.log(`Mission submitted: ${missionId}`);
        }
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

## 📋 Agent Status Values

| Status | Description |
|--------|-------------|
| `available` | Agent is ready to accept missions |
| `busy` | Agent is currently executing a mission |
| `offline` | Agent is not responding or unavailable |

## 📋 Common Agent Types

| Agent Type | Purpose | Capabilities |
|------------|---------|--------------|
| `researcher` | Research and information gathering | Web search, document analysis |
| `writer` | Content creation and documentation | Writing, formatting, publishing |
| `analyst` | Data analysis and interpretation | Statistical analysis, pattern recognition |
| `developer` | Code generation and debugging | Programming, testing, deployment |
| `tester` | Quality assurance and testing | Test case execution, bug reporting |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Agent not found |
| `BAD_REQUEST` | 400 | Invalid mission parameters |
| `INVALID_INPUT` | 400 | Malformed request body |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## 📚 Related Endpoints

- [Submit Mission](mission.md)
- [List Missions](missions.md)
- [Ask Orchestrator](ask.md)

## 📖 Further Reading

- [Orchestrator API Overview](README.md)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/requests.md)