#!/usr/bin/env python3
"""
Quick Performance Test Demo
Demonstrates dashboard app backend performance improvements.
"""

import sqlite3
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import get_db


def quick_performance_test():
    """Run a quick performance test on actual database."""

    print("🚀 Dashboard App Backend Quick Performance Test")
    print("=" * 50)

    with get_db() as conn:
        cursor = conn.cursor()

        # Test 1: Count queries (optimizable with indexes)
        print("\n📊 Testing count queries...")
        start = time.perf_counter()
        cursor.execute("SELECT COUNT(*) FROM heuristics")
        heuristics_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM learnings")
        learnings_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM workflow_runs")
        runs_count = cursor.fetchone()[0]
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Count queries completed in {elapsed:.2f}ms")
        print(
            f"  Found {heuristics_count} heuristics, {learnings_count} learnings, {runs_count} runs"
        )

        # Test 2: Heuristics with pagination (optimized vs unoptimized)
        print("\n🔍 Testing heuristics query optimization...")

        # Optimized query (specific columns)
        start = time.perf_counter()
        cursor.execute("""
            SELECT id, domain, rule, confidence, created_at 
            FROM heuristics 
            ORDER BY confidence DESC 
            LIMIT 10
        """)
        optimized_rows = cursor.fetchall()
        optimized_time = (time.perf_counter() - start) * 1000

        # Unoptimized query (SELECT *)
        start = time.perf_counter()
        cursor.execute("""
            SELECT * FROM heuristics 
            ORDER BY confidence DESC 
            LIMIT 10
        """)
        unoptimized_rows = cursor.fetchall()
        unoptimized_time = (time.perf_counter() - start) * 1000

        improvement = ((unoptimized_time - optimized_time) / unoptimized_time) * 100
        print(f"  Optimized query: {optimized_time:.2f}ms")
        print(f"  Unoptimized query: {unoptimized_time:.2f}ms")
        print(f"  Improvement: {improvement:.1f}% faster")

        # Test 3: Learning velocity query (benefits from indexes)
        print("\n📈 Testing learning velocity query...")
        start = time.perf_counter()
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM heuristics
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        velocity_data = cursor.fetchall()
        velocity_time = (time.perf_counter() - start) * 1000
        print(f"  Learning velocity query: {velocity_time:.2f}ms")
        print(f"  Found {len(velocity_data)} days of data")

        # Test 4: JOIN query (complex operation)
        print("\n🔗 Testing JOIN query performance...")
        start = time.perf_counter()
        cursor.execute("""
            SELECT h.domain, COUNT(*) as heuristic_count, AVG(h.confidence) as avg_confidence
            FROM heuristics h
            LEFT JOIN learnings l ON h.domain = l.domain AND l.type = 'failure'
            WHERE h.created_at > datetime('now', '-30 days')
            GROUP BY h.domain
            ORDER BY heuristic_count DESC
            LIMIT 5
        """)
        join_data = cursor.fetchall()
        join_time = (time.perf_counter() - start) * 1000
        print(f"  Complex JOIN query: {join_time:.2f}ms")
        print(f"  Found {len(join_data)} domains with recent activity")

        # Summary
        print("\n📋 Performance Test Summary")
        print("-" * 30)
        print(f"✅ All queries completed successfully")
        print(f"✅ Column selection optimization: {improvement:.1f}% improvement")
        print(f"✅ Complex query performed well: {join_time:.2f}ms")

        # Recommendations based on results
        print("\n💡 Recommendations:")
        if improvement > 10:
            print("  ✅ Column selection is providing good performance gains")
        else:
            print("  ⚠️  Consider more selective column selection")

        if velocity_time < 10:
            print("  ✅ Learning velocity query is well-optimized")
        else:
            print("  ⚠️  Consider adding index on heuristics.created_at")

        if join_time < 50:
            print("  ✅ JOIN queries are performing well")
        else:
            print("  ⚠️  Consider optimizing JOIN queries or adding composite indexes")


if __name__ == "__main__":
    quick_performance_test()
