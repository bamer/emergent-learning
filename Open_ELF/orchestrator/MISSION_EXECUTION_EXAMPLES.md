# Unified Orchestrator Mission Execution Examples

## Overview

The Unified Orchestrator can execute various types of missions through file-based requests, API calls, or direct commands. This document provides practical examples of mission execution patterns.

## Mission Request Format

All missions follow a standardized JSON format placed in the coordination directory:

```json
{
  "taskId": "unique-identifier",
  "role": "agent-type",
  "description": "Detailed mission description",
  "context": "Additional context information",
  "priority": "high|medium|low",
  "deadline": "ISO timestamp (optional)"
}
```

## Example 1: Research Mission

### Mission File Creation
```bash
# Create a research mission file
cat > /home/bamer/.opencode/emergent-learning/.coordination/missions/mission-research-001.json << EOF
{
  "taskId": "research-001",
  "role": "researcher",
  "description": "Analyze performance bottlenecks in the database query system and identify optimization opportunities",
  "context": "Recent monitoring shows 30% increase in query response times over the past week",
  "priority": "high"
}
EOF
```

### Expected Execution Flow
1. **Detection**: Orchestrator detects new mission file
2. **Assignment**: Mission assigned to researcher agent
3. **Analysis**: Researcher investigates database queries
4. **Reporting**: Findings documented with evidence
5. **Learning**: [LEARNED:database] Query optimization patterns identified

### Sample Output
```markdown
## Research Mission Complete: Database Performance Analysis

### Findings
- **Primary Bottleneck**: Unindexed JOIN operations in user lookup queries
- **Secondary Issue**: Excessive N+1 queries in session management
- **Root Cause**: Recent feature additions increased query complexity

### Evidence
- Slow query log analysis shows 45% of delays from 3 query patterns
- Execution plan reveals missing indexes on user.email column
- Profiling data confirms N+1 pattern in session loading

### Recommendations
1. Add composite index on (users.org_id, users.active)
2. Implement eager loading for session-user relationships
3. Cache frequent lookup results

[LEARNED:database-optimization] Composite indexes on frequently joined columns improve 70% query performance
```

## Example 2: Implementation Mission

### Mission File Creation
```bash
# Create an implementation mission file
cat > /home/bamer/.opencode/emergent-learning/.coordination/missions/mission-implement-002.json << EOF
{
  "taskId": "implement-002",
  "role": "coder",
  "description": "Implement the database optimization recommendations from research-001, including index creation and query refactoring",
  "context": "Follow the researcher's findings to improve query performance by at least 40%",
  "priority": "high"
}
EOF
```

### Expected Execution Flow
1. **Planning**: Break implementation into database and code changes
2. **Database Changes**: Create recommended indexes
3. **Code Refactoring**: Update query patterns to avoid N+1
4. **Testing**: Verify performance improvements
5. **Documentation**: Update relevant documentation

### Sample Output
```markdown
## Implementation Mission Complete: Database Optimization

### Changes Made
- **Indexes Added**: 
  - `CREATE INDEX idx_users_org_active ON users(org_id, active)`
  - `CREATE INDEX idx_sessions_user_id ON sessions(user_id)`
- **Code Refactored**:
  - Replaced N+1 user loading with single JOIN query
  - Added query result caching for frequent lookups
  - Updated session management to use bulk operations

### Performance Results
- **Before**: Average query time 850ms
- **After**: Average query time 220ms (74% improvement)
- **Peak Load**: Handled 5x previous throughput

### Validation
- All existing tests pass
- New performance tests added
- Load testing confirms stability under stress

[LEARNED:performance] Early indexing during design phase prevents 80% of optimization emergencies
```

## Example 3: System Health Mission

### Mission File Creation
```bash
# Create a system health mission file
cat > /home/bamer/.opencode/emergent-learning/.coordination/missions/mission-health-003.json << EOF
{
  "taskId": "health-003",
  "role": "sentinel",
  "description": "Conduct comprehensive system health check and generate detailed report",
  "context": "Monthly health assessment to ensure system stability and identify potential issues",
  "priority": "medium"
}
EOF
```

### Expected Execution Flow
1. **Infrastructure Check**: CPU, memory, disk usage
2. **Service Verification**: All services responding correctly
3. **Database Health**: Integrity checks and performance metrics
4. **Security Audit**: Vulnerability scanning and access review
5. **Report Generation**: Comprehensive health assessment

### Sample Output
```markdown
## Sentinel System Health Report
**Generated**: 2026-02-05T14:30:22Z
**Agent**: Sentinel via Unified Orchestrator
**Scope**: Full System Assessment

### Executive Summary
**Overall Status**: ✅ HEALTHY - All systems nominal

### Infrastructure Analysis

| Component | Status | Metrics | Trend |
|-----------|--------|---------|-------|
| CPU Usage | ✅ | 32% avg / 65% peak | → |
| Memory | ✅ | 4.2GB / 8GB | ↓ |
| Disk Space | ✅ | 156GB free / 256GB | ↔ |
| API Latency | ✅ | 45ms avg / 120ms peak | ↓ |
| Error Rate | ✅ | 0.1% | ↓ |

### Service Status
- **OpenCode Server**: ✅ Running (v1.2.4)
- **Database**: ✅ Healthy (Integrity check passed)
- **Dashboard**: ✅ Responsive (200 OK)
- **Watcher**: ✅ Active (Cycle every 30s)
- **Orchestrator**: ✅ Operational (Processing events normally)

### Security Assessment
- **Firewall**: ✅ Active with current rules
- **SSH Access**: ✅ Limited to authorized keys
- **Dependencies**: ✅ All up-to-date
- **Vulnerabilities**: ✅ 0 critical, 2 low (being addressed)

### Recommendations

#### Immediate Actions (🟢 LOW)
- Clean up old log files (>30 days) to free 2GB disk space
- Review and rotate developer SSH keys (3 unused keys found)

#### Preventive Measures
- Schedule monthly dependency security scans
- Implement automated backup verification procedures
- Add monitoring for anomalous login patterns

### Escalation Status
**No escalation required** - All systems operating within normal parameters

[LEARNED:health-monitoring] Regular comprehensive checks catch 95% of potential issues before impact
```

## Example 4: Automated Recovery Mission

### Event Triggered Mission
```bash
# This mission is automatically generated by the orchestrator when detecting issues
# No manual creation required - shown for documentation purposes

{
  "taskId": "recovery-auto-004",
  "role": "architect",
  "description": "Investigate and resolve database connection pool exhaustion that occurred at 14:23:15",
  "context": "Automatic escalation from Unified Orchestrator monitoring system. Service temporarily restored but root cause unknown.",
  "priority": "critical"
}
```

### Expected Execution Flow
1. **Incident Analysis**: Review logs and metrics from failure time
2. **Root Cause Identification**: Determine what caused pool exhaustion
3. **Solution Design**: Architect fix to prevent recurrence
4. **Implementation Planning**: Steps to deploy solution safely
5. **Post-Mortem**: Document lessons learned

### Sample Output
```markdown
## Architect Mission Complete: Database Connection Pool Exhaustion Resolution

### Incident Analysis
- **Time**: 14:23:15 UTC
- **Symptoms**: Service unavailable, 'Too many connections' errors
- **Duration**: 4 minutes downtime, 12 minutes degraded performance
- **Impact**: 2,347 requests failed, user complaints increased 340%

### Root Cause Investigation
- **Primary Cause**: Connection leak in user session management
- **Secondary Factor**: Insufficient pool size for peak load
- **Trigger Event**: Unexpected traffic spike from marketing campaign

#### Evidence Chain:
1. Connection count graph showed steady climb over 2 hours
2. Memory profiling revealed unclosed database connections in SessionManager
3. Code review confirmed missing connection close in error handling path
4. Load testing reproduced issue under simulated conditions

### Solution Architecture
- **Immediate Fix**: Patch SessionManager to ensure connection closure
- **Configuration**: Increase pool size from 50 to 100 connections
- **Monitoring**: Add connection pool usage alerts at 80% threshold
- **Resilience**: Implement connection timeout and retry logic

### Implementation Plan

#### Phase 1 - Hot Fix (Deploy within 2 hours)
1. Apply SessionManager patch
2. Restart services
3. Monitor connection metrics

#### Phase 2 - Configuration Update (Within 24 hours)
1. Increase pool size
2. Add monitoring alerts
3. Update deployment documentation

#### Phase 3 - Resilience Improvements (Within 1 week)
1. Implement circuit breaker pattern
2. Add request queuing for high load
3. Enhance logging for connection tracking

### Outcome
- **Fix Deployed**: 14:52 UTC (29 minutes from detection)
- **Performance**: Connection usage now peaks at 65%
- **Reliability**: Zero connection pool incidents in 48 hours
- **Monitoring**: Alerts configured and tested

### Lessons Learned

[LEARNED:resilience] Always close resources in finally blocks to prevent leaks  
[LEARNED:scaling] Connection pools should scale with expected peak load plus 50% buffer  
[LEARNED:monitoring] Proactive alerts at 80% utilization prevent 90% of exhaustion incidents

### Preventive Measures Added
- Code review checklist includes resource management verification
- Automated test for connection leak detection
- Monthly load testing with 2x expected peak scenarios
```

## Example 5: Creative Innovation Mission

### Mission File Creation
```bash
# Create an innovation mission file
cat > /home/bamer/.opencode/emergent-learning/.coordination/missions/mission-innovation-005.json << EOF
{
  "taskId": "innovation-005",
  "role": "creative",
  "description": "Explore alternative approaches to the current file monitoring system that could reduce resource consumption by 50%",
  "context": "Current watcher system uses 15% CPU during normal operation. Looking for more efficient solutions.",
  "priority": "medium"
}
EOF
```

### Expected Execution Flow
1. **Constraint Analysis**: Understand current system limitations
2. **Alternative Research**: Investigate different monitoring approaches
3. **Concept Development**: Design innovative solutions
4. **Feasibility Assessment**: Evaluate technical and operational viability
5. **Recommendation**: Present creative alternatives

### Sample Output
```markdown
## Creative Mission Complete: Innovative File Monitoring Approaches

### Challenge Definition
Current file monitoring system consumes 15% CPU during normal operation, limiting scalability and increasing costs. Goal is to reduce this by 50% while maintaining or improving monitoring effectiveness.

### Alternative Approaches Explored

#### 1. Event-Driven File System (inotify/fanotify)
**Concept**: Use kernel-level file system events instead of polling
**Benefits**: Near-zero CPU when idle, instant change detection
**Challenges**: Platform-specific implementation, complexity in distributed systems

#### 2. Hybrid Tiered Monitoring
**Concept**: Different monitoring frequencies based on file importance
**Benefits**: 70% reduction in checks for non-critical files
**Challenges**: Requires file classification system

#### 3. Blockchain-Inspired Immutable Logs
**Concept**: Treat file changes like blockchain transactions
**Benefits**: Tamper-proof audit trail, efficient change detection
**Challenges**: Storage overhead, complex implementation

#### 4. Machine Learning Pattern Prediction
**Concept**: Predict file change patterns to optimize monitoring schedule
**Benefits**: Adaptive monitoring reduces unnecessary checks by 60%
**Challenges**: Training data requirement, false negative risk

### Recommended Innovation: Adaptive Tiered Monitoring

#### Architecture
- **Tier 1 (Critical)**: <1s monitoring for config files, binaries
- **Tier 2 (Important)**: 10s monitoring for source code, data files
- **Tier 3 (Routine)**: 60s monitoring for logs, temp files
- **Tier 4 (Archive)**: 300s monitoring for backup, old files

#### Implementation
1. File classification algorithm based on extension, location, usage patterns
2. Dynamic tier adjustment based on recent change frequency
3. Intelligent batching to reduce system calls
4. Predictive scheduling using historical data

#### Expected Benefits
- **CPU Reduction**: From 15% to 6% (60% decrease)
- **Battery Life**: 25% improvement on mobile systems
- **Scalability**: Support 5x more files with same resources
- **Responsiveness**: Faster detection for critical changes

### Proof of Concept Results
- **Prototype**: Built simplified version monitoring 10,000 files
- **Results**: CPU usage dropped from 15% to 5.8% (61% reduction)
- **Detection Time**: <1s for critical files, <30s for others
- **Reliability**: 99.9% change detection accuracy maintained

### Implementation Roadmap

#### Phase 1: Prototype Enhancement (2 weeks)
- Add dynamic tier adjustment based on ML predictions
- Implement batching for system call optimization
- Build monitoring effectiveness dashboard

#### Phase 2: Production Integration (4 weeks)
- Gradual rollout starting with non-critical files
- Parallel running with current system for validation
- Performance monitoring and fine-tuning

#### Phase 3: Full Deployment (2 weeks)
- Complete migration to adaptive monitoring
- Decommission old polling system
- Document and train team on new approach

### Innovation Impact

[LEARNED:innovation] Constraint-based thinking often leads to breakthrough solutions  
[LEARNED:efficiency] Adaptive systems outperform static ones by 40-60% typically  
[LEARNED:simplicity] Sometimes the most elegant solution combines several simple ideas

#### Broader Applications
This adaptive tiered approach could be applied to:
- Database query optimization (frequent vs infrequent queries)
- API rate limiting (critical vs routine requests)
- Network monitoring (security vs performance checks)
```

## Best Practices for Mission Creation

### 1. Clear Objective Definition
```json
// Good - Specific and measurable
{
  "taskId": "performance-001",
  "role": "researcher",
  "description": "Reduce database query response time by 30% for user profile lookups",
  "priority": "high"
}

// Poor - Vague and unmeasurable
{
  "taskId": "improve-db",
  "role": "researcher", 
  "description": "Make database faster",
  "priority": "high"
}
```

### 2. Adequate Context Provision
Include enough information for the agent to succeed without clarification:

```json
{
  "taskId": "security-002",
  "role": "skeptic",
  "description": "Evaluate the security implications of the proposed OAuth2 implementation",
  "context": "New authentication system being developed in branch feature/oauth2. Specifically review token storage, refresh mechanisms, and third-party integration security. Reference RFC 6749 compliance requirements.",
  "priority": "critical"
}
```

### 3. Appropriate Priority Setting
Match urgency with impact:

- **Critical**: Production issues, security vulnerabilities, system downtime
- **High**: Performance degradations, important feature implementations
- **Medium**: Routine improvements, documentation updates, code refactoring  
- **Low**: Nice-to-have optimizations, experimental features

### 4. Learning Integration
Always include opportunities to extract insights:

```bash
# After mission completion, the orchestrator automatically adds:
[LEARNED:mission-type] Key insight from this execution
[LEARNED:efficiency] Process improvement discovered
```

These examples demonstrate the power and flexibility of the Unified Orchestrator's mission execution capabilities, showing how it can handle everything from routine tasks to complex problem-solving missions requiring multiple agent types and sophisticated analysis.