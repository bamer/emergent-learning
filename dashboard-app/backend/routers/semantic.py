"""
Semantic Search Router - Dashboard API for ELF semantic search

Provides endpoints for:
- Semantic search across indexed files (simplified - keyword based)
- Embedding statistics
- Search history
"""

import logging
import sqlite3
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/semantic", tags=["semantic"])

BASE_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = BASE_DIR / "memory" / "index.db"


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str
    top_k: int = 5
    source_type: Optional[str] = None
    min_similarity: float = 0.0


@router.get("/health")
async def semantic_health():
    """Check semantic search availability."""
    try:
        # Check if database exists and is accessible
        if not DB_PATH.exists():
            return {"status": "unavailable", "error": "Database not found"}

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        conn.close()

        return {"status": "healthy", "embeddings_count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/stats")
async def semantic_stats():
    """Get semantic search statistics."""
    try:
        if not DB_PATH.exists():
            return {"error": "Database not found", "total_embeddings": 0}

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Count embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]

        # Count by source type
        cursor.execute(
            "SELECT source_type, COUNT(*) FROM embeddings GROUP BY source_type"
        )
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_embeddings": total,
            "by_source_type": by_type,
            "semantic_available": True,
        }
    except Exception as e:
        return {"error": str(e), "total_embeddings": 0}


@router.post("/search")
async def semantic_search(request: SemanticSearchRequest):
    """
    Perform semantic search across indexed files.

    Note: This is a simplified keyword-based search for now.
    Full semantic search requires the embedding service to be running.
    """
    try:
        if not DB_PATH.exists():
            return {"error": "Database not found", "results": []}

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Parse search query
        query_lower = request.query.lower()
        query_words = set(query_lower.split())

        # Fetch ALL embeddings (without LIMIT) to calculate similarity for all
        where_clause = ""
        params = []

        if request.source_type:
            where_clause = "WHERE source_type = ?"
            params = [request.source_type]

        # Fetch embeddings - ALL of them, not limited by created_at
        sql = f"""
            SELECT id, source_id, source_type, metadata, created_at
            FROM embeddings
            {where_clause}
            ORDER BY created_at DESC
        """

        cursor.execute(sql, params)
        all_rows = cursor.fetchall()
        conn.close()

        # Calculate keyword-based similarity scores for ALL results
        results = []
        for row in all_rows:
            metadata = row["metadata"]
            if isinstance(metadata, str):
                try:
                    import json

                    metadata = json.loads(metadata)
                except:
                    metadata = {"text": metadata}

            # Build searchable text from multiple sources
            searchable_parts = []

            # 1. Source ID (filename)
            source_id = row["source_id"]
            if source_id:
                searchable_parts.append(source_id.lower())

            # 2. Source type
            source_type = row["source_type"]
            if source_type:
                searchable_parts.append(source_type.lower())

            # 3. Metadata content
            if isinstance(metadata, dict):
                # Add path
                if metadata.get("path"):
                    searchable_parts.append(metadata["path"].lower())
                # Add any text content
                if metadata.get("text"):
                    searchable_parts.append(metadata["text"].lower())
            elif isinstance(metadata, str):
                searchable_parts.append(metadata.lower())

            # Combine all searchable text
            full_text = " ".join(searchable_parts)
            content_words = set(full_text.split())

            # Calculate similarity with multiple factors
            similarity = 0.0

            # Factor 1: Word overlap (Jaccard)
            if query_words and content_words:
                intersection = query_words.intersection(content_words)
                union = query_words.union(content_words)
                word_similarity = len(intersection) / len(union) if union else 0.0
                similarity += word_similarity * 0.4  # 40% weight

            # Factor 2: Exact phrase match in full text
            if query_lower in full_text:
                similarity += 0.3  # 30% boost

            # Factor 3: Partial word matches (substring matching)
            for qword in query_words:
                if len(qword) > 2:  # Only for words longer than 2 chars
                    if qword in full_text:
                        similarity += 0.05  # Small boost per matching word

            # Factor 4: Filename matching
            for qword in query_words:
                if qword in source_id.lower():
                    similarity += 0.15  # 15% boost if word in filename

            # Cap at 1.0
            similarity = min(1.0, similarity)

            # Filter by min_similarity
            if similarity < request.min_similarity:
                continue

            results.append(
                {
                    "id": row["id"],
                    "source_id": row["source_id"],
                    "source_type": row["source_type"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                    "similarity": round(similarity, 3),
                    "text": full_text[:1000] if full_text else None,
                }
            )

        # Sort by similarity (highest first) - KEY FIX!
        results.sort(key=lambda x: x["similarity"], reverse=True)

        # Limit to top_k AFTER sorting by similarity
        results = results[: request.top_k]

        return {
            "query": request.query,
            "results": results,
            "count": len(results),
            "total_matches": len(results),
            "note": "Keyword-based similarity search",
        }

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return {"error": str(e), "results": []}


@router.get("/embeddings")
async def list_embeddings(source_type: Optional[str] = None, limit: int = 50):
    """List all indexed embeddings."""
    try:
        if not DB_PATH.exists():
            return {"embeddings": [], "count": 0, "error": "Database not found"}

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

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            metadata = row["metadata"]
            if isinstance(metadata, str):
                try:
                    import json

                    metadata = json.loads(metadata)
                except:
                    metadata = {"text": metadata}

            results.append(
                {
                    "id": row["id"],
                    "source_id": row["source_id"],
                    "source_type": row["source_type"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                }
            )

        return {"embeddings": results, "count": len(results)}

    except Exception as e:
        logger.error(f"List embeddings error: {e}")
        return {"embeddings": [], "count": 0, "error": str(e)}


@router.post("/index")
async def index_file(file_path: str, source_type: str = "file"):
    """
    Manually index a file into semantic search.
    Note: This is a placeholder - actual indexing requires the embedding service.
    """
    return {
        "status": "not_implemented",
        "message": "File indexing requires the semantic embedding service to be running",
        "file_path": file_path,
        "source_type": source_type,
    }
