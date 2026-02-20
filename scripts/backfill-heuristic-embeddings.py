#!/usr/bin/env python3
"""Backfill missing heuristic embeddings in the global ELF database."""

import json

import sqlite3
from datetime import datetime
from pathlib import Path
from Open_ELF.utils.elf_logging import get_logger

import requests

BASE_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = BASE_DIR / "memory" / "index.db"

OLLAMA_SERVER = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [backfill-heuristic-embeddings] %(message)s",
)
logger = get_logger("unknown")


def generate_embedding(text: str):
    """Generate embedding using Ollama nomic-embed-text model."""
    try:
        response = requests.post(
            f"{OLLAMA_SERVER}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30,
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("embedding")
        logger.warning(f"Ollama embedding failed: HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
    return None


def save_embedding(conn, heuristic_id, text, metadata=None) -> bool:
    """Save heuristic embedding to the embeddings table."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM embeddings WHERE source_type = ? AND source_id = ?",
            ("heuristic", str(heuristic_id)),
        )
        if cursor.fetchone():
            return True

        embedding_vector = generate_embedding(text)
        if not embedding_vector:
            logger.warning(f"No embedding generated for heuristic {heuristic_id}")
            return False

        cursor.execute(
            """
            INSERT INTO embeddings
            (source_id, source_type, text_content, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(heuristic_id),
                "heuristic",
                text,
                json.dumps(embedding_vector),
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat(),
            ),
        )
        return True
    except Exception as e:
        logger.warning(f"Error saving embedding: {e}")
        return False


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT h.id, h.domain, h.rule, h.explanation, h.confidence, h.source_type
        FROM heuristics h
        LEFT JOIN embeddings e
            ON e.source_type = 'heuristic'
            AND e.source_id = CAST(h.id AS TEXT)
        WHERE e.id IS NULL
        ORDER BY h.created_at DESC
        """
    )
    heuristics = cursor.fetchall()

    if not heuristics:
        logger.info("No missing heuristic embeddings found.")
        conn.close()
        return

    logger.info("Missing heuristic embeddings: %s", len(heuristics))

    created = 0
    skipped = 0
    for h in heuristics:
        text = f"{h['domain']}: {h['rule']}. {h['explanation'] or ''}".strip()
        ok = save_embedding(
            conn,
            h["id"],
            text,
            metadata={
                "domain": h["domain"],
                "confidence": h["confidence"],
                "source_type": h["source_type"],
            },
        )
        if ok:
            created += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()

    logger.info("Backfill complete: created=%s skipped=%s", created, skipped)


if __name__ == "__main__":
    main()
