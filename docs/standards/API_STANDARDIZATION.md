"""
API Standardization Requirements - ELF Ecosystem
================================================
This document defines the REST API standards that all services must follow
for consistency, maintainability, and interoperability.

Standard Version: 1.0
Last Updated: 2026-02-18
"""

# ==============================================================================
# 1. URL PATH STRUCTURE
# ==============================================================================

"""
All API endpoints MUST follow this naming convention:

/api/v{version}/{resource}/{action}

Examples:
✅ GET    /api/v1/sessions
✅ GET    /api/v1/sessions/{id}
✅ POST   /api/v1/sessions
✅ PUT    /api/v1/sessions/{id}
✅ DELETE /api/v1/sessions/{id}
✅ POST   /api/v1/sessions/{id}/archive
✅ GET    /api/v1/heuristics?domain=frontend&limit=10

❌ GET    /getSessions              (Use kebab-case)
❌ GET    /v2/sessions              (Use /api/v2/)
❌ GET    /api/heuristics           (Include version)
"""

# ==============================================================================
# 2. HTTP METHODS & SEMANTICS
# ==============================================================================

"""
GET    - Retrieve resources (safe, idempotent)
POST   - Create resources
PUT    - Update/replace entire resource
PATCH  - Partial updates
DELETE - Remove resources

HEAD   - Get headers only (rarely used)
OPTIONS - Get allowed methods (handled by CORS)

Status Code Standardization:
┌─────────┬─────────────────────────────────────┐
│ Code    │ Use Case                            │
├─────────┼─────────────────────────────────────┤
│ 200     │ OK                                  │
│ 201     │ Created                             │
│ 204     │ No Content (successful, no body)    │
│ 400     │ Bad Request (validation error)      │
│ 401     │ Unauthorized                        │
│ 403     │ Forbidden                           │
│ 404     │ Not Found                           │
│ 409     │ Conflict (duplicate/invalid state)  │
│ 422     │ Unprocessable Entity                │
│ 429     │ Rate Limited                        │
│ 500     │ Internal Server Error               │
│ 503     │ Service Unavailable                 │
└─────────┴─────────────────────────────────────┘
"""

# ==============================================================================
# 3. REQUEST BODY STRUCTURE
# ==============================================================================

"""
Standard Request Body Format:
{
    "data": { ... },           // Primary payload
    "meta": { ... },          // Optional metadata
    "timestamp": "ISO-8601"   // Optional client timestamp
}

Example:
{
    "data": {
        "title": "Use refs for useEffect callbacks",
        "domain": "react",
        "confidence": 0.9
    },
    "meta": {
        "source": "user",
        "client_version": "1.0.0"
    }
}
"""

# ==============================================================================
# 4. RESPONSE BODY STRUCTURE
# ==============================================================================

"""
SUCCESS Response Format:
{
    "success": true,
    "data": { ... },           // Response payload
    "meta": {
        "timestamp": "ISO-8601",
        "request_id": "uuid",
        "version": "1.0"
    }
}

ERROR Response Format:
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Title is required",
        "details": { ... },           // Optional: additional error info
        "request_id": "uuid"
    },
    "meta": {
        "timestamp": "ISO-8601",
        "version": "1.0"
    }
}

Example Error Response:
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "validation failed",
        "details": {
            "title": ["This field is required."],
            "confidence": ["Must be between 0 and 1"]
        },
        "request_id": "123e4567-e89b-12d3-a456-426614174000"
    },
    "meta": {
        "timestamp": "2026-02-18T12:00:00Z",
        "version": "1.0"
    }
}
"""

# ==============================================================================
# 5. PAGINATION
# ==============================================================================

"""
Query Parameters for Pagination:
?limit=10&offset=0

Response Format:
{
    "success": true,
    "data": [ ...items... ],
    "meta": {
        "pagination": {
            "limit": 10,
            "offset": 0,
            "total": 50,
            "has_more": true
        },
        "timestamp": "ISO-8601"
    }
}

Cursor-based Pagination (preferred for large datasets):
?cursor=abc123&limit=10

Response Format:
{
    "success": true,
    "data": [ ...items... ],
    "meta": {
        "pagination": {
            "limit": 10,
            "cursor": "xyz789",
            "has_more": true
        },
        "timestamp": "ISO-8601"
    }
}
"""

# ==============================================================================
# 6. FILTERING & SORTING
# ==============================================================================

"""
Filtering:
?field=value&field2=value2

Example:
?domain=frontend&is_golden=true&confidence_min=0.8

Sorting:
?sort=-created_at   // Descending (most recent first)
?sort=domain       // Ascending (A-Z)
?sort=created_at,-updated_at  // Multiple sorts

Combined:
?domain=react&sort=-created_at&limit=10
"""

# ==============================================================================
# 7. ERROR CODE STANDARDIZATION
# ==============================================================================

ERROR_CODES = {
    # Validation (4xx)
    "VALIDATION_ERROR": "Request validation failed",
    "MISSING_REQUIRED_FIELD": "Required field is missing",
    "INVALID_TYPE": "Invalid data type",
    "INVALID_RANGE": "Value out of valid range",

    # Authentication & Authorization (401/403)
    "UNAUTHORIZED": "Authentication required",
    "FORBIDDEN": "Insufficient permissions",
    "INVALID_TOKEN": "Invalid or expired token",

    # Not Found (404)
    "NOT_FOUND": "Resource not found",
    "RESOURCE_NOT_FOUND": "Requested resource does not exist",

    # Conflict (409)
    "DUPLICATE_ENTRY": "Resource already exists",
    "STATE_CONFLICT": "Invalid state transition",

    # Rate Limiting (429)
    "RATE_LIMIT_EXCEEDED": "Too many requests",

    # Server Errors (5xx)
    "INTERNAL_ERROR": "Internal server error",
    "DATABASE_ERROR": "Database operation failed",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "TIMEOUT": "Request timeout",
}

# ==============================================================================
# 8. TIMESTAMP FORMATS
# ==============================================================================

"""
All timestamps MUST use ISO-8601 format:
"2026-02-18T12:00:00Z"
"2026-02-18T12:00:00.123Z"
"2026-02-18T12:00:00-08:00"  // With timezone

All timezone-sensitive operations MUST use UTC internally.
"""

# ==============================================================================
# 9. ID FORMATS
# ==============================================================================

"""
Resource IDs MUST be UUID v4 format:
"123e4567-e89b-12d3-a456-426614174000"

For backward compatibility with SQLite auto-increment IDs:
- Accept integer IDs in requests
- Convert to UUID internally
- Standardize on UUID for new resources
"""

# ==============================================================================
# 10. SECURITY REQUIREMENTS
# ==============================================================================

"""
INPUT VALIDATION:
✅ All inputs sanitized and validated
✅ SQL injection protection (parameterized queries)
✅ XSS prevention (content escaping)

HEADERS:
✅ X-Frame-Options: DENY
✅ X-Content-Type-Options: nosniff
✅ X-XSS-Protection: 1; mode=block
✅ Referrer-Policy: strict-origin-when-cross-origin
✅ Permissions-Policy: geolocation=(), microphone=(), camera=()

CORS:
✅ Restrict to allowed origins only
✅ Validate credentials
✅ Limit allowed methods

REQUEST SIZE:
✅ Max upload size: 10MB
✅ Rate limiting: 100 requests/min per IP

RESPONSES:
✅ No sensitive data in error messages
✅ No stack traces in production
✅ Server version hidden
"""

# ==============================================================================
# 11. API VERSIONING STRATEGY
# ==============================================================================

"""
URL Versioning (Preferred):
/api/v1/resource
/api/v2/resource  <-- Breaking changes

Header Versioning (Alternative):
X-API-Version: 1

Breaking Changes Include:
- Removing fields
- Renaming fields
- Changing field types
- Changing required fields
- Changing error codes
- Removing endpoints

Non-Breaking Changes Include:
- Adding optional fields
- Adding new endpoints
- Adding new query parameters
- Adding new values to enums
"""

# ==============================================================================
# 12. DOCUMENTATION REQUIREMENTS
# ==============================================================================

"""
ALL endpoints MUST have:
✅ Clear description
✅ Request body schema (with examples)
✅ Response body schema (with examples)
✅ Error response schema
✅ Authentication requirements
✅ Rate limits (if any)

Use FastAPI automatic docs:
- /docs (Swagger UI)
- /redoc (ReDoc)
"""

# ==============================================================================
# 13. IMPLEMENTATION CHECKLIST
# ==============================================================================

"""
For each new endpoint:
☑ Follow URL path structure (/api/v1/{resource})
☑ Use correct HTTP method (GET/POST/PUT/DELETE)
☑ Return standard response format
☑ Include proper error handling
☑ Use ISO-8601 timestamps
☑ UUID v4 for resource IDs
☑ Add security headers
☑ Document in OpenAPI/Swagger
☑ Add validation for all inputs
☑ Use parameterized queries
☑ Implement rate limiting
☑ Log all requests/ responses
☑ Handle CORS properly
"""