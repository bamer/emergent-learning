#!/usr/bin/env python3
"""
Optimiseur de requêtes SQL SELECT *
Remplace automatiquement les SELECT * par des colonnes spécifiques optimisées
"""

import os
import re
from pathlib import Path


def get_table_columns():
    """Retourne les colonnes connues pour chaque table"""
    return {
        "users": ["id", "github_id", "username", "email", "avatar_url", "created_at"],
        "heuristics": [
            "id",
            "domain",
            "rule",
            "confidence",
            "is_golden",
            "updated_at",
            "created_at",
        ],
        "learnings": ["id", "type", "title", "summary", "domain", "created_at"],
        "decisions": ["id", "title", "status", "domain", "created_at"],
        "assumptions": [
            "id",
            "statement",
            "status",
            "severity",
            "domain",
            "violation_count",
            "created_at",
        ],
        "invariants": [
            "id",
            "statement",
            "status",
            "severity",
            "domain",
            "violation_count",
            "created_at",
        ],
        "spike_reports": [
            "id",
            "title",
            "description",
            "status",
            "domain",
            "created_at",
        ],
        "game_state": [
            "user_id",
            "score",
            "level",
            "achievements",
            "last_activity",
            "created_at",
        ],
        "workflow_runs": ["id", "workflow_name", "status", "phase", "created_at"],
        "node_executions": [
            "id",
            "run_id",
            "node_id",
            "status",
            "result",
            "started_at",
            "completed_at",
        ],
        "trails": [
            "id",
            "location",
            "scent",
            "strength",
            "agent_id",
            "message",
            "created_at",
        ],
        "conductor_decisions": [
            "id",
            "run_id",
            "decision_type",
            "reasoning",
            "timestamp",
        ],
        "workflow_edges": ["id", "from_node", "to_node", "condition", "created_at"],
        "system_health": [
            "id",
            "timestamp",
            "status",
            "db_integrity",
            "db_size_mb",
            "disk_free_mb",
            "git_status",
            "stale_locks",
        ],
    }


def optimize_select_queries(file_path):
    """Optimise les requêtes SELECT * dans un fichier"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    table_columns = get_table_columns()
    changes = []

    # Pattern pour SELECT * FROM table
    patterns = [
        (
            r"SELECT \* FROM (\w+) WHERE",
            r"SELECT id,\1.* FROM \1 WHERE",
        ),  # Cas où on a WHERE
        (
            r"SELECT \* FROM (\w+)\s*ORDER BY",
            r"SELECT id,\1.* FROM \1 ORDER BY",
        ),  # Cas avec ORDER BY
        (r"SELECT \* FROM (\w+)$", r"SELECT id,\1.* FROM \1"),  # Cas simple
    ]

    for pattern, replacement in patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            table = match.group(1)
            if table in table_columns:
                # Créer une requête optimisée avec seulement les colonnes utilisées
                columns = table_columns[table]
                # Inclure les colonnes essentielles + quelques autres importantes
                essential_cols = ["id"] + [
                    col
                    for col in columns
                    if col in ["created_at", "updated_at", "status", "name", "title"]
                ]

                optimized_cols = ", ".join(essential_cols)
                new_query = replacement.replace(
                    f"SELECT id,{table}.*", f"SELECT {optimized_cols}", 1
                )

                content = content.replace(match.group(0), new_query)
                changes.append(f"Ligne {match.start()}: {table} -> {optimized_cols}")

    if changes:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return changes
    return None


def main():
    """Optimise tous les fichiers Python dans le backend"""
    backend_path = Path("/home/bamer/.opencode/emergent-learning/dashboard-app/backend")
    router_files = list(backend_path.rglob("*.py"))

    total_changes = 0
    optimized_files = []

    for file_path in router_files:
        changes = optimize_select_queries(file_path)
        if changes:
            optimized_files.append((str(file_path), len(changes)))
            total_changes += len(changes)

    print(f"✅ Optimisation terminée:")
    print(f"   - Fichiers optimisés: {len(optimized_files)}")
    print(f"   - Total requêtes optimisées: {total_changes}")

    for file_path, count in optimized_files:
        print(f"   - {file_path}: {count} requêtes optimisées")


if __name__ == "__main__":
    main()
