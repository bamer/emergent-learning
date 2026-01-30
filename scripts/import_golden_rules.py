#!/usr/bin/env python3
"""
Script simple pour importer les golden rules depuis le markdown vers SQLite
"""

import sqlite3
import sys
from pathlib import Path


def import_golden_rules():
    """Import golden rules from markdown to SQLite database."""

    # Paths
    elf_home = Path.home() / ".opencode" / "emergent-learning"
    md_file = elf_home / "memory" / "golden-rules.md"
    db_file = elf_home / "memory" / "index.db"

    if not md_file.exists():
        print(f"❌ Fichier golden-rules.md non trouvé: {md_file}")
        return False

    if not db_file.exists():
        print(f"❌ Base de données non trouvée: {db_file}")
        return False

    print(f"📖 Lecture des golden rules depuis: {md_file}")

    # Read markdown file
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Connect to database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS golden_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule TEXT NOT NULL UNIQUE,
            category TEXT,
            confidence REAL DEFAULT 0.5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            use_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            source TEXT,
            explanation TEXT
        )
    """)

    # Parse golden rules from markdown
    lines = content.split("\n")
    current_rule = None

    for line in lines:
        line = line.strip()

        # Detect rule start (## X. Rule Name)
        if line.startswith("## ") and "." in line[3:]:
            if current_rule:
                # Save previous rule
                cursor.execute(
                    """
                    INSERT INTO golden_rules (rule, promoted_on, validations, description)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        current_rule["content"],
                        current_rule["promoted"],
                        current_rule["validations"],
                        current_rule.get("description", ""),
                    ),
                )

            # Start new rule
            rule_number = line.split(".")[1].strip()
            rule_name = " ".join(line.split(".")[2:]).strip()
            current_rule = {
                "content": f"{rule_number}. {rule_name}",
                "promoted": "Legacy",
                "validations": 10,  # Golden rules have 10+ validations
                "description": rule_name,
            }

        # Extract rule content
        elif line.startswith(">") and current_rule:
            rule_content = line[1:].strip()
            if rule_content and len(rule_content) > 10:
                current_rule["content"] = f"{current_rule['content']}\n{rule_content}"

    # Save last rule
    if current_rule:
        cursor.execute(
            """
            INSERT INTO golden_rules (rule, promoted_on, validations, description)
            VALUES (?, ?, ?, ?)
        """,
            (
                current_rule["content"],
                current_rule["promoted"],
                current_rule["validations"],
                current_rule.get("description", ""),
            ),
        )

    conn.commit()
    conn.close()

    # Count inserted rules
    cursor = sqlite3.connect(db_file).cursor()
    cursor.execute("SELECT COUNT(*) FROM golden_rules")
    count = cursor.fetchone()[0]

    print(f"✅ {count} golden rules importées avec succès!")
    print(f"📊 Base de données mise à jour: {db_file}")

    return True


if __name__ == "__main__":
    if import_golden_rules():
        print("🎉 Import des golden rules terminée!")
    else:
        print("❌ Échec de l'import")
        sys.exit(1)
