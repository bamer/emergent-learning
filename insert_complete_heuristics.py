#!/usr/bin/env python3
"""
Insert heuristics with ALL required columns filled properly
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the backend utils to the path
backend_path = Path(__file__).parent / "dashboard-app" / "backend"
sys.path.insert(0, str(backend_path))

from utils.database import get_db


def insert_complete_heuristics():
    """Insert heuristics with all required columns filled."""

    print("🔄 Inserting complete heuristics...")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            heuristics = [
                {
                    "domain": "swarm_coordination",
                    "rule": "Protocole Contexte Plat",
                    "explanation": "Swarm exige écriture fichiers, retour chemins uniquement",
                    "confidence": 0.8,
                    "is_golden": 1,
                    "source_type": "user_interaction",
                },
                {
                    "domain": "swarm_architecture",
                    "rule": "Abstraction Modèle",
                    "explanation": "Swarm doit abstraire différences modèles derrière interface unifiée",
                    "confidence": 0.7,
                    "is_golden": 0,
                    "source_type": "user_interaction",
                },
                {
                    "domain": "swarm_coordination",
                    "rule": "Coordination > Communication",
                    "explanation": "Coordination fichier bat communication messages pour fiabilité",
                    "confidence": 0.9,
                    "is_golden": 1,
                    "source_type": "user_interaction",
                },
            ]

            for h in heuristics:
                # Check if already exists
                cursor.execute(
                    "SELECT id FROM heuristics WHERE rule = ? AND domain = ?",
                    (h["rule"], h["domain"]),
                )
                existing = cursor.fetchone()

                if existing:
                    print(f"⚠️  Heuristic already exists: {h['rule']}")
                    continue

                # Insert with ALL required columns
                cursor.execute(
                    """
                    INSERT INTO heuristics (
                        domain, rule, explanation, source_type, source_id,
                        confidence, times_validated, times_violated, is_golden,
                        project_path, status, dormant_since, revival_conditions,
                        times_revived, times_contradicted, min_applications,
                        last_confidence_update, update_count_today, update_count_reset_date,
                        last_used_at, confidence_ema, ema_alpha, ema_warmup_remaining,
                        last_ema_update, fraud_flags, is_quarantined, last_fraud_check,
                        created_at, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now')
                    )
                """,
                    (
                        h["domain"],
                        h["rule"],
                        h["explanation"],
                        h["source_type"],
                        None,
                        h["confidence"],
                        0,
                        0,
                        h["is_golden"],
                        None,
                        "active",
                        None,
                        None,
                        0,
                        0,
                        0,
                        datetime.now().isoformat(),
                        0,
                        datetime.now().date(),
                        datetime.now().isoformat(),
                        h["confidence"],
                        0.1,
                        10,
                        datetime.now().isoformat(),
                        0,
                        0,
                        datetime.now().isoformat(),
                    ),
                )

                heuristic_id = cursor.lastrowid
                golden_status = "👑 Golden" if h["is_golden"] else "💡 Regular"
                print(
                    f"✅ Inserted: {h['rule']} ({golden_status}) - ID: {heuristic_id}"
                )

            conn.commit()

            # Verify results
            cursor.execute("""
                SELECT id, rule, domain, is_golden, confidence 
                FROM heuristics 
                WHERE domain LIKE '%swarm%' 
                ORDER BY created_at DESC
            """)
            swarm_heuristics = cursor.fetchall()

            print(f"\n📊 Swarm Heuristics Summary:")
            for h_id, rule, domain, is_golden, confidence in swarm_heuristics:
                status = "👑" if is_golden else "💡"
                print(f"  {status} {rule} (confidence: {confidence})")

            print(f"\n🎯 Total: {len(swarm_heuristics)} swarm heuristics in database")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = insert_complete_heuristics()
    if success:
        print("\n🌐 Dashboard should now show the new heuristics!")
        print("🔄 Refresh: http://localhost:3001")
    else:
        print("\n❌ Failed to insert heuristics")
