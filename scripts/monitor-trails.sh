#!/bin/bash
# Monitor and compare both trail systems

DB="/home/bamer/.opencode/emergent-learning/memory/index.db"

echo "🐜 Pheromone Trails Monitoring Tool"
echo "===================================="
echo ""
echo "📊 System Overview"
echo "-------------------"

# Count both tables
TRAILS_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM trails;")
PHEROMONE_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM pheromone_trails;")

echo "🕸️  trails (transient):     $TRAILS_COUNT records"
echo "🐜 pheromone_trails (persistence): $PHEROMONE_COUNT records"
echo ""

# Show trails schema differences
echo "📋 Schema Comparison"
echo "-------------------"
echo ""
echo "🕸️  trails table (transient, per-access):"
sqlite3 "$DB" ".schema trails" | grep -E "^\s+\w+" | sed 's/^/    /'
echo ""
echo "🐜 pheromone_trails table (aggregated, per-file):"
sqlite3 "$DB" ".schema pheromone_trails" | grep -E "^\s+\w+" | sed 's/^/    /'
echo ""

# Recent trails
echo "🕸️  Recent trails (last 5):"
sqlite3 "$DB" << 'SQL'
.mode box
.headers on
SELECT 
    substr(location, -35) as file,
    scent,
    strength,
    created_at as 'time'
FROM trails
ORDER BY created_at DESC
LIMIT 5;
SQL
echo ""

# Pheromone hotspots
echo "🐜 Pheromone Hotspots (top 10 by access):"
sqlite3 "$DB" << 'SQL'
.mode box
.headers on
SELECT 
    substr(file_path, -35) as file,
    tool_name as 'tool',
    access_count as 'count',
    total_weight as 'weight',
    datetime(last_access) as 'last_access'
FROM pheromone_trails
ORDER BY access_count DESC, total_weight DESC
LIMIT 10;
SQL
echo ""

# Usage analysis
echo "📈 Usage by Tool:"
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
SELECT 
    tool_name,
    COUNT(*) as files,
    SUM(access_count) as total_accesses,
    ROUND(AVG(total_weight), 2) as avg_weight
FROM pheromone_trails
GROUP BY tool_name
ORDER BY total_accesses DESC;
SQL
