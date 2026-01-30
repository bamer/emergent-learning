#!/usr/bin/env python3
"""
Script simple pour inserer les golden rules
"""

import sqlite3
from pathlib import Path


def main():
    elf_home = Path.home() / ".opencode" / "emergent-learning"
    db_path = elf_home / "memory" / "index.db"
    golden_rules_file = elf_home / "memory" / "golden-rules.md"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Golden rules manuelles
    golden_rules = [
        (
            "1",
            "Query Before Acting",
            "Always check existing knowledge before starting a task",
        ),
        (
            "2",
            "Document Failures Immediately",
            "Record failures while context is fresh, before moving on",
        ),
        (
            "3",
            "Extract Heuristics, Not Just Outcomes",
            "Don't just note what happened; extract transferable principle",
        ),
        (
            "4",
            "Break It Before Shipping It",
            "Actively try to break your solution before declaring it done",
        ),
        (
            "5",
            "Escalate Uncertainty",
            "When unsure about high-stakes decisions, escalate to CEO",
        ),
        (
            "6",
            "Record Learnings Before Ending Session",
            "Before closing any significant work session, review and record what was learned",
        ),
        (
            "7",
            "Obey Direct Commands Immediately",
            "When user gives a direct action command, execute it FIRST before anything else",
        ),
        (
            "8",
            "Log Before Summary",
            "Complete all logging to building BEFORE giving user a summary",
        ),
        (
            "9",
            "useEffect Callback Dependencies Cause Loops",
            "useEffect with callback deps causes reconnect loops - use refs for callbacks",
        ),
        (
            "10",
            "Trust User Reality Over Tool Metadata",
            "When user reports something is broken/empty/wrong, believe them immediately",
        ),
        (
            "11",
            "No External APIs - Subscription Only",
            "NEVER suggest external API calls - use Claude Code subagents",
        ),
        (
            "12",
            "Always Use Async Subagents",
            "Default to run_in_background=True for ALL subagent spawns",
        ),
    ]

    print("📖 Insertion des golden rules manuelles...")

    for number, name, explanation in golden_rules:
        cursor.execute(
            """
            INSERT OR REPLACE INTO heuristics 
            (rule, domain, explanation, confidence, is_golden, status, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                f"{number}. {name}",
                "core-principles",
                explanation,
                1.0,
                1,
                "active",
                "golden-rule",
            ),
        )

    conn.commit()
    conn.close()

    print(f"✅ {len(golden_rules)} golden rules insérées")


if __name__ == "__main__":
    main()
