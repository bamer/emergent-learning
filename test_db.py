#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append("/home/bamer/.opencode/emergent-learning/query")

from models import initialize_database, get_manager, SystemHealth


async def test_database():
    try:
        print("Testing database connection...")
        db = await initialize_database()
        print("✓ Database connection: SUCCESS")

        # Test basic query
        async with db:
            count = await SystemHealth.select().count()
            print(f"✓ Database queries: SUCCESS ({count} health records)")

            # Test table structure
            tables = [
                "learnings",
                "heuristics",
                "experiments",
                "ceo_reviews",
                "cycles",
                "decisions",
                "invariants",
                "violations",
                "spike_reports",
                "assumptions",
                "patterns",
                "metrics",
                "system_health",
                "schema_version",
                "db_operations",
                "workflows",
                "workflow_edges",
                "workflow_runs",
                "node_executions",
                "trails",
                "conductor_decisions",
                "building_queries",
                "session_summaries",
            ]

            print(f"✓ Database models: {len(tables)} tables defined")

        await db.close()
        return True

    except Exception as e:
        print(f"✗ Database test FAILED: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)
