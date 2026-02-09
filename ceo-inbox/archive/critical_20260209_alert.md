# Critical Alert: Monitoring System Issue

**Timestamp**: 2026-02-09T01:41:01Z
**Status**: Critical
**Issue**: HTTPConnectionPool(host='localhost', port=3001): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x75abc37a2e10>: Failed to establish a new connection: [Errno 111] Connection refused'))**
**Affected Component**: EventBridge (expected on port 3001)
**Root Cause**: The service expected on port 3001 is not responding; connection refused indicates no process is listening or the service failed to start.
**Immediate Actions**:
1. Verify EventBridge process status
2. Attempt to restart EventBridge
3. Check logs for detailed error messages
**Escalation**: Created in ceo-inbox/ for CEO review