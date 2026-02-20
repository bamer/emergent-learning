import logging

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Persistence Router - API endpoints for saving data to the database.

Provides endpoints for:
- Creating trails
- Recording heuristics
- Adding timeline events
- Recording learnings
"""

import json

import requests
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_critical,
        log_error,
        log_warning,
        log_info,
    )

    logger = get_logger("persistence")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("persistence")

try:
    from utils.database import get_db, dict_from_row
except ImportError:
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from utils.database import get_db, dict_from_row

# Try to import EventChronicle for dual logging
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "event_chronicle"))
    from event_chronicle import EventChronicle

    HAS_EVENT_CHRONICLE = True
except ImportError:
    HAS_EVENT_CHRONICLE = False

# Ollama configuration
OLLAMA_SERVER = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

# Initialize EventChronicle if available
event_chronicle = EventChronicle() if HAS_EVENT_CHRONICLE else None

router = APIRouter(prefix="/api/v1/persistence", tags=["persistence"])

# ==============================================================================
# Models
# ==============================================================================


class TrailCreate(BaseModel):
    location: str
    location_type: str = "file"
    scent: str  # 'discovery', 'warning', 'blocker', 'hot', 'info'
    strength: int = 1
    agent_id: Optional[str] = None
    message: Optional[str] = None
    session_id: Optional[str] = None


class HeuristicCreate(BaseModel):
    domain: str
    rule: str
    explanation: Optional[str] = None
    confidence: float = 0.5
    source_type: str = "auto"  # 'auto', 'manual', 'ceo', 'agent'
    is_golden: bool = False


class TimelineEventCreate(BaseModel):
    event_type: str
    source: str
    summary: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status: str = "info"


class LearningCreate(BaseModel):
    title: str
    description: str
    category: str = "general"
    confidence: float = 0.5
    source: str = "dashboard"


# ==============================================================================
# Trails Endpoints
# ==============================================================================


@router.post("/trails")
async def create_trail(trail: TrailCreate):
    """Create a new trail in the database."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO trails (location, location_type, scent, strength, agent_id, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trail.location,
                    trail.location_type,
                    trail.scent,
                    trail.strength,
                    trail.agent_id,
                    trail.message,
                    datetime.now().isoformat(),
                ),
            )

            trail_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Created trail {trail_id}: {trail.scent} at {trail.location}")

            return {
                "status": "ok",
                "trail_id": trail_id,
                "message": f"Trail created successfully: {trail.scent}",
            }

    except Exception as e:
        logger.error(f"Error creating trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trails/batch")
async def create_trails_batch(trails: List[TrailCreate]):
    """Create multiple trails in a batch."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            created_ids = []

            for trail in trails:
                cursor.execute(
                    """
                    INSERT INTO trails (location, location_type, scent, strength, agent_id, message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trail.location,
                        trail.location_type,
                        trail.scent,
                        trail.strength,
                        trail.agent_id,
                        trail.message,
                        datetime.now().isoformat(),
                    ),
                )
                created_ids.append(cursor.lastrowid)

            conn.commit()

            logger.info(f"Created {len(created_ids)} trails in batch")

            return {"status": "ok", "trail_ids": created_ids, "count": len(created_ids)}

    except Exception as e:
        logger.error(f"Error creating trails batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Embedding Functions
# ==============================================================================


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Ollama nomic-embed-text model."""
    try:
        response = requests.post(
            f"{OLLAMA_SERVER}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=10,
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
    conn, source_id: int, source_type: str, text: str, metadata: Optional[Dict] = None
):
    """Save embedding to the embeddings table."""
    try:
        embedding_vector = generate_embedding(text)
        if not embedding_vector:
            logger.warning(f"No embedding generated for {source_type} {source_id}")
            return False

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO embeddings 
            (source_id, source_type, text_content, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                source_type,
                text,
                json.dumps(embedding_vector),
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat(),
            ),
        )
        logger.info(f"Saved embedding for {source_type} {source_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving embedding: {e}")
        return False


def generate_and_save_embedding_async(
    source_id: int, source_type: str, text: str, metadata: Optional[Dict] = None
):
    """Generate and save embedding asynchronously in background.

    This function runs in a background task and can take several minutes
    (embedding generation can take 5+ minutes).
    """
    try:
        logger.info(
            f"Starting async embedding generation for {source_type} {source_id}"
        )

        # Generate embedding (this can take 5+ minutes)
        embedding_vector = generate_embedding(text)

        if not embedding_vector:
            logger.warning(f"No embedding generated for {source_type} {source_id}")
            return False

        # Save to database in a new connection
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO embeddings 
                (source_id, source_type, text_content, embedding, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    source_type,
                    text,
                    json.dumps(embedding_vector),
                    json.dumps(metadata) if metadata else None,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

        logger.info(f"Successfully saved embedding for {source_type} {source_id}")
        return True
    except Exception as e:
        logger.error(
            f"Error in async embedding generation for {source_type} {source_id}: {e}"
        )
        return False


# ==============================================================================
# Heuristics Endpoints
# ==============================================================================


@router.post("/heuristics")
async def create_heuristic(
    heuristic: HeuristicCreate, background_tasks: BackgroundTasks
):
    """Create a new heuristic in the database with automatic embedding generation."""
    heuristic_id = None
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Check for duplicates
            cursor.execute(
                "SELECT id FROM heuristics WHERE domain = ? AND rule = ?",
                (heuristic.domain, heuristic.rule),
            )
            if cursor.fetchone():
                return {"status": "error", "message": "Heuristic already exists"}

            cursor.execute(
                """
                INSERT INTO heuristics 
                (domain, rule, explanation, confidence, times_validated, times_violated, 
                 is_golden, source_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
                """,
                (
                    heuristic.domain,
                    heuristic.rule,
                    heuristic.explanation,
                    heuristic.confidence,
                    heuristic.is_golden,
                    heuristic.source_type,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            heuristic_id = cursor.lastrowid

            # Commit immediately before embedding generation (which can take 5+ minutes)
            conn.commit()

            logger.info(f"Created heuristic {heuristic_id}: {heuristic.domain}")

        # Schedule embedding generation in background task
        # This prevents blocking the HTTP response
        embedding_text = (
            f"{heuristic.domain}: {heuristic.rule}. {heuristic.explanation or ''}"
        )
        background_tasks.add_task(
            generate_and_save_embedding_async,
            heuristic_id,
            "heuristic",
            embedding_text,
            {
                "domain": heuristic.domain,
                "confidence": heuristic.confidence,
                "is_golden": heuristic.is_golden,
            },
        )

        return {
            "status": "ok",
            "heuristic_id": heuristic_id,
            "message": f"Heuristic created successfully. Embedding will be generated in background.",
        }

    except Exception as e:
        logger.error(f"Error creating heuristic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heuristics/batch")
async def create_heuristics_batch(heuristics: List[HeuristicCreate]):
    """Create multiple heuristics in a batch with embeddings."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            created_ids = []
            skipped = 0
            embeddings_created = 0

            for heuristic in heuristics:
                # Check for duplicates
                cursor.execute(
                    "SELECT id FROM heuristics WHERE domain = ? AND rule = ?",
                    (heuristic.domain, heuristic.rule),
                )
                if cursor.fetchone():
                    skipped += 1
                    continue

                cursor.execute(
                    """
                    INSERT INTO heuristics 
                    (domain, rule, explanation, confidence, times_validated, times_violated, 
                     is_golden, source_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
                    """,
                    (
                        heuristic.domain,
                        heuristic.rule,
                        heuristic.explanation,
                        heuristic.confidence,
                        heuristic.is_golden,
                        heuristic.source_type,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )
                heuristic_id = cursor.lastrowid
                created_ids.append(heuristic_id)

                # Generate and save embedding for each heuristic
                embedding_text = f"{heuristic.domain}: {heuristic.rule}. {heuristic.explanation or ''}"
                if save_embedding(
                    conn,
                    heuristic_id,
                    "heuristic",
                    embedding_text,
                    metadata={
                        "domain": heuristic.domain,
                        "confidence": heuristic.confidence,
                        "is_golden": heuristic.is_golden,
                    },
                ):
                    embeddings_created += 1

            conn.commit()

            logger.info(
                f"Created {len(created_ids)} heuristics with {embeddings_created} embeddings, skipped {skipped} duplicates"
            )

            return {
                "status": "ok",
                "heuristic_ids": created_ids,
                "created": len(created_ids),
                "skipped": skipped,
                "embeddings_created": embeddings_created,
            }

    except Exception as e:
        logger.error(f"Error creating heuristics batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Timeline Events Endpoints
# ==============================================================================


@router.post("/timeline/events")
async def create_timeline_event(event: TimelineEventCreate):
    """Create a new event in the event_chronicle."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO event_chronicle 
                (timestamp, event_type, source, summary, data, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    event.event_type,
                    event.source,
                    event.summary,
                    json.dumps(event.data) if event.data else None,
                    event.status,
                    datetime.now().isoformat(),
                ),
            )

            event_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Created timeline event {event_id}: {event.event_type}")

            return {
                "status": "ok",
                "event_id": event_id,
                "message": f"Event created successfully: {event.event_type}",
            }

    except Exception as e:
        logger.error(f"Error creating timeline event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeline/events/batch")
async def create_timeline_events_batch(events: List[TimelineEventCreate]):
    """Create multiple timeline events in a batch."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            created_ids = []

            for event in events:
                cursor.execute(
                    """
                    INSERT INTO event_chronicle 
                    (timestamp, event_type, source, summary, data, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now().isoformat(),
                        event.event_type,
                        event.source,
                        event.summary,
                        json.dumps(event.data) if event.data else None,
                        event.status,
                        datetime.now().isoformat(),
                    ),
                )
                created_ids.append(cursor.lastrowid)

            conn.commit()

            logger.info(f"Created {len(created_ids)} timeline events")

            return {"status": "ok", "event_ids": created_ids, "count": len(created_ids)}

    except Exception as e:
        logger.error(f"Error creating timeline events batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Learnings Endpoints
# ==============================================================================


@router.post("/learnings")
async def create_learning(learning: LearningCreate):
    """Create a new learning in the database with automatic embedding generation."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO learnings 
                (title, description, category, confidence, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    learning.title,
                    learning.description,
                    learning.category,
                    learning.confidence,
                    learning.source,
                    datetime.now().isoformat(),
                ),
            )

            learning_id = cursor.lastrowid

            # Generate and save embedding for the learning
            embedding_text = f"{learning.title}. {learning.description} Category: {learning.category}"
            save_embedding(
                conn,
                learning_id,
                "learning",
                embedding_text,
                metadata={
                    "category": learning.category,
                    "confidence": learning.confidence,
                    "source": learning.source,
                },
            )

            conn.commit()

            logger.info(
                f"Created learning {learning_id} with embedding: {learning.title}"
            )

            return {
                "status": "ok",
                "learning_id": learning_id,
                "message": f"Learning created successfully with embedding: {learning.title}",
            }

    except Exception as e:
        logger.error(f"Error creating learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learnings/batch")
async def create_learnings_batch(learnings: List[LearningCreate]):
    """Create multiple learnings in a batch with embeddings."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            created_ids = []
            embeddings_created = 0

            for learning in learnings:
                cursor.execute(
                    """
                    INSERT INTO learnings 
                    (title, description, category, confidence, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        learning.title,
                        learning.description,
                        learning.category,
                        learning.confidence,
                        learning.source,
                        datetime.now().isoformat(),
                    ),
                )
                learning_id = cursor.lastrowid
                created_ids.append(learning_id)

                # Generate and save embedding
                embedding_text = f"{learning.title}. {learning.description} Category: {learning.category}"
                if save_embedding(
                    conn,
                    learning_id,
                    "learning",
                    embedding_text,
                    metadata={
                        "category": learning.category,
                        "confidence": learning.confidence,
                        "source": learning.source,
                    },
                ):
                    embeddings_created += 1

            conn.commit()

            logger.info(
                f"Created {len(created_ids)} learnings with {embeddings_created} embeddings"
            )

            return {
                "status": "ok",
                "learning_ids": created_ids,
                "count": len(created_ids),
                "embeddings_created": embeddings_created,
            }

    except Exception as e:
        logger.error(f"Error creating learnings batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))
