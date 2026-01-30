#!/usr/bin/env python3
"""
Index all important ELF files into semantic search database

Usage:
    python index_elf_files.py [--reset]
"""

import sys
import requests
from pathlib import Path
from datetime import datetime
import argparse

BASE_DIR = Path.home() / ".opencode" / "emergent-learning"
SEMANTIC_API = "http://localhost:5001"

# Files to index
FILES_TO_INDEX = [
    # Core agents
    "agents/dashboard_sentinel.py",
    "agents/agent_execution_engine.py",
    "agents/pattern_response_handler.py",
    "agents/opencode_client.py",
    "agents/sentinel_startup.py",
    # Core system
    "src/orchestrator.py",
    "src/semantic/daemon.py",
    "query/ollama_embedder.py",
    "query/query.py",
    "query/checkin.py",
    # Hooks
    "hooks/learning-loop/post_tool_learning.py",
    "hooks/learning-loop/record_pheromone.py",
    "hooks/learning-loop/trail_helper.py",
    # Scripts
    "scripts/record-success.sh",
    "scripts/record-failure.sh",
    "scripts/validate-heuristic.py",
    "scripts/enable-wal-mode.sh",
    "scripts/db-queue.py",
    # Dashboard
    "dashboard-app/backend/main.py",
    "dashboard-app/backend/utils/database.py",
    # Memory
    "memory/elmemory.db",
]


def index_file(file_path: str) -> bool:
    """Index a single file into semantic database."""
    full_path = BASE_DIR / file_path

    if not full_path.exists():
        print(f"  ⚠️  Not found: {file_path}")
        return False

    try:
        # Read file (handle binary files gracefully)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()[:8000]  # First 8000 chars
        except:
            print(f"  ⚠️  Cannot read: {file_path}")
            return False

        # Determine file type
        suffix = full_path.suffix
        file_type = {
            ".py": "python",
            ".sh": "bash",
            ".md": "markdown",
            ".json": "json",
            ".db": "database",
            ".sql": "sql",
        }.get(suffix, "text")

        # Store via API
        response = requests.post(
            f"{SEMANTIC_API}/store",
            json={
                "text": f"File: {file_path}\nType: {file_type}\n\n{content}",
                "source_id": file_path,
                "source_type": file_type,
                "metadata": {
                    "path": str(full_path),
                    "size": len(content),
                    "indexed_at": datetime.now().isoformat(),
                },
            },
            timeout=60,
        )

        if response.status_code == 200:
            print(f"  ✅ Indexed: {file_path}")
            return True
        else:
            print(f"  ❌ Failed: {file_path} (HTTP {response.status_code})")
            return False

    except Exception as e:
        print(f"  ❌ Error: {file_path} - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Index ELF files into semantic search")
    parser.add_argument(
        "--reset", action="store_true", help="Clear existing embeddings first"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🔍 ELF Semantic Indexer")
    print("=" * 60 + "\n")

    # Check daemon
    try:
        response = requests.get(f"{SEMANTIC_API}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Semantic daemon not responding")
            return 1
        data = response.json()
        print(f"✅ Daemon ready: {data['embeddings_stored']} existing embeddings\n")
    except Exception as e:
        print(f"❌ Cannot connect to daemon: {e}")
        return 1

    # Reset if requested
    if args.reset:
        print("🗑️  Clearing existing embeddings...")
        # Note: Would need DELETE endpoint, skipping for now
        print("   (Reset not implemented - appending to existing)\n")

    # Index files
    print(f"📁 Indexing {len(FILES_TO_INDEX)} files...\n")

    success_count = 0
    fail_count = 0

    for file_path in FILES_TO_INDEX:
        if index_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    # Show stats
    print("\n" + "=" * 60)
    print(f"✅ Successfully indexed: {success_count} files")
    print(f"❌ Failed: {fail_count} files")
    print("=" * 60 + "\n")

    # Test search
    print("🔎 Testing semantic search...")
    test_queries = [
        "agent orchestration",
        "database connection",
        "monitoring system",
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
                    print(f"\n  '{query}':")
                    for r in results[:2]:
                        print(f"    → {r['source_id']} ({r['similarity']:.3f})")
        except Exception as e:
            print(f"  ❌ Search error: {e}")

    print("\n✨ Indexing complete!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
