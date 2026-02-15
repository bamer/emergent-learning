#!/usr/bin/env python3
"""
Initialise les golden rules dans la base de données.
À exécuter UNE SEULE FOIS lors de l'installation/setup.
"""

import sqlite3
import re
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent
DB_PATH = ELF_DIR / "memory" / "index.db"
MARKDOWN_FILE = ELF_DIR / "memory" / "golden-rules.md"

# Setup logging
try:
    from Open_ELF.utils.elf_logging import get_logger

    logger = get_logger("init_golden_rules")
except ImportError:
    import logging

    logger = logging.getLogger("init_golden_rules")




def init_golden_rules():
    """Initialize golden rules in database."""
    if not DB_PATH.exists():
        logger.error(f"Base de données non trouvée: {DB_PATH}")
        return False


    logger.info(f"{len(rules)} règles trouvées dans golden-rules.md")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    timestamp = "2026-02-10T00:00:00"
    inserted = 0
    updated = 0

    for rule_text in rules:
        # Check if rule already exists
        cursor.execute(
            "SELECT id, is_golden FROM heuristics WHERE rule = ?", (rule_text,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update to golden if not already
            if not existing[1]:
                cursor.execute(
                    "UPDATE heuristics SET is_golden = 1, updated_at = ? WHERE id = ?",
                    (timestamp, existing[0]),
                )
                updated += 1
                logger.debug(f"Mise à jour: {rule_text[:50]}...")
        else:
            # Insert new golden rule
            cursor.execute(
                """INSERT INTO heuristics
                    (domain, rule, explanation, confidence, is_golden, source_type,
                     times_validated, times_violated, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "general",
                    rule_text,
                    "Golden rule from golden-rules.md",
                    0.95,
                    1,
                    "golden",
                    10,
                    0,
                    timestamp,
                    timestamp,
                ),
            )
            inserted += 1
            logger.debug(f"Insertion: {rule_text[:50]}...")

    conn.commit()
    conn.close()

    logger.info(f"Terminé: {inserted} nouvelles, {updated} mises à jour")
    return True


if __name__ == "__main__":
    logger.info("Initialisation des Golden Rules")
    success = init_golden_rules()
    sys.exit(0 if success else 1)
