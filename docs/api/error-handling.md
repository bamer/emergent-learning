# Error Handling

## 📋 Error Response Format

All ELF APIs return consistent error responses with the following structure:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context or field-specific errors",
      "timestamp": "2026-02-12T10:30:15Z"
    }
  }
}
```

## 🚨 HTTP Status Codes

### 4xx Client Errors

| Code | Description | Meaning |
|------|-------------|---------|
| 400 | Bad Request | Invalid request format or missing required fields |
| 401 | Unauthorized | Authentication required or invalid credentials |
| 403 | Forbidden | Insufficient permissions to access resource |
| 404 | Not Found | Requested resource does not exist |
| 405 | Method Not Allowed | HTTP method not supported for this endpoint |
| 429 | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Description | Meaning |
|------|-------------|---------|
| 500 | Internal Server Error | Unexpected server error |
| 501 | Not Implemented | Feature not yet implemented |
| 502 | Bad Gateway | Invalid response from upstream service |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Upstream service timeout |

## 📦 Standard Error Codes

### General Errors
- `BAD_REQUEST` - Invalid request parameters
- `INVALID_INPUT` - Malformed or invalid input data
- `MISSING_REQUIRED_FIELD` - Required field not provided
- `RESOURCE_NOT_FOUND` - Requested resource does not exist
- `METHOD_NOT_ALLOWED` - HTTP method not supported

### Authentication Errors
- `UNAUTHORIZED` - Missing or invalid authentication
- `FORBIDDEN` - Insufficient permissions
- `TOKEN_EXPIRED` - Authentication token expired

### Business Logic Errors
- `VALIDATION_ERROR` - Data validation failed
- `CONFLICT` - Resource conflict (e.g., duplicate)
- `UNSUPPORTED_OPERATION` - Operation not supported

### System Errors
- `INTERNAL_ERROR` - Unexpected internal error
- `SERVICE_UNAVAILABLE` - Service temporarily offline
- `TIMEOUT` - Request timed out
- `DATABASE_ERROR` - Database operation failed

## 📝 Detailed Error Examples

### Missing Required Field
```json
{
  "status": "error",
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "Required field 'agent_type' is missing",
    "details": {
      "field": "agent_type",
      "location": "request_body"
    }
  }
}
```

### Invalid Input Format
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid JSON format in request body",
    "details": {
      "position": 45,
      "expected": "valid JSON object"
    }
  }
}
```

### Resource Not Found
```json
{
  "status": "error",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Mission with ID 'mission_12345' not found",
    "details": {
      "resource_type": "mission",
      "resource_id": "mission_12345"
    }
  }
}
```

### Service Unavailable
```json
{
  "status": "error",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "EventBridge service is currently unavailable",
    "details": {
      "service": "event_bridge",
      "retry_after": 30
    }
  }
}
```

## 🛠️ Client Implementation

### Python Example
```python
import requests

def handle_api_call(url, data):
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            error_data = response.json()
            print(f"Validation error: {error_data['error']['message']}")
        elif response.status_code == 404:
            print("Resource not found")
        elif response.status_code >= 500:
            print("Server error, please try again later")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        raise
```

### JavaScript Example
```javascript
async function handleApiCall(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`${errorData.error.code}: ${errorData.error.message}`);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError) {
            throw new Error('Network error');
        }
        throw error;
    }
}
```

## 🔄 Retry Logic

For transient errors, implement exponential backoff:

```python
import time
import random

def api_call_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data)
            if response.status_code < 500:
                return response.json()
            # For 5xx errors, retry with backoff
        except requests.exceptions.RequestException:
            pass
            
        if attempt < max_retries - 1:
            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
    
    raise Exception("Max retries exceeded")
```

## 📊 Error Monitoring

All errors are logged with structured data for monitoring:

```json
{
  "timestamp": "2026-02-12T10:30:15Z",
  "error_code": "DATABASE_ERROR",
  "message": "Failed to connect to database",
  "stack_trace": "...",
  "request_id": "req_12345",
  "user_id": "user_67890",
  "endpoint": "/api/v1/mission"
}
```

## 🛡️ Security Considerations

Error responses are sanitized to prevent information leakage:

- Database connection strings are redacted
- Stack traces are not exposed in production
- Internal system details are hidden
- Sensitive data is filtered from error messages

## 📚 Further Reading

- [Authentication](authentication.md)
- [Rate Limiting](rate-limiting.md)
- [API Changelog](changelog.md)