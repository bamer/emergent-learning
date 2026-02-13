# JavaScript EventBridge Client Examples

JavaScript examples for interacting with the ELF EventBridge API using the fetch API and Node.js.

## 🚀 Quick Start

### Basic Setup
```javascript
// Base URL for the EventBridge
const EVENTBRIDGE_URL = 'http://localhost:9998';

async function makeEventBridgeRequest(method, endpoint, data = null) {
    const url = `${EVENTBRIDGE_URL}${endpoint}`;
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
        console.error('EventBridge request failed:', error);
        return {
            status: 'error',
            error: {
                message: error.message || 'Unknown error'
            }
        };
    }
}
```

### Check EventBridge Status
```javascript
async function checkEventBridgeStatus() {
    try {
        const response = await makeEventBridgeRequest('GET', '/status');
        
        if (response.status === 'success') {
            const data = response.data;
            const statusIcon = data.running ? '🟢' : '🔴';
            console.log(`${statusIcon} EventBridge Status`);
            console.log(`   Running: ${data.running}`);
            console.log(`   Events Processed: ${data.events_processed.toLocaleString()}`);
            console.log(`   Uptime: ${data.uptime_seconds} seconds`);
            console.log(`   Last Event: ${data.last_event_time || 'Never'}`);
            if (data.version) {
                console.log(`   Version: ${data.version}`);
            }
            return data;
        } else {
            console.error('❌ Error:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to check EventBridge status:', error);
        return null;
    }
}

// Usage
checkEventBridgeStatus();
```

### Check System Health
```javascript
async function checkSystemHealth() {
    try {
        const response = await makeEventBridgeRequest('GET', '/api/v1/health');
        
        if (response.status === 'success') {
            const data = response.data;
            const statusIcons = {
                'healthy': '🟢',
                'degraded': '🟡',
                'unhealthy': '🔴'
            };
            const statusIcon = statusIcons[data.status] || '❓';
            
            console.log(`${statusIcon} System Health: ${data.status}`);
            console.log(`   Service: ${data.service}`);
            console.log(`   Running: ${data.running}`);
            console.log(`   Events: ${data.events.toLocaleString()}`);
            console.log(`   Timestamp: ${data.timestamp}`);
            return data;
        } else {
            console.error('❌ Error:', response.error.message);
            return null;
        }
    } catch (error) {
        console.error('Failed to check system health:', error);
        return null;
    }
}

// Usage
checkSystemHealth();
```

## 📋 Detailed Examples

### Check Component Health
```javascript
async function checkComponentHealth(component) {
    try {
        const response = await makeEventBridgeRequest('GET', `/api/v1/health/${component}`);
        
        if (response.status === 'success') {
            const data = response.data;
            const statusIcons = {
                'healthy': '🟢',
                'degraded': '🟡',
                'unhealthy': '🔴'
            };
            const statusIcon = statusIcons[data.status] || '❓';
            
            console.log(`${statusIcon} ${component.charAt(0).toUpperCase() + component.slice(1)} Health: ${data.status}`);
            
            if (data.details && Object.keys(data.details).length > 0) {
                console.log('   Details:');
                for (const [key, value] of Object.entries(data.details)) {
                    console.log(`     ${key}: ${value}`);
                }
            }
            
            if (data.confidence !== undefined) {
                console.log(`   Confidence: ${data.confidence.toFixed(2)}`);
            }
            
            if (data.recommendation) {
                console.log(`   Recommendation: ${data.recommendation}`);
            }
            return data;
        } else {
            const errorCode = response.error.code || 'UNKNOWN';
            if (errorCode === 'RESOURCE_NOT_FOUND') {
                console.log(`❓ Component '${component}' not found`);
            } else {
                console.error(`❌ Error checking ${component} health:`, response.error.message);
            }
            return null;
        }
    } catch (error) {
        console.error(`Failed to check ${component} health:`, error);
        return null;
    }
}

// Usage
const components = ['event_bridge', 'mission_bridge', 'sentinel_monitor'];
for (const component of components) {
    await checkComponentHealth(component);
    console.log();
}
```

### Get Event Statistics
```javascript
async function getEventStatistics() {
    // First check if monitoring API is available (port 9997)
    try {
        const monitoringResponse = await fetch('http://localhost:9997/stats');
        if (monitoringResponse.ok) {
            const stats = await monitoringResponse.json();
            if (stats.status === 'success') {
                const eventsData = stats.data.events || {};
                console.log('📊 Event Processing Statistics');
                console.log(`   Events per minute: ${eventsData.per_minute?.toFixed(1) || 0}`);
                
                const recentEvents = eventsData.recent || [];
                if (recentEvents.length > 0) {
                    console.log('   Recent Events:');
                    recentEvents.slice(0, 5).forEach(event => { // Top 5
                        console.log(`     ${event.event_type.padEnd(25)} ${event.count.toLocaleString().padStart(6)}`);
                    });
                }
                return stats;
            }
        }
    } catch (error) {
        // Monitoring API not available, continue with fallback
    }
    
    // Fallback to basic status info
    console.log('ℹ️  Detailed event statistics require monitoring API (port 9997)');
    const response = await makeEventBridgeRequest('GET', '/status');
    if (response.status === 'success') {
        const data = response.data;
        console.log(`📈 Total Events Processed: ${data.events_processed?.toLocaleString() || 0}`);
        if (data.event_stats) {
            const eventStats = data.event_stats;
            console.log(`   Event Types: ${eventStats.total_types || 0}`);
            const topEvents = eventStats.top_events || {};
            if (Object.keys(topEvents).length > 0) {
                console.log('   Top Event Types:');
                Object.entries(topEvents)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .forEach(([eventType, count]) => {
                        console.log(`     ${eventType.padEnd(25)} ${count.toLocaleString().padStart(6)}`);
                    });
            }
        }
    }
    
    return response;
}

// Usage
getEventStatistics();
```

## ⚠️ Error Handling Examples

### Robust Connection Handling
```javascript
async function robustEventBridgeCheck(retries = 3, timeout = 10000) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            // First check if port is accessible using a timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            const response = await fetch(`${EVENTBRIDGE_URL}/status`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                console.warn(`📡 Timeout on attempt ${attempt}/${retries}`);
            } else {
                console.warn(`📡 Connection attempt ${attempt}/${retries} failed: ${error.message}`);
            }
            
            if (attempt < retries) {
                // Exponential backoff
                const delay = Math.pow(2, attempt) * 1000;
                console.log(`   Waiting ${delay}ms before retry...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            } else {
                return {
                    status: 'error',
                    error: {
                        code: 'CONNECTION_FAILED',
                        message: `Cannot connect to EventBridge after ${retries} attempts`
                    }
                };
            }
        }
    }
}

// Usage
const response = await robustEventBridgeCheck(3, 15000);
if (response.status === 'success') {
    console.log('✅ EventBridge is responsive');
    const data = response.data;
    console.log(`   Running: ${data.running}`);
    console.log(`   Events: ${data.events_processed?.toLocaleString() || 0}`);
} else {
    console.error('❌ EventBridge check failed:', response.error.message);
}
```

### Handle Different Response Scenarios
```javascript
async function comprehensiveStatusCheck() {
    console.log('🔍 Performing comprehensive EventBridge status check...');
    console.log('='.repeat(50));
    
    // 1. Basic connectivity check
    console.log('1. Connectivity Check');
    try {
        const response = await fetch(`${EVENTBRIDGE_URL}/status`, { timeout: 5000 });
        if (response.ok) {
            console.log('   🟢 Connection successful');
        } else {
            console.log(`   🔴 HTTP ${response.status}: ${response.statusText}`);
            return false;
        }
    } catch (error) {
        console.log(`   🔴 Connection failed: ${error.message}`);
        return false;
    }
    
    // 2. JSON parsing check
    console.log('2. Response Parsing');
    try {
        const response = await fetch(`${EVENTBRIDGE_URL}/status`);
        const data = await response.json();
        console.log('   🟢 JSON parsing successful');
        
        // 3. Status validation
        console.log('3. Status Validation');
        if (data.status === 'success') {
            console.log('   🟢 Status OK');
            const bridgeData = data.data;
            
            // 4. Data field validation
            const requiredFields = ['running', 'events_processed', 'opencode_server'];
            const missingFields = requiredFields.filter(field => !(field in bridgeData));
            
            if (missingFields.length > 0) {
                console.log(`   🔴 Missing required fields: ${missingFields.join(', ')}`);
                return false;
            } else {
                console.log('   🟢 All required fields present');
                
                // 5. Logical validation
                console.log('4. Logical Validation');
                if (typeof bridgeData.running !== 'boolean') {
                    console.log('   🔴 \'running\' field should be boolean');
                    return false;
                } else if (!Number.isInteger(bridgeData.events_processed)) {
                    console.log('   🔴 \'events_processed\' field should be integer');
                    return false;
                } else if (bridgeData.events_processed < 0) {
                    console.log('   🔴 \'events_processed\' should be non-negative');
                    return false;
                } else {
                    console.log('   🟢 All validations passed');
                    return true;
                }
            }
        } else {
            console.log(`   🔴 API returned error: ${data.error?.message || 'Unknown error'}`);
            return false;
        }
    } catch (error) {
        console.log(`   🔴 JSON parsing failed: ${error.message}`);
        return false;
    }
}

// Usage
if (await comprehensiveStatusCheck()) {
    console.log('\n✅ EventBridge is fully operational');
} else {
    console.log('\n❌ EventBridge has issues that need attention');
}
```

## 🛠️ Advanced Examples

### Continuous Monitoring Script
```javascript
class EventBridgeMonitor {
    constructor(logFile = 'eventbridge_monitor.log') {
        this.logFile = logFile;
        this.monitoring = false;
        this.intervalId = null;
    }
    
    startMonitoring(interval = 60000) {
        if (this.monitoring) {
            console.log('🔬 Already monitoring');
            return;
        }
        
        this.monitoring = true;
        console.log(`🔬 Starting EventBridge monitoring (interval: ${interval/1000}s)`);
        console.log('Press Ctrl+C to stop');
        console.log('-'.repeat(50));
        
        // Run immediately
        this._collectMetrics();
        
        // Set up interval
        this.intervalId = setInterval(() => {
            this._collectMetrics();
        }, interval);
        
        // Handle graceful shutdown
        process.on('SIGINT', () => {
            console.log('\n🛑 Stopping monitoring...');
            this.stopMonitoring();
            process.exit(0);
        });
    }
    
    stopMonitoring() {
        this.monitoring = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        console.log('🛑 Monitoring stopped');
    }
    
    async _collectMetrics() {
        const timestamp = new Date().toISOString();
        
        try {
            // Get EventBridge status
            const response = await fetch(`${EVENTBRIDGE_URL}/status`);
            if (response.ok) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    const bridgeData = data.data;
                    const running = bridgeData.running || false;
                    const eventsProcessed = bridgeData.events_processed || 0;
                    const uptime = bridgeData.uptime_seconds || 0;
                    
                    // Calculate events per minute (approximate)
                    const eventsPerMinute = uptime > 0 ? (eventsProcessed / uptime) * 60 : 0;
                    const status = running ? 'healthy' : 'unhealthy';
                    
                    // Log to console
                    const statusIcon = running ? '🟢' : '🔴';
                    console.log(`[${timestamp}] ${statusIcon} Events: ${eventsProcessed.toLocaleString()} | Uptime: ${uptime}s | Rate: ${eventsPerMinute.toFixed(1)}/min`);
                    
                    // Check for anomalies
                    this._checkAnomalies(eventsPerMinute, status);
                } else {
                    this._logError(timestamp, 'API error', data.error || {});
                    console.log(`[${timestamp}] ❌ API Error: ${data.error?.message || 'Unknown'}`);
                }
            } else {
                this._logError(timestamp, 'HTTP error', { status: response.status });
                console.log(`[${timestamp}] ❌ HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this._logError(timestamp, 'Connection error', { error: error.message });
            console.log(`[${timestamp}] ❌ Connection Error: ${error.message}`);
        }
    }
    
    _logError(timestamp, errorType, details) {
        // In a real implementation, you would write to a log file
        // For this example, we'll just log to console
        console.error(`[${timestamp}] ERROR: ${errorType} -`, details);
    }
    
    _checkAnomalies(eventsPerMinute, status) {
        const alerts = [];
        
        // High event rate
        if (eventsPerMinute > 1000) {
            alerts.push(`⚠️  High event rate: ${eventsPerMinute.toFixed(1)}/min`);
        }
        
        // Low event rate
        else if (eventsPerMinute < 1 && status === 'healthy') {
            alerts.push(`⚠️  Low event rate: ${eventsPerMinute.toFixed(1)}/min`);
        }
        
        // Log alerts
        alerts.forEach(alert => {
            const timestamp = new Date().toISOString();
            console.log(`   ${alert}`);
            // In a real implementation, you would also log to a file
        });
    }
}

// Usage
// const monitor = new EventBridgeMonitor();
// monitor.startMonitoring(30000); // Check every 30 seconds
```

### Health Dashboard Generator
```javascript
async function generateHealthDashboard(outputFile = 'health_dashboard.html') {
    const fs = require('fs').promises;
    
    const htmlTemplate = `
<!DOCTYPE html>
<html>
<head>
    <title>ELF EventBridge Health Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .status-card { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 15px 0; border-left: 4px solid #ddd; }
        .status-card.healthy { border-left-color: #28a745; }
        .status-card.degraded { border-left-color: #ffc107; }
        .status-card.unhealthy { border-left-color: #dc3545; }
        .status-icon { font-size: 24px; margin-right: 10px; }
        .metric { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .metric:last-child { border-bottom: none; }
        .refresh-info { text-align: center; color: #666; font-size: 14px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ELF EventBridge Health Dashboard</h1>
            <p>Generated at {timestamp}</p>
        </div>
        
        {status_section}
        
        {components_section}
        
        {metrics_section}
        
        <div class="refresh-info">
            <p>This dashboard auto-refreshes every 60 seconds</p>
        </div>
    </div>
    
    <script>
        setTimeout(function(){ location.reload(); }, 60000);
    </script>
</body>
</html>
`;
    
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    
    // Get status information
    let statusResponse, healthResponse;
    try {
        statusResponse = await makeEventBridgeRequest('GET', '/status');
        healthResponse = await makeEventBridgeRequest('GET', '/api/v1/health');
    } catch (error) {
        console.error('Failed to get status information:', error);
        return false;
    }
    
    // Build status section
    let statusSection = '';
    if (statusResponse.status === 'success') {
        const data = statusResponse.data;
        const running = data.running || false;
        const statusClass = running ? 'healthy' : 'unhealthy';
        const statusIcon = running ? '🟢' : '🔴';
        const statusText = running ? 'Running' : 'Stopped';
        
        statusSection = `
        <div class="status-card ${statusClass}">
            <h2><span class="status-icon">${statusIcon}</span>EventBridge Status</h2>
            <div class="metric"><span>Status:</span><strong>${statusText}</strong></div>
            <div class="metric"><span>Events Processed:</span><strong>${(data.events_processed || 0).toLocaleString()}</strong></div>
            <div class="metric"><span>Uptime:</span><strong>${data.uptime_seconds || 0} seconds</strong></div>
            <div class="metric"><span>Last Event:</span><strong>${data.last_event_time || 'Never'}</strong></div>
        </div>
        `;
    } else {
        statusSection = `
        <div class="status-card unhealthy">
            <h2><span class="status-icon">❌</span>EventBridge Status</h2>
            <p>Unable to retrieve status information</p>
        </div>
        `;
    }
    
    // Build components section
    const components = ['event_bridge', 'mission_bridge', 'sentinel_monitor'];
    let componentsHtml = '';
    
    for (const component of components) {
        try {
            const compResponse = await makeEventBridgeRequest('GET', `/api/v1/health/${component}`);
            if (compResponse.status === 'success') {
                const compData = compResponse.data;
                const compStatus = compData.status || 'unknown';
                const statusClasses = {
                    'healthy': 'healthy',
                    'degraded': 'degraded',
                    'unhealthy': 'unhealthy',
                    'unknown': ''
                };
                const statusIcons = {
                    'healthy': '🟢',
                    'degraded': '🟡',
                    'unhealthy': '🔴',
                    'unknown': '❓'
                };
                
                componentsHtml += `
                <div class="status-card ${statusClasses[compStatus] || ''}">
                    <h3><span class="status-icon">${statusIcons[compStatus] || '❓'}</span>${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                    <div class="metric"><span>Status:</span><strong>${compStatus.charAt(0).toUpperCase() + compStatus.slice(1)}</strong></div>
                </div>
                `;
            } else {
                componentsHtml += `
                <div class="status-card">
                    <h3><span class="status-icon">❌</span>${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                    <p>Unable to retrieve health information</p>
                </div>
                `;
            }
        } catch (error) {
            componentsHtml += `
            <div class="status-card">
                <h3><span class="status-icon">❌</span>${component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                <p>Error retrieving health information</p>
            </div>
            `;
        }
    }
    
    const componentsSection = `
    <h2>Component Health</h2>
    ${componentsHtml}
    `;
    
    // Build metrics section
    let metricsSection = '<h2>System Metrics</h2><p>Monitoring service not available</p>';
    try {
        const monitoringResponse = await fetch('http://localhost:9997/stats');
        if (monitoringResponse.ok) {
            const stats = await monitoringResponse.json();
            if (stats.status === 'success') {
                const statsData = stats.data;
                const learning = statsData.learning || {};
                const tools = statsData.tools || {};
                
                metricsSection = `
                <h2>System Metrics</h2>
                <div class="status-card">
                    <h3><span class="status-icon">📊</span>Learning Metrics</h3>
                    <div class="metric"><span>Heuristics:</span><strong>${(learning.heuristics || 0).toLocaleString()}</strong></div>
                    <div class="metric"><span>Golden Rules:</span><strong>${(learning.golden_rules || 0).toLocaleString()}</strong></div>
                    <div class="metric"><span>Trails:</span><strong>${(learning.trails || 0).toLocaleString()}</strong></div>
                    <div class="metric"><span>Pheromones:</span><strong>${(learning.pheromone_trails || 0).toLocaleString()}</strong></div>
                </div>
                <div class="status-card">
                    <h3><span class="status-icon">🔧</span>Tool Metrics</h3>
                    <div class="metric"><span>Tools Detected:</span><strong>${(tools.tools_detected || 0).toLocaleString()}</strong></div>
                </div>
                `;
            }
        }
    } catch (error) {
        // Monitoring service not available, use default message
    }
    
    // Generate complete HTML
    const htmlContent = htmlTemplate
        .replace('{timestamp}', timestamp)
        .replace('{status_section}', statusSection)
        .replace('{components_section}', componentsSection)
        .replace('{metrics_section}', metricsSection);
    
    // Write to file
    try {
        await fs.writeFile(outputFile, htmlContent);
        console.log(`✅ Health dashboard generated: ${outputFile}`);
        return true;
    } catch (error) {
        console.error('❌ Failed to generate dashboard:', error);
        return false;
    }
}

// Usage in Node.js environment
// generateHealthDashboard('eventbridge_dashboard.html');
```

## 📚 Related Examples

- [Orchestrator JavaScript Examples](orchestrator-client.md)
- [cURL EventBridge Examples](../../curl/eventbridge-examples.md)
- [Python EventBridge Examples](../../python/eventbridge-client.md)

## 📖 Further Reading

- [EventBridge API Documentation](../../endpoints/eventbridge/)
- [OpenAPI Specification](../../openapi/eventbridge.yaml)
- [Schema Definitions](../../schemas/)