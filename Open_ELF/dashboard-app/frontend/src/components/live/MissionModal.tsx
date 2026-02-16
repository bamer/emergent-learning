import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X, Zap, Play, RefreshCw, Cpu, Activity, Code, Search, Lightbulb, FileCode, Sparkles, Wand2, XCircle, Bug, Database, Shield, Rocket, GitBranch, Puzzle, ShieldCheck, Layout, Monitor, Smartphone, Globe, Server, Terminal, Coffee, Target, Map, Layers, Box, Users, MessageSquare, Clock, TrendingUp, Heart, Wrench, Hammer, Zap as Lightning, Rocket as Launch } from 'lucide-react';
import { useNotificationContext } from '../../context/NotificationContext';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  provider_id: string;
  is_default?: boolean;
}

interface PromptCategory {
  category: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  prompts: {
    label: string;
    text: string;
  }[];
}

interface MissionResult {
  mode: string;
  agent_type?: string;
  heuristics_count: number;
  execution_time_ms: number;
  response_preview?: string;
}

interface MissionStatus {
  mission_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  session_id?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

interface AsyncMissionResult {
  mission_id: string;
  status: string;
  result?: string;
  error?: string;
  heuristics?: any[];
  duration_seconds?: number;
  completed_at?: string;
}

interface MissionModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  selectedAgentName?: string | null;
}

const PROMPT_CATEGORIES: PromptCategory[] = [
  {
    category: 'Development',
    icon: Code,
    description: 'Code creation, refactoring, and implementation',
    prompts: [
      { label: 'Write Clean Code', text: 'Write production-ready code with clean, readable, and maintainable structures. Include comprehensive error handling, type hints, inline comments, and follow SOLID principles. Structure your code with single-responsibility functions and meaningful variable names.' },
      { label: 'Refactor Legacy API', text: 'Refactor this legacy API endpoint to modern REST standards. Implement proper HTTP status codes, request validation, error handling, pagination, rate limiting, and comprehensive API documentation. Ensure backward compatibility during migration.' },
      { label: 'Add Data Validation', text: 'Implement robust input validation using Pydantic/Vitest/zod based on your stack. Validate all inputs, sanitize outputs, handle edge cases, and provide clear error messages. Ensure data integrity and prevent injection attacks.' },
      { label: 'Optimize Algorithm', text: 'Analyze this algorithm\'s time and space complexity. Identify bottlenecks, propose optimizations, implement caching strategies, and reduce unnecessary computations. Benchmark before and after improvements with measurable gains.' },
      { label: 'Implement Caching Layer', text: 'Design and implement a multi-level caching strategy (in-memory, distributed, CDN). Configure cache invalidations, TTL policies, and cache warming. Monitor cache hit rates and optimize for performance.' },
      { label: 'Add Error Monitoring', text: 'Integrate comprehensive error tracking and monitoring. Set up alerts for critical errors, log structured error data, implement error boundaries, and create dashboards for tracking error rates and trends over time.' },
      { label: 'Code Security Audit', text: 'Perform a thorough security audit of this code. Check for SQL injection, XSS, CSRF, authentication bypasses, exposed secrets, insecure dependencies, OWASP Top 10 vulnerabilities, and data exposure. Provide remediation steps.' },
      { label: 'Implement Logging Framework', text: 'Set up structured logging with appropriate log levels (DEBUG, INFO, WARN, ERROR, CRITICAL). Include context metadata, correlation IDs, request tracing, structured formats (JSON), log rotation, and centralized log aggregation.' },
      { label: 'Add Unit Tests', text: 'Write comprehensive unit tests covering happy paths, edge cases, error scenarios, boundary conditions, and integration points. Use testing frameworks with mocking, fixtures, parameterized tests, and aim for >90% code coverage.' },
      { label: 'Create Integration Tests', text: 'Design and implement end-to-end integration tests. Set up test databases, mock external services, test API contracts, verify data flows across services, and ensure system compatibility after deployments.' },
      { label: 'Database Migration Script', text: 'Create a safe, reversible database migration script. Include schema changes, data transformations, rollback procedures, performance considerations, and validation steps. Test on staging before production deployment.' },
      { label: 'Implement Rate Limiting', text: 'Design and implement rate limiting strategies (token bucket, sliding window, fixed window). Configure per-user, per-IP, and global limits. Handle rate limit exceeded responses with proper HTTP headers and countdown timers.' },
      { label: 'Add Feature Flag System', text: 'Implement a feature flag/launch management system. Allow dynamic enable/disable of features, percentage rollouts, A/B testing support, user targeting, and phased deployments without code changes.' },
      { label: 'Create WebSocket Handler', text: 'Build a WebSocket server for real-time bidirectional communication. Handle connection lifecycle, authentication, message routing, heartbeat/ping-pong, reconnection logic, and graceful degradation to polling.' },
      { label: 'Implement File Upload System', text: 'Create a secure file upload and processing system. Handle validation (size, type, virus scan), multipart streaming uploads, resumable uploads, file storage (local, S3), thumbnail generation, and cleanup of orphaned files.' },
      { label: 'Add API Versioning', text: 'Implement API versioning strategy (URL-based, header-based). Maintain backward compatibility, document version differences, sunset old versions gracefully, and provide clear migration guides for API consumers.' },
      { label: 'Create Background Job Queue', text: 'Set up a background job processing system (Celery, Bull, Sidekiq). Implement job queues, worker pools, job retries, dead letter queues, priority scheduling, and job monitoring dashboards.' },
      { label: 'Add Internationalization (i18n)', text: 'Implement comprehensive internationalization support. Handle timezone conversions, date/time formatting, number/currency localization, RTL layouts, message extraction/translation, and language switching without page reloads.' },
      { label: 'Create API Documentation', text: 'Generate comprehensive API documentation using OpenAPI/Swagger. Include all endpoints, request/response schemas, authentication details, error responses, example requests, and interactive testing capabilities.' },
      { label: 'Implement Health Check System', text: 'Create detailed health check endpoints. Check database connectivity, external service health, disk/memory/CPU usage, service dependencies, and provide overall health status with degraded/healthy states.' },
      { label: 'Add Request ID Tracing', text: 'Implement distributed tracing with unique request IDs. Trace requests across service boundaries, include timing information, link to logs, and visualize trace flows for performance analysis and debugging.' },
    ]
  },
  {
    category: 'Debug & Troubleshoot',
    icon: Bug,
    description: 'Investigate issues and fix bugs',
    prompts: [
      { label: 'Diagnose Production Bug', text: 'Systematically diagnose this production bug. Analyze error logs, reproduce locally, identify root cause of failure, isolate the problematic component, and propose a safe fix with rollback plan.' },
      { label: 'Memory Leak Investigation', text: 'Investigate this memory leak thoroughly. Use memory profiling tools, analyze object retention, identify circular references, check event listener cleanup, timer/interval handling, and provide patch with leak-free code.' },
      { label: 'Performance Bottleneck', text: 'Identify and resolve performance bottlenecks. Profile CPU usage, memory allocation, I/O operations, network calls, database queries. Optimize hot paths, implement caching, lazy loading, and batch operations.' },
      { label: 'Race Condition Debug', text: 'Debug this race condition issue. Analyze concurrent execution flows, identify shared state mutations, add proper synchronization (locks, semaphores), implement atomic operations, and verify thread safety.' },
      { label: 'Investigate Crash', text: 'Thoroughly investigate this system crash. Analyze stack traces, core dumps, system logs. Identify crash-inducing inputs, error conditions, memory corruption, null dereferences, and implement defensive programming.' },
      { label: 'Fix Race Conditions', text: 'Identify and resolve all race conditions in this concurrent code. Use proper synchronization primitives (mutexes, condition variables), avoid shared mutable state, design race-free algorithms, and implement thread-safe data structures.' },
      { label: 'Debug Async Issue', text: 'Debug this asynchronous code issue. Trace promise chains, callback hell, race conditions, error propagation, unhandled promise rejections. Ensure proper async/await usage, error handling, and resource cleanup.' },
      { label: 'Investigate Timeout', text: 'Investigate and resolve timeout issues. Identify slow operations causing timeouts, optimize database queries, reduce network latency, implement request timeouts with retries, and add timeout monitoring and alerting.' },
      { label: 'Fix Authentication Bug', text: 'Debug and fix this authentication issue. Verify token generation/validation, session handling, password hashing, OAuth flows, multi-factor authentication, and ensure proper security best practices are followed.' },
      { label: 'Database Lock Investigation', text: 'Investigate database locking issues. Identify deadlocks, lock contention, lock timeouts, long-running transactions holding locks. Optimize queries, reduce transaction scope, add proper indexing, and implement retry logic.' },
      { label: 'Fix Security Vulnerability', text: 'Identify and patch this security vulnerability. Analyze attack vectors, fix injection points, sanitize user inputs, validate data types, implement proper authentication/authorization, and add security tests.' },
      { label: 'Debug Third-Party Integration', text: 'Debug issues with this third-party integration. Verify API key/configuration validity, check rate limits/handling, validate request/response formats, implement robust error handling, fallbacks, and retry logic.' },
      { label: 'Investigate High CPU Usage', text: 'Investigate abnormally high CPU usage. Profile the application, identify CPU-intensive code paths, optimize algorithms, reduce unnecessary computations, implement caching, and add CPU monitoring alerts.' },
      { label: 'Fix Data Consistency Issue', text: 'Debug and fix this data consistency problem. Identify race conditions, write conflicts, transaction isolation issues, caching inconsistencies. Implement proper transaction management, locking strategies, and data validation.' },
      { label: 'Debug Network Connectivity', text: 'Troubleshoot network connectivity issues. Check firewall rules, DNS resolution, proxy configuration, SSL certificates, connection pooling, timeouts, retries, and implement circuit breaker patterns.' },
      { label: 'Investigate Memory Corruption', text: 'Debug memory corruption issues. Use memory analysis tools, identify buffer overflows, use-after-free, dangling pointers. Fix allocation/deallocation, implement bounds checking, and add memory sanitizers.' },
      { label: 'Fix Configuration Error', text: 'Debug and fix this configuration error. Verify configuration file formats, environment variable loading, default values, type conversions, validation rules. Implement configuration schema validation and error messages.' },
      { label: 'Investigate Resource Exhaustion', text: 'Investigate resource exhaustion issues (file descriptors, memory, connections). Identify resource leaks, implement proper cleanup, increase system limits where needed, add resource monitoring, and implement graceful degradation.' },
      { label: 'Debug Concurrency Bug', text: 'Debug this concurrency bug. Analyze thread interactions, shared state access, blocking operations, deadlock potential. Implement proper concurrency control (thread pools, async processing, message queues).' },
      { label: 'Fix Integration Flaky Test', text: 'Debug and fix this flaky integration test. Identify timing issues, race conditions, external dependencies, parallel test conflicts. Add proper waits, mocks, deterministic test data, and isolate tests.' },
      { label: 'Investigate Slow Query', text: 'Investigate this slow database query. Analyze query execution plan, identify missing indexes, inefficient joins, N+1 queries. Optimize queries, add appropriate indexes, consider denormalization, and implement query monitoring.' },
      { label: 'Debug State Synchronization', text: 'Debug this state synchronization issue between components. Trace state updates, identify inconsistent states, implement proper synchronization mechanisms (event sourcing, state machines, CRDTs), and validate state transitions.' },
    ]
  },
  {
    category: 'Architecture',
    icon: Layers,
    description: 'System design and architectural decisions',
    prompts: [
      { label: 'Design Microservices', text: 'Design a microservices architecture for this feature. Define service boundaries, communication patterns (REST/gRPC/GraphQL), data consistency strategies, service discovery, load balancing, and migration path from monolith.' },
      { label: 'CQRS Implementation', text: 'Design and implement Command Query Responsibility Separation. Separate read and write models, implement event sourcing, define aggregate boundaries, handle eventual consistency, and create projections for read optimization.' },
      { label: 'Event-Driven Design', text: 'Design an event-driven architecture. Define events, commands, queries, aggregates. Implement message brokers (Kafka/RabbitMQ), event schemas, event ordering/idempotency, and saga pattern for distributed transactions.' },
      { label: 'Database Sharding Strategy', text: 'Design a database sharding strategy. Define shard keys, sharding algorithms, cross-shard operations, data rebalancing, query routing, and ensure transaction constraints are maintained across shards.' },
      { label: 'API Gateway Design', text: 'Design an API gateway architecture. Handle request routing, rate limiting, authentication/authorization, request/response transformation, service composition, circuit breaking, and observability/tracing.' },
      { label: 'Design Message Queue', text: 'Design a reliable message queue system. Define message formats, queues/exchanges/topics, delivery guarantees, dead letter queues, consumer groups, and implement exactly-once/at-least-once semantics.' },
      { label: 'Load Balancer Design', text: 'Design a comprehensive load balancing strategy. Choose algorithms (round-robin, least connections, IP hash), implement health checks, session persistence, circuit breaking, and handle graceful degradation.' },
      { label: 'Service Mesh Design', text: 'Design a service mesh architecture. Implement service-to-service encryption, mTLS, observability (metrics/tracing/logs), traffic management, circuit breaking, and policy enforcement (rate limiting, access control).' },
      { label: 'Design Data Pipeline', text: 'Design a scalable data processing pipeline. Define stages (ingestion, transformation, enrichment, aggregation), implement stream processing (Apache Flink/Kafka), batch jobs, data quality checks, and scheduling.' },
      { label: 'Caching Architecture', text: 'Design a multi-level caching architecture. Define cache layers (browser, CDN, application, database), cache consistency strategies, invalidation logic, warm-up strategies, and monitoring for cache effectiveness.' },
      { label: 'Design Real-time System', text: 'Design a high-throughput real-time system. Implement WebSocket connections, event streaming, connection pooling, message ordering, backpressure handling, and horizontal scalability with stateless services.' },
      { label: 'Database Replication', text: 'Design database replication strategy. Choose replication modes (master-slave, multi-master, active-active), handle conflict resolution, ensure data consistency, implement read/write splitting, and plan for failover.' },
      { label: 'Design Disaster Recovery', text: 'Design comprehensive disaster recovery plan. Define RPO/RTO objectives, backup strategies (hot/cold), failover procedures, data restoration testing, and ensure business continuity during catastrophic failures.' },
      { label: 'API Version Strategy', text: 'Design API versioning strategy for long-term maintainability. Choose URL-based vs header-based versioning, define deprecation policies, implement backward compatibility layers, and manage breaking changes gracefully.' },
      { label: 'Design Scalable Auth', text: 'Design a scalable authentication and authorization system. Implement JWT tokens, refresh tokens, session management, OAuth/OpenID Connect, RBAC/ABAC, token revocation, and support multi-tenant SSO.' },
      { label: 'Design Observability Stack', text: 'Design comprehensive observability architecture. Instrument metrics, structured logging, distributed tracing. Implement alerting, dashboards, anomaly detection, and ensure visibility across all system layers.' },
      { label: 'Design Schema Evolution', text: 'Design database schema evolution strategy. Plan for backward/forward compatibility, implement schema migrations, handle data transformations, and ensure zero-downtime migrations with rollforward/rollback capabilities.' },
      { label: 'Design Feature Toggle', text: 'Design a feature flag/toggle system. Implement dynamic configuration, progressive rollouts, A/B testing support, user segmentation, emergency kill switches, and audit trails for flag changes.' },
      { label: 'Design CDN Strategy', text: 'Design Content Delivery Network strategy. Choose CDN providers, implement caching rules (TTL, purging), geo-routing, image optimization, video streaming acceleration, and implement failover between CDN providers.' },
    ]
  },
  {
    category: 'Database',
    icon: Database,
    description: 'Database design and optimization',
    prompts: [
      { label: 'Design Database Schema', text: 'Design a normalized database schema. Define tables, relationships, indexes, constraints. Ensure 3NF/BCNF normalization, handle many-to-many relationships, optimize for query patterns, and consider future scalability.' },
      { label: 'Optimize Slow Queries', text: 'Analyze and optimize slow database queries. Review execution plans, identify missing indexes, fix inefficient joins, eliminate N+1 queries, implement query hints/rewrites, and monitor query performance improvements.' },
      { label: 'Create Indexing Strategy', text: 'Design a comprehensive indexing strategy. Identify query patterns, choose index types (B-tree, hash, full-text, GiST), create composite indexes, monitor index usage, and implement index maintenance and rebuild procedures.' },
      { label: 'Implement Database Partitioning', text: 'Design and implement database partitioning strategy. Choose partition scheme (range, list, hash), define partition keys, handle cross-partition queries, implement partition pruning for performance, and manage partition lifecycle.' },
      { label: 'Database Migration Plan', text: 'Plan and execute safe database migration. Design atomic changes, create rollback procedures, validate data integrity, minimize downtime, use feature flags, and test thoroughly on staging environments.' },
      { label: 'Implement Data Encryption', text: 'Implement database encryption at rest and in transit. Choose encryption algorithms (AES-256), key management strategies, column-level encryption, transparent data encryption (TDE), and ensure compliance with security standards.' },
      { label: 'Design Data Archival', text: 'Design data archiving strategy. Define data retention policies, implement automated archiving jobs, compress/archive to cold storage, maintain data availability, and ensure regulatory compliance for data retention.' },
      { label: 'Database Connection Pooling', text: 'Optimize database connection pooling. Configure pool size, connection timeout, idle connection management, validation queries. Monitor pool metrics, prevent connection leaks, and implement graceful degradation under load.' },
      { label: 'Implement Event Sourcing', text: 'Design and implement event sourcing pattern. Store events as immutable facts, build projections/read models, handle snapshotting for performance, implement event replay, and ensure event schema evolution.' },
      { label: 'Create Stored Procedures', text: 'Write optimized stored procedures. Implement business logic in database, reduce roundtrips, ensure transaction integrity, handle exceptions properly, and maintain code organization and documentation within the database.' },
      { label: 'Database Replication Lag', text: 'Monitor and address replication lag. Identify causes (slow queries, network issues, long transactions), optimize replication topology, implement alerts, and create strategies for handling lag scenarios in applications.' },
      { label: 'Implement Soft Delete', text: 'Design and implement soft delete pattern. Add deleted_at columns, create unique constraints on active records, handle cascade soft deletes, implement data cleanup jobs, and maintain referential integrity.' },
      { label: 'Database Backup Strategy', text: 'Design comprehensive backup strategy. Schedule full/incremental/differential backups, test restore procedures, implement point-in-time recovery, offsite backup storage, and backup encryption and retention policies.' },
      { label: 'Optimize Transaction Scope', text: 'Analyze and optimize database transactions. Reduce transaction duration, minimize lock contention, implement optimistic/pessimistic locking, handle transactions across bounded contexts, and implement distributed transactions where necessary.' },
      { label: 'Implement Full-Text Search', text: 'Implement full-text search capabilities. Configure search indexes, handle stemming/lemmatization, implement relevance ranking, implement search suggestions/autocomplete, and integrate with application search UI.' },
      { label: 'Database Cache Warming', text: 'Implement database cache warming strategies. Pre-load frequently accessed data into cache, implement cache population on application startup, schedule periodic cache refreshes, and handle cache coherence with database updates.' },
      { label: 'Create Materialized Views', text: 'Design and implement materialized views for complex queries. Identify query aggregation patterns, create refreshable views, schedule refresh intervals, optimize view definitions, and monitor view refresh performance.' },
      { label: 'Implement Database Sharding', text: 'Design database sharding strategy. Choose shard key, implement consistent hashing, handle cross-shard queries, enable automatic rebalancing, and implement sharding middleware or proxy layer.' },
      { label: 'Optimize Schema for Read/Write', text: 'Analyze and optimize database schema for read-heavy vs write-heavy workloads. Denormalize for read performance, optimize indexes, use appropriate data types, implement read replicas, and consider write-ahead logging efficiency.' },
      { label: 'Database Foreign Key Strategy', text: 'Design foreign key relationships. Choose ON DELETE/UPDATE actions (CASCADE, SET NULL, RESTRICT), implement referential integrity, handle circular dependencies, and optimize foreign key constraint checks.' },
    ]
  },
  {
    category: 'Security',
    icon: ShieldCheck,
    description: 'Security audits and implementations',
    prompts: [
      { label: 'Security Audit Report', text: 'Perform comprehensive security audit. Test for OWASP Top 10 vulnerabilities (injection, broken auth, XSS, CSRF, misconfiguration, sensitive data exposure, XXE, broken access control, security logging, CSRF). Provide remediation checklist with priority levels.' },
      { label: 'Implement Rate Limiting', text: 'Design and implement rate limiting for API protection. Configure token bucket/slide window algorithms, per-user/IP limits, burst capacity, distributed rate limiting with Redis, and HTTP 429 responses with Retry-After headers.' },
      { label: 'API Authentication Design', text: 'Design secure authentication system. Implement JWT tokens with secure signing, refresh token rotation, PKCE flow for OAuth, multi-factor authentication, API key management, and revoked token blacklisting.' },
      { label: 'Input Sanitization', text: 'Implement comprehensive input sanitization and validation. Sanitize user inputs (XSS, SQL injection), validate data types (length, format, range), escape outputs, use parameterized queries/prepared statements, and implement allow-list validation.' },
      { label: 'Implement RBAC', text: 'Design role-based access control system. Define roles, permissions, resources hierarchies. Implement fine-grained permissions, role inheritance, permission checks at multiple layers (API, service, database), and maintain audit logs.' },
      { label: 'Encrypt Sensitive Data', text: 'Implement data encryption at rest and in transit. Use strong encryption (AES-256-GCM), secure key management (KMS, key rotation), field-level encryption, TLS 1.3 for all network communications, and secure secrets management.' },
      { label: 'Session Security', text: 'Design secure session management. Use secure random session IDs, implement session timeout and renewal, store session data securely (signed/encrypted cookies), prevent session fixation/hijacking, and implement session revocation.' },
      { label: 'Security Headers', text: 'Implement security HTTP headers. Set Content-Security-Policy, X-Frame-Options (DENY/SAMEORIGIN), X-XSS-Protection, Strict-Transport-Security (HSTS), X-Content-Type-Options, and X-Permitted-Cross-Domain-Policies.' },
      { label: 'Implement Secret Scanning', text: 'Set up secret scanning in CI/CD pipelines. Scan code for hardcoded secrets (API keys, passwords, tokens), use pattern matching, integrate with secret management tools, block commits with secrets, and rotate exposed secrets immediately.' },
      { label: 'DDoS Protection', text: 'Design DDoS mitigation strategy. Implement rate limiting, IP whitelisting/blacking, CAPTCHAs, CDN protection, traffic analytics, automatic detection of attack patterns, and emergency response procedures during attacks.' },
      { label: 'Secure File Upload', text: 'Implement secure file upload handling. Validate file types (MIME, magic numbers), scan for viruses, enforce size limits, store outside webroot, generate safe filenames, sanitize file contents, and implement access control.' },
      { label: 'SQL Injection Prevention', text: 'Audit and fix SQL injection vulnerabilities. Replace string concatenation with parameterized queries, use ORM safely, implement input validation, use least-privilege database accounts, and enable query logging and monitoring.' },
      { label: 'XSS Prevention', text: 'Prevent cross-site scripting attacks. Implement output encoding/escaping, use Content-Security-Policy headers, validate and sanitize inputs, set HTTPOnly and Secure cookies, enable X-XSS-Protection, and perform regular security testing.' },
      { label: 'CSRF Protection', text: 'Implement CSRF protection. Use anti-CSRF tokens, validate tokens on state-changing operations, set SameSite cookie attributes, verify Origin/Referer headers, and implement double-submit cookie pattern.' },
      { label: 'Secure API Design', text: 'Design secure REST API endpoints. Use HTTPS only, implement authentication/authorization, validate all inputs, use proper HTTP methods, limit response data, implement rate limiting, error messages without sensitive data.' },
      { label: 'Implement Audit Logging', text: 'Design comprehensive audit logging system. Log security events (login, logout, failed auth, data access), include user context, timestamps, IP addresses. Protect log integrity, monitor for suspicious activity, and define log retention policies.' },
      { label: 'Secure Dependencies', text: 'Audit and secure project dependencies. Check for known vulnerabilities, use package managers with security scanning, update dependencies regularly, subscribe to security advisories, and implement dependency allowlisting/blocklisting.' },
      { label: 'Penetration Testing', text: 'Perform security penetration testing. Use automated scanners (OWASP ZAP, Burp Suite), manual testing (logic flaws, business logic bypasses), test authentication bypasses, authorization bypasses, and document findings with severity ratings.' },
      { label: 'Secure Configuration', text: 'Audit and secure system configuration. Harden default credentials, disable unnecessary services/features, update patched versions, use secure configurations (TLS, encryption), restrict file permissions, and follow CIS benchmarks.' },
    ]
  },
  {
    category: 'DevOps & Deployment',
    icon: Server,
    description: 'Infrastructure and deployment',
    prompts: [
      { label: 'Dockerfile Optimization', text: 'Write optimized Dockerfile. Use multi-stage builds, layer caching, minimal base images (alpine), build-time vs run-time dependencies, .dockerignore for smaller builds, and document build steps and runtime requirements.' },
      { label: 'Docker Compose Setup', text: 'Create complete Docker Compose configuration. Define services, networks, volumes, environment variables. Implement health checks, depends_on with conditions, restart policies, and development/production config overrides.' },
      { label: 'CI/CD Pipeline Design', text: 'Design end-to-end CI/CD pipeline. Define stages (build, test, security scan, deploy), parallel execution, artifact caching, environment promotion, rollback capabilities, and notification/integration phases.' },
      { label: 'Kubernetes Deployment', text: 'Create Kubernetes deployment manifests. Design deployments, services, ingress, configmaps, secrets. Implement health checks (liveness/readiness probes), resource limits, HPA autoscaling, and update strategies.' },
      { label: 'Terraform Infrastructure', text: 'Write Terraform infrastructure as code. Define resources (VPC, subnets, EC2, RDS), use modules for reusability, implement secrets management, state file management, and validate with terraform plan before apply.' },
      { label: 'Health Check Endpoint', text: 'Implement comprehensive health check endpoints. Check service health, database connectivity, external service dependencies, disk/memory/CPU usage. Return detailed health status with degraded/healthy states and metrics.' },
      { label: 'Graceful Shutdown', text: 'Implement graceful shutdown handling. Handle SIGTERM/SIGINT signals, complete in-flight requests, close database connections, flush buffers, release resources, and allow configurable timeout before force kill.' },
      { label: 'Monitoring Setup', text: 'Set up comprehensive monitoring infrastructure. Deploy Prometheus/Grafana, define metrics (business, infrastructure, custom), configure alerting rules, create dashboards, and ensure observability across all services.' },
      { label: 'Log Aggregation', text: 'Implement centralized log aggregation. Set up ELK stack (Elasticsearch, Logstash, Kibana) or Loki/Promtail. Configure log shipping, parsing, indexing, retention policies, and create log analysis dashboards.' },
      { label: 'Load Testing Script', text: 'Write comprehensive load testing script. Define realistic user scenarios, configure concurrent users, ramp-up patterns, think time. Measure response times, throughput, error rates, and identify breaking points.' },
      { label: 'Auto-scaling Policy', text: 'Design auto-scaling policies based on metrics. Configure scaling triggers (CPU, memory, request count), scale-up/scale-down thresholds, cooldown periods, minimum/maximum instance counts, and predictive scaling strategies.' },
      { label: 'Blue-Green Deployment', text: 'Implement blue-green deployment strategy. Configure load balancer weights, switch traffic without downtime, test green environment before cutover, implement rapid rollback, and manage database migrations.' },
      { label: 'Rollback Procedure', text: 'Design and test rollback procedures. Document rollback steps, verify data integrity, restore previous deployments, rollback database migrations, and minimize user impact during failures.' },
      { label: 'Secrets Management', text: 'Implement secure secrets management. Use HashiCorp Vault or AWS Secrets Manager, enforce least-privilege access, implement secret rotation, audit secret access, and inject secrets securely at runtime.' },
      { label: 'Service Discovery', text: 'Implement service discovery mechanism. Use Consul, etcd, or Kubernetes built-in registration. Configure health checks for service registration, implement service resolution, load balancing across instances.' },
      { label: 'Environment Variables', text: 'Design comprehensive environment variable configuration. Separate dev/staging/production configs, use .env.local for local development, validate required variables, provide sensible defaults, and document all variables.' },
      { label: 'Database Backup Automation', text: 'Automate database backup procedures. Schedule automated backups, verify backup integrity, test restore procedures, implement backup monitoring/alerting, and manage backup retention policies.' },
      { label: 'SSL Certificate Management', text: 'Implement SSL/TLS certificate management. Use Let\'s Encrypt with automated renewal, configure certificate rotation, manage CA bundles, enforce secure TLS configurations, and monitor certificate expiry.' },
      { label: 'Infrastructure Monitoring', text: 'Set up infrastructure monitoring. Monitor CPU, memory, disk, network, GPU usage. Configure alerts for resource exhaustion, create capacity planning dashboards, and implement predictive scaling based on trends.' },
      { label: 'Disaster Recovery Testing', text: 'Design and execute disaster recovery tests. Simulate service failures, test failover procedures, verify data integrity after failover, measure RTO/RPO objectives, and document recovery procedures.' },
    ]
  },
  {
    category: 'Testing',
    icon: Layout,
    description: 'Test strategies and implementation',
    prompts: [
      { label: 'Write Unit Tests', text: 'Write comprehensive unit tests following test-driven development. Test individual functions/methods in isolation, mock external dependencies, test edge cases and error conditions, achieve >90% code coverage, and keep tests fast and independent.' },
      { label: 'Create Integration Tests', text: 'Design integration tests for API endpoints. Test request/response contracts, database operations, external service calls, error handling, data flow across services, and use test fixtures for consistent test data.' },
      { label: 'E2E Test Framework', text: 'Set up end-to-end testing framework (Playwright/Cypress). Create realistic user journey tests, handle authentication/session management, test multiple browsers, implement test isolation, and integrate with CI/CD pipelines.' },
      { label: 'Performance Test Scenarios', text: 'Design performance test scenarios covering typical user journeys, peak load conditions, stress tests, endurance tests, soak tests. Define success criteria (response times, error rates), and test before production releases.' },
      { label: 'Test Data Management', text: 'Design comprehensive test data management strategy. Create test fixtures/factories, seed test databases, manage test data isolation/rollback, generate synthetic test data, and use test data builders for flexibility.' },
      { label: 'Visual Testing', text: 'Implement visual regression testing. Configure screenshot comparison (Percy/Playwright), handle image differences, manage baseline updates, test across browsers/devices, and integrate visual testing into CI/CD.' },
      { label: 'Contract Testing', text: 'Implement contract testing for API consumer and provider agreements. Define API contracts, generate tests from contracts, verify contract compatibility, detect breaking changes early, and enforce contract compliance in CI/CD.' },
      { label: 'Accessibility Testing', text: 'Perform comprehensive accessibility testing. Test keyboard navigation, screen reader compatibility (NVDA, JAWS), color contrast, focus indicators, ARIA attributes, and ensure WCAG 2.1 AA/AAA compliance.' },
      { label: 'Mobile Testing Strategy', text: 'Design mobile device testing strategy. Test on physical device pool, use simulators/emulators, cover various screen sizes/OS versions, test touch gestures, mobile network conditions, and device-specific features.' },
      { label: 'Chaos Engineering', text: 'Design chaos engineering experiments. Inject failures (latency, network drops, process failures), test system resilience, design fallback mechanisms, measure recovery time objectives (RTO), and document failure modes.' },
      { label: 'Security Testing', text: 'Implement security testing in CI/CD. Run vulnerability scans (SAST, DAST, SCA), penetration testing for APIs, test for OWASP vulnerabilities, authenticate/authorization bypasses, and ensure secrets scanning.' },
      { label: 'Test Coverage Analysis', text: 'Analyze test coverage comprehensively. Measure code coverage (line, branch, function, statement), identify uncovered code paths, coverage reports by module, set coverage thresholds (e.g., 80%), and track coverage trends.' },
      { label: 'Flaky Test Elimination', text: 'Identify and fix flaky tests. Analyze test failures, isolate timing issues, mock external dependencies, use deterministic test data, implement retries for intermittent failures, and remove flaky tests from critical paths.' },
      { label: 'API Testing Framework', text: 'Design and implement API testing framework. Test endpoints with various HTTP methods, status codes, request/response validation, auth headers, error scenarios, and integrate with API documentation (Swagger/OpenAPI).' },
      { label: 'Load Testing Script', text: 'Create load testing scripts (k6, JMeter, Gatling). Define realistic user scenarios, simulate concurrent users, configure ramp-up, measure throughput, response times, error rates, and generate performance reports.' },
      { label: 'Component Testing', text: 'Implement component-level testing for UI frameworks. Test components in isolation, mock child components, test props/state/events, verify rendering, implement snapshot testing (Jest snapshots), and test user interactions.' },
      { label: 'Test Environment Setup', text: 'Design test environment strategy. Create isolated test environments (dev, staging, UAT), manage test data seeding, environment-specific configurations, clean up between test runs, and automate test environment provisioning.' },
      { label: 'Mutation Testing', text: 'Implement mutation testing to assess test quality. Use mutation testing tools (Stryker, PIT), introduce code mutants, verify tests catch mutants, analyze mutation scores, and identify weak test coverage areas.' },
      { label: 'Behavior-Driven Tests', text: 'Design BDD tests using Gherkin syntax. Define Given-When-Then scenarios, make tests readable by non-technical stakeholders, test acceptance criteria, integrate with test frameworks (Cucumber), and link tests to user stories.' },
      { label: 'Regression Testing', text: 'Design comprehensive regression testing suite. Prioritize critical paths and high-risk areas, automate manual tests, smoke tests, sanity tests, full regression tests, and integrate into release gates.' },
      { label: 'Test Automation Maintenance', text: 'Establish test automation maintenance practices. Review and update tests regularly, refactor duplicate tests, remove obsolete tests, maintain test data, update test documentation, and monitor test execution trends.' },
      { label: 'Analytics and Reporting', text: 'Design test analytics and reporting dashboard. Track test results, pass/fail rates, execution time trends, flaky tests, code coverage changes. Create executive summaries and detailed reports for quality metrics.' },
    ]
  },
  {
    category: 'Frontend',
    icon: Smartphone,
    description: 'User interface and experience',
    prompts: [
      { label: 'React Component Design', text: 'Design a reusable, accessible React component. Define props interface, state management, event handlers, hooks usage, styling approach (CSS, styled-components, Tailwind), and ensure accessibility (ARIA, keyboard navigation, screen readers).' },
      { label: 'UI/UX Optimization', text: 'Optimize user interface and experience. Improve visual hierarchy, reduce cognitive load, optimize navigation flow, implement micro-interactions, reduce page load time, and ensure consistency across the application.' },
      { label: 'Responsive Design', text: 'Ensure responsive design across devices. Implement mobile-first approach, fluid layouts, flexible grids, responsive images, typography scaling, breakpoint strategies, and test on various screen sizes/devices.' },
      { label: 'Accessibility Audit', text: 'Perform comprehensive accessibility audit. Check WCAG 2.1 AA/AAA compliance, test with screen readers, verify keyboard navigation, ensure color contrast ratios, check focus indicators, and fix ARIA usage and semantic HTML.' },
      { label: 'Performance Optimization', text: 'Optimize frontend performance. Implement code splitting, lazy loading, tree shaking, image optimization (WebP, resize), compression, caching strategies, reduce bundle size with Webpack/Vite analysis.' },
      { label: 'State Management', text: 'Design optimal state management strategy. Choose between Redux, Zustand, Context, Recoil. Implement centralized vs decentralized state, handle async state, optimize re-renders, and ensure predictable state updates.' },
      { label: 'Form Validation', text: 'Implement comprehensive form validation. Real-time validation, error messaging, validation schemas (Zod/Yup), async validation, dirty state tracking, field-level vs form-level validation, and user-friendly error displays.' },
      { label: 'Data Visualization', text: 'Design data visualization components. Choose charting library (Chart.js, Recharts, D3), implement interactive charts, handle large datasets, ensure accessibility (alt text, keyboard navigation), optimize rendering performance.' },
      { label: 'Animation Design', text: 'Add polished animations and transitions. Use Framer Motion or CSS animations, implement smooth page transitions, micro-interactions for feedback, loading skeletons, ensure performant animations (60fps), and respect prefers-reduced-motion.' },
      { label: 'Component Library', text: 'Build reusable component library. Document components with Storybook, define design tokens (colors, spacing, typography), create variants (sizes, states), implement dark mode support, and ensure consistency.' },
      { label: 'PWA Implementation', text: 'Progressive web app implementation. Create service worker for offline support, implement app manifest, enable add to home screen, use background sync, optimize for fast initial load, and ensure mobile experience.' },
      { label: 'SEO Optimization', text: 'Optimize for search engines. Implement SSR/SSG (Next.js/Nuxt), meta tags, structured data (JSON-LD), sitemap generation, robots.txt, Open Graph tags, and optimize Core Web Vitals (LCP, FID, CLS).' },
      { label: 'Testing Framework', text: 'Set up React testing framework. Configure Jest, React Testing Library, test utilities. Write unit tests for components, integration tests for hooks, E2E tests with Playwright/Cypress, and integrate with CI/CD.' },
      { label: 'Error Boundary', text: 'Implement global error boundary for React. Catch component errors, display fallback UI, log errors to monitoring, implement error recovery strategies, track error rates, and ensure gracefully degraded experience.' },
      { label: 'Internationalization', text: 'Implement i18n support. Manage translations (i18next), format dates/numbers/currencies, RTL layout support, language switcher, locale-aware content, and ensure efficient translation loading.' },
      { label: 'Theme System', text: 'Design theme system with light/dark mode. Use CSS custom properties/variables, implement theme toggle, persist theme preference, design color palettes, typography scales, spacing system, and ensure smooth theme transitions.' },
      { label: 'Mobile App Optimization', text: 'Optimize for mobile devices. Touch gestures (swipe, pinch, tap), viewport meta tags, mobile performance, offline support via PWA, app-like experience (smooth scrolling, no reloads).' },
      { label: 'Real-time Updates', text: 'Implement real-time data updates. Use WebSockets, Server-Sent Events, or polling strategies. Optimize subscription/unsubscriptions, handle connection resilience, implement optimistic UI updates, and handle conflicts.' },
      { label: 'Image Optimization', text: 'Optimize images for web performance. Use responsive images (srcset, sizes), convert to WebP format, implement lazy loading, use CDN/image optimization services, compress images, and implement image resizing/cropping.' },
      { label: 'Bundle Optimization', text: 'Analyze and optimize bundle size. Use webpack-bundle-analyzer or rollup-plugin-visualizer. Implement code splitting, dynamic imports, tree shaking, remove unused dependencies, minify code, and optimize vendor chunking.' },
      { label: 'Form Analytics', text: 'Implement form analytics and optimization. Track form abandonment, field errors, completion time, validate user inputs minimally, implement progressive profiling, optimize form conversion rates, and A/B test form designs.' },
      { label: 'Accessibility Testing', text: 'Perform accessibility testing and fixes. Test with screen readers (NVDA, JAWS, VoiceOver), verify keyboard navigation (tab order, focus), check color contrast, implement ARIA labels, test with mobile assistive tech.' },
      { label: 'Design System', text: 'Design comprehensive design system. Document design tokens (colors, typography, spacing, shadows), create atomic components, design patterns, ensure consistent implementation, and provide Figma/Sketch exports.' },
    ]
  },
  {
    category: 'Infrastructure',
    icon: Globe,
    description: 'Cloud services and infrastructure',
    prompts: [
      { label: 'AWS Architecture Design', text: 'Design AWS infrastructure architecture. Choose EC2 vs Lambda/serverless, design VPC structure, select RDS instances, S3 buckets, CloudFront distribution, implement security groups, IAM policies, and cost optimization.' },
      { label: 'Kubernetes Cluster Setup', text: 'Set up Kubernetes cluster. Configure control plane (etcd, API server), worker nodes, networking (CNI, CNI), storage (PVs, storage classes), RBAC policies, monitoring (Prometheus, Grafana), and logging (ELK stack).' },
      { label: 'CI/CD Pipeline Setup', text: 'Set up complete CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins). Configure build stages, test automation, security scanning, deployment to staging, approval gates, production deployment with rollback capabilities.' },
      { label: 'Load Balancer Config', text: 'Configure load balancer for high availability. Choose ALB/NLB/ELB on AWS or GLB on GCP, configure health checks, routing rules, SSL/TLS termination, sticky sessions, and failover handling.' },
      { label: 'CDN Configuration', text: 'Configure Content Delivery Network. Set up CloudFront (AWS) or Cloud CDN (GCP), configure caching rules (static/dynamic content), origin configuration, custom domain names, SSL certificates, and invalidation policies.' },
      { label: 'Database Cluster', text: 'Design database cluster for high availability. Configure primary-replica setup, read replicas, automatic failover, multi-AZ deployment, connection pooling, backup strategy, and monitoring/alerting.' },
      { label: 'Infrastructure Monitoring', text: 'Set up infrastructure monitoring. Deploy Prometheus for metrics collection, configure Grafana dashboards, set up alerting rules (PagerDuty, Slack, email), monitor resources (CPU, memory, disk, network), and log aggregation.' },
      { label: 'Cost Optimization', text: 'Optimize cloud infrastructure costs. Use rightsizing, reserved instances, spot instances, auto-scaling policies, cost allocation tags, monitor spend with AWS Cost Explorer/GCP Billing, and implement budget alerts.' },
      { label: 'Security Hardening', text: 'Secure infrastructure configuration. Implement VPC with private subnets, security groups with least privilege, IAM policies with minimal permissions, encryption at rest and in transit, secrets management, and security audits.' },
      { label: 'Disaster Recovery', text: 'Design disaster recovery strategy. Implement multi-region deployment, configure backup and restore procedures, test failover scenarios, define RTO/RPO objectives, set up data replication, and emergency response procedures.' },
      { label: 'Secret Management', text: 'Implement secrets management (AWS Secrets Manager, HashiCorp Vault). Store secrets securely, rotate credentials automatically, audit secret access, inject secrets at runtime, use IAM roles instead of credentials.' },
      { label: 'Service Mesh', text: 'Set up service mesh (Istio, Linkerd). Implement mTLS encryption, configure observability (tracing, metrics, logs), enable traffic management (canary, blue-green), implement circuit breaking, and enforce policies.' },
      { label: 'Container Registry', text: 'Set up container registry (AWS ECR, GCR, Docker Hub). Configure repository permissions, implement image scanning (Trivy, Clair), set up CI/CD integration, manage image tags/versions, and enable replication.' },
      { label: 'SSL/TLS Management', text: 'Manage SSL/TLS certificates. Use AWS Certificate Manager or cert-manager for K8s, configure automatic renewal, enforce HTTPS, set up perfect forward secrecy, and monitor certificate expiry.' },
      { label: 'Infrastructure as Code', text: 'Implement infrastructure as code (Terraform, Pulumi, AWS CDK). Define infrastructure declaratively, version control infrastructure, enable code reviews for changes, automated provisioning, and ensure reproducible deployments.' },
      { label: 'Auto-scaling Strategy', text: 'Configure auto-scaling policies. Set up AWS Auto Scaling Groups or GCP Autoscaler, define scaling policies based on metrics (CPU, memory, requests), configure cooldown periods, and monitor scaling events.' },
      { label: 'Network Architecture', text: 'Design network architecture. Configure VPC/VPC peering, subnets, route tables, NAT gateways, VPN connections, security groups firewall rules, and network segmentation for security.' },
      { label: 'Storage Strategy', text: 'Design storage architecture. Choose storage types (EBS, S3, EFS) based on needs, configure IOPS, throughput, encryption, lifecycle policies, backup/restore, and migration between storage types.' },
      { label: 'Observability Stack', text: 'Set up observability stack. Install Logging (Elasticsearch/Kibana), Monitoring (Prometheus/Grafana), Tracing (Jaeger, Tempo). Configure alerting, dashboards, log aggregation, and correlated tracing.' },
      { label: 'Backup Strategy', text: 'Design backup strategy for critical systems. Schedule automated backups, implement point-in-time recovery, test restore procedures, offsite backup storage, backup encryption, and retention policies.' },
      { label: 'Migration Planning', text: 'Plan infrastructure migration. Assess current environment, design target state, plan migration phases, minimize downtime, data migration strategy, rollback procedures, and post-migration validation.' },
      { label: 'Performance Tuning', text: 'Optimize infrastructure performance. Tune database parameters, configure network optimization, adjust auto-scaling thresholds, optimize caching layer, monitor resource utilization, and implement performance baselines.' },
      { label: 'Compliance Implementation', text: 'Implement infrastructure compliance (SOC2, HIPAA, PCI-DSS). Configure audit logging, encryption requirements, access controls, data retention, vulnerability scanning, and prepare compliance documentation.' },
    ]
  },
  {
    category: 'Productivity',
    icon: Zap,
    description: 'Efficiency and workflow improvements',
    prompts: [
      { label: 'Automation Script', text: 'Create automation script to eliminate repetitive manual tasks. Write efficient Python/Bash scripts, handle errors gracefully, add logging and documentation, make scripts configurable, and integrate with scheduling/cron jobs.' },
      { label: 'Workflow Optimization', text: 'Analyze and optimize existing workflow. Identify bottlenecks, redundant steps, manual interventions. Propose automation, standardize processes, implement monitoring, and measure time/cost savings.' },
      { label: 'Code Snippet Library', text: 'Create reusable code snippet library. Document common patterns, best practices, utility functions. Organize by category, make snippets searchable, include examples and caveats, and integrate with IDE snippets.' },
      { label: 'Project Scaffolding', text: 'Create project scaffolding tool. Set up project structure, configure build tools, add linters/prettier, configure testing framework, create templates for components/modules, and document getting started guide.' },
      { label: 'Documentation Improvement', text: 'Improve project documentation. Generate API docs from code, create architecture diagrams (Mermaid, PlantUML), write README with examples, document environment setup, and create onboarding guides for new team members.' },
      { label: 'Git Workflow Setup', text: 'Set up Git workflow and best practices. Configure branch strategy (Git Flow, GitHub Flow), commit message conventions, peer review process, CI/CD hooks, release workflow, and documentation standards.' },
      { label: 'Task Management', text: 'Design task management system. Define task categories, priorities, assignees, deadlines. Implement tracking, notifications, reporting, integration with calendars, and workflows for task lifecycle.' },
      { label: 'Code Review Automation', text: 'Automate code review process. Configure automated checks (lints, tests, security scans), set up PR templates, require reviewer approvals, integrate with CI/CD, and generate review metrics.' },
      { label: 'Performance Dashboard', text: 'Create performance monitoring dashboard. Display key metrics (response times, throughput, error rates), set up alerts, historical trending, drill-down capabilities, and real-time updates via WebSockets.' },
      { label: 'Deployment Automation', text: 'Automate deployment process. Create deployment scripts, configure staging/production environments, implement blue-green deployments, rollback procedures, health checks, and integrate with CI/CD pipeline.' },
      { label: 'Testing Automation Setup', text: 'Set up automated testing infrastructure. Configure test runners (Jest, pytest), parallel test execution, test reporting, integrate with CI/CD, set up test data factories, and handle test environment setup.' },
      { label: 'Communication System', text: 'Design communication system for team. Configure messaging (Slack/Teams), email notifications, meeting scheduling, status updates, escalation paths, and integration with project management tools.' },
      { label: 'Knowledge Base', text: 'Create team knowledge base. Document architecture, decisions (ADRs), troubleshooting guides, runbooks, onboarding materials, and make searchable with tags/categories.' },
      { label: 'Time Tracking', text: 'Implement time tracking system. Log time per task, project, client. Generate time reports, identify time sinks, optimize allocation, integrate with billing/invoicing, and provide analytics.' },
      { label: 'Alert System', text: 'Design comprehensive alert system. Configure alert rules, severity levels, notifications channels (email, Slack, SMS, PagerDuty), on-call schedules, escalation policies, and reduce false positives.' },
      { label: 'Backup Procedures', text: 'Automate backup procedures. Schedule backups for code, databases, configurations. Implement encryption, offsite storage, retention policies, test restore procedures, and monitoring for backup failures.' },
      { label: 'Developer Environment', text: 'Create standardized developer environment. Configure IDE settings, install dependencies, set up tools (linters, formatters), create scripts for common tasks, document setup process, and ensure reproducible environment.' },
      { label: 'Release Management', text: 'Design release management workflow. Version numbering (semantic versioning), release notes generation, release candidates, testing phase, approval gates, deployment procedures, and rollback plans.' },
      { label: 'Code Review Checklist', text: 'Create code review checklist. Include quality standards, security checks, performance considerations, documentation requirements, testing requirements, and make checklist enforceable in PR process.' },
      { label: 'Performance Profiling', text: 'Set up performance profiling tools. Configure APM (New Relic, Datadog), profiling in development, identify bottlenecks, track performance metrics, set targets, and alert on degradation.' },
      { label: 'Analytics Dashboard', text: 'Build analytics dashboard for business metrics. Track user engagement, conversion rates, feature usage, retention, churn. Create reports, export data, set up real-time monitoring, and integrate with data warehouse.' },
    ]
  },
];

export function MissionModal({ isOpen, onClose, apiBaseUrl, selectedAgentName }: MissionModalProps) {
  const notifications = useNotificationContext();
  const [missionText, setMissionText] = useState('');
  const [executionMode, setExecutionMode] = useState<'smart' | 'auto' | 'swarm' | 'manual'>('smart');
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<MissionResult | null>(null);
  const [modalKey, setModalKey] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<string>('Development');
  const [selectedPrompt, setSelectedPrompt] = useState<string>('');

  // Async mission state
  const [currentMission, setCurrentMission] = useState<MissionStatus | null>(null);
  const [asyncMissionResult, setAsyncMissionResult] = useState<AsyncMissionResult | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [showFullResult, setShowFullResult] = useState(false);

  // Fetch available models
  useEffect(() => {
    if (!isOpen) return;
    
    const fetchModels = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/agents/models`);
        if (response.ok) {
          const data = await response.json();
          // API returns { models: [...], count: N, default_provider: ... }
          const models = Array.isArray(data.models) ? data.models : (Array.isArray(data) ? data : []);
          setAvailableModels(models);
          if (models.length > 0 && !selectedModel) {
            const defaultModel = models.find((m: ModelInfo) => m.is_default);
            setSelectedModel(defaultModel ? defaultModel.id : models[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to fetch models:", err);
        setAvailableModels([]);  // Ensure it's always an array
      }
    };

    fetchModels();
  }, [isOpen, selectedModel]);

  // Poll mission status if running
  useEffect(() => {
    if (!currentMission || currentMission.status !== 'running') {
      return;
    }

    const pollMissionStatus = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/api/v1/missions/${currentMission.mission_id}/status`
        );
        if (response.ok) {
          const statusData = await response.json();

          if (
            statusData.status === 'completed' ||
            statusData.status === 'failed'
          ) {
            setCurrentMission({ ...currentMission, ...statusData });
            setAsyncMissionResult({
              mission_id: statusData.mission_id,
              status: statusData.status,
              result: statusData.result,
              error: statusData.error,
              heuristics: statusData.heuristics,
              duration_seconds: statusData.duration_seconds,
              completed_at: statusData.completed_at,
            });

            if (pollingInterval) {
              clearInterval(pollingInterval);
              setPollingInterval(null);
            }
          }
        }
      } catch (err) {
        console.error("Failed to poll mission status:", err);
      }
    };

    pollMissionStatus();

    const interval = setInterval(pollMissionStatus, 2000);
    setPollingInterval(interval);

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [currentMission, apiBaseUrl, pollingInterval]);

  const handleExecute = useCallback(async () => {
    if (!missionText.trim()) {
      notifications.addNotification(
        'Mission Error',
        'Please enter a mission description',
        'info'
      );
      return;
    }

    setIsExecuting(true);
    setLastResult(null);
    setAsyncMissionResult(null);
    setCurrentMission(null);

    try {
      console.log(`Executing mission: ${missionText.substring(0, 50)}...`);

      const body: any = {
        task: missionText,
        mode: executionMode,
      };

      if (executionMode === 'manual' && selectedModel) {
        body.model_id = selectedModel;
        body.agent_type = selectedAgentName;
      }

      console.log('Sending request:', {
        url: `${apiBaseUrl}/api/v1/missions`,
        body: JSON.stringify(body, null, 2)
          .substring(0, 500)
      });

      const response = await fetch(`${apiBaseUrl}/api/v1/missions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      console.log('Response status:', response.status);
      console.log('Response data:', {
        status: data.status,
        has_mission_id: !!data.mission_id,
        has_result: !!data.result
      });

      setLastResult({
        mode: executionMode,
        agent_type: data.agent_type,
        heuristics_count: data.heuristics_count || 0,
        execution_time_ms: data.execution_time_ms || 0,
        response_preview: data.response_preview,
      });

      if (data.mission_id && (data.status === 'pending' || data.status === 'running')) {
        console.log('Mission started with ID:', data.mission_id);
        setCurrentMission({
          mission_id: data.mission_id,
          status: data.status,
          created_at: data.created_at || new Date().toISOString(),
        });

        // Clear the mission text after submission
        setMissionText('');
        setSelectedPrompt('');
      } else if (data.result) {
        setAsyncMissionResult({
          mission_id: '',
          status: 'completed',
          result: data.result,
          error: undefined,
          duration_seconds: data.execution_time_ms / 1000,
        });
      } else if (data.error) {
        notifications.addNotification('Mission Failed', data.error, 'error');
      }
    } catch (err: any) {
      console.error('Mission execution error:', err);
      notifications.addNotification('Mission Error', err.message || 'Failed to execute mission', 'error');
    } finally {
      setIsExecuting(false);
    }
  }, [
    missionText,
    executionMode,
    apiBaseUrl,
    notifications,
    selectedModel,
    selectedAgentName,
  ]);

  const handleCancelMission = async () => {
    if (!currentMission) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/missions/${currentMission.mission_id}/cancel`,
        {
          method: 'POST',
        }
      );

      if (response.ok) {
        setCurrentMission(null);
        notifications.addNotification(
          'Mission Cancelled',
          'The mission has been cancelled successfully',
          'info'
        );
      }
    } catch (err: any) {
      notifications.addNotification(
        'Cancel Failed',
        err.message || 'Failed to cancel mission',
        'error'
      );
    }
  };

  const handleClose = () => {
    // Clear polling interval
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setCurrentMission(null);
    setAsyncMissionResult(null);
    setMissionText('');
    setModalKey((k) => k + 1);
    onClose();
  };

  if (!isOpen) return null;

  const selectedCategoryData = PROMPT_CATEGORIES.find(
    (c) => c.category === selectedCategory
  );

  return createPortal(
    <div className="fixed inset-0 z-[9999] overflow-hidden">
      <div
        className="absolute inset-0 bg-gray-900/90 backdrop-blur-sm animate-in fade-in"
        onClick={handleClose}
      />
      <div className="absolute inset-y-0 right-0 w-[700px] max-h-[90vh] bg-slate-900 shadow-2xl animate-in slide-in-from-right overflow-y-auto custom-scrollbar rounded-l-xl">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Zap className="w-6 h-6 text-violet-400" />
              <h2 className="text-xl font-bold text-white">Mission Control</h2>
            </div>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400 hover:text-white" />
            </button>
          </div>

          {/* Mode Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Execution Mode
            </label>
            <div className="grid grid-cols-4 gap-2">
              {(['smart', 'auto', 'swarm', 'manual'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setExecutionMode(mode)}
                  className={`px-3 py-2 text-sm font-medium rounded-lg border transition-all ${
                    executionMode === mode
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'bg-transparent border-slate-600 text-slate-400 hover:border-violet-500 hover:text-violet-400'
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Model Selection (for manual mode) */}
          {executionMode === 'manual' && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-600 bg-slate-800 text-white"
              >
                {availableModels.map((model, index) => (
                  <option key={`${model.id}-${model.provider_id || index}`} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Category Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Category
            </label>
            <div className="grid grid-cols-5 gap-2">
              {PROMPT_CATEGORIES.map((cat) => {
                const CatIcon = cat.icon;
                return (
                  <button
                    key={cat.category}
                    onClick={() => {
                      setSelectedCategory(cat.category);
                      setSelectedPrompt('');
                    }}
                    title={cat.description}
                    className={`p-2 rounded-lg border text-sm font-medium transition-all flex flex-col items-center gap-1 ${
                      selectedCategory === cat.category
                        ? 'bg-violet-600/30 border-violet-500 text-violet-300'
                        : 'bg-slate-800/30 border-slate-600 text-slate-400 hover:border-violet-500 hover:text-violet-400'
                    }`}
                  >
                    <CatIcon className="w-4 h-4 flex-shrink-0" />
                    <span className="text-xs">{cat.category}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Prompt Selection */}
          {selectedCategoryData && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                {selectedCategoryData.category} Prompts
              </label>
              <div
                className="grid grid-cols-2 gap-2 max-h-[200px] overflow-y-auto custom-scrollbar pr-2"
              >
                {selectedCategoryData.prompts.map((prompt) => (
                  <button
                    key={prompt.label}
                    onClick={() => {
                      setMissionText(prompt.text);
                      setSelectedPrompt(prompt.label);
                    }}
                    title={prompt.text.substring(0, 200)}
                    className={`p-3 text-left rounded-lg border text-sm transition-all ${
                      selectedPrompt === prompt.label
                        ? 'bg-violet-600/30 border-violet-500 text-violet-300'
                        : 'bg-slate-800/30 border-slate-600 text-slate-400 hover:border-violet-500 hover:text-violet-400'
                    }`}
                  >
                    <div className="font-medium truncate">{prompt.label}</div>
                    <div className="text-xs text-slate-500 truncate mt-1">
                      {prompt.text.substring(0, 60)}...
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Mission Text Area */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Mission Description
            </label>
            <textarea
              value={missionText}
              onChange={(e) => setMissionText(e.target.value)}
              rows={6}
              placeholder="Enter your mission description here..."
              className="w-full px-3 py-2 text-sm text-white rounded-lg border border-slate-600 bg-slate-800 placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50"
            />
          </div>

          {/* Execute Button */}
          <button
            onClick={handleExecute}
            disabled={isExecuting || !missionText.trim()}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-violet-600 hover:bg-violet-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all"
          >
            {isExecuting ? (
              <>
                <Cpu className="w-5 h-5 animate-spin" />
                Executing...
                <span>({currentMission ? 'Running Mission' : 'Processing'})</span>
              </>
            ) : (
              <>
                <Rocket className="w-5 h-5" />
                Execute Mission
              </>
            )}
          </button>

          {/* Cancel Mission Button */}
          {currentMission && (
            <button
              onClick={handleCancelMission}
              className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 font-medium rounded-lg transition-all"
            >
              <XCircle className="w-4 h-4" />
              Cancel Mission
            </button>
          )}

          {/* Async Mission Status */}
          {currentMission && (
            <div className="mt-6 p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">
                  Current Mission
                </span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    currentMission.status === 'running'
                      ? 'bg-cyan-500/20 text-cyan-400'
                      : currentMission.status === 'completed' || currentMission.status === 'failed'
                      ? 'bg-violet-500/20 text-violet-400'
                      : 'bg-yellow-500/20 text-yellow-400'
                  }`}
                >
                  {currentMission.status}
                </span>
              </div>
              <div className="text-xs text-slate-500">
                Mission ID: {currentMission.mission_id}
              </div>
              <div className="text-xs text-slate-500">
                Started:{' '}
                {currentMission.started_at
                  ? new Date(currentMission.started_at).toLocaleString()
                  : 'Not started'}
              </div>
            </div>
          )}

          {/* Async Mission Result */}
          {asyncMissionResult && (
            <div className="mt-6 p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">
                  Mission Result
                </span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    asyncMissionResult.status === 'completed'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-red-500/20 text-red-400'
                  }`}
                >
                  {asyncMissionResult.status === 'completed' ? 'Completed' : 'Failed'}
                </span>
              </div>
              {asyncMissionResult.result && (
                <div className="mt-3 max-h-50 overflow-y-auto">
                  <pre className="text-xs text-slate-300 whitespace-pre-wrap">
                    {asyncMissionResult.result.substring(0, 2000)}
                    {asyncMissionResult.result.length > 2000 && '...'}
                  </pre>
                </div>
              )}
              {asyncMissionResult.error && (
                <div className="mt-3 text-xs text-red-400 font-mono">
                  {asyncMissionResult.error}
                </div>
              )}
              {asyncMissionResult.heuristics && asyncMissionResult.heuristics.length > 0 && (
                <div className="mt-3 text-xs text-slate-400">
                  Heuristics: {asyncMissionResult.heuristics.length} extracted
                </div>
              )}
              {asyncMissionResult.duration_seconds && (
                <div className="mt-3 text-xs text-slate-400">
                  Duration:{' '}
                  {asyncMissionResult.duration_seconds.toFixed(2)}s
                </div>
              )}
            </div>
          )}

          {/* Last Result */}
          {lastResult && !asyncMissionResult && (
            <div className="mt-6 p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="text-sm font-medium text-slate-300 mb-2">
                Last Execution Result
              </div>
              <div className="space-y-2 text-xs text-slate-400">
                <div>Mode: {lastResult.mode}</div>
                <div>Agent: {lastResult.agent_type || 'N/A'}</div>
                <div>
                  Heuristics:{' '}
                  {lastResult.heuristics_count}
                </div>
                <div>
                  Time:{' '}
                  {(lastResult.execution_time_ms / 1000).toFixed(2)}s
                </div>
                {lastResult.response_preview && (
                  <div>
                    Preview:{' '}
                    {lastResult.response_preview.substring(0, 200)}
                    {lastResult.response_preview.length > 200 && '...'}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}