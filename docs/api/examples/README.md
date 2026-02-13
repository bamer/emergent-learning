# API Code Examples

This directory contains code examples for integrating with the ELF API system in various programming languages.

## 📋 Example Categories

### [cURL Examples](curl/)
Command-line examples using cURL for quick testing and automation:
- Basic API calls
- Authentication examples
- Error handling demonstrations

### [Python Examples](python/)
Python client library examples:
- Using the requests library
- Asyncio examples
- Error handling patterns
- Authentication workflows

### [JavaScript Examples](javascript/)
JavaScript/Node.js client examples:
- Using fetch API
- Axios library examples
- Async/await patterns
- Browser and Node.js compatibility

## 🚀 Quick Start Examples

### cURL
```bash
# Check EventBridge status
curl http://localhost:9998/status

# Submit a mission
curl -X POST http://localhost:9998/api/v1/mission \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "mission": "Research AI developments"
  }'
```

### Python
```python
import requests

# Check EventBridge status
response = requests.get("http://localhost:9998/status")
print(response.json())

# Submit a mission
mission_data = {
    "agent_type": "researcher",
    "mission": "Research AI developments"
}
response = requests.post(
    "http://localhost:9998/api/v1/mission",
    json=mission_data
)
print(response.json())
```

### JavaScript
```javascript
// Check EventBridge status
fetch('http://localhost:9998/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Submit a mission
const missionData = {
  agent_type: "researcher",
  mission: "Research AI developments"
};

fetch('http://localhost:9998/api/v1/mission', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(missionData)
})
.then(response => response.json())
.then(data => console.log(data));
```

## 📁 Directory Structure

```
examples/
├── README.md              # This file
├── curl/                  # cURL examples
│   ├── orchestrator-examples.md
│   └── eventbridge-examples.md
├── python/                # Python examples
│   ├── orchestrator-client.md
│   └── eventbridge-client.md
└── javascript/            # JavaScript examples
    ├── orchestrator-client.md
    └── eventbridge-client.md
```

## 🛠️ Example Conventions

All examples follow these conventions:

### Error Handling
Examples demonstrate proper error handling patterns:
- HTTP status code checking
- JSON parsing error handling
- Network timeout handling
- Retry logic for transient errors

### Authentication
Examples show authentication patterns:
- API key usage
- OAuth 2.0 integration
- Session management

### Best Practices
Examples follow language-specific best practices:
- Proper resource cleanup
- Connection pooling
- Asynchronous operation patterns
- Memory management

## 📚 Related Documentation

- [API Overview](../overview.md)
- [Endpoint Documentation](../endpoints/)
- [Schema Documentation](../schemas/)

## 📖 Language Support

Currently supported languages:
- **cURL** - Command-line HTTP client
- **Python** - Popular scripting language
- **JavaScript** - Web and Node.js environments

Planned language support:
- **Java** - Enterprise applications
- **Go** - High-performance services
- **C#** - Microsoft ecosystem