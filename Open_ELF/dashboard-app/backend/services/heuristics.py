"""
Service layer for ELF dashboard business logic.

Separates business concerns from HTTP handling and data access.
Services orchestrate operations, enforce business rules, and manage transactions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from ..repositories import IHeuristicsRepository
from ..models import HeuristicUpdate, ActionResult


class HeuristicsService:
    """Service for heuristics business logic."""

    def __init__(self, repository: IHeuristicsRepository):
        self.repository = repository

    async def list_heuristics(
        self,
        domain: Optional[str] = None,
        is_golden: Optional[bool] = None,
        limit: int = 50,
        order_by: str = "confidence DESC",
    ) -> List[Dict[str, Any]]:
        """List heuristics with filtering and business validation."""

        # Business logic: Validate inputs
        if limit < 1 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")

        # Delegate to repository
        return await self.repository.find_all(
            domain=domain, is_golden=is_golden, limit=limit, order_by=order_by
        )

    async def get_heuristic_by_id(self, heuristic_id: int) -> Optional[Dict[str, Any]]:
        """Get single heuristic by ID."""

        if heuristic_id < 1:
            raise ValueError("Heuristic ID must be positive")

        return await self.repository.find_by_id(heuristic_id)

    async def create_heuristic(self, data: Dict[str, Any]) -> int:
        """Create new heuristic with business validation."""

        # Business validation
        required_fields = ["rule", "domain"]
        for field in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                raise ValueError(f"Field '{field}' is required and cannot be empty")

        # Business rule: Default confidence for new heuristics
        if "confidence" not in data:
            data["confidence"] = 0.5

        # Business rule: New heuristics are not golden by default
        if "is_golden" not in data:
            data["is_golden"] = False

        # Delegate to repository
        return await self.repository.create(data)

    async def update_heuristic(
        self, heuristic_id: int, update: HeuristicUpdate
    ) -> ActionResult:
        """Update heuristic with business logic."""

        # Get existing heuristic
        existing = await self.repository.find_by_id(heuristic_id)
        if not existing:
            return ActionResult(success=False, message="Heuristic not found")

        # Business logic: Only certain fields can be updated
        allowed_updates = {}
        if update.rule is not None and update.rule.strip():
            allowed_updates["rule"] = update.rule.strip()

        if update.explanation is not None and update.explanation.strip():
            allowed_updates["explanation"] = update.explanation.strip()

        if update.domain is not None and update.domain.strip():
            allowed_updates["domain"] = update.domain.strip()

        if update.is_golden is not None:
            # Business rule: Cannot promote to golden if confidence < 0.8
            if update.is_golden and existing.get("confidence", 0) < 0.8:
                return ActionResult(
                    success=False,
                    message="Cannot promote heuristic with confidence < 0.8",
                )
            allowed_updates["is_golden"] = update.is_golden

        if not allowed_updates:
            return ActionResult(success=False, message="No valid updates provided")

        # Delegate to repository
        success = await self.repository.update(heuristic_id, allowed_updates)

        return ActionResult(
            success=success,
            message="Heuristic updated successfully" if success else "Update failed",
        )

    async def promote_to_golden(self, heuristic_id: int) -> ActionResult:
        """Promote heuristic to golden rule with business validation."""

        # Get existing heuristic
        existing = await self.repository.find_by_id(heuristic_id)
        if not existing:
            return ActionResult(success=False, message="Heuristic not found")

        # Business rule: Check confidence threshold
        confidence = existing.get("confidence", 0)
        if confidence < 0.8:
            return ActionResult(
                success=False,
                message=f"Cannot promote heuristic with confidence {confidence:.2f}. Minimum required: 0.8",
            )

        # Business rule: Check if already golden
        if existing.get("is_golden", False):
            return ActionResult(
                success=False, message="Heuristic is already a golden rule"
            )

        # Delegate to repository
        success = await self.repository.promote_to_golden(heuristic_id)

        return ActionResult(
            success=success,
            message="Heuristic promoted to golden rule"
            if success
            else "Promotion failed",
        )

    async def demote_from_golden(self, heuristic_id: int) -> ActionResult:
        """Demote golden rule back to regular heuristic."""

        # Get existing heuristic
        existing = await self.repository.find_by_id(heuristic_id)
        if not existing:
            return ActionResult(success=False, message="Heuristic not found")

        # Business rule: Check if currently golden
        if not existing.get("is_golden", False):
            return ActionResult(success=False, message="Heuristic is not a golden rule")

        # Delegate to repository
        success = await self.repository.demote_from_golden(heuristic_id)

        return ActionResult(
            success=success,
            message="Heuristic demoted from golden rule"
            if success
            else "Demotion failed",
        )

    async def delete_heuristic(self, heuristic_id: int) -> ActionResult:
        """Delete heuristic with business validation."""

        # Get existing heuristic
        existing = await self.repository.find_by_id(heuristic_id)
        if not existing:
            return ActionResult(success=False, message="Heuristic not found")

        # Business rule: Cannot delete golden rules without special permission
        if existing.get("is_golden", False):
            return ActionResult(
                success=False,
                message="Cannot delete golden rules. Demote first, then delete.",
            )

        # Delegate to repository
        success = await self.repository.delete(heuristic_id)

        return ActionResult(
            success=success,
            message="Heuristic deleted successfully" if success else "Deletion failed",
        )


# Factory function for dependency injection
def create_heuristics_service(repository: IHeuristicsRepository) -> HeuristicsService:
    """Factory function to create heuristics service."""
    return HeuristicsService(repository)
