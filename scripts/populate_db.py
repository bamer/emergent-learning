#!/usr/bin/env python3
"""
Script simple pour remplir la base de données ELF
"""

import sqlite3
from pathlib import Path


def populate_elf_database():
    """Remplit la base de données ELF avec les données de base."""

    elf_home = Path.home() / ".opencode" / "emergent-learning"
    db_path = elf_home / "memory" / "index.db"
    golden_rules_file = elf_home / "memory" / "golden-rules.md"

    if not db_path.exists():
        print("❌ Base de données non trouvée")
        return False

    print("🔄 Remplissage de la base de données ELF...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Insérer les golden rules dans heuristics
        if golden_rules_file.exists():
            print("📖 Lecture et insertion des golden rules...")

            with open(golden_rules_file, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\\n")
            rule_count = 0

            for line in lines:
                line = line.strip()

                if line.startswith("## ") and "." in line[3:]:
                    # Extraire numéro et nom de la règle
                    parts = line.split(".")
                    if len(parts) >= 2:
                        rule_number = parts[1].strip()
                        rule_name = " ".join(parts[2:]).strip()

                        # Insérer dans heuristics
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO heuristics 
                            (rule, domain, explanation, confidence, is_golden, status, category)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                f"{rule_number}. {rule_name}",
                                "core-principles",
                                f"Rule: {rule_name}",
                                1.0,
                                1,
                                "active",
                                "golden-rule",
                            ),
                        )
                        rule_count += 1

            print(f"✅ {rule_count} golden rules insérées")

        # 2. Insérer les agents ELF
        elf_agents = [
            ("researcher", "investigation", 0.6),
            ("architect", "architecture", 0.7),
            ("creative", "innovation", 0.8),
            ("skeptic", "risk-analysis", 0.4),
            ("learning-extractor", "learning-synthesis", 0.5),
        ]

        print("🤖 Insertion des agents ELF...")

        for agent_name, domain, temp in elf_agents:
            cursor.execute(
                """
                INSERT OR REPLACE INTO agent_config 
                (agent_name, agent_type, mission, model_id, provider_id, temperature, domain)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agent_name,
                    "primary",
                    f"Mission spécialisée ELF pour {domain}",
                    "opencode/big-pickle",
                    "opencode",
                    temp,
                    domain,
                ),
            )

        print(f"✅ {len(elf_agents)} agents insérés")

        conn.commit()
        conn.close()

        print("\\n🎉 Base de données ELF remplie avec succès!")

        # Vérification
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM heuristics")
        heuristics_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_config")
        agents_count = cursor.fetchone()[0]

        print(f"📊 Résultats: {heuristics_count} heuristics, {agents_count} agents")

        conn.close()

        return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = populate_elf_database()
    exit(0 if success else 1)
