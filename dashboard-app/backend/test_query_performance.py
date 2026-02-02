#!/usr/bin/env python3
"""
Comprehensive Performance Testing Script for Dashboard-App Backend

Tests query performance before and after index creation, measuring:
- Query execution time
- Data transfer size (specific columns vs SELECT *)
- Memory usage

Generates reports showing before/after comparisons and recommendations.
"""

import sqlite3
import time
import tracemalloc
import psutil
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import get_db, get_base_path, GLOBAL_DB_PATH


@dataclass
class TestResult:
    """Single test result with performance metrics."""

    test_name: str
    query: str
    execution_time_ms: float
    memory_usage_mb: float
    rows_returned: int
    columns_returned: int
    data_size_kb: float
    error: str = None


@dataclass
class PerformanceReport:
    """Complete performance test report."""

    timestamp: str
    test_results: List[TestResult]
    mock_data_stats: Dict[str, int]
    indexes_created: List[str]
    recommendations: List[str]
    summary: Dict[str, Any]


class PerformanceTester:
    """Main performance testing class."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or GLOBAL_DB_PATH
        self.test_results: List[TestResult] = []
        self.indexes_created = []

    def create_test_database(self):
        """Create a test database with mock data."""
        print("Creating test database with mock data...")

        # Remove existing test database
        test_db = self.db_path.parent / "test_performance.db"
        if test_db.exists():
            test_db.unlink()

        # Create fresh test database
        with sqlite3.connect(test_db) as conn:
            cursor = conn.cursor()

            # Create tables (using same schema as main database)
            self._create_tables(cursor)

            # Generate mock data
            stats = self._generate_mock_data(cursor)

            conn.commit()

        print(f"Test database created: {test_db}")
        return test_db, stats

    def _create_tables(self, cursor):
        """Create all necessary tables for testing."""
        # Simplified schema for performance testing
        cursor.execute("""
            CREATE TABLE heuristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                rule TEXT NOT NULL,
                explanation TEXT,
                confidence REAL DEFAULT 0.5,
                times_validated INTEGER DEFAULT 0,
                times_violated INTEGER DEFAULT 0,
                is_golden BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                domain TEXT,
                severity INTEGER DEFAULT 3,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE workflow_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_name TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                total_nodes INTEGER DEFAULT 0,
                completed_nodes INTEGER DEFAULT 0,
                failed_nodes INTEGER DEFAULT 0,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_name TEXT,
                metric_value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _generate_mock_data(self, cursor) -> Dict[str, int]:
        """Generate realistic mock data for performance testing."""
        stats = {}

        # Generate heuristics (1000 records)
        domains = [
            "react",
            "python",
            "testing",
            "api",
            "database",
            "frontend",
            "backend",
            "security",
        ]
        for i in range(1000):
            cursor.execute(
                """
                INSERT INTO heuristics (domain, rule, explanation, confidence, times_validated, times_violated, is_golden)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    domains[i % len(domains)],
                    f"Rule {i}: Always handle null checks before data processing",
                    f"Explanation {i}: This prevents runtime errors and improves reliability",
                    0.5 + (i % 50) / 100,
                    i % 10,
                    i % 3,
                    i % 100 == 0,
                ),
            )
        stats["heuristics"] = 1000

        # Generate learnings (2000 records)
        types = ["failure", "success", "observation"]
        for i in range(2000):
            cursor.execute(
                """
                INSERT INTO learnings (type, title, summary, domain, severity)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    types[i % len(types)],
                    f"Learning {i}: {types[i % len(types)]} in {domains[i % len(domains)]}",
                    f"Summary {i}: Discovered issue with data validation layer",
                    domains[i % len(domains)],
                    (i % 5) + 1,
                ),
            )
        stats["learnings"] = 2000

        # Generate workflow runs (5000 records)
        statuses = ["completed", "failed", "pending", "running"]
        for i in range(5000):
            started_days = i % 30
            completed_days = i % 29 if i % 30 != 0 else 0
            status = statuses[i % len(statuses)]
            total_nodes = 5 + (i % 10)

            cursor.execute(
                """
                INSERT INTO workflow_runs (workflow_name, status, total_nodes, completed_nodes, failed_nodes, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', '-' || ? || ' days'), datetime('now', '-' || ? || ' days'))
            """,
                (
                    f"Workflow_{i % 50}",
                    status,
                    total_nodes,
                    int(total_nodes * 0.8)
                    if status == "completed"
                    else int(total_nodes * 0.3),
                    int(total_nodes * 0.1) if status == "failed" else 0,
                    started_days,
                    completed_days,
                ),
            )
        stats["workflow_runs"] = 5000

        # Generate metrics (10000 records)
        metric_types = [
            "heuristic_validated",
            "heuristic_violated",
            "auto_failure_capture",
            "task_outcome",
        ]
        for i in range(10000):
            minutes_ago = i % 60
            cursor.execute(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, timestamp)
                VALUES (?, ?, ?, datetime('now', '-' || ? || ' minutes'))
            """,
                (
                    metric_types[i % len(metric_types)],
                    f"metric_{i}",
                    i * 1.5,
                    minutes_ago,
                ),
            )
        stats["metrics"] = 10000

        # Generate workflows (500 records)
        for i in range(500):
            cursor.execute(
                """
                INSERT INTO workflows (name, description)
                VALUES (?, ?)
            """,
                (
                    f"Workflow Definition {i}",
                    f"Description for workflow {i} with detailed explanation of its purpose and functionality",
                ),
            )
        stats["workflows"] = 500

        return stats

    @contextmanager
    def measure_performance(self):
        """Context manager to measure query performance."""
        # Start memory tracking
        tracemalloc.start()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.perf_counter()

        try:
            yield
        finally:
            end_time = time.perf_counter()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            execution_time = (end_time - start_time) * 1000  # ms
            memory_used = memory_after - memory_before
            peak_memory = peak / 1024 / 1024  # MB

            # Store for use in test methods
            self._last_measurement = {
                "execution_time_ms": execution_time,
                "memory_used_mb": memory_used,
                "peak_memory_mb": peak_memory,
            }

    def execute_test_query(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: Tuple = (),
        test_name: str = "",
    ) -> TestResult:
        """Execute a test query and measure performance."""
        try:
            with self.measure_performance():
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Calculate data size
                data_size = 0
                for row in rows:
                    data_size += sum(len(str(val)) for val in row)

                return TestResult(
                    test_name=test_name,
                    query=query,
                    execution_time_ms=self._last_measurement["execution_time_ms"],
                    memory_usage_mb=self._last_measurement["peak_memory_mb"],
                    rows_returned=len(rows),
                    columns_returned=len(rows[0]) if rows else 0,
                    data_size_kb=data_size / 1024,
                )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                query=query,
                execution_time_ms=0,
                memory_usage_mb=0,
                rows_returned=0,
                columns_returned=0,
                data_size_kb=0,
                error=str(e),
            )

    def test_stats_endpoint(self, conn: sqlite3.Connection) -> TestResult:
        """Test /api/v1/stats endpoint performance."""
        # Simulate consolidated stats query
        query = """
            SELECT
                (SELECT COUNT(*) FROM workflow_runs) as total_runs,
                (SELECT COUNT(*) FROM heuristics) as total_heuristics,
                (SELECT COUNT(*) FROM heuristics WHERE is_golden = 1) as golden_rules,
                (SELECT COUNT(*) FROM learnings) as total_learnings,
                (SELECT COUNT(*) FROM learnings WHERE type = 'failure') as failures,
                (SELECT COUNT(*) FROM learnings WHERE type = 'success') as successes,
                (SELECT AVG(confidence) FROM heuristics) as avg_confidence,
                (SELECT SUM(times_validated) FROM heuristics) as total_validations
        """
        return self.execute_test_query(conn, query, test_name="stats_endpoint")

    def test_learning_velocity_endpoint(self, conn: sqlite3.Connection) -> TestResult:
        """Test /api/v1/learning-velocity endpoint performance."""
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM heuristics
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        return self.execute_test_query(
            conn, query, test_name="learning_velocity_endpoint"
        )

    def test_heuristics_endpoint(self, conn: sqlite3.Connection) -> TestResult:
        """Test /api/v1/heuristics endpoint with pagination."""
        # Test optimized query (specific columns)
        query_optimized = """
            SELECT id, domain, rule, explanation, confidence, times_validated, 
                   times_violated, is_golden, created_at, updated_at
            FROM heuristics
            ORDER BY confidence DESC
            LIMIT 50 OFFSET 0
        """
        result_optimized = self.execute_test_query(
            conn, query_optimized, test_name="heuristics_endpoint_optimized"
        )

        # Test unoptimized query (SELECT *)
        query_unoptimized = """
            SELECT *
            FROM heuristics
            ORDER BY confidence DESC
            LIMIT 50 OFFSET 0
        """
        result_unoptimized = self.execute_test_query(
            conn, query_unoptimized, test_name="heuristics_endpoint_unoptimized"
        )

        # Return both for comparison
        self.test_results.extend([result_optimized, result_unoptimized])
        return result_optimized

    def test_learnings_endpoint(self, conn: sqlite3.Connection) -> TestResult:
        """Test /api/v1/knowledge/learnings endpoint with pagination."""
        # Test optimized query
        query_optimized = """
            SELECT id, type, title, summary, domain, created_at, updated_at
            FROM learnings
            ORDER BY created_at DESC
            LIMIT 50 OFFSET 0
        """
        result_optimized = self.execute_test_query(
            conn, query_optimized, test_name="learnings_endpoint_optimized"
        )

        # Test unoptimized query
        query_unoptimized = """
            SELECT *
            FROM learnings
            ORDER BY created_at DESC
            LIMIT 50 OFFSET 0
        """
        result_unoptimized = self.execute_test_query(
            conn, query_unoptimized, test_name="learnings_endpoint_unoptimized"
        )

        self.test_results.extend([result_optimized, result_unoptimized])
        return result_optimized

    def test_workflows_list_endpoint(self, conn: sqlite3.Connection) -> TestResult:
        """Test /api/v1/workflows/list endpoint performance."""
        query = """
            SELECT w.id, w.name, w.description, w.created_at, w.updated_at
            FROM workflows w
            ORDER BY w.created_at DESC
            LIMIT 100 OFFSET 0
        """
        return self.execute_test_query(conn, query, test_name="workflows_list_endpoint")

    def create_indexes(self, conn: sqlite3.Connection):
        """Create performance indexes."""
        print("Creating performance indexes...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_heuristics_confidence ON heuristics(confidence DESC)",
            "CREATE INDEX IF NOT EXISTS idx_heuristics_domain ON heuristics(domain)",
            "CREATE INDEX IF NOT EXISTS idx_heuristics_created ON heuristics(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(type)",
            "CREATE INDEX IF NOT EXISTS idx_learnings_domain ON learnings(domain)",
            "CREATE INDEX IF NOT EXISTS idx_learnings_created ON learnings(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_runs_created ON workflow_runs(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at DESC)",
        ]

        for index_sql in indexes:
            cursor = conn.cursor()
            cursor.execute(index_sql)
            index_name = index_sql.split("idx_")[1].split(" ")[0]
            self.indexes_created.append(f"idx_{index_name}")

        conn.commit()
        print(f"Created {len(indexes)} performance indexes")

    def run_performance_tests(
        self, test_db: Path
    ) -> Tuple[List[TestResult], List[TestResult]]:
        """Run performance tests before and after index creation."""
        # Test before indexes
        print("\n=== Running Tests BEFORE Index Creation ===")
        before_results = []

        with sqlite3.connect(test_db) as conn:
            # Test all endpoints
            before_results.append(self.test_stats_endpoint(conn))
            before_results.append(self.test_learning_velocity_endpoint(conn))
            before_results.append(self.test_heuristics_endpoint(conn))
            before_results.append(self.test_learnings_endpoint(conn))
            before_results.append(self.test_workflows_list_endpoint(conn))

        # Create indexes
        with sqlite3.connect(test_db) as conn:
            self.create_indexes(conn)

        # Test after indexes
        print("\n=== Running Tests AFTER Index Creation ===")
        after_results = []

        with sqlite3.connect(test_db) as conn:
            # Test all endpoints again
            after_results.append(self.test_stats_endpoint(conn))
            after_results.append(self.test_learning_velocity_endpoint(conn))
            after_results.append(self.test_heuristics_endpoint(conn))
            after_results.append(self.test_learnings_endpoint(conn))
            after_results.append(self.test_workflows_list_endpoint(conn))

        return before_results, after_results

    def generate_recommendations(
        self, before_results: List[TestResult], after_results: List[TestResult]
    ) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []

        # Calculate improvements
        for before, after in zip(before_results, after_results):
            if before.error or after.error:
                continue

            improvement = (
                (before.execution_time_ms - after.execution_time_ms)
                / before.execution_time_ms
            ) * 100

            if improvement > 50:
                recommendations.append(
                    f"✅ {after.test_name}: Excellent {improvement:.1f}% performance improvement with indexes"
                )
            elif improvement > 20:
                recommendations.append(
                    f"✅ {after.test_name}: Good {improvement:.1f}% performance improvement with indexes"
                )
            elif improvement < 0:
                recommendations.append(
                    f"⚠️  {after.test_name}: Performance degraded by {abs(improvement):.1f}% - investigate index strategy"
                )

        # Add specific recommendations based on query patterns
        recommendations.extend(
            [
                "📊 Use specific column selection instead of SELECT * to reduce data transfer",
                "📊 Implement proper pagination with LIMIT and OFFSET for large datasets",
                "📊 Consider adding covering indexes for frequently accessed columns",
                "📊 Monitor query execution plans regularly for optimization opportunities",
                "📊 Use parameterized queries to prevent SQL injection and improve cache performance",
                "📊 Consider database connection pooling for high-traffic scenarios",
            ]
        )

        return recommendations

    def generate_report(
        self,
        before_results: List[TestResult],
        after_results: List[TestResult],
        mock_stats: Dict[str, int],
    ) -> PerformanceReport:
        """Generate comprehensive performance report."""

        # Calculate summary statistics
        summary = {
            "total_tests": len(before_results),
            "avg_time_before": sum(
                r.execution_time_ms for r in before_results if not r.error
            )
            / len(before_results)
            if before_results
            else 0,
            "avg_time_after": sum(
                r.execution_time_ms for r in after_results if not r.error
            )
            / len(after_results)
            if after_results
            else 0,
            "overall_improvement": 0,
            "data_reduction_optimized": 0,
        }

        # Calculate overall improvement
        total_before = sum(r.execution_time_ms for r in before_results if not r.error)
        total_after = sum(r.execution_time_ms for r in after_results if not r.error)
        if total_before > 0:
            summary["overall_improvement"] = (
                (total_before - total_after) / total_before
            ) * 100

        # Calculate data reduction from optimized queries
        optimized = [
            r for r in self.test_results if "optimized" in r.test_name and not r.error
        ]
        unoptimized = [
            r for r in self.test_results if "unoptimized" in r.test_name and not r.error
        ]

        if optimized and unoptimized:
            avg_optimized = sum(r.data_size_kb for r in optimized) / len(optimized)
            avg_unoptimized = sum(r.data_size_kb for r in unoptimized) / len(
                unoptimized
            )
            if avg_unoptimized > 0:
                summary["data_reduction_optimized"] = (
                    (avg_unoptimized - avg_optimized) / avg_unoptimized
                ) * 100

        recommendations = self.generate_recommendations(before_results, after_results)

        return PerformanceReport(
            timestamp=datetime.now().isoformat(),
            test_results=before_results + after_results + self.test_results,
            mock_data_stats=mock_stats,
            indexes_created=self.indexes_created,
            recommendations=recommendations,
            summary=summary,
        )

    def save_report(self, report: PerformanceReport, output_path: str = None):
        """Save performance report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"performance_report_{timestamp}.json"

        # Convert report to JSON-serializable format
        report_dict = asdict(report)

        with open(output_path, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"\n📄 Performance report saved to: {output_path}")
        return output_path

    def print_summary(self, report: PerformanceReport):
        """Print a human-readable summary of performance test results."""
        print("\n" + "=" * 60)
        print("🚀 DASHBOARD APP BACKEND PERFORMANCE TEST RESULTS")
        print("=" * 60)

        print(f"\n📅 Test Date: {report.timestamp}")
        print(f"\n📊 Mock Data Generated:")
        for table, count in report.mock_data_stats.items():
            print(f"  - {table}: {count:,} records")

        print(f"\n📈 Performance Summary:")
        print(f"  - Total tests run: {report.summary['total_tests']}")
        print(
            f"  - Average query time (before): {report.summary['avg_time_before']:.2f}ms"
        )
        print(
            f"  - Average query time (after): {report.summary['avg_time_after']:.2f}ms"
        )
        print(
            f"  - Overall performance improvement: {report.summary['overall_improvement']:.1f}%"
        )

        if report.summary["data_reduction_optimized"] > 0:
            print(
                f"  - Data reduction with specific columns: {report.summary['data_reduction_optimized']:.1f}%"
            )

        print(f"\n🔧 Indexes Created ({len(report.indexes_created)}):")
        for idx in report.indexes_created:
            print(f"  - {idx}")

        print(f"\n💡 Recommendations:")
        for rec in report.recommendations[:5]:  # Show top 5
            print(f"  {rec}")

        if len(report.recommendations) > 5:
            print(f"  ... and {len(report.recommendations) - 5} more recommendations")

        print("\n" + "=" * 60)


def main():
    """Main function to run performance tests."""
    parser = argparse.ArgumentParser(
        description="Dashboard App Backend Performance Tester"
    )
    parser.add_argument(
        "--output", "-o", help="Output file for report (default: auto-generated)"
    )
    parser.add_argument("--db-path", help="Custom database path for testing")
    parser.add_argument(
        "--no-cleanup", action="store_true", help="Keep test database after testing"
    )

    args = parser.parse_args()

    # Initialize tester
    tester = PerformanceTester(args.db_path)

    try:
        # Create test database with mock data
        test_db, mock_stats = tester.create_test_database()

        # Run performance tests
        before_results, after_results = tester.run_performance_tests(test_db)

        # Generate report
        report = tester.generate_report(before_results, after_results, mock_stats)

        # Save report
        output_file = tester.save_report(report, args.output)

        # Print summary
        tester.print_summary(report)

        # Cleanup
        if not args.no_cleanup:
            test_db.unlink()
            print(f"\n🧹 Test database cleaned up: {test_db}")

        return output_file

    except Exception as e:
        print(f"\n❌ Error during performance testing: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
