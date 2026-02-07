"""
Workflows Router - Workflow management.
"""

import sys
from pathlib import Path

from fastapi import APIRouter

from models import WorkflowCreate, ActionResult
from utils.database import get_db, dict_from_row

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from elf_logging import get_logger, log_critical, log_error, log_warning, log_info

    logger = get_logger("workflows")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("workflows")

router = APIRouter(prefix="/api/v1", tags=["workflows"])

# Path will be set from main.py
EMERGENT_LEARNING_PATH = None


def set_paths(elf_path: Path):
    """Set the paths for workflow operations."""
    global EMERGENT_LEARNING_PATH
    EMERGENT_LEARNING_PATH = elf_path


@router.get("/workflows")
async def get_workflows(limit: int = 100, offset: int = 0):
    """Get workflow definitions with pagination.

    Args:
        limit: Maximum number of workflows to return (default: 100)
        offset: Number of workflows to skip for pagination (default: 0)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # OPTIMIZATION: Replaced SELECT * with specific columns for better performance
        # OPTIMIZATION: Added pagination to prevent memory issues with large datasets
        cursor.execute(
            """
            SELECT w.id, w.name, w.description, w.nodes, w.edges, 
                   w.created_at, w.updated_at, COUNT(DISTINCT we.id) as edge_count
            FROM workflows w
            LEFT JOIN workflow_edges we ON w.id = we.workflow_id
            GROUP BY w.id, w.name, w.description, w.nodes, w.edges, w.created_at, w.updated_at
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )  # Parameter binding prevents SQL injection
        return [dict_from_row(r) for r in cursor]


@router.post("/workflows")
async def create_workflow(workflow: WorkflowCreate) -> ActionResult:
    """Create a new workflow."""
    try:
        if EMERGENT_LEARNING_PATH is None:
            return ActionResult(success=False, message="Paths not configured")

        sys.path.insert(0, str(EMERGENT_LEARNING_PATH / "conductor"))
        from conductor import Conductor

        conductor = Conductor()
        workflow_id = conductor.create_workflow(
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=workflow.edges,
        )

        return ActionResult(
            success=True,
            message=f"Created workflow '{workflow.name}'",
            data={"workflow_id": workflow_id},
        )
    except Exception as e:
        logger.error(f"Error creating workflow '{workflow.name}': {e}", exc_info=True)
        return ActionResult(
            success=False,
            message="Failed to create workflow. Please check workflow configuration.",
        )
