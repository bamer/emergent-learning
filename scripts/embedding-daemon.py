#!/usr/bin/env python3
"""
ELF Embedding Daemon - Automatic Learning Pipeline

Continuously monitors the database for unembedded content and generates
embeddings automatically. Fixes the broken learning loop where:
- Work happens → Heuristics created → **NEVER embedded** → Never retrieved

This daemon ensures:
1. All heuristics are embedded with semantic vectors
2. All golden rules are embedded for retrieval
3. All learnings are indexed for context
4. Embedding pipeline runs continuously (not just on-demand)

Usage:
    python embedding-daemon.py              # Run once (for testing)
    python embedding-daemon.py --daemon     # Run continuously
    python embedding-daemon.py --interval 300  # Custom interval (seconds)
"""

import json

import os
import sqlite3
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from Open_ELF.utils.elf_logging import get_logger
from typing import Optional, List, Dict, Any

import requests

# Configuration
BASE_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = BASE_DIR / "memory" / "index.db"
LOG_PATH = BASE_DIR / ".logs" / "embedding-daemon.log"
PID_FILE = BASE_DIR / ".embedding-daemon.pid"

OLLAMA_SERVER = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_INTERVAL = 300  # 5 minutes
BATCH_SIZE = 50  # Process in batches to avoid overwhelming Ollama

# Setup logging
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [embedding-daemon] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)
logger = get_logger("unknown")


class EmbeddingDaemon:
    """Daemon that continuously generates embeddings for unembedded content."""

    def __init__(self, interval: int = DEFAULT_INTERVAL):
        self.interval = interval
        self.db_path = DB_PATH
        self.ollama_server = OLLAMA_SERVER
        self.embedding_model = EMBEDDING_MODEL
        self.batch_size = BATCH_SIZE
        self.stats = {
            "heuristics_embedded": 0,
            "golden_rules_embedded": 0,
            "learnings_embedded": 0,
            "failures": 0,
            "last_run": None,
        }

    def check_ollama(self) -> bool:
        """Verify Ollama embedding server is available."""
        try:
            response = requests.get(f"{self.ollama_server}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if (
                    self.embedding_model in model_names
                    or f"{self.embedding_model}:latest" in model_names
                ):
                    return True
                else:
                    logger.error(
                        f"Embedding model '{self.embedding_model}' not found in Ollama"
                    )
                    return False
            return False
        except Exception as e:
            logger.error(f"Ollama server not accessible: {e}")
            return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector using Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_server}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=30,
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("embedding")
            else:
                logger.warning(f"Ollama embedding failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            return None

    def save_embedding(
        self,
        conn,
        source_id: str,
        source_type: str,
        text: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Save embedding to database."""
        try:
            cursor = conn.cursor()

            # Check if already embedded
            cursor.execute(
                "SELECT id FROM embeddings WHERE source_type = ? AND source_id = ?",
                (source_type, str(source_id)),
            )
            if cursor.fetchone():
                return True  # Already exists

            # Generate embedding
            embedding_vector = self.generate_embedding(text)
            if not embedding_vector:
                return False

            # Save to database
            cursor.execute(
                """
                INSERT INTO embeddings
                (source_id, source_type, text_content, embedding, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(source_id),
                    source_type,
                    text,
                    json.dumps(embedding_vector),
                    json.dumps(metadata) if metadata else None,
                    datetime.now().isoformat(),
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Error saving embedding: {e}")
            return False

    def embed_heuristics(self, conn) -> int:
        """Embed unembedded heuristics. Returns count embedded."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT h.id, h.domain, h.rule, h.explanation, h.confidence, h.source_type
            FROM heuristics h
            LEFT JOIN embeddings e ON e.source_type = 'heuristic' 
                AND e.source_id = CAST(h.id AS TEXT)
            WHERE e.id IS NULL
            ORDER BY h.created_at DESC
            LIMIT ?
            """,
            (self.batch_size,),
        )
        heuristics = cursor.fetchall()

        if not heuristics:
            return 0

        count = 0
        for h in heuristics:
            text = f"{h['domain']}: {h['rule']}. {h['explanation'] or ''}".strip()
            metadata = {
                "domain": h["domain"],
                "confidence": h["confidence"],
                "source_type": h["source_type"],
            }
            if self.save_embedding(conn, h["id"], "heuristic", text, metadata):
                count += 1
                logger.debug(f"Embedded heuristic {h['id']}: {h['rule'][:50]}...")

        return count

    def embed_golden_rules(self, conn) -> int:
        """Embed unembedded golden rules. Returns count embedded."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT gr.id, gr.rule, gr.category, gr.confidence, gr.explanation
            FROM golden_rules gr
            LEFT JOIN embeddings e ON e.source_type = 'golden_rule'
                AND e.source_id = CAST(gr.id AS TEXT)
            WHERE e.id IS NULL
            ORDER BY gr.confidence DESC
            LIMIT ?
            """,
            (self.batch_size,),
        )
        rules = cursor.fetchall()

        if not rules:
            return 0

        count = 0
        for r in rules:
            text = f"{r['category']}: {r['rule']}. {r['explanation'] or ''}".strip()
            metadata = {
                "category": r["category"],
                "confidence": r["confidence"],
                "is_golden": True,
            }
            if self.save_embedding(conn, r["id"], "golden_rule", text, metadata):
                count += 1
                logger.debug(f"Embedded golden rule {r['id']}: {r['rule'][:50]}...")

        return count

    def embed_learnings(self, conn) -> int:
        """Embed unembedded learnings. Returns count embedded."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT l.id, l.title, l.description, l.summary, l.outcome, 
                   l.domain, l.severity, l.type
            FROM learnings l
            LEFT JOIN embeddings e ON e.source_type = 'learning'
                AND e.source_id = CAST(l.id AS TEXT)
            WHERE e.id IS NULL
            ORDER BY l.created_at DESC
            LIMIT ?
            """,
            (self.batch_size,),
        )
        learnings = cursor.fetchall()

        if not learnings:
            return 0

        count = 0
        for l in learnings:
            # Combine fields for embedding text
            parts = []
            if l["title"]:
                parts.append(l["title"])
            if l["description"]:
                parts.append(l["description"])
            if l["summary"]:
                parts.append(l["summary"])
            if l["outcome"]:
                parts.append(f"Outcome: {l['outcome']}")

            text = f"{l['domain'] or 'general'}: {l['type'] or 'learning'} - {' '.join(parts)}".strip()

            metadata = {
                "domain": l["domain"],
                "type": l["type"],
                "severity": l["severity"],
            }
            if self.save_embedding(conn, l["id"], "learning", text, metadata):
                count += 1
                logger.debug(f"Embedded learning {l['id']}: {text[:50]}...")

        return count

    def get_embedding_stats(self, conn) -> Dict[str, int]:
        """Get current embedding statistics."""
        cursor = conn.cursor()
        stats = {}

        # Total embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        stats["total_embeddings"] = cursor.fetchone()[0]

        # Embeddings by type
        cursor.execute(
            "SELECT source_type, COUNT(*) FROM embeddings GROUP BY source_type"
        )
        for row in cursor.fetchall():
            stats[f"{row[0]}_embedded"] = row[1]

        # Unembedded heuristics
        cursor.execute(
            """
            SELECT COUNT(*) FROM heuristics h
            LEFT JOIN embeddings e ON e.source_type = 'heuristic'
                AND e.source_id = CAST(h.id AS TEXT)
            WHERE e.id IS NULL
            """
        )
        stats["heuristics_unembedded"] = cursor.fetchone()[0]

        # Unembedded golden rules
        cursor.execute(
            """
            SELECT COUNT(*) FROM golden_rules gr
            LEFT JOIN embeddings e ON e.source_type = 'golden_rule'
                AND e.source_id = CAST(gr.id AS TEXT)
            WHERE e.id IS NULL
            """
        )
        stats["golden_rules_unembedded"] = cursor.fetchone()[0]

        return stats

    def run_once(self) -> Dict[str, int]:
        """Run one embedding cycle. Returns statistics."""
        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return {"error": "database_not_found"}

        if not self.check_ollama():
            logger.error("Ollama server not available, skipping cycle")
            return {"error": "ollama_unavailable"}

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        try:
            results = {
                "heuristics": self.embed_heuristics(conn),
                "golden_rules": self.embed_golden_rules(conn),
                "learnings": self.embed_learnings(conn),
                "timestamp": datetime.now().isoformat(),
            }

            conn.commit()

            # Update stats
            self.stats["heuristics_embedded"] += results["heuristics"]
            self.stats["golden_rules_embedded"] += results["golden_rules"]
            self.stats["learnings_embedded"] += results["learnings"]
            self.stats["last_run"] = datetime.now().isoformat()

            total = sum(
                [results["heuristics"], results["golden_rules"], results["learnings"]]
            )

            if total > 0:
                logger.info(
                    f"Embedded {total} items: "
                    f"{results['heuristics']} heuristics, "
                    f"{results['golden_rules']} golden rules, "
                    f"{results['learnings']} learnings"
                )
            else:
                logger.debug("No new content to embed")

            # Get updated stats
            results["current_stats"] = self.get_embedding_stats(conn)

            return results

        except Exception as e:
            logger.error(f"Error during embedding cycle: {e}")
            self.stats["failures"] += 1
            return {"error": str(e)}
        finally:
            conn.close()

    def run_daemon(self):
        """Run continuously as daemon."""
        logger.info(f"Starting embedding daemon (interval: {self.interval}s)")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Ollama: {self.ollama_server}")
        logger.info(f"Model: {self.embedding_model}")

        # Write PID file
        PID_FILE.write_text(str(os.getpid()))

        try:
            while True:
                self.run_once()
                logger.debug(f"Sleeping for {self.interval}s...")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """Get daemon statistics."""
        return self.stats.copy()


def main():
    parser = argparse.ArgumentParser(description="ELF Embedding Daemon")
    parser.add_argument(
        "--daemon", "-d", action="store_true", help="Run continuously as daemon"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Interval between cycles in seconds (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--status", "-s", action="store_true", help="Show daemon status"
    )
    parser.add_argument(
        "--once", "-o", action="store_true", help="Run once and exit (for testing)"
    )

    args = parser.parse_args()

    daemon = EmbeddingDaemon(interval=args.interval)

    if args.status:
        if PID_FILE.exists():
            pid = PID_FILE.read_text().strip()
            print(f"Daemon is running (PID: {pid})")
            print(f"Log file: {LOG_PATH}")
        else:
            print("Daemon is not running")

        # Show current embedding stats
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            stats = daemon.get_embedding_stats(conn)
            conn.close()
            print(f"\nEmbedding Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

    elif args.once:
        print("Running embedding cycle once...")
        results = daemon.run_once()
        print(f"\nResults: {json.dumps(results, indent=2)}")

    elif args.daemon:
        daemon.run_daemon()

    else:
        # Default: run once
        print("Running embedding cycle (use --daemon for continuous mode)...")
        results = daemon.run_once()
        print(f"\nResults: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()
