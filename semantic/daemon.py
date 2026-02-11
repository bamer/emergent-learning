#!/usr/bin/env python3
"""
Semantic Search Daemon - Flask API for ELF embeddings

Provides REST API endpoints for:
- Generating embeddings via Ollama (nomic-embed-text)
- Storing and retrieving embeddings from SQLite
- Semantic search with similarity scoring
- Health checks and status

Port: 5001
Endpoints:
  POST /embed         - Generate embedding for text
  POST /store         - Store text with embedding
  POST /search        - Semantic search
  GET  /health        - Health check
  GET  /stats         - Statistics

Usage:
  python daemon.py              # Start daemon
  python daemon.py --daemon     # Background mode
"""

import os
import sys
import json
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import argparse
import aiohttp  # FOR ASYNC HTTP REQUESTS (MANDATORY per ELF guidelines)

# Add parent directories to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from query.ollama_embedder import (
    OllamaEmbedder,
    ollama_available,
    DEFAULT_MODEL,
    DEFAULT_EMBEDDING_DIM,
    OLLAMA_API_URL,
)

# Setup unified ELF logging
try:
    from Open_ELF.utils.elf_logging import get_logger

    logger = get_logger("semantic-daemon")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Configuration
DB_PATH = BASE_DIR / "memory" / "index.db"
EMBEDDING_DIM = DEFAULT_EMBEDDING_DIM
DEFAULT_TOP_K = 5

# Initialize embedder
embedder = OllamaEmbedder()


def get_db_connection():
    """Get SQLite connection with WAL mode."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


async def generate_embedding_async(text: str) -> Optional[np.ndarray]:
    """
    Async embedding generation using aiohttp.
    Follows ELF async/await pattern (MANDATORY).
    """
    try:
        if not ollama_available():
            logger.error("Ollama not available")
            return None

        payload = {
            "model": DEFAULT_MODEL,
            "prompt": text[:10000],  # Limit text size
        }

        # Use aiohttp with relaxed timeout (120 seconds per guidelines)
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(OLLAMA_API_URL, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Ollama error: {response.status}")
                    return None

                data = await response.json()
                if "embedding" not in data:
                    logger.error("No embedding in response")
                    return None

                embedding = np.array(data["embedding"])

                # Ensure embedding has expected dimension
                if len(embedding) != EMBEDDING_DIM:
                    logger.error(
                        f"Wrong embedding dimension: {len(embedding)} vs {EMBEDDING_DIM}"
                    )
                    return None

                return embedding

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


@app.route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint - async."""
    ollama_status = ollama_available()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        embedding_count = cursor.fetchone()[0]
        conn.close()
        db_status = True
    except Exception as e:
        embedding_count = 0
        db_status = False
        logger.error(f"DB health check failed: {e}")

    return jsonify(
        {
            "status": "healthy" if ollama_status and db_status else "degraded",
            "ollama": ollama_status,
            "database": db_status,
            "model": DEFAULT_MODEL,
            "embedding_dim": EMBEDDING_DIM,
            "embeddings_stored": embedding_count,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/stats", methods=["GET"])
async def get_stats():
    """Get statistics about stored embeddings - async."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Count by source
        cursor.execute(
            "SELECT source_type, COUNT(*) FROM embeddings GROUP BY source_type"
        )
        by_source = {row[0]: row[1] for row in cursor.fetchall()}

        # Total count
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]

        # Recent additions (last 24h)
        cursor.execute("""
            SELECT COUNT(*) FROM embeddings
            WHERE created_at > datetime('now', '-1 day')
        """)
        recent = cursor.fetchone()[0]

        conn.close()

        return jsonify(
            {
                "total_embeddings": total,
                "by_source": by_source,
                "dimension": EMBEDDING_DIM,
                "recent_24h": recent,
            }
        )

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/embed", methods=["POST"])
async def generate_embedding():
    """Generate embedding for text - async."""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400

        text = data["text"]
        if not text.strip():
            return jsonify({"error": "Empty text"}), 400

        # Generate embedding (async function)
        embedding = await generate_embedding_async(text)

        if embedding is None:
            return jsonify({"error": "Failed to generate embedding"}), 500

        return jsonify(
            {
                "embedding": embedding.tolist(),
                "dimension": len(embedding),
                "model": DEFAULT_MODEL,
            }
        )

    except Exception as e:
        logger.error(f"Embed error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/store", methods=["POST"])
async def store_embedding():
    """Store text with its embedding - async."""
    try:
        data = request.get_json()
        required = ["text", "source_id", "source_type"]

        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing '{field}' field"}), 400

        text = data["text"]
        source_id = data["source_id"]
        source_type = data["source_type"]
        metadata = json.dumps(data.get("metadata", {}))

        # Generate embedding (async function)
        embedding = await generate_embedding_async(text)

        if embedding is None:
            return jsonify({"error": "Failed to generate embedding"}), 500

        conn = get_db_connection()
        cursor = conn.cursor()

        # Store embedding
        cursor.execute(
            """
            INSERT INTO embeddings (source_id, source_type, text_content, embedding, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (source_id, source_type, text, json.dumps(embedding.tolist()), metadata),
        )

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "embedding_id": source_id})

    except Exception as e:
        logger.error(f"Store error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
async def semantic_search():
    """Perform semantic search - async."""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "Missing 'query' field"}), 400

        query = data["query"]
        top_k = data.get("top_k", DEFAULT_TOP_K)
        source_type_filter = data.get("source_type")

        # Generate embedding for query (async)
        query_embedding = await generate_embedding_async(query)

        if query_embedding is None:
            return jsonify({"error": "Failed to generate query embedding"}), 500

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all embeddings
        if source_type_filter:
            cursor.execute(
                "SELECT id, source_id, source_type, text_content, embedding FROM embeddings WHERE source_type = ?",
                (source_type_filter,),
            )
        else:
            cursor.execute(
                "SELECT id, source_id, source_type, text_content, embedding FROM embeddings"
            )

        results = []
        for row in cursor.fetchall():
            try:
                stored_embedding = np.array(json.loads(row["embedding"]))
                similarity = cosine_similarity(query_embedding, stored_embedding)

                results.append(
                    {
                        "id": row["id"],
                        "source_id": row["source_id"],
                        "source_type": row["source_type"],
                        "content": row["text_content"],
                        "similarity": similarity,
                    }
                )
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                continue

        conn.close()

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:top_k]

        return jsonify({"query": query, "results": results, "count": len(results)})

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500


def init_database():
    """Initialize database tables if they don't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if embeddings table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                text_content TEXT NOT NULL,
                embedding TEXT NOT NULL,  -- JSON array
                metadata TEXT,  -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_source 
            ON embeddings(source_type, source_id)
        """)

        # Add BLOB column for faster embedding storage (migration-safe)
        try:
            cursor.execute("ALTER TABLE embeddings ADD COLUMN embedding_blob BLOB")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # FTS5 virtual table for candidate pre-filtering
        # Handle potential shadow table corruption from crashes
        fts5_shadow_tables = [
            "embeddings_fts_data",
            "embeddings_fts_idx",
            "embeddings_fts_docsize",
            "embeddings_fts_config",
        ]

        # Check for orphaned shadow tables (FTS5 virtual table missing but shadows exist)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'embeddings_fts%'
            ORDER BY name
        """)
        existing_fts_tables = [row[0] for row in cursor.fetchall()]

        has_virtual = "embeddings_fts" in existing_fts_tables
        has_shadows = any(t in existing_fts_tables for t in fts5_shadow_tables)

        # Inconsistency detected: shadows exist but no virtual table
        if has_shadows and not has_virtual:
            logger.warning(
                "FTS5 shadow table inconsistency detected: orphaned shadow tables found, rebuilding FTS5 index"
            )
            # Drop all orphaned shadow tables
            for table in fts5_shadow_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info("Dropped orphaned FTS5 shadow tables")
            conn.commit()

        # Create FTS5 virtual table
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_fts
                USING fts5(text_content, source_type, content=embeddings, content_rowid=id)
            """)
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                logger.warning(
                    f"FTS5 creation failed (shadow conflict), forcing full rebuild: {e}"
                )
                # Force rebuild: drop virtual and all shadow tables
                cursor.execute("DROP TABLE IF EXISTS embeddings_fts")
                for table in fts5_shadow_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                cursor.execute("""
                    CREATE VIRTUAL TABLE embeddings_fts
                    USING fts5(text_content, source_type, content=embeddings, content_rowid=id)
                """)
                logger.info("FTS5 index rebuilt successfully after shadow conflict")
            else:
                raise

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Database init error: {e}")
        raise


@app.route("/file_search", methods=["GET"])
async def file_search():
    """File search endpoint - async."""
    try:
        query = request.args.get("q", "")
        if not query:
            return jsonify({"error": "Missing query"}), 400

        # Use semantic search
        query_embedding = await generate_embedding_async(query)
        if query_embedding is None:
            return jsonify({"error": "Failed to generate query embedding"}), 500

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, source_id, source_type, text_content, embedding FROM embeddings"
        )
        results = []
        for row in cursor.fetchall():
            try:
                stored_embedding = np.array(json.loads(row["embedding"]))
                similarity = cosine_similarity(query_embedding, stored_embedding)
                if similarity > 0.5:  # Threshold
                    results.append(
                        {
                            "id": row["id"],
                            "source_id": row["source_id"],
                            "source_type": row["source_type"],
                            "content": row["text_content"],
                            "similarity": similarity,
                        }
                    )
            except Exception:
                continue

        results.sort(key=lambda x: x["similarity"], reverse=True)
        conn.close()

        return jsonify({"results": results[:10]})

    except Exception as e:
        logger.error(f"File search error: {e}")
        return jsonify({"error": str(e)}), 500


def main():
    parser = argparse.ArgumentParser(description="ELF Semantic Search Daemon")
    parser.add_argument(
        "--port", type=int, default=5001, help="Port to run on (default: 5001)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    args = parser.parse_args()

    # Initialize database
    init_database()

    # Start server
    logger.info(f"Starting ELF Semantic Daemon on {args.host}:{args.port}")
    logger.info(f"Model: {DEFAULT_MODEL} ({EMBEDDING_DIM} dimensions)")
    logger.info(f"Database: {DB_PATH}")

    # Run Flask app
    app.run(host=args.host, port=args.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
