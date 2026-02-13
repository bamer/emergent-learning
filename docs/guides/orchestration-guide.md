# ELF Orchestration Guide

This guide provides comprehensive information on how to effectively use the ELF orchestration system to manage agents, missions, and system components.

## 🎯 Understanding Orchestration

The ELF orchestration system provides centralized management of the entire framework through the Unified Orchestrator, which coordinates:

- **Agent Management**: Deployment and control of specialized agents
- **Mission Execution**: Task assignment and monitoring
- **Service Coordination**: System component interaction
- **Health Monitoring**: Component status and recovery
- **Decision Making**: AI-powered coordination

## 🚀 Core Concepts

### Agents
Specialized components that perform specific functions:
- **Researcher**: Information gathering and analysis
- **Writer**: Content creation and documentation
- **Analyst**: Data analysis and interpretation
- **Developer**: Code generation and debugging
- **Tester**: Quality assurance and testing

### Missions
Tasks or jobs assigned to agents with:
- **Clear objectives**: Well-defined goals
- **Specific scope**: Bounded requirements
- **Measurable outcomes**: Success criteria
- **Progress tracking**: Status monitoring

### Coordination
System-wide synchronization through:
- **Request/Response**: Direct communication
- **Event Publishing**: Asynchronous notifications
- **State Management**: Shared context
- **Resource Allocation**: Efficient distribution

## 🛠️ Orchestration API Overview

### Base URL
```
http://localhost:9998
```

### Authentication
Currently no authentication required for local development.

### Common Headers
```
Content-Type: application/json
Accept: application/json
```

## 📋 Key Endpoints

### Mission Management
- `POST /api/v1/mission` - Submit a new mission
- `GET /api/v1/mission/{id}` - Get mission details
- `POST /api/v1/mission/{id}/status` - Update mission status
- `GET /api/v1/missions` - List active missions

### Agent Management
- `GET /api/v1/agents` - List available agents
- `POST /api/v1/agents/{type}/run` - Run a specific agent

### Coordination
- `POST /api/v1/ask` - Request coordination or decisions
- `GET /api/v1/health/{component}` - Check component health

## 🎯 Practical Examples

### 1. Submitting a Research Mission

```bash
curl -X POST http://localhost:9998/api/v1/mission \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "mission": "Research quantum computing advances in 2026",
    "source": "api_guide"
  }'
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "mission_id": "mission_20260212_153045_abc123",
    "status": "submitted",
    "estimated_time": 600,
    "priority": 5,
    "confidence": 0.92
  }
}
```

### 2. Monitoring Mission Progress

```bash
curl -X GET http://localhost:9998/api/v1/mission/mission_20260212_153045_abc123
```

### 3. Coordinating Multiple Agents

```bash
# Ask orchestrator to coordinate a complex task
curl -X POST http://localhost:9998/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "component": "api_client",
    "request_type": "coordination",
    "data": {
      "task": "market_analysis",
      "requirements": {
        "research": "Renewable energy trends",
        "analysis": "Financial impact assessment",
        "report": "Executive summary"
      }
    },
    "priority": 7
  }'
```

## 🐍 Python Orchestration Example

```python
import requests
import time
import json

class ELFOrchestrator:
    def __init__(self, base_url="http://localhost:9998"):
        self.base_url = base_url
    
    def submit_mission(self, agent_type, mission, priority=5):
        """Submit a mission to an agent."""
        payload = {
            "agent_type": agent_type,
            "mission": mission,
            "priority": priority
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/mission",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Mission submission failed: {response.text}")
    
    def get_mission_status(self, mission_id):
        """Get the status of a mission."""
        response = requests.get(
            f"{self.base_url}/api/v1/mission/{mission_id}"
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get mission status: {response.text}")
    
    def wait_for_completion(self, mission_id, timeout=300, poll_interval=10):
        """Wait for a mission to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_mission_status(mission_id)
            
            if status["status"] == "success":
                mission_data = status["data"]
                if mission_data["status"] in ["completed", "failed", "cancelled"]:
                    return mission_data
            
            print(f"Mission {mission_id}: {mission_data['status']} "
                  f"({mission_data.get('progress', 0)}%)")
            
            time.sleep(poll_interval)
        
        raise Exception(f"Mission {mission_id} did not complete within {timeout} seconds")
    
    def coordinate_complex_task(self, task_description):
        """Coordinate a complex task involving multiple agents."""
        # Step 1: Research phase
        print("Starting research phase...")
        research_mission = self.submit_mission(
            "researcher",
            f"Research {task_description}",
            priority=6
        )
        
        research_id = research_mission["data"]["mission_id"]
        print(f"Research mission submitted: {research_id}")
        
        # Wait for research to complete
        research_result = self.wait_for_completion(research_id)
        print("Research phase completed")
        
        # Step 2: Analysis phase
        print("Starting analysis phase...")
        analysis_mission = self.submit_mission(
            "analyst",
            f"Analyze research findings: {research_result.get('mission', 'Research data')}",
            priority=6
        )
        
        analysis_id = analysis_mission["data"]["mission_id"]
        print(f"Analysis mission submitted: {analysis_id}")
        
        # Wait for analysis to complete
        analysis_result = self.wait_for_completion(analysis_id)
        print("Analysis phase completed")
        
        # Step 3: Report generation
        print("Starting report generation...")
        report_mission = self.submit_mission(
            "writer",
            f"Create executive summary based on: {analysis_result.get('mission', 'Analysis data')}",
            priority=5
        )
        
        report_id = report_mission["data"]["mission_id"]
        print(f"Report mission submitted: {report_id}")
        
        # Wait for report to complete
        report_result = self.wait_for_completion(report_id)
        print("Report generation completed")
        
        return {
            "research": research_result,
            "analysis": analysis_result,
            "report": report_result
        }

# Usage example
if __name__ == "__main__":
    orchestrator = ELFOrchestrator()
    
    try:
        # Submit a simple mission
        result = orchestrator.submit_mission(
            "researcher",
            "Research artificial intelligence trends in 2026"
        )
        print("Mission submitted:", json.dumps(result, indent=2))
        
        # Coordinate a complex task
        complex_result = orchestrator.coordinate_complex_task(
            "sustainable technology market opportunities"
        )
        print("Complex task completed:", json.dumps(complex_result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
```

## 📄 JavaScript Orchestration Example

```javascript
class ELFOrchestrator {
    constructor(baseUrl = 'http://localhost:9998') {
        this.baseUrl = baseUrl;
    }
    
    async submitMission(agentType, mission, priority = 5) {
        const response = await fetch(`${this.baseUrl}/api/v1/mission`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_type: agentType,
                mission: mission,
                priority: priority
            })
        });
        
        if (!response.ok) {
            throw new Error(`Mission submission failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async getMissionStatus(missionId) {
        const response = await fetch(`${this.baseUrl}/api/v1/mission/${missionId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to get mission status: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async waitForCompletion(missionId, timeout = 300000, pollInterval = 10000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const status = await this.getMissionStatus(missionId);
            
            if (status.status === 'success') {
                const missionData = status.data;
                if (['completed', 'failed', 'cancelled'].includes(missionData.status)) {
                    return missionData;
                }
            }
            
            console.log(`Mission ${missionId}: ${missionData.status} (${missionData.progress || 0}%)`);
            
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
        
        throw new Error(`Mission ${missionId} did not complete within ${timeout/1000} seconds`);
    }
    
    async coordinateComplexTask(taskDescription) {
        try {
            // Step 1: Research phase
            console.log('Starting research phase...');
            const researchMission = await this.submitMission(
                'researcher',
                `Research ${taskDescription}`,
                6
            );
            
            const researchId = researchMission.data.mission_id;
            console.log(`Research mission submitted: ${researchId}`);
            
            // Wait for research to complete
            const researchResult = await this.waitForCompletion(researchId);
            console.log('Research phase completed');
            
            // Step 2: Analysis phase
            console.log('Starting analysis phase...');
            const analysisMission = await this.submitMission(
                'analyst',
                `Analyze research findings: ${researchResult.mission || 'Research data'}`,
                6
            );
            
            const analysisId = analysisMission.data.mission_id;
            console.log(`Analysis mission submitted: ${analysisId}`);
            
            // Wait for analysis to complete
            const analysisResult = await this.waitForCompletion(analysisId);
            console.log('Analysis phase completed');
            
            // Step 3: Report generation
            console.log('Starting report generation...');
            const reportMission = await this.submitMission(
                'writer',
                `Create executive summary based on: ${analysisResult.mission || 'Analysis data'}`,
                5
            );
            
            const reportId = reportMission.data.mission_id;
            console.log(`Report mission submitted: ${reportId}`);
            
            // Wait for report to complete
            const reportResult = await this.waitForCompletion(reportId);
            console.log('Report generation completed');
            
            return {
                research: researchResult,
                analysis: analysisResult,
                report: reportResult
            };
        } catch (error) {
            console.error('Orchestration error:', error);
            throw error;
        }
    }
}

// Usage example
(async () => {
    const orchestrator = new ELFOrchestrator();
    
    try {
        // Submit a simple mission
        const result = await orchestrator.submitMission(
            'researcher',
            'Research artificial intelligence trends in 2026'
        );
        console.log('Mission submitted:', JSON.stringify(result, null, 2));
        
        // Coordinate a complex task
        const complexResult = await orchestrator.coordinateComplexTask(
            'sustainable technology market opportunities'
        );
        console.log('Complex task completed:', JSON.stringify(complexResult, null, 2));
        
    } catch (error) {
        console.error('Error:', error);
    }
})();
```

## 🎯 Advanced Orchestration Patterns

### 1. Parallel Mission Execution

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelOrchestrator(ELFOrchestrator):
    def __init__(self, base_url="http://localhost:9998", max_workers=5):
        super().__init__(base_url)
        self.max_workers = max_workers
    
    def submit_multiple_missions(self, missions):
        """Submit multiple missions in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all missions
            future_to_mission = {
                executor.submit(self._submit_single_mission, mission): mission 
                for mission in missions
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_mission):
                mission_desc = future_to_mission[future]
                try:
                    mission_id = future.result()
                    results[mission_desc] = mission_id
                except Exception as e:
                    print(f"Mission failed for '{mission_desc}': {e}")
                    results[mission_desc] = None
        
        return results
    
    def _submit_single_mission(self, mission_data):
        """Submit a single mission."""
        response = requests.post(
            f"{self.base_url}/api/v1/mission",
            json=mission_data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["data"]["mission_id"]
        else:
            raise Exception(f"Failed to submit mission: {response.text}")
```

### 2. Conditional Mission Chains

```python
class ConditionalOrchestrator(ELFOrchestrator):
    async def conditional_workflow(self, initial_mission, success_condition, alternative_mission):
        """Execute a mission with a conditional follow-up."""
        # Execute initial mission
        initial_result = await self.submit_mission(**initial_mission)
        initial_id = initial_result["data"]["mission_id"]
        
        # Wait for completion
        result = await self.wait_for_completion(initial_id)
        
        # Check condition
        if success_condition(result):
            # Execute success path
            success_result = await self.submit_mission(**alternative_mission)
            return {
                "initial": result,
                "follow_up": await self.wait_for_completion(
                    success_result["data"]["mission_id"]
                )
            }
        else:
            # Return initial result only
            return {"initial": result, "follow_up": None}
```

## 🛡️ Error Handling and Recovery

### Robust Mission Submission

```python
def robust_mission_submission(self, agent_type, mission, max_retries=3):
    """Submit a mission with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/mission",
                json={
                    "agent_type": agent_type,
                    "mission": mission
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                print(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Request failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed after {max_retries} attempts: {e}")
```

## 📊 Monitoring and Observability

### Mission Tracking Dashboard

```python
class MissionTracker:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.active_missions = {}
    
    def track_mission(self, mission_id, description):
        """Start tracking a mission."""
        self.active_missions[mission_id] = {
            "description": description,
            "start_time": time.time(),
            "status": "submitted"
        }
    
    def update_mission_status(self, mission_id, status, progress=None):
        """Update mission status."""
        if mission_id in self.active_missions:
            self.active_missions[mission_id]["status"] = status
            if progress is not None:
                self.active_missions[mission_id]["progress"] = progress
    
    def get_mission_report(self):
        """Generate a mission status report."""
        report = []
        for mission_id, info in self.active_missions.items():
            duration = time.time() - info["start_time"]
            report.append({
                "mission_id": mission_id,
                "description": info["description"],
                "status": info["status"],
                "duration": f"{duration:.1f}s"
            })
        return report
```

## 📚 Related Documentation

- [API Quick Start Guide](quickstart.md)
- [Monitoring Integration Guide](monitoring-integration.md)
- [Orchestrator API Documentation](../api/endpoints/orchestrator/)
- [Agent Management](../api/endpoints/orchestrator/agents.md)
- [Mission Management](../api/endpoints/orchestrator/mission.md)

## 📖 Further Reading

- [ELF Architecture Overview](../api/overview.md)
- [API Design Principles](../architecture/api-design.md)
- [Error Handling Best Practices](../api/error-handling.md)
- [Rate Limiting Policies](../api/rate-limiting.md)