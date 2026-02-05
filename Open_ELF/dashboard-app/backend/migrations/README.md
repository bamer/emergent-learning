# Database Migrations

This directory contains database migration scripts for the dashboard backend.

## Usage

### Run All Pending Migrations
```bash
python migrations/run_migration.py
```

### Run a Specific Migration
```bash
python migrations/run_migration.py --migration <migration_file.sql>
```

### List Migration Status
```bash
python migrations/run_migration.py --list
```

### Run Against Project Database
```bash
python migrations/run_migration.py --scope project
```

### Verbose Output
```bash
python migrations/run_migration.py --verbose
```

## Migration Files

### 001_add_performance_indexes.sql
**Date:** 2026-02-02  
**Purpose:** Add performance indexes to optimize query performance

Creates 55 indexes across the following tables:
- **Heuristics** (6 indexes) - Domain-based queries, golden rules, validation tracking
- **Learnings** (6 indexes) - Type/domain filtering, severity, temporal queries
- **Decisions** (5 indexes) - Status/domain access, supersession, temporal patterns
- **Workflow Runs** (5 indexes) - Status monitoring, temporal analytics
- **Building Queries** (2 indexes) - Temporal and performance analysis
- **Metrics** (3 indexes) - Type filtering, timestamp queries
- **Node Executions** (6 indexes) - Run tracking, agent/session queries
- **Trails** (7 indexes) - Location/scent searches, expiration
- **Session Summaries** (2 indexes) - Staleness, temporal queries
- **Spike Reports** (2 indexes) - Temporal analytics, usefulness
- **Invariants** (3 indexes) - Status/domain, violation tracking
- **Assumptions** (3 indexes) - Status/domain, confidence

## Migration Tracking

Migrations are tracked in the `schema_migrations` table with:
- `filename` - Migration file name (unique)
- `checksum` - MD5 hash of migration content
- `applied_at` - When migration was applied
- `execution_time_ms` - How long it took
- `scope` - Database scope (global/project)

## Safety Features

- **Idempotent:** Migrations can be re-run safely
- **Checksum validation:** Detects changes to migration files
- **Rollback on error:** Failed migrations are automatically rolled back
- **IF NOT EXISTS:** All CREATE INDEX statements use IF NOT EXISTS

## Expected Performance Improvements

- **Heuristics queries:** 10-100x faster for domain-based access
- **Learning queries:** 5-50x faster for type/domain filtering  
- **Decision queries:** 10-100x faster for status/domain access
- **Workflow queries:** 20-200x faster for run monitoring
- **Analytics queries:** 5-50x faster for time-based analysis

## Notes

- Indexes use SQLite syntax with `IF NOT EXISTS` for safety
- Composite indexes are optimized for common query patterns
- Timestamp-based indexes use descending order for recency queries
- The migration runner supports both global and project databases