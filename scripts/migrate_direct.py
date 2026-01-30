#!/usr/bin/env python3
"""
Migration directe vers le nouveau système ELF (sans patcher l'ancien)
"""

import sqlite3
import sys
from pathlib import Path


def migrate_to_new_system():
    """Migration directe vers le nouveau système."""
    print("🚀 Migration directe vers nouveau système ELF")
    print("=" * 60)

    elf_home = Path.home() / ".opencode" / "emergent-learning"
    db_path = elf_home / "memory" / "index.db"

    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False

    print("🔄 Connexion à la base de données...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Supprimer l'ancienne table heuristics conflictuelle
        print("🗑️ Suppression de l'ancienne table heuristics...")
        cursor.execute("DROP TABLE IF EXISTS heuristics")

        # Créer la nouvelle table compatible avec le nouveau query.py
        print("📋 Création de la nouvelle table heuristics...")
        cursor.execute("""
            CREATE TABLE heuristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule TEXT NOT NULL UNIQUE,
                domain TEXT,
                explanation TEXT,
                source TEXT,
                confidence REAL DEFAULT 0.5,
                is_golden INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                use_count INTEGER DEFAULT 0,
                validations INTEGER DEFAULT 0,
                category TEXT DEFAULT 'general',
                agent_name TEXT,
                name TEXT
            )
        """)

        # Insérer les golden rules depuis le markdown
        golden_rules_file = elf_home / "memory" / "golden-rules.md"
        if golden_rules_file.exists():
            print("📖 Lecture des golden rules...")
            with open(golden_rules_file, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            current_rule = None
            rule_count = 0

            for line in lines:
                line = line.strip()

                if line.startswith("## ") and "." in line[3:]:
                    if current_rule:
                        # Insérer la règle précédente
                        cursor.execute(
                            """
                            INSERT INTO heuristics 
                            (rule, domain, explanation, source, confidence, is_golden, status, agent_name, name)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                f"{current_rule.get('number')}. {current_rule.get('name')}",
                                "core-principles",
                                current_rule.get("explanation", ""),
                                "elf-framework",
                                1.0,
                                1,
                                "active",
                                None,
                                f"{current_rule.get('number')}. {current_rule.get('name')}",
                            ),
                        )
                        rule_count += 1

                    rule_number = line.split(".")[1].strip()
                    rule_name = " ".join(line.split(".")[2:]).strip()
                    current_rule = {
                        "number": rule_number,
                        "name": rule_name,
                        "explanation": f"Rule: {rule_name}",
                        "domain": "core-principles",
                        "source": "elf-framework",
                        "confidence": 1.0,
                        "is_golden": 1,
                        "status": "active",
                    }

                elif line.startswith(">") and current_rule:
                    rule_content = line[1:].strip()
                    if rule_content and len(rule_content) > 10:
                        current_rule["explanation"] = (
                            f"{current_rule.get('explanation')}\\n{rule_content}"
                        )

            # Insérer la dernière règle
            if current_rule:
                cursor.execute(
                    """
                    INSERT INTO heuristics 
                    (rule, domain, explanation, source, confidence, is_golden, status, agent_name, name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        f"{current_rule.get('number')}. {current_rule.get('name')}",
                        "core-principles",
                        current_rule.get("explanation", ""),
                        "elf-framework",
                        1.0,
                        1,
                        "active",
                        None,
                        f"{current_rule.get('number')}. {current_rule.get('name')}",
                    ),
                )
                rule_count += 1

        # Créer la table agent_config pour le nouvel orchestrateur
        print("📝 Création de la table agent_config...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT UNIQUE NOT NULL,
                agent_type TEXT NOT NULL,
                mission TEXT,
                model_id TEXT DEFAULT 'opencode/big-pickle',
                provider_id TEXT DEFAULT 'opencode',
                temperature REAL DEFAULT 0.6,
                prompt_file TEXT,
                domain TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insérer les agents ELF avec leurs missions
        elf_agents = [
            {
                "agent_name": "researcher",
                "mission": "Investigation approfondie, collecte de preuves, validation contre standards",
                "domain": "investigation",
                "temperature": 0.6,
            },
            {
                "agent_name": "architect",
                "mission": "Conception système robuste et évolutive, patterns et scalabilité",
                "domain": "architecture",
                "temperature": 0.7,
            },
            {
                "agent_name": "creative",
                "mission": "Génération de solutions innovantes et alternatives non-conformistes",
                "domain": "innovation",
                "temperature": 0.8,
            },
            {
                "agent_name": "skeptic",
                "mission": "Analyse critique, identification des risques et scénarios de défaillance",
                "domain": "risk-analysis",
                "temperature": 0.4,
            },
            {
                "agent_name": "learning-extractor",
                "mission": "Synthèse des apprentissages, extraction de principes et méta-apprentissage",
                "domain": "learning-synthesis",
                "temperature": 0.5,
            },
        ]

        for agent in elf_agents:
            cursor.execute(
                """
                INSERT OR REPLACE INTO agent_config 
                (agent_name, agent_type, mission, model_id, provider_id, temperature, prompt_file, domain)
                VALUES (?, 'primary', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agent["agent_name"],
                    agent["mission"],
                    agent.get("model_id", "opencode/big-pickle"),
                    agent.get("provider_id", "opencode"),
                    agent.get("temperature", 0.6),
                    "Mission spécialisée ELF",
                    agent["domain"],
                ),
            )

        # Valider la migration
        cursor.execute("COMMIT")
        conn.close()

        print(f"✅ {rule_count} golden rules migrées")
        print(f"✅ {len(elf_agents)} agents ELF configurés")
        print("✅ Système ELF migré avec succès!")

        print("\n🎯 État final:")
        print("  ✅ Base de données compatible avec nouveau query.py")
        print("  ✅ Golden rules migrées comme heuristics")
        print("  ✅ Agents ELF configurés avec missions")
        print("  ✅ Table agent_config créée pour orchestrateur")

        print("\n🔄 Prochaines étapes:")
        print("  1. Démarrer l'orchestrateur ELF")
        print("  2. Tester le workflow complet")
        print("  3. Mettre à jour le dashboard")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_to_new_system()
    sys.exit(0 if success else 1)
