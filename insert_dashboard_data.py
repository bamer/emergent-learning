#!/usr/bin/env python3
"""
Insert data using the same method as the dashboard backend
"""

import sys
import os
from pathlib import Path

# Add the backend utils to the path
backend_path = Path(__file__).parent / "dashboard-app" / "backend"
sys.path.insert(0, str(backend_path))

from utils.database import get_db
from datetime import datetime


def insert_dashboard_learning():
    """Insert a learning using the dashboard's database utilities."""

    print("🔄 Inserting learning using dashboard backend utilities...")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Insert the swarm analysis learning
            cursor.execute(
                """
                INSERT INTO learnings (type, filepath, title, summary, tags, domain, severity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
                (
                    "observation",
                    "/analysis/swarm_mode_elf_dashboard.md",
                    "Swarm Mode Analysis - Dashboard",
                    "User asked to analyse swarm mode activation in ELF. Response: The swarm mode enables unlimited scaling with flat context protocol. Multi-agent configuration via run-swarm.py already implemented. Discovered 3 heuristics and production tests recommended.",
                    "swarm,coordination,multi-agent,ELF",
                    "multi_agent_systems",
                    3,
                ),
            )

            learning_id = cursor.lastrowid
            print(f"✅ Inserted learning with ID: {learning_id}")

            # Insert heuristics using the same method
            heuristics = [
                (
                    "Protocole Contexte Plat",
                    "Swarm exige écriture fichiers, retour chemins uniquement",
                    0.8,
                    "swarm_coordination",
                ),
                (
                    "Abstraction Modèle",
                    "Swarm doit abstraire différences modèles derrière interface unifiée",
                    0.7,
                    "swarm_architecture",
                ),
                (
                    "Coordination > Communication",
                    "Coordination fichier bat communication messages pour fiabilité",
                    0.9,
                    "swarm_coordination",
                ),
            ]

            for rule, explanation, confidence, domain in heuristics:
                is_golden = 1 if confidence >= 0.8 else 0
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO heuristics (domain, rule, explanation, source_type, confidence, is_golden, created_at, updated_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
                """,
                    (
                        domain,
                        rule,
                        explanation,
                        "user_interaction",
                        confidence,
                        is_golden,
                        "active",
                    ),
                )

                if cursor.rowcount > 0:
                    print(f"✅ Inserted heuristic: {rule} (confidence: {confidence})")

            # Insert spike report
            cursor.execute(
                """
                INSERT OR IGNORE INTO spike_reports (domain, query, title, topic, tags, time_invested_minutes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
                (
                    "swarm_coordination",
                    "Swarm mode activation experiments",
                    "Swarm Mode Production Tests",
                    "multi_agent_systems",
                    "swarm,experiments,production",
                    45,
                ),
            )

            if cursor.rowcount > 0:
                print("✅ Inserted spike report: Swarm Mode Production Tests")

            conn.commit()

            # Verify insertion
            cursor.execute("SELECT COUNT(*) FROM learnings WHERE title LIKE '%Swarm%'")
            swarm_learnings = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM heuristics WHERE domain LIKE '%swarm%'"
            )
            swarm_heuristics = cursor.fetchone()[0]

            print(f"\n📊 Final Results:")
            print(f"  📚 Swarm learnings: {swarm_learnings}")
            print(f"  💡 Swarm heuristics: {swarm_heuristics}")
            print(f"  🎯 Data should now appear in dashboard!")

            return True

    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = insert_dashboard_learning()
    if success:
        print("\n🌐 Refresh dashboard at: http://localhost:3001")
        print("💡 Use Ctrl+F5 for hard refresh if needed")
    else:
        print("\n❌ Insertion failed - check the error above")
