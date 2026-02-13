# API Schema Documentation

This directory contains detailed documentation for all data schemas used in the ELF API system.

## 📋 Schema Categories

### [Common Objects](common-objects.md)
Reusable data structures used across multiple endpoints:
- Status responses
- Error objects
- Health check results
- Timestamp formats

### [Request Schemas](requests.md)
Data structures for API request bodies:
- Orchestrator requests
- Mission submissions
- Agent execution requests
- Status update requests

### [Response Schemas](responses.md)
Data structures for API response bodies:
- Success responses
- Error responses
- Health check responses
- Mission status responses

### [Enumeration Types](enums.md)
Defined enumeration values used throughout the API:
- Status values
- Priority levels
- Component types
- Event types

## 📐 Schema Format

All schemas are documented using JSON Schema notation and follow these conventions:

### Field Documentation
Each field includes:
- **Name**: Field identifier
- **Type**: Data type (string, integer, boolean, object, array)
- **Required**: Whether the field is mandatory
- **Description**: Purpose and usage of the field
- **Constraints**: Validation rules, if applicable
- **Example**: Sample value

### Example Schema Documentation
```json
{
  "mission_id": {
    "type": "string",
    "description": "Unique identifier for the mission",
    "format": "mission-id",
    "example": "mission_20260212_103015_12345"
  }
}
```

## 📚 Related Documentation

- [OpenAPI Specifications](../openapi/)
- [Endpoint Documentation](../endpoints/)
- [Code Examples](../examples/)

## 📖 Schema Evolution

Schema changes follow semantic versioning:
- **Major versions**: Breaking changes to existing fields
- **Minor versions**: New optional fields or enum values
- **Patch versions**: Non-breaking clarifications or corrections

See [API Changelog](../changelog.md) for detailed schema evolution history.