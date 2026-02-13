# JavaScript Orchestrator Client Examples

JavaScript examples for interacting with the ELF Orchestrator API using the fetch API and Node.js.

## 🚀 Quick Start

### Basic Setup
```javascript
// Base URL for the orchestrator
const BASE_URL = 'http://localhost:9998';

async function makeRequest(method, endpoint, data = null) {
    const url = `${BASE_URL}${endpoint}`;
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        return {
            status: 'error',
            error: {
                message: error.message || 'Unknown error'
            }
        };
    }
}
```

### Check Orchestrator Status
```javascript
async function checkOrchestratorStatus() {
    try {
        const response = await makeRequest('GET', '/status');
        
        if (response.status === 'success') {
            const data = response.data;
            console.log(`Orchestrator running: ${data.running}`);
            console.log(`Events processed: ${data.events_processed.toLocaleString()}`);
            console.log(`Uptime: ${data.uptime_seconds} seconds`);
            return data;
        } else {
            console.error('Error:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to check orchestrator status:', error);
        return null;
    }
}

// Usage
checkOrchestratorStatus();
```

### Submit a Mission
```javascript
async function submitMission(agentType, mission, taskId = null) {
    const payload = {
        agent_type: agentType,
        mission: mission
    };
    
    if (taskId) {
        payload.task_id = taskId;
    }
    
    try {
        const response = await makeRequest('POST', '/api/v1/mission', payload);
        
        if (response.status === 'success') {
            const missionId = response.data.mission_id;
            console.log(`Mission submitted successfully: ${missionId}`);
            return missionId;
        } else {
            console.error('Error submitting mission:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to submit mission:', error);
        return null;
    }
}

// Usage
const missionId = await submitMission(
    'researcher',
    'Research the latest developments in artificial intelligence'
);
```

## 📋 Detailed Examples

### Ask Orchestrator for Coordination
```javascript
async function askOrchestrator(component, requestType, data, priority = 1) {
    const payload = {
        component: component,
        request_type: requestType,
        data: data,
        priority: priority
    };
    
    try {
        const response = await makeRequest('POST', '/api/v1/ask', payload);
        
        if (response.status === 'success') {
            console.log('Orchestrator response received:');
            console.log(JSON.stringify(response.data, null, 2));
            return response.data;
        } else {
            console.error('Error:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to ask orchestrator:', error);
        return null;
    }
}

// Usage
const result = await askOrchestrator(
    'dashboard',
    'coordination',
    { action: 'list_agents' },
    5
);
```

### Get Mission Details
```javascript
async function getMissionDetails(missionId) {
    try {
        const response = await makeRequest('GET', `/api/v1/mission/${missionId}`);
        
        if (response.status === 'success') {
            const missionData = response.data;
            console.log(`Mission ID: ${missionData.mission_id}`);
            console.log(`Agent Type: ${missionData.agent_type}`);
            console.log(`Status: ${missionData.status}`);
            console.log(`Progress: ${missionData.progress || 0}%`);
            return missionData;
        } else {
            console.error('Error:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to get mission details:', error);
        return null;
    }
}

// Usage
const missionData = await getMissionDetails('mission_20260212_103015_12345');
```

### Update Mission Status
```javascript
async function updateMissionStatus(missionId, status, progress = null) {
    const payload = { status: status };
    
    if (progress !== null) {
        payload.progress = progress;
    }
    
    try {
        const response = await makeRequest('POST', `/api/v1/mission/${missionId}/status`, payload);
        
        if (response.status === 'success') {
            console.log(`Mission ${missionId} status updated to ${status}`);
            return response.data;
        } else {
            console.error('Error updating mission:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to update mission status:', error);
        return null;
    }
}

// Usage
const updateResult = await updateMissionStatus('mission_20260212_103015_12345', 'running', 25.0);
```

### List Active Missions
```javascript
async function listActiveMissions() {
    try {
        const response = await makeRequest('GET', '/api/v1/missions');
        
        if (response.status === 'success') {
            const { missions, total, active } = response.data;
            
            console.log(`Total missions: ${total}`);
            console.log(`Active missions: ${active}`);
            
            missions.forEach(mission => {
                console.log(`- ${mission.mission_id}: ${mission.mission} (${mission.status})`);
            });
            
            return missions;
        } else {
            console.error('Error:', response.error.message);
            return [];
        }
    } catch (error) {
        console.error('Failed to list missions:', error);
        return [];
    }
}

// Usage
const missions = await listActiveMissions();
```

### Check Component Health
```javascript
async function checkComponentHealth(component) {
    try {
        const response = await makeRequest('GET', `/api/v1/health/${component}`);
        
        if (response.status === 'success') {
            const healthData = response.data;
            console.log(`${component} health: ${healthData.status}`);
            if (healthData.details) {
                console.log(`Details: ${JSON.stringify(healthData.details)}`);
            }
            return healthData;
        } else {
            console.error(`Error checking ${component} health:`, response.error.message);
            return null;
        }
    } catch (error) {
        console.error(`Failed to check ${component} health:`, error);
        return null;
    }
}

// Usage
const health = await checkComponentHealth('event_bridge');
```

### List Available Agents
```javascript
async function listAgents() {
    try {
        const response = await makeRequest('GET', '/api/v1/agents');
        
        if (response.status === 'success') {
            const agents = response.data.agents;
            console.log('Available agents:');
            agents.forEach(agent => {
                console.log(`- ${agent.name} (${agent.type}): ${agent.status}`);
            });
            return agents;
        } else {
            console.error('Error:', response.error.message);
            return [];
        }
    } catch (error) {
        console.error('Failed to list agents:', error);
        return [];
    }
}

// Usage
const agents = await listAgents();
```

### Run a Specific Agent
```javascript
async function runAgent(agentType, mission) {
    const payload = { mission: mission };
    
    try {
        const response = await makeRequest('POST', `/api/v1/agents/${agentType}/run`, payload);
        
        if (response.status === 'success') {
            const missionId = response.data.mission_id;
            console.log(`Agent ${agentType} started mission: ${missionId}`);
            return missionId;
        } else {
            console.error('Error running agent:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to run agent:', error);
        return null;
    }
}

// Usage
const missionId = await runAgent('researcher', 'Analyze market trends for renewable energy');
```

## ⚠️ Error Handling Examples

### Comprehensive Error Handling
```javascript
async function robustApiCall(method, endpoint, data = null, retries = 3, timeout = 30000) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            const url = `${BASE_URL}${endpoint}`;
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                signal: controller.signal
            };
            
            if (data && (method === 'POST' || method === 'PUT')) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(url, options);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                console.warn(`Timeout on attempt ${attempt}/${retries}`);
            } else {
                console.warn(`Attempt ${attempt}/${retries} failed: ${error.message}`);
            }
            
            if (attempt < retries) {
                // Exponential backoff
                const delay = Math.pow(2, attempt) * 1000;
                console.log(`Retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            } else {
                return {
                    status: 'error',
                    error: {
                        message: `Failed after ${retries} attempts: ${error.message}`
                    }
                };
            }
        }
    }
}

// Usage
const response = await robustApiCall('GET', '/status');
```

### Handle Different Error Types
```javascript
function handleApiErrors(response) {
    if (response.status === 'error') {
        const errorCode = response.error.code || 'UNKNOWN';
        const errorMessage = response.error.message || 'Unknown error';
        const errorDetails = response.error.details || {};
        
        switch (errorCode) {
            case 'RESOURCE_NOT_FOUND':
                console.error(`Resource not found: ${errorMessage}`);
                break;
            case 'BAD_REQUEST':
                console.error(`Invalid request: ${errorMessage}`);
                break;
            case 'INTERNAL_ERROR':
                console.error(`Server error: ${errorMessage}`);
                break;
            case 'RATE_LIMIT_EXCEEDED':
                console.error(`Rate limit exceeded: ${errorMessage}`);
                // Could implement retry logic here
                break;
            default:
                console.error(`API error (${errorCode}): ${errorMessage}`);
        }
        
        if (Object.keys(errorDetails).length > 0) {
            console.error('Details:', JSON.stringify(errorDetails, null, 2));
        }
        
        return false;
    }
    return true;
}

// Usage
const response = await makeRequest('GET', '/api/v1/mission/nonexistent');
if (handleApiErrors(response)) {
    // Process successful response
    console.log('Success!');
}
```

## 🛠️ Advanced Examples

### Mission Monitoring Class
```javascript
class MissionMonitor {
    constructor(missionId) {
        this.missionId = missionId;
        this.monitoring = false;
        this.intervalId = null;
    }
    
    async startMonitoring(callback = null, interval = 10000) {
        if (this.monitoring) {
            console.log('Already monitoring');
            return;
        }
        
        this.monitoring = true;
        console.log(`Started monitoring mission ${this.missionId}`);
        
        const monitorFunction = async () => {
            if (!this.monitoring) return;
            
            try {
                const response = await makeRequest('GET', `/api/v1/mission/${this.missionId}`);
                
                if (response.status === 'success') {
                    const missionData = response.data;
                    const status = missionData.status;
                    
                    if (callback) {
                        callback(missionData);
                    } else {
                        console.log(`Mission ${this.missionId}: ${status} (${missionData.progress || 0}%)`);
                    }
                    
                    // Stop monitoring if mission is complete
                    if (['completed', 'failed', 'cancelled'].includes(status)) {
                        this.stopMonitoring();
                        console.log(`Mission ${this.missionId} finished with status: ${status}`);
                    }
                } else {
                    console.error(`Error monitoring mission: ${response.error.message}`);
                }
            } catch (error) {
                console.error('Monitoring error:', error);
            }
        };
        
        // Run immediately
        await monitorFunction();
        
        // Set up interval
        this.intervalId = setInterval(monitorFunction, interval);
    }
    
    stopMonitoring() {
        this.monitoring = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        console.log(`Stopped monitoring mission ${this.missionId}`);
    }
}

// Usage
const monitor = new MissionMonitor('mission_20260212_103015_12345');

function missionCallback(missionData) {
    console.log(`Mission update: ${missionData.status} - ${missionData.progress || 0}%`);
}

// Start monitoring
await monitor.startMonitoring(missionCallback, 10000); // Check every 10 seconds

// Stop monitoring after 2 minutes
setTimeout(() => {
    monitor.stopMonitoring();
}, 120000);
```

### Batch Mission Processor
```javascript
class BatchMissionProcessor {
    constructor(maxConcurrent = 5) {
        this.maxConcurrent = maxConcurrent;
    }
    
    async submitMissions(missions) {
        const results = {};
        const promises = [];
        
        // Process missions in batches
        for (let i = 0; i < missions.length; i += this.maxConcurrent) {
            const batch = missions.slice(i, i + this.maxConcurrent);
            const batchPromises = batch.map(mission => this._submitSingleMission(mission));
            
            try {
                const batchResults = await Promise.allSettled(batchPromises);
                batchResults.forEach((result, index) => {
                    const missionDesc = batch[index].mission;
                    if (result.status === 'fulfilled') {
                        results[missionDesc] = result.value;
                    } else {
                        console.error(`Mission '${missionDesc}' failed:`, result.reason);
                        results[missionDesc] = null;
                    }
                });
            } catch (error) {
                console.error('Batch processing error:', error);
            }
        }
        
        return results;
    }
    
    async _submitSingleMission(missionData) {
        const response = await makeRequest('POST', '/api/v1/mission', missionData);
        
        if (response.status === 'success') {
            return response.data.mission_id;
        } else {
            throw new Error(`Failed to submit mission '${missionData.mission}': ${response.error.message}`);
        }
    }
}

// Usage
const processor = new BatchMissionProcessor(3);

const missions = [
    {
        agent_type: 'researcher',
        mission: 'Research AI ethics'
    },
    {
        agent_type: 'writer',
        mission: 'Write technical documentation'
    },
    {
        agent_type: 'analyst',
        mission: 'Analyze performance metrics'
    }
];

const missionIds = await processor.submitMissions(missions);
console.log('Submitted missions:');
for (const [desc, missionId] of Object.entries(missionIds)) {
    if (missionId) {
        console.log(`  ${desc} -> ${missionId}`);
    } else {
        console.log(`  ${desc} -> FAILED`);
    }
}
```

### Health Check with Alerting
```javascript
class HealthChecker {
    constructor(smtpConfig = null) {
        this.smtpConfig = smtpConfig;
    }
    
    async checkAllComponents() {
        const components = ['event_bridge', 'orchestrator', 'dashboard', 'learning_processor'];
        const healthStatus = {};
        
        for (const component of components) {
            try {
                const response = await makeRequest('GET', `/api/v1/health/${component}`);
                healthStatus[component] = response.status === 'success' 
                    ? response.data.status 
                    : 'error';
            } catch (error) {
                console.error(`Error checking ${component} health:`, error);
                healthStatus[component] = 'error';
            }
        }
        
        return healthStatus;
    }
    
    async sendAlert(subject, message, recipient) {
        // In a real implementation, you would use an email service
        // For this example, we'll just log the alert
        console.log('EMAIL ALERT (simulated):');
        console.log(`To: ${recipient}`);
        console.log(`Subject: ${subject}`);
        console.log(`Message: ${message}`);
        
        // Example using a hypothetical email service:
        /*
        if (this.smtpConfig) {
            try {
                const emailService = require('some-email-service');
                await emailService.send({
                    from: this.smtpConfig.from,
                    to: recipient,
                    subject: subject,
                    text: message
                });
                console.log(`Alert sent to ${recipient}`);
            } catch (error) {
                console.error('Failed to send alert:', error);
            }
        }
        */
    }
    
    async runHealthCheck(alertRecipient = null) {
        console.log('Running system health check...');
        
        const healthStatus = await this.checkAllComponents();
        const unhealthyComponents = Object.entries(healthStatus)
            .filter(([component, status]) => status !== 'healthy')
            .map(([component, status]) => component);
        
        console.log('Component Health:');
        for (const [component, status] of Object.entries(healthStatus)) {
            const statusIcons = {
                'healthy': '🟢',
                'degraded': '🟡',
                'unhealthy': '🔴',
                'error': '❌'
            };
            const icon = statusIcons[status] || '❓';
            console.log(`  ${icon} ${component}: ${status}`);
        }
        
        if (unhealthyComponents.length > 0) {
            const alertMsg = `ALERT: Unhealthy components detected: ${unhealthyComponents.join(', ')}`;
            console.log(`\n${alertMsg}`);
            
            if (alertRecipient) {
                await this.sendAlert(
                    'ELF System Health Alert',
                    alertMsg,
                    alertRecipient
                );
            }
        } else {
            console.log('\n✅ All components are healthy');
        }
        
        return {
            healthStatus,
            hasIssues: unhealthyComponents.length > 0,
            unhealthyComponents
        };
    }
}

// Usage
const checker = new HealthChecker();
const result = await checker.runHealthCheck('admin@example.com');
```

## 📚 Related Examples

- [EventBridge JavaScript Examples](eventbridge-client.md)
- [cURL Orchestrator Examples](../../curl/orchestrator-examples.md)
- [Python Orchestrator Examples](../../python/orchestrator-client.md)

## 📖 Further Reading

- [Orchestrator API Documentation](../../endpoints/orchestrator/)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/)