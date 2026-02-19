#!/usr/bin/env python3
"""Test de la structure des tables ELF avant migration"""

import sqlite3
from pathlib import Path


def test_table_structure():
    """Test la structure des tables ELF."""
    db_path = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"

    if not db_path.exists():
        print("❌ Base de données non trouvée")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 Test de la structure des tables:")

    # Test heuristics table
    try:
        cursor.execute("PRAGMA table_info(heuristics)")
        columns = cursor.fetchall()
        heuristics_cols = [col[1] for col in columns]
        print(f"✅ Colonnes heuristics: {heuristics_cols}")

        # Test un INSERT
        cursor.execute(
            "INSERT INTO heuristics (rule, domain, explanation) VALUES (?, ?, ?)",
            ("test.rule", "test-domain", "test explanation"),
        )
        print("✅ INSERT test réussi dans heuristics")

    except Exception as e:
        print(f"❌ Erreur table heuristics: {e}")

    # Test si agent_config existe
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_config'"
        )
        result = cursor.fetchone()
        if result:
            print("✅ Table agent_config existe")
        else:
            print("❌ Table agent_config n'existe pas")

    except Exception as e:
        print(f"❌ Erreur test agent_config: {e}")

    conn.close()


if __name__ == "__main__":
    test_table_structure()
