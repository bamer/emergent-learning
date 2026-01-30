"""
Semantic Search Router - Dashboard API for ELF semantic search

Provides endpoints for:
- Semantic search across indexed files
- Embedding statistics
- Search history
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query
import requests
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/semantic", tags=["semantic"])

BASE_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = BASE_DIR / "memory" / "index.db"
SEMANTIC_API = "http://localhost:5001"


@router.get("/health")
async def semantic_health():
    """Check semantic daemon health."""
    try:
        response = requests.get(f"{SEMANTIC_API}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@router.get("/stats")
async def semantic_stats():
    """Get semantic search statistics."""
    try:
        response = requests.get(f"{SEMANTIC_API}/stats", timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@router.post("/search")
async def semantic_search(
    query: str, top_k: int = 5, source_type: Optional[str] = None
):
    """
    Perform semantic search across indexed files.

    Args:
        query: Search query text
        top_k: Number of results to return (default: 5)
        source_type: Optional filter by file type (python, bash, etc.)
    """
    try:
        payload = {"query": query, "top_k": top_k}
        if source_type:
            payload["source_type"] = source_type

        response = requests.post(f"{SEMANTIC_API}/search", json=payload, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Search failed: {response.status_code}"}

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return {"error": str(e)}


@router.get("/embeddings")
async def list_embeddings(source_type: Optional[str] = None, limit: int = 50):
    """List all indexed embeddings."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if source_type:
            cursor.execute(
                """
                SELECT id, source_id, source_type, metadata, created_at
                FROM embeddings
                WHERE source_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (source_type, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, source_id, source_type, metadata, created_at
                FROM embeddings
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

        results = []
        for row in cursor.fetchall():
            import json

            results.append(
                {
                    "id": row["id"],
                    "source_id": row["source_id"],
                    "source_type": row["source_type"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                }
            )

        conn.close()

        return {"embeddings": results, "count": len(results)}

    except Exception as e:
        logger.error(f"List embeddings error: {e}")
        return {"error": str(e)}


@router.get("/trails")
async def get_pheromone_trails(limit: int = 20):
    """Get pheromone trails (hot files)."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT location, scent, strength, message, created_at
            FROM trails
            ORDER BY strength DESC, created_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "location": row["location"],
                    "scent": row["scent"],
                    "strength": row["strength"],
                    "message": row["message"],
                    "created_at": row["created_at"],
                }
            )

        conn.close()

        return {"trails": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Trails error: {e}")
        return {"error": str(e)}


@router.post("/index-file")
async def index_file(file_path: str):
    """
    Manually index a file into semantic search.

    Args:
        file_path: Relative path from ELF base (e.g., "agents/dashboard_sentinel.py")
    """
    try:
        full_path = BASE_DIR / file_path

        if not full_path.exists():
            return {"error": "File not found"}

        # Read file
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()[:8000]
        except:
            return {"error": "Cannot read file"}

        # Store via semantic API
        suffix = full_path.suffix
        file_type = {
            ".py": "python",
            ".sh": "bash",
            ".md": "markdown",
            ".json": "json",
        }.get(suffix, "text")

        response = requests.post(
            f"{SEMANTIC_API}/store",
            json={
                "text": f"File: {file_path}\nType: {file_type}\n\n{content}",
                "source_id": file_path,
                "source_type": file_type,
                "metadata": {"indexed_manually": True},
            },
            timeout=60,
        )

        if response.status_code == 200:
            return {"status": "indexed", "file": file_path}
        else:
            return {"error": f"Indexing failed: {response.status_code}"}

    except Exception as e:
        logger.error(f"Index file error: {e}")
        return {"error": str(e)}
