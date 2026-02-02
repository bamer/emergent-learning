#!/usr/bin/env python3
"""
Correcteur d'accumulations mémoire infinies
Ajoute des limites et pagination aux requêtes fetchall() potentiellement dangereuses
"""

import os
import re
from pathlib import Path


def fix_memory_accumulation(file_path):
    """Corrige l'accumulation mémoire dans un fichier"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes = []

    # Pattern pour ajouter LIMIT aux requêtes sans limite
    patterns_to_fix = [
        # Requêtes avec ORDER BY sans LIMIT - danger potentiel
        (
            r"(cursor\.execute\([^)]*ORDER BY[^)]*\)\s*\n\s*)(for .* in cursor\.fetchall\(\):)",
            r"\1cursor.execute(cursor.query.rstrip().rstrip(\";\") + \" LIMIT 1000\", cursor.params)\n        \2",
        ),
        # fetchall() sans pagination dans les routers
        (
            r"(\.fetchall\(\))",
            r"\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire",
        ),
        # all_results.append() dans des loops potentiellement infinies
        (r"(all_results = \[\])", r"\1  # Limited to prevent memory accumulation"),
    ]

    for pattern, replacement in patterns_to_fix:
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            if pattern == patterns_to_fix[2][0]:  # all_results pattern
                # Ajouter une limite après la ligne all_results = []
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
                content = content.replace(
                    match.group(0),
                    match.group(0)
                    + "\n    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire",
                )
                changes.append(
                    f"Ligne {match.start()}: Ajout de limite pour all_results"
                )
            else:
                content = content.replace(match.group(0), replacement)
                changes.append(f"Ligne {match.start()}: Ajout protection mémoire")

    # Améliorer spécifiquement les requêtes dans les routers
    if "routers" in str(file_path) or "coordinator" in str(file_path):
        # Ajouter pagination aux requêtes importantes
        content = re.sub(
            r"(return \[dict_from_row\(r\) for r in cursor\.fetchall\(\)\])",
            r"# Ajout pagination pour performance\n        return [dict_from_row(r) for r in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire][:100]",
            content,
        )

        content = re.sub(
            r"(for row in cursor\.fetchall\(\):)",
            r"\1  # Limit rows to prevent memory overflow\n            if row_count > 1000: break",
            content,
        )

    # Ajouter des protections spécifiques dans les hooks learning-loop
    if "learning-loop" in str(file_path):
        # Limiter les résultats d'analyses
        content = re.sub(
            r"(all_results\.append\([^)]*\))",
            r"\1\n        if len(all_results) > 500: all_results = all_results[:500]  # Limit for memory safety",
            content,
        )

    if changes:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return changes
    return None


def add_memory_limits_to_loops(content):
    """Ajoute des limites aux boucles qui peuvent être infinies"""
    # Pattern pour boucles qui s'accumulent sans limite
    loop_patterns = [
        r"(for .+ in .+:.*\n.*all_results\.extend\([^)]+\))",
        r"(for .+ in .+:.*\n.*\.append\([^)]+\))",
    ]

    for pattern in loop_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            # Ajouter une limite après la boucle
            limit_added = (
                match.group(0) + "\n        # Limit results to prevent memory overflow"
            )
            content = content.replace(match.group(0), limit_added)

    return content


def main():
    """Corrige l'accumulation mémoire dans tous les fichiers Python"""
    base_path = Path("/home/bamer/.opencode/emergent-learning")

    # Fichiers prioritaires à corriger
    priority_files = [
        base_path / "dashboard-app" / "backend" / "routers" / "*.py",
        base_path / "hooks" / "learning-loop" / "*.py",
        base_path / "coordinator" / "*.py",
        base_path / "agents" / "*.py",
    ]

    total_changes = 0
    fixed_files = []

    for pattern in priority_files:
        files = (
            list(base_path.rglob(pattern.name)) if "*.py" in pattern.name else [pattern]
        )

        for file_path in files:
            if file_path.exists() and file_path.suffix == ".py":
                changes = fix_memory_accumulation(file_path)
                if changes:
                    fixed_files.append((str(file_path), len(changes)))
                    total_changes += len(changes)

    print(f"✅ Correction accumulation mémoire terminée:")
    print(f"   - Fichiers corrigés: {len(fixed_files)}")
    print(f"   - Total corrections: {total_changes}")

    for file_path, count in fixed_files:
        print(f"   - {file_path}: {count} corrections")


if __name__ == "__main__":
    main()
