#!/usr/bin/env python3
"""
Test script for creating pheromone trails and embeddings

Usage:
    python test_trails_and_embeddings.py

This script:
1. Creates sample trails in the database
2. Generates embeddings for key files
3. Tests semantic search
4. Displays statistics
"""

import sys
import sqlite3
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
import random

# Configuration
BASE_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = BASE_DIR / "memory" / "index.db"
SEMANTIC_API = "http://localhost:5001"

# Sample files to create trails for
SAMPLE_FILES = [
    ("src/semantic/daemon.py", "discovery", "Created semantic search daemon"),
    ("agents/dashboard_sentinel.py", "hot", "Main monitoring agent"),
    ("agents/agent_execution_engine.py", "hot", "Agent orchestration system"),
    ("memory/index.db", "hot", "Central database"),
    ("query/ollama_embedder.py", "discovery", "Ollama embedding backend"),
    ("hooks/learning-loop/post_tool_learning.py", "discovery", "Auto-learning hook"),
    ("dashboard-app/backend/main.py", "hot", "Dashboard backend"),
    ("scripts/record-success.sh", "discovery", "Success recording script"),
    ("scripts/validate-heuristic.py", "discovery", "Heuristic validation"),
    ("agents/opencode_client.py", "hot", "OpenCode API client"),
    ("agents/pattern_response_handler.py", "discovery", "Pattern handler"),
    ("src/orchestrator.py", "hot", "Main orchestrator"),
]


def create_trails():
    """Create sample trails in the database."""
    print("🐜 Creating pheromone trails...")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    created_count = 0
    for file_path, scent, message in SAMPLE_FILES:
        try:
            # Create trail with varying strength and timestamps
            strength = round(random.uniform(0.7, 1.0), 2)
            created_at = datetime.now() - timedelta(hours=random.randint(0, 48))
            expires_at = created_at + timedelta(days=7)

            cursor.execute(
                """
                INSERT INTO trails (location, location_type, scent, strength, 
                                  agent_id, message, created_at, expires_at)
                VALUES (?, 'file', ?, ?, 'test-agent', ?, ?, ?)
            """,
                (
                    file_path,
                    scent,
                    strength,
                    message,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )

            created_count += 1
            print(f"  ✓ Trail: {file_path} ({scent}, strength={strength})")

        except Exception as e:
            print(f"  ✗ Failed: {file_path} - {e}")

    conn.commit()
    conn.close()

    print(f"\n✅ Created {created_count} trails\n")
    return created_count


def store_embeddings():
    """Store embeddings for key files via semantic daemon."""
    print("🔍 Storing embeddings...")

    stored_count = 0
    for file_path, _, description in SAMPLE_FILES[:6]:  # First 6 files
        full_path = BASE_DIR / file_path

        if not full_path.exists():
            print(f"  ⚠ File not found: {file_path}")
            continue

        try:
            # Read file content
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()[:5000]  # First 5000 chars

            # Store via API
            response = requests.post(
                f"{SEMANTIC_API}/store",
                json={
                    "text": f"File: {file_path}\n\n{content}",
                    "source_id": file_path,
                    "source_type": "file",
                    "metadata": {"description": description, "size": len(content)},
                },
                timeout=30,
            )

            if response.status_code == 200:
                stored_count += 1
                print(f"  ✓ Embedded: {file_path}")
            else:
                print(f"  ✗ Failed: {file_path} - {response.status_code}")

        except Exception as e:
            print(f"  ✗ Error: {file_path} - {e}")

    print(f"\n✅ Stored {stored_count} embeddings\n")
    return stored_count


def test_semantic_search():
    """Test semantic search functionality."""
    print("🔎 Testing semantic search...")

    test_queries = [
        "agent orchestration",
        "database locking",
        "monitoring system",
        "semantic search",
        "learning framework",
    ]

    for query in test_queries:
        try:
            response = requests.post(
                f"{SEMANTIC_API}/search", json={"query": query, "top_k": 3}, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if results:
                    print(f"\n  Query: '{query}'")
                    print(f"  Found {len(results)} results:")
                    for r in results[:2]:
                        print(f"    - {r['source_id']} (similarity: {r['similarity']})")
                else:
                    print(f"  Query: '{query}' - No results")
            else:
                print(f"  ✗ Search failed for '{query}': {response.status_code}")

        except Exception as e:
            print(f"  ✗ Error searching '{query}': {e}")

    print()


def show_statistics():
    """Display database statistics."""
    print("📊 Database Statistics:")
    print("=" * 50)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Trails
    cursor.execute("SELECT COUNT(*) FROM trails")
    trail_count = cursor.fetchone()[0]

    cursor.execute("SELECT scent, COUNT(*) FROM trails GROUP BY scent")
    by_scent = cursor.fetchall()

    # Embeddings
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    embedding_count = cursor.fetchone()[0]

    cursor.execute("SELECT source_type, COUNT(*) FROM embeddings GROUP BY source_type")
    by_source = cursor.fetchall()

    # Heuristics
    cursor.execute("SELECT COUNT(*) FROM heuristics")
    heuristic_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 1")
    golden_count = cursor.fetchone()[0]

    # Learnings
    cursor.execute("SELECT COUNT(*) FROM learnings")
    learning_count = cursor.fetchone()[0]

    conn.close()

    print(f"\n🐜 Trails: {trail_count}")
    for scent, count in by_scent:
        print(f"   - {scent}: {count}")

    print(f"\n🔍 Embeddings: {embedding_count}")
    for source, count in by_source:
        print(f"   - {source}: {count}")

    print(f"\n🧠 Heuristics: {heuristic_count} ({golden_count} golden)")
    print(f"📚 Learnings: {learning_count}")

    print("\n" + "=" * 50)


def main():
    print("\n" + "=" * 60)
    print("🧪 ELF TEST: Trails & Embeddings")
    print("=" * 60 + "\n")

    # Check daemon
    try:
        response = requests.get(f"{SEMANTIC_API}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Semantic daemon is running\n")
        else:
            print("❌ Semantic daemon not responding\n")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to semantic daemon: {e}")
        print(f"   Start it with: python src/semantic/daemon.py\n")
        return 1

    # Create trails
    trail_count = create_trails()

    # Store embeddings
    embedding_count = store_embeddings()

    # Test search
    test_semantic_search()

    # Show stats
    show_statistics()

    print("\n✨ Test complete!")
    print(f"   Created: {trail_count} trails, {embedding_count} embeddings\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
