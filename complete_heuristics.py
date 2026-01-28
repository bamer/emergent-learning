#!/usr/bin/env python3
"""
Complete the swarm data insertion with heuristics
"""

import sqlite3


def insert_heuristics():
    conn = sqlite3.connect("/home/bamer/.opencode/emergent-learning/memory/index.db")
    cursor = conn.cursor()

    # Insert the discovered heuristics with proper columns
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

    inserted_count = 0
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
            inserted_count += 1
            print(
                f"✅ Inserted: {rule} (confidence: {confidence}, golden: {'Yes' if is_golden else 'No'})"
            )

    conn.commit()

    # Verify
    cursor.execute('SELECT COUNT(*) FROM heuristics WHERE domain LIKE "%swarm%"')
    heuristic_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 1")
    golden_count = cursor.fetchone()[0]

    print(f"\n📊 Heuristics Summary:")
    print(f"  🔗 Swarm heuristics: {heuristic_count}")
    print(f"  👑 Total golden rules: {golden_count}")

    conn.close()
    return inserted_count


if __name__ == "__main__":
    count = insert_heuristics()
    print(f"\n🎯 Successfully inserted {count} new heuristics!")
