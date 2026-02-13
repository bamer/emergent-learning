# Python Orchestrator Client Examples

Python examples for interacting with the ELF Orchestrator API using the requests library.

## 🚀 Quick Start

### Basic Setup
```python
import requests
import json
from typing import Dict, Any, Optional

# Base URL for the orchestrator
BASE_URL = "http://localhost:9998"

def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make a request to the orchestrator API."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {"status": "error", "error": {"message": str(e)}}
```

### Check Orchestrator Status
```python
def check_orchestrator_status():
    """Check the orchestrator status."""
    response = make_request("GET", "/status")
    
    if response["status"] == "success":
        data = response["data"]
        print(f"Orchestrator running: {data['running']}")
        print(f"Events processed: {data['events_processed']}")
        print(f"Uptime: {data['uptime_seconds']} seconds")
    else:
        print(f"Error: {response['error']['message']}")

# Usage
check_orchestrator_status()
```

### Submit a Mission
```python
def submit_mission(agent_type: str, mission: str, task_id: Optional[str] = None):
    """Submit a mission to the orchestrator."""
    payload = {
        "agent_type": agent_type,
        "mission": mission
    }
    
    if task_id:
        payload["task_id"] = task_id
    
    response = make_request("POST", "/api/v1/mission", payload)
    
    if response["status"] == "success":
        mission_id = response["data"]["mission_id"]
        print(f"Mission submitted successfully: {mission_id}")
        return mission_id
    else:
        print(f"Error submitting mission: {response['error']['message']}")
        return None

# Usage
mission_id = submit_mission(
    "researcher",
    "Research the latest developments in artificial intelligence"
)
```

## 📋 Detailed Examples

### Ask Orchestrator for Coordination
```python
def ask_orchestrator(component: str, request_type: str, data: Dict, priority: int = 1):
    """Ask the orchestrator for coordination or decisions."""
    payload = {
        "component": component,
        "request_type": request_type,
        "data": data,
        "priority": priority
    }
    
    response = make_request("POST", "/api/v1/ask", payload)
    
    if response["status"] == "success":
        print("Orchestrator response received:")
        print(json.dumps(response["data"], indent=2))
        return response["data"]
    else:
        print(f"Error: {response['error']['message']}")
        return None

# Usage
result = ask_orchestrator(
    component="dashboard",
    request_type="coordination",
    data={"action": "list_agents"},
    priority=5
)
```

### Get Mission Details
```python
def get_mission_details(mission_id: str):
    """Get details for a specific mission."""
    response = make_request("GET", f"/api/v1/mission/{mission_id}")
    
    if response["status"] == "success":
        mission_data = response["data"]
        print(f"Mission ID: {mission_data['mission_id']}")
        print(f"Agent Type: {mission_data['agent_type']}")
        print(f"Status: {mission_data['status']}")
        print(f"Progress: {mission_data.get('progress', 0)}%")
        return mission_data
    else:
        print(f"Error: {response['error']['message']}")
        return None

# Usage
mission_data = get_mission_details("mission_20260212_103015_12345")
```

### Update Mission Status
```python
def update_mission_status(mission_id: str, status: str, progress: Optional[float] = None):
    """Update the status of a mission."""
    payload = {"status": status}
    
    if progress is not None:
        payload["progress"] = progress
    
    response = make_request("POST", f"/api/v1/mission/{mission_id}/status", payload)
    
    if response["status"] == "success":
        print(f"Mission {mission_id} status updated to {status}")
        return response["data"]
    else:
        print(f"Error updating mission: {response['error']['message']}")
        return None

# Usage
update_mission_status("mission_20260212_103015_12345", "running", 25.0)
```

### List Active Missions
```python
def list_active_missions():
    """Get a list of active missions."""
    response = make_request("GET", "/api/v1/missions")
    
    if response["status"] == "success":
        missions = response["data"]["missions"]
        total = response["data"]["total"]
        active = response["data"]["active"]
        
        print(f"Total missions: {total}")
        print(f"Active missions: {active}")
        
        for mission in missions:
            print(f"- {mission['mission_id']}: {mission['mission']} ({mission['status']})")
        
        return missions
    else:
        print(f"Error: {response['error']['message']}")
        return []

# Usage
missions = list_active_missions()
```

### Check Component Health
```python
def check_component_health(component: str):
    """Check the health of a specific component."""
    response = make_request("GET", f"/api/v1/health/{component}")
    
    if response["status"] == "success":
        health_data = response["data"]
        print(f"{component} health: {health_data['status']}")
        if "details" in health_data:
            print(f"Details: {health_data['details']}")
        return health_data
    else:
        print(f"Error checking {component} health: {response['error']['message']}")
        return None

# Usage
health = check_component_health("event_bridge")
```

### List Available Agents
```python
def list_agents():
    """Get a list of available agents."""
    response = make_request("GET", "/api/v1/agents")
    
    if response["status"] == "success":
        agents = response["data"]["agents"]
        print("Available agents:")
        for agent in agents:
            print(f"- {agent['name']} ({agent['type']}): {agent['status']}")
        return agents
    else:
        print(f"Error: {response['error']['message']}")
        return []

# Usage
agents = list_agents()
```

### Run a Specific Agent
```python
def run_agent(agent_type: str, mission: str):
    """Run a specific agent with a mission."""
    payload = {"mission": mission}
    
    response = make_request("POST", f"/api/v1/agents/{agent_type}/run", payload)
    
    if response["status"] == "success":
        mission_id = response["data"]["mission_id"]
        print(f"Agent {agent_type} started mission: {mission_id}")
        return mission_id
    else:
        print(f"Error running agent: {response['error']['message']}")
        return None

# Usage
mission_id = run_agent("researcher", "Analyze market trends for renewable energy")
```

## ⚠️ Error Handling Examples

### Comprehensive Error Handling
```python
import time
from requests.exceptions import ConnectionError, Timeout, RequestException

def robust_api_call(method: str, endpoint: str, data: Optional[Dict] = None, 
                   retries: int = 3, timeout: int = 30):
    """Make a robust API call with error handling and retries."""
    url = f"{BASE_URL}{endpoint}"
    
    for attempt in range(retries):
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response: {e}")
                return {"status": "error", "error": {"message": "Invalid JSON response"}}
                
        except ConnectionError as e:
            print(f"Connection error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return {"status": "error", "error": {"message": "Connection failed"}}
                
        except Timeout as e:
            print(f"Timeout error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return {"status": "error", "error": {"message": "Request timeout"}}
                
        except RequestException as e:
            print(f"Request error: {e}")
            return {"status": "error", "error": {"message": str(e)}}
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"status": "error", "error": {"message": "Unexpected error"}}

# Usage
response = robust_api_call("GET", "/status")
```

### Handle Different Error Types
```python
def handle_api_errors(response: Dict):
    """Handle different types of API errors."""
    if response["status"] == "error":
        error_code = response["error"].get("code", "UNKNOWN")
        error_message = response["error"].get("message", "Unknown error")
        error_details = response["error"].get("details", {})
        
        if error_code == "RESOURCE_NOT_FOUND":
            print(f"Resource not found: {error_message}")
        elif error_code == "BAD_REQUEST":
            print(f"Invalid request: {error_message}")
        elif error_code == "INTERNAL_ERROR":
            print(f"Server error: {error_message}")
        elif error_code == "RATE_LIMIT_EXCEEDED":
            print(f"Rate limit exceeded: {error_message}")
            # Could implement retry logic here
        else:
            print(f"API error ({error_code}): {error_message}")
        
        if error_details:
            print(f"Details: {error_details}")
        
        return False
    return True

# Usage
response = make_request("GET", "/api/v1/mission/nonexistent")
if handle_api_errors(response):
    # Process successful response
    print("Success!")
```

## 🛠️ Advanced Examples

### Mission Monitoring Class
```python
import time
import threading
from typing import Callable

class MissionMonitor:
    """Monitor mission progress and notify on completion."""
    
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.monitoring = False
        self.thread = None
    
    def start_monitoring(self, callback: Callable[[Dict], None] = None):
        """Start monitoring mission progress."""
        if self.monitoring:
            print("Already monitoring")
            return
        
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, args=(callback,))
        self.thread.daemon = True
        self.thread.start()
        print(f"Started monitoring mission {self.mission_id}")
    
    def stop_monitoring(self):
        """Stop monitoring mission progress."""
        self.monitoring = False
        if self.thread:
            self.thread.join()
        print(f"Stopped monitoring mission {self.mission_id}")
    
    def _monitor_loop(self, callback: Callable[[Dict], None] = None):
        """Internal monitoring loop."""
        while self.monitoring:
            try:
                response = make_request("GET", f"/api/v1/mission/{self.mission_id}")
                
                if response["status"] == "success":
                    mission_data = response["data"]
                    status = mission_data["status"]
                    
                    if callback:
                        callback(mission_data)
                    else:
                        print(f"Mission {self.mission_id}: {status} "
                              f"({mission_data.get('progress', 0)}%)")
                    
                    # Stop monitoring if mission is complete
                    if status in ["completed", "failed", "cancelled"]:
                        self.monitoring = False
                        print(f"Mission {self.mission_id} finished with status: {status}")
                else:
                    print(f"Error monitoring mission: {response['error']['message']}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)

# Usage
monitor = MissionMonitor("mission_20260212_103015_12345")

def mission_callback(mission_data):
    print(f"Mission update: {mission_data['status']} - {mission_data.get('progress', 0)}%")

monitor.start_monitoring(mission_callback)

# Let it run for a while, then stop
time.sleep(120)
monitor.stop_monitoring()
```

### Batch Mission Processor
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

class BatchMissionProcessor:
    """Process multiple missions concurrently."""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.results = queue.Queue()
    
    def submit_missions(self, missions: list) -> Dict[str, str]:
        """Submit multiple missions and return their IDs."""
        mission_ids = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all missions
            future_to_mission = {
                executor.submit(self._submit_single_mission, mission): mission 
                for mission in missions
            }
            
            # Collect results
            for future in as_completed(future_to_mission):
                mission_desc = future_to_mission[future]
                try:
                    mission_id = future.result()
                    if mission_id:
                        mission_ids[mission_desc] = mission_id
                except Exception as e:
                    print(f"Mission submission failed for '{mission_desc}': {e}")
                    mission_ids[mission_desc] = None
        
        return mission_ids
    
    def _submit_single_mission(self, mission_data: Dict) -> Optional[str]:
        """Submit a single mission."""
        response = make_request("POST", "/api/v1/mission", mission_data)
        
        if response["status"] == "success":
            return response["data"]["mission_id"]
        else:
            print(f"Failed to submit mission '{mission_data['mission']}': "
                  f"{response['error']['message']}")
            return None

# Usage
processor = BatchMissionProcessor(max_workers=3)

missions = [
    {
        "agent_type": "researcher",
        "mission": "Research AI ethics"
    },
    {
        "agent_type": "writer",
        "mission": "Write technical documentation"
    },
    {
        "agent_type": "analyst",
        "mission": "Analyze performance metrics"
    }
]

mission_ids = processor.submit_missions(missions)
print("Submitted missions:")
for desc, mission_id in mission_ids.items():
    if mission_id:
        print(f"  {desc} -> {mission_id}")
    else:
        print(f"  {desc} -> FAILED")
```

### Health Check with Alerting
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class HealthChecker:
    """Check system health and send alerts."""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 email_user: str = None, email_password: str = None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password
    
    def check_all_components(self) -> Dict[str, str]:
        """Check health of all components."""
        components = ["event_bridge", "orchestrator", "dashboard", 
                     "learning_processor"]
        health_status = {}
        
        for component in components:
            response = make_request("GET", f"/api/v1/health/{component}")
            
            if response["status"] == "success":
                health_status[component] = response["data"]["status"]
            else:
                health_status[component] = "error"
        
        return health_status
    
    def send_alert(self, subject: str, message: str, recipient: str):
        """Send an email alert."""
        if not all([self.smtp_server, self.email_user, self.email_password]):
            print("Email configuration incomplete - printing alert instead:")
            print(f"Subject: {subject}")
            print(f"Message: {message}")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Alert sent to {recipient}")
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    def run_health_check(self, alert_recipient: str = None):
        """Run a comprehensive health check."""
        print("Running system health check...")
        
        health_status = self.check_all_components()
        unhealthy_components = [
            comp for comp, status in health_status.items() 
            if status != "healthy"
        ]
        
        print("Component Health:")
        for component, status in health_status.items():
            status_icon = {
                "healthy": "🟢",
                "degraded": "🟡",
                "unhealthy": "🔴",
                "error": "❌"
            }.get(status, "❓")
            print(f"  {status_icon} {component}: {status}")
        
        if unhealthy_components:
            alert_msg = (f"ALERT: Unhealthy components detected: "
                        f"{', '.join(unhealthy_components)}")
            print(f"\n{alert_msg}")
            
            if alert_recipient:
                self.send_alert(
                    "ELF System Health Alert",
                    alert_msg,
                    alert_recipient
                )
        else:
            print("\n✅ All components are healthy")

# Usage
checker = HealthChecker()
checker.run_health_check("admin@example.com")
```

## 📚 Related Examples

- [EventBridge Python Examples](eventbridge-client.md)
- [cURL Orchestrator Examples](../../curl/orchestrator-examples.md)
- [JavaScript Orchestrator Examples](../../javascript/orchestrator-client.md)

## 📖 Further Reading

- [Orchestrator API Documentation](../../endpoints/orchestrator/)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/)