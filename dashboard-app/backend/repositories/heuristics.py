"""
Concrete implementation of heuristics repository using SQLite database.

Implements IHeuristicsRepository interface to provide data access for heuristics
while using the connection pool for better concurrency.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from ..interfaces import IHeuristicsRepository
from ..utils.database import get_db_pool


class HeuristicsRepository(IHeuristicsRepository):
    """SQLite implementation of heuristics repository."""

    def __init__(self):
        self._pool = get_db_pool()

    async def find_all(
        self,
        domain: Optional[str] = None,
        is_golden: Optional[bool] = None,
        limit: int = 50,
        order_by: str = "confidence DESC",
    ) -> List[Dict[str, Any]]:
        """Find heuristics with optional filtering."""

        # Validate order_by to prevent SQL injection
        valid_order_by = [
            "confidence DESC",
            "confidence ASC",
            "created_at DESC",
            "created_at ASC",
            "updated_at DESC",
            "updated_at ASC",
        ]
        if order_by not in valid_order_by:
            order_by = "confidence DESC"

        # Build query dynamically
        conditions = []
        params = []

        if domain:
            conditions.append("domain = ?")
            params.append(domain)

        if is_golden is not None:
            conditions.append("is_golden = ?")
            params.append(1 if is_golden else 0)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT id, domain, rule, explanation, confidence,
                   times_validated, times_violated, is_golden, 
                   source_type, created_at, updated_at
            FROM heuristics
            {where_clause}
            ORDER BY {order_by}
            LIMIT ?
        """

        params.append(limit)

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    async def find_by_id(self, heuristic_id: int) -> Optional[Dict[str, Any]]:
        """Find heuristic by ID."""

        query = """
            SELECT id, domain, rule, explanation, confidence,
                   times_validated, times_violated, is_golden, 
                   source_type, created_at, updated_at
            FROM heuristics
            WHERE id = ?
        """

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (heuristic_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def create(self, heuristic_data: Dict[str, Any]) -> int:
        """Create new heuristic and return ID (UPSERT: reinforce if exists)."""

        query = """
            INSERT INTO heuristics (
                domain, rule, explanation, confidence,
                times_validated, times_violated, is_golden,
                source_type, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain, rule) DO UPDATE SET
                times_validated = times_validated + 1,
                confidence = MIN(1.0, confidence + 0.05),
                updated_at = excluded.updated_at
        """

        params = (
            heuristic_data.get("domain", "general"),
            heuristic_data.get("rule", ""),
            heuristic_data.get("explanation"),
            heuristic_data.get("confidence", 0.5),
            heuristic_data.get("times_validated", 0),
            heuristic_data.get("times_violated", 0),
            heuristic_data.get("is_golden", False),
            heuristic_data.get("source_type"),
            heuristic_data.get("created_at", datetime.now().isoformat()),
            heuristic_data.get("updated_at", datetime.now().isoformat()),
        )

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    async def update(self, heuristic_id: int, update_data: Dict[str, Any]) -> bool:
        """Update heuristic and return success status."""

        # Build dynamic update query
        set_clauses = []
        params = []

        updatable_fields = [
            "domain",
            "rule",
            "explanation",
            "confidence",
            "times_validated",
            "times_violated",
            "is_golden",
            "source_type",
        ]

        for field in updatable_fields:
            if field in update_data:
                set_clauses.append(f"{field} = ?")
                params.append(update_data[field])

        if not set_clauses:
            return False  # Nothing to update

        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        # Add heuristic_id for WHERE clause
        params.append(heuristic_id)

        query = f"""
            UPDATE heuristics
            SET {", ".join(set_clauses)}
            WHERE id = ?
        """

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    async def delete(self, heuristic_id: int) -> bool:
        """Delete heuristic and return success status."""

        query = "DELETE FROM heuristics WHERE id = ?"

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (heuristic_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def promote_to_golden(self, heuristic_id: int) -> bool:
        """Promote heuristic to golden rule."""

        query = """
            UPDATE heuristics
            SET is_golden = 1, updated_at = ?
            WHERE id = ? AND is_golden = 0
        """

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (datetime.now().isoformat(), heuristic_id))
            conn.commit()
            return cursor.rowcount > 0

    async def demote_from_golden(self, heuristic_id: int) -> bool:
        """Demote golden rule back to regular heuristic."""

        query = """
            UPDATE heuristics
            SET is_golden = 0, updated_at = ?
            WHERE id = ? AND is_golden = 1
        """

        async with self._pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (datetime.now().isoformat(), heuristic_id))
            conn.commit()
            return cursor.rowcount > 0


# Factory function for dependency injection
def create_heuristics_repository() -> IHeuristicsRepository:
    """Factory function to create heuristics repository."""
    return HeuristicsRepository()
