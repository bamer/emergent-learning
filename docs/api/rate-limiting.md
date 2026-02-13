# Rate Limiting

## 📏 Rate Limiting Policy

To ensure fair usage and system stability, ELF APIs implement rate limiting. These limits are designed to prevent abuse while allowing legitimate usage patterns.

## ⚡ Current Limits

### Per-IP Address Limits
- **General API Calls**: 1,000 requests per minute
- **Write Operations**: 100 requests per minute
- **Burst Allowance**: 200 requests (refills at 1,000/min)

### Per-User Limits (Future)
- **Authenticated Users**: Higher limits based on tier
- **Anonymous Users**: Default limits apply

## 📊 Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 60
X-RateLimit-Burst-Limit: 200
X-RateLimit-Burst-Remaining: 199
```

## ⚠️ Rate Limit Response

When rate limits are exceeded, the API returns a 429 status code:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 45
Content-Type: application/json

{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_in_seconds": 45
    }
  }
}
```

## 🔄 Rate Limit Categories

### Read Operations
- Status checks
- Health endpoints
- Data retrieval
- **Limit**: 1,000 requests/minute

### Write Operations
- Mission submissions
- Configuration changes
- Data modifications
- **Limit**: 100 requests/minute

### Administrative Operations
- System commands
- Service management
- Critical operations
- **Limit**: 10 requests/minute

## 🛠️ Client Implementation

### Python Example
```python
import time
import requests
from typing import Optional

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}{endpoint}"
        
        while True:
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Check for rate limit
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', '60'))
                    print(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"API request failed: {e}")

# Usage
client = ApiClient("http://localhost:9998")
status = client.make_request("GET", "/status")
```

### JavaScript Example
```javascript
class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.rateLimitResetTime = 0;
    }
    
    async makeRequest(method, endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        // Check if we're still in cooldown period
        const now = Date.now();
        if (now < this.rateLimitResetTime) {
            const waitTime = this.rateLimitResetTime - now;
            throw new Error(`Rate limit exceeded. Wait ${Math.ceil(waitTime/1000)} seconds.`);
        }
        
        try {
            const response = await fetch(url, {
                method,
                ...options
            });
            
            // Handle rate limiting
            if (response.status === 429) {
                const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
                this.rateLimitResetTime = now + (retryAfter * 1000);
                throw new Error(`Rate limit exceeded. Try again in ${retryAfter} seconds.`);
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            throw new Error(`API request failed: ${error.message}`);
        }
    }
}

// Usage
const client = new ApiClient('http://localhost:9998');
client.makeRequest('GET', '/status')
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

## 📈 Adaptive Rate Limiting

The system implements adaptive rate limiting based on:

1. **System Load**: Limits may decrease under high load
2. **Error Rates**: Excessive errors may trigger stricter limits
3. **Resource Usage**: High resource consumption may reduce limits

### Dynamic Adjustments
- Normal conditions: Standard limits
- High load: 50% reduction in limits
- Critical conditions: 80% reduction in limits

## 🧪 Testing Rate Limits

### Checking Current Usage
```bash
# Check rate limit status without consuming quota
curl -i http://localhost:9998/status
```

### Simulating Rate Limiting
```python
import requests
import time

def test_rate_limit():
    url = "http://localhost:9998/status"
    
    # Make rapid requests to hit rate limit
    for i in range(100):
        response = requests.get(url)
        print(f"Request {i+1}: {response.status_code}")
        
        if response.status_code == 429:
            print("Rate limit hit!")
            reset_time = response.headers.get('X-RateLimit-Reset', '60')
            print(f"Reset in {reset_time} seconds")
            break
        
        time.sleep(0.1)  # Small delay between requests
```

## 🚨 Abuse Prevention

### Detection Mechanisms
- Unusual request patterns
- Automated scraping attempts
- Brute force attacks
- Resource exhaustion attempts

### Response Actions
1. **Temporary Blocks**: 5-15 minute blocks for minor violations
2. **Extended Blocks**: 1-24 hour blocks for moderate violations
3. **Permanent Blocks**: For severe or repeated violations

### IP Whitelisting (Admin Only)
Authorized IPs can be whitelisted for higher limits:
```bash
# Admin-only endpoint (future feature)
curl -X POST http://localhost:9998/admin/ip-whitelist \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100", "limit_multiplier": 5}'
```

## 📊 Monitoring and Analytics

Rate limit data is collected for analysis:

```json
{
  "timestamp": "2026-02-12T10:30:15Z",
  "ip_address": "192.168.1.100",
  "endpoint": "/api/v1/mission",
  "requests_count": 150,
  "rate_limit_exceeded": true,
  "blocked_duration_seconds": 60,
  "user_agent": "CustomClient/1.0"
}
```

## 🛠️ Configuration (Admin)

Rate limits can be configured via environment variables:

```bash
# .env file
ELF_RATE_LIMIT_GENERAL=1000
ELF_RATE_LIMIT_WRITE=100
ELF_RATE_LIMIT_ADMIN=10
ELF_BURST_ALLOWANCE=200
```

## 📚 Further Reading

- [Authentication](authentication.md)
- [Error Handling](error-handling.md)
- [API Changelog](changelog.md)