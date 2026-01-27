#!/usr/bin/env python3
"""
Insert swarm mode analysis data into ELF database
"""

import sqlite3


def insert_swarm_data():
    conn = sqlite3.connect("/home/bamer/.claude/emergent-learning/memory/index.db")
    cursor = conn.cursor()

    # Insert the swarm analysis as a learning
    cursor.execute(
        """
    INSERT INTO learnings (type, filepath, title, summary, tags, domain, severity, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """,
        (
            "observation",
            "/analysis/swarm_mode_elF.md",
            "Swarm Mode Analysis",
            "User asked to analyse swarm mode activation in ELF. Response: The swarm mode enables unlimited scaling with flat context protocol. Multi-agent configuration via run-swarm.py already implemented. Discovered 3 heuristics and production tests recommended.",
            "swarm,coordination,multi-agent,ELF",
            "multi_agent_systems",
            3,
        ),
    )

    # Insert the discovered heuristics
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

    # Create a spike report for swarm experiments
    cursor.execute(
        """
    INSERT INTO spike_reports (domain, query, title, topic, tags, time_invested_minutes, created_at, updated_at)
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

    conn.commit()
    print(f"✅ Inserted 1 learning, {len(heuristics)} heuristics, 1 spike report")
    print("🎯 Swarm mode analysis now in ELF database!")

    # Verify insertion
    cursor.execute('SELECT COUNT(*) FROM learnings WHERE title LIKE "%Swarm%"')
    learning_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM heuristics WHERE domain LIKE "%swarm%"')
    heuristic_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM spike_reports WHERE tags LIKE "%swarm%"')
    spike_count = cursor.fetchone()[0]

    print(
        f"📊 Verification: {learning_count} learning, {heuristic_count} heuristics, {spike_count} spike reports"
    )

    conn.close()


if __name__ == "__main__":
    insert_swarm_data()
