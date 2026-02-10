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
import logging

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
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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


def generate_embedding_sync(text: str) -> Optional[np.ndarray]:
    """
    Synchronous embedding generation using requests.
    Avoids asyncio issues with Flask's event loop.
    """
    try:
        if not ollama_available():
            logger.error("Ollama not available")
            return None

        payload = {
            "model": DEFAULT_MODEL,
            "prompt": text[:10000],  # Limit text size
        }

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)

        if response.status_code != 200:
            logger.error(f"Ollama error: {response.status_code}")
            return None

        data = response.json()
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
def health_check():
    """Health check endpoint."""
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
def get_stats():
    """Get statistics about stored embeddings."""
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
                "recent_24h": recent,
                "model": DEFAULT_MODEL,
                "dimension": EMBEDDING_DIM,
            }
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/embed", methods=["POST"])
def generate_embedding():
    """Generate embedding for text."""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400

        text = data["text"]
        if not text.strip():
            return jsonify({"error": "Empty text"}), 400

        # Generate embedding
        embedding = generate_embedding_sync(text)

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
def store_embedding():
    """Store text with its embedding."""
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

        # Generate embedding
        embedding = generate_embedding_sync(text)

        if embedding is None:
            return jsonify({"error": "Failed to generate embedding"}), 500

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO embeddings (source_id, source_type, text_content, embedding, embedding_blob, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                source_id,
                source_type,
                text,
                json.dumps(embedding.tolist()),
                embedding.astype(np.float32).tobytes(),
                metadata,
                datetime.now().isoformat(),
            ),
        )

        embedding_id = cursor.lastrowid

        # Update FTS index
        cursor.execute(
            """
            INSERT INTO embeddings_fts(rowid, text_content, source_type)
            VALUES (?, ?, ?)
        """,
            (embedding_id, text, source_type),
        )

        conn.commit()
        conn.close()

        return jsonify(
            {
                "id": embedding_id,
                "source_id": source_id,
                "source_type": source_type,
                "dimension": len(embedding),
                "status": "stored",
            }
        )

    except Exception as e:
        logger.error(f"Store error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def semantic_search():
    """Semantic search across stored embeddings."""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "Missing 'query' field"}), 400

        query = data["query"]
        top_k = data.get("top_k", DEFAULT_TOP_K)
        source_type = data.get("source_type")  # Optional filter
        min_similarity = data.get("min_similarity", 0.0)  # Optional threshold

        if not query.strip():
            return jsonify({"error": "Empty query"}), 400

        # Generate query embedding
        query_embedding = generate_embedding_sync(query)

        if query_embedding is None:
            return jsonify({"error": "Failed to generate query embedding"}), 500

        # Search in database
        conn = get_db_connection()
        cursor = conn.cursor()

        # FTS5 candidate pre-filtering
        try:
            fts_query = " OR ".join(
                f'"{word}"'
                for word in query.split()
                if len(word) > 2 and word.isalnum()
            )
            if fts_query and source_type:
                cursor.execute(
                    """
                    SELECT rowid FROM embeddings_fts
                    WHERE embeddings_fts MATCH ? AND source_type = ?
                    LIMIT 200
                """,
                    (fts_query, source_type),
                )
            elif fts_query:
                cursor.execute(
                    """
                    SELECT rowid FROM embeddings_fts
                    WHERE embeddings_fts MATCH ?
                    LIMIT 200
                """,
                    (fts_query,),
                )
            else:
                cursor.execute("SELECT id FROM embeddings LIMIT 200")
            candidate_ids = [row[0] for row in cursor.fetchall()]
        except Exception:
            # FTS fallback: use direct query with limit
            cursor.execute("SELECT id FROM embeddings LIMIT 500")
            candidate_ids = [row[0] for row in cursor.fetchall()]

        if not candidate_ids:
            conn.close()
            return jsonify(
                {
                    "query": query,
                    "results": [],
                    "total_matches": 0,
                    "returned": 0,
                    "min_similarity_applied": min_similarity,
                }
            )

        placeholders = ",".join("?" * len(candidate_ids))
        cursor.execute(
            f"""
            SELECT id, source_id, source_type, text_content,
                   COALESCE(embedding_blob, NULL) as emb_blob,
                   embedding, metadata, created_at
            FROM embeddings WHERE id IN ({placeholders})
        """,
            candidate_ids,
        )

        results = []
        for row in cursor.fetchall():
            try:
                emb_blob = row["emb_blob"]
                if emb_blob:
                    stored_embedding = np.frombuffer(emb_blob, dtype=np.float32)
                else:
                    stored_embedding = np.array(json.loads(row["embedding"]))
                similarity = cosine_similarity(query_embedding, stored_embedding)

                results.append(
                    {
                        "id": row["id"],
                        "source_id": row["source_id"],
                        "source_type": row["source_type"],
                        "text": row["text_content"][:500],
                        "similarity": round(similarity, 4),
                        "metadata": json.loads(row["metadata"])
                        if row["metadata"]
                        else {},
                        "created_at": row["created_at"],
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to process embedding {row['id']}: {e}")
                continue

        conn.close()

        # Sort by similarity and take top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)

        # Filter by minimum similarity threshold
        if min_similarity > 0:
            results = [r for r in results if r["similarity"] >= min_similarity]

        top_results = results[:top_k]

        return jsonify(
            {
                "query": query,
                "results": top_results,
                "total_matches": len(results),
                "returned": len(top_results),
                "min_similarity_applied": min_similarity,
            }
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/search/file", methods=["POST"])
def search_by_file():
    """Search for content similar to a file."""
    try:
        data = request.get_json()
        if not data or "file_path" not in data:
            return jsonify({"error": "Missing 'file_path' field"}), 400

        file_path = data["file_path"]
        top_k = data.get("top_k", DEFAULT_TOP_K)

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return jsonify({"error": f"Failed to read file: {e}"}), 400

        # Generate embedding
        file_embedding = generate_embedding_sync(content[:10000])  # Limit size

        if file_embedding is None:
            return jsonify({"error": "Failed to generate embedding"}), 500

        # Search
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, source_id, source_type, text_content,
                   COALESCE(embedding_blob, NULL) as emb_blob,
                   embedding, metadata, created_at
            FROM embeddings LIMIT 500
        """)

        results = []
        for row in cursor.fetchall():
            try:
                emb_blob = row["emb_blob"]
                if emb_blob:
                    stored_embedding = np.frombuffer(emb_blob, dtype=np.float32)
                else:
                    stored_embedding = np.array(json.loads(row["embedding"]))
                similarity = cosine_similarity(file_embedding, stored_embedding)

                results.append(
                    {
                        "id": row["id"],
                        "source_id": row["source_id"],
                        "source_type": row["source_type"],
                        "text": row["text_content"][:500],
                        "similarity": round(similarity, 4),
                        "created_at": row["created_at"],
                    }
                )
            except:
                continue

        conn.close()

        results.sort(key=lambda x: x["similarity"], reverse=True)

        return jsonify(
            {
                "file": file_path,
                "results": results[:top_k],
                "total_matches": len(results),
            }
        )

    except Exception as e:
        logger.error(f"File search error: {e}")
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
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_fts 
            USING fts5(text_content, source_type, content=embeddings, content_rowid=id)
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Database init error: {e}")
        raise


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

    # Check Ollama
    if not ollama_available():
        logger.error("Ollama is not running! Start it with: ollama serve")
        sys.exit(1)

    # Initialize database
    init_database()

    # Start server
    logger.info(f"Starting ELF Semantic Daemon on {args.host}:{args.port}")
    logger.info(f"Model: {DEFAULT_MODEL} ({EMBEDDING_DIM} dimensions)")
    logger.info(f"Database: {DB_PATH}")

    if args.daemon:
        # Run in background
        import daemon

        with daemon.DaemonContext():
            app.run(host=args.host, port=args.port, threaded=True)
    else:
        app.run(host=args.host, port=args.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
