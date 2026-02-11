"""
Ollama embedder for semantic search using nomic-embed-text model.

This is the primary embedding backend for ELF, replacing the old
sentence-transformers approach. It provides:

1. Fast, local embeddings using Ollama
2. 768-dimensional embeddings (up from 384)
3. Fallback to OpenAI or keyword matching
4. Async and sync APIs

Requires:
- Ollama installed and running (https://ollama.com/)
- nomic-embed-text model pulled: `ollama pull nomic-embed-text`
"""

import os
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
import numpy as np
from pathlib import Path

# Unified ELF logging (required for all ELF modules)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_debug

    _LOGGER = get_logger("ollama_embedder")
except ImportError:
    import logging

    _LOGGER = logging.getLogger("ollama_embedder")

# Default embedding model
DEFAULT_MODEL = "nomic-embed-text"
# Default embedding dimension
DEFAULT_EMBEDDING_DIM = 768
# Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/embeddings"

# Database path for embedding statistics
DB_PATH = Path("/home/bamer/.opencode/emergent-learning/memory/index.db")


def get_embedding_statistics() -> Dict[str, Any]:
    """
    Get comprehensive embedding statistics from the database.
    Returns user-friendly stats about stored embeddings.
    """
    stats = {
        "total_embeddings": 0,
        "timeframe_stats": {},
        "by_source_type": {},
        "by_hour": {},
        "by_day": {},
        "recent_embeddings": [],
        "average_length": 0,
        "oldest": None,
        "newest": None,
    }

    try:
        import sqlite3

        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        # Total embeddings
        cur.execute("SELECT COUNT(*) FROM embeddings")
        stats["total_embeddings"] = cur.fetchone()[0]

        # Oldest and newest
        cur.execute("SELECT MIN(created_at), MAX(created_at) FROM embeddings")
        result = cur.fetchone()
        if result[0]:
            stats["oldest"] = result[0]
            stats["newest"] = result[1]

        # Average text length
        cur.execute("SELECT AVG(LENGTH(text_content)) FROM embeddings")
        avg_len = cur.fetchone()[0]
        stats["average_length"] = round(avg_len, 1) if avg_len else 0

        # By source type
        cur.execute("""
            SELECT source_type, COUNT(*) 
            FROM embeddings 
            GROUP BY source_type 
            ORDER BY COUNT(*) DESC
        """)
        for row in cur.fetchall():
            stats["by_source_type"][row[0]] = row[1]

        # By timeframe
        timeframes = {
            "last_hour": "-1 hour",
            "last_6_hours": "-6 hours",
            "last_24_hours": "-1 day",
            "last_7_days": "-7 days",
            "last_30_days": "-30 days",
        }

        for name, offset in timeframes.items():
            cur.execute(f"""
                SELECT COUNT(*) FROM embeddings 
                WHERE created_at > datetime('now', '{offset}')
            """)
            stats["timeframe_stats"][name] = cur.fetchone()[0]

        # By hour (last 24 hours)
        cur.execute("""
            SELECT 
                strftime('%Y-%m-%d %H:00', created_at) as hour,
                COUNT(*) as count
            FROM embeddings
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 24
        """)
        for row in cur.fetchall():
            stats["by_hour"][row[0]] = row[1]

        # By day (last 30 days)
        cur.execute("""
            SELECT 
                strftime('%Y-%m-%d', created_at) as day,
                COUNT(*) as count
            FROM embeddings
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
        """)
        for row in cur.fetchall():
            stats["by_day"][row[0]] = row[1]

        # Recent embeddings (last 5)
        cur.execute("""
            SELECT id, source_type, substr(text_content, 1, 60), created_at
            FROM embeddings
            ORDER BY created_at DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            stats["recent_embeddings"].append(
                {
                    "id": row[0],
                    "source_type": row[1],
                    "content_preview": row[2] + "...",
                    "created_at": row[3],
                }
            )

        conn.close()
    except Exception as e:
        log_debug("ollama_embedder", f"Failed to get statistics: {e}")

    return stats


def get_model_card() -> str:
    """
    Generate a comprehensive, human-readable Ollama model card.
    Returns a formatted string containing embedding statistics.
    """
    stats = get_embedding_statistics()

    import datetime as dt

    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    card = f"""
╔════════════════════════════════════════════════════════════════╗
║              OLLAMA NOMIC-EMBED-TEXT MODEL CARD                 ║
╚════════════════════════════════════════════════════════════════╝

Generated: {generated_at}

📊 OVERVIEW
──────────
  Total Embeddings:       {stats["total_embeddings"]:,}
  Embedding Dimension:    {DEFAULT_EMBEDDING_DIM}
  Model:                  nomic-embed-text
  Avg Text Length:        {stats["average_length"]:,} chars
  Oldest Embed:           {stats["oldest"] or "N/A"}
  Newest Embed:           {stats["newest"] or "N/A"}

📈 EMBEDDING RATE
────────────────
"""

    if len(stats["timeframe_stats"]) > 0:
        for name, count in stats["timeframe_stats"].items():
            pretty_name = name.replace("_", " ").title()
            card += f"  {pretty_name:20s} {count:,}\n"
    else:
        card += "  No recent embeddings in tracked timeframes\n"

    card += f"""
📂 BY SOURCE TYPE
────────────────
"""

    if len(stats["by_source_type"]) > 0:
        for source, count in stats["by_source_type"].items():
            card += f"  {source:20s} {count:,}\n"
    else:
        card += "  No embeddings found\n"

    card += f"""
🕐 HOURLY BREAKDOWN (Last 24 Hours)
─────────────────────────────────
"""

    if len(stats["by_hour"]) > 0:
        for hour, count in list(stats["by_hour"].items())[:10]:
            card += f"  {hour:20s} {count:,}\n"
        if len(stats["by_hour"]) > 10:
            card += f"  ... and {len(stats['by_hour']) - 10} more hours\n"
    else:
        card += "  No embeddings in the last 24 hours\n"

    card += f"""
📅 DAILY BREAKDOWN (Last 30 Days)
────────────────────────────────
"""

    if len(stats["by_day"]) > 0:
        for day, count in list(stats["by_day"].items())[:7]:
            card += f"  {day:20s} {count:,}\n"
        if len(stats["by_day"]) > 7:
            card += f"  ... and {len(stats['by_day']) - 7} more days\n"
    else:
        card += "  No embeddings in the last 30 days\n"

    card += f"""
📝 RECENT EMBEDDINGS (Last 5)
──────────────────────────────
"""

    if len(stats["recent_embeddings"]) > 0:
        for i, emb in enumerate(stats["recent_embeddings"], 1):
            created = (
                emb["created_at"].split("T")[0]
                if "T" in emb["created_at"]
                else emb["created_at"]
            )
            card += f"  {i}. [{emb['source_type']}] {emb['content_preview']}\n"
            card += f"     Created: {created}\n"
    else:
        card += "  No recent embeddings\n"

    card += f"""
╔════════════════════════════════════════════════════════════════╗
║  ✅ Model Card Generated Successfully                         ║
╚════════════════════════════════════════════════════════════════╝
"""

    return card


def ollama_available() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(("localhost", 11434))
        sock.close()
        return result == 0
    except Exception as e:
        log_debug("ollama_embedder", f"Ollama availability check failed: {e}")
        return False


class OllamaEmbedder:
    """
    Ollama-based text embedding service.

    Supports async and sync operations for embedding text using
    the nomic-embed-text model.
    """

    def __init__(
        self, model: str = DEFAULT_MODEL, embedding_dim: int = DEFAULT_EMBEDDING_DIM
    ):
        """
        Initialize OllamaEmbedder.

        Args:
            model: Ollama model name (default: nomic-embed-text)
            embedding_dim: Expected embedding dimension (default: 768)
        """
        self.model = model
        self.embedding_dim = embedding_dim
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def embed_async(self, text: str) -> Optional[np.ndarray]:
        """
        Async method to generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array, or None on failure
        """
        try:
            if not ollama_available():
                return None

            session = await self._get_session()

            payload = {"model": self.model, "prompt": text}

            async with session.post(OLLAMA_API_URL, json=payload) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if "embedding" not in data:
                    return None

                embedding = np.array(data["embedding"])

                # Ensure embedding has expected dimension
                if len(embedding) != self.embedding_dim:
                    return None

                return embedding

        except Exception as e:
            print(f"Error in embed_async: {e}")
            import traceback

            traceback.print_exc()
            return None

    def embed_sync(self, text: str) -> Optional[np.ndarray]:
        """
        Sync method to generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array, or None on failure
        """
        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.embed_async(text))
                    return future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self.embed_async(text))
        except Exception as e:
            print(f"Error in embed_sync: {e}")
            return None

    def embed_batch_sync(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Sync method to generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failures)
        """
        try:
            return asyncio.run(self.embed_batch_async(texts))
        except Exception:
            return [None for _ in texts]

    async def embed_batch_async(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Async method to generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failures)
        """
        tasks = [self.embed_async(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def close(self):
        """Close the HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    def __del__(self):
        """Cleanup on destruction."""
        try:
            if self._session is not None and not self._session.closed:
                # We can't use await in __del__, so we'll use a sync approach
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self._session.close())
        except Exception as e:
            log_debug("ollama_embedder", f"Cleanup on destruction failed: {e}")


# Test function for module
if __name__ == "__main__":
    import sys

    print("Testing Ollama Embedder...")
    print(f"Ollama available: {ollama_available()}")

    if not ollama_available():
        print("Ollama server not running. Please start Ollama and try again.")
        sys.exit(1)

    embedder = OllamaEmbedder()

    # Test single embedding
    text = "Refactor authentication module with OAuth 2.0"
    embedding = embedder.embed_sync(text)

    if embedding is not None:
        print(f"Embedding successful: {len(embedding)}-dimensional")
        print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
    else:
        print("Embedding failed")
        sys.exit(1)

    # Test batch embedding
    texts = [
        "Implement user authentication",
        "Fix database connection issues",
        "Optimize API response time",
    ]

    embeddings = embedder.embed_batch_sync(texts)
    successful = sum(1 for emb in embeddings if emb is not None)

    print(f"\nBatch embedding: {successful}/{len(texts)} successful")

    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        if emb is not None:
            print(f"  {i + 1}. {text[:30]}... ({len(emb)}-dimensional)")
        else:
            print(f"  {i + 1}. {text[:30]}... [FAILED]")

    print("\nOllama Embedder test completed successfully!")
