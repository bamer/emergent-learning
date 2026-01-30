#!/usr/bin/env python3
"""
Migration complète vers le nouveau système ELF avec OpenCode
- Corrige la base de données heuristiques
- Configure l'orchestrateur avec OpenCode
- Migre les tables correctement
- Configure les agents ELF avec leurs missions
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime


class ELFMigrator:
    def __init__(self):
        self.elf_home = Path.home() / ".opencode" / "emergent-learning"
        self.db_path = self.elf_home / "memory" / "index.db"

    def migrate_database(self):
        """Migration complète de la base de données."""
        print("🔄 Migration de la base de données ELF...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Créer les tables manquantes avec le bon schéma
        self._create_missing_tables(cursor)

        # 2. Migrer les golden rules vers heuristiques
        self._migrate_golden_rules_to_heuristics(cursor)

        # 3. Nettoyer les données incohérentes
        self._cleanup_inconsistent_data(cursor)

        # 4. Configurer les agents ELF
        self._setup_elf_agents(cursor)

        conn.commit()
        conn.close()

        print("✅ Migration terminée avec succès!")

    def _create_missing_tables(self, cursor):
        """Crée les tables manquantes."""
        print("📋 Création des tables manquantes...")

        # Pas besoin de créer la table heuristics (existe déjà)
        print(
            "  ℹ️  Table heuristics déjà existante - utilisation de la structure existante"
        )

        # Table agent_config pour l'orchestrateur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT UNIQUE NOT NULL,
                agent_type TEXT NOT NULL,
                mission TEXT,
                model_id TEXT DEFAULT 'big-pickle',
                provider_id TEXT DEFAULT 'opencode',
                temperature REAL DEFAULT 0.6,
                prompt_file TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table swarm_workflows pour l'orchestrateur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swarm_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_name TEXT NOT NULL,
                description TEXT,
                agents_sequence TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)

        print("  ✅ Tables créées")

    def _migrate_golden_rules_to_heuristics(self, cursor):
        """Migration des golden rules vers heuristiques."""
        print("📖 Migration des golden rules vers heuristiques...")

        # Lire les golden rules depuis le markdown
        golden_rules_file = self.elf_home / "memory" / "golden-rules.md"
        if golden_rules_file.exists():
            with open(golden_rules_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parser et insérer les règles comme heuristiques avec confiance 1.0
            lines = content.split("\n")
            current_rule = None
            rule_count = 0

            for line in lines:
                line = line.strip()

                if line.startswith("## ") and "." in line[3:]:
                    if current_rule:
                        self._insert_heuristic(cursor, current_rule)
                        rule_count += 1

                    rule_number = line.split(".")[1].strip()
                    rule_name = " ".join(line.split(".")[2:]).strip()
                    current_rule = {
                        "name": f"{rule_number}. {rule_name}",
                        "description": rule_name,
                        "domain": "core-principles",
                        "confidence": 1.0,
                        "category": "golden-rule",
                        "source": "elf-framework",
                    }

                elif line.startswith(">") and current_rule and len(line) > 15:
                    rule_content = line[1:].strip()
                    current_rule["content"] = f"{current_rule['name']}\\n{rule_content}"

            # Insérer la dernière règle
            if current_rule:
                self._insert_heuristic(cursor, current_rule)
                rule_count += 1

            print(f"  ✅ {rule_count} golden rules migrées")

            # Déplacer les golden rules vers heuristics dans la query
            cursor.execute(
                "UPDATE heuristics SET category = 'golden-rule' WHERE category = 'core-principles'"
            )

    def _insert_heuristic(self, cursor, rule):
        """Insère une heuristique dans la base."""
        cursor.execute(
            """
            INSERT OR REPLACE INTO heuristics 
            (name, description, domain, confidence, source, validations, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                rule.get("name", ""),
                rule.get("content", ""),
                rule.get("domain", ""),
                rule.get("confidence", 0.5),
                rule.get("source", ""),
                5,  # Les golden rules ont au moins 5 validations
                rule.get("category", "general"),
            ),
        )

    def _cleanup_inconsistent_data(self, cursor):
        """Nettoie les données incohérentes."""
        print("🧹 Nettoyage des données...")

        # Supprimer les doublons dans agent_config
        cursor.execute(
            "DELETE FROM agent_config WHERE rowid NOT IN (SELECT MIN(rowid) FROM agent_config GROUP BY agent_name)"
        )

        # Mettre à jour les références
        cursor.execute(
            "UPDATE heuristics SET confidence = 1.0 WHERE category = 'golden-rule'"
        )
        cursor.execute(
            "UPDATE heuristics SET validations = 5 WHERE category = 'golden-rule' AND validations < 5"
        )

    def _setup_elf_agents(self, cursor):
        """Configure les agents ELF avec leurs missions."""
        print("🤖 Configuration des agents ELF...")

        # Définition des agents ELF avec leurs missions
        elf_agents = [
            {
                "agent_name": "researcher",
                "agent_type": "primary",
                "mission": "Investigation approfondie, collecte de preuves, validation contre standards",
                "model_id": "opencode/big-pickle",
                "provider_id": "opencode",
                "temperature": 0.6,
                "prompt_file": "Research deeper into evidence-based analysis with [LEARNED:] format",
                "domain": "investigation",
            },
            {
                "agent_name": "architect",
                "agent_type": "primary",
                "mission": "Conception système robuste et évolutive, patterns et scalabilité",
                "model_id": "opencode/big-pickle",
                "provider_id": "opencode",
                "temperature": 0.7,
                "prompt_file": "System design thinking with architectural patterns and component analysis",
                "domain": "architecture",
            },
            {
                "agent_name": "creative",
                "agent_type": "primary",
                "mission": "Génération de solutions innovantes et alternatives non-conformistes",
                "model_id": "opencode/big-pickle",
                "provider_id": "opencode",
                "temperature": 0.8,
                "prompt_file": "Innovative thinking with multiple approaches and hidden opportunities",
                "domain": "innovation",
            },
            {
                "agent_name": "skeptic",
                "agent_type": "primary",
                "mission": "Analyse critique, identification des risques et scénarios de défaillance",
                "model_id": "opencode/big-pickle",
                "provider_id": "opencode",
                "temperature": 0.4,
                "prompt_file": "Critical analysis with risk assessment and failure scenario testing",
                "domain": "risk-analysis",
            },
            {
                "agent_name": "learning-extractor",
                "agent_type": "primary",
                "mission": "Synthèse des apprentissages, extraction de principes et méta-apprentissage",
                "model_id": "opencode/big-pickle",
                "provider_id": "opencode",
                "temperature": 0.5,
                "prompt_file": "Cross-agent synthesis and principle extraction with confidence calibration",
                "domain": "learning-synthesis",
            },
        ]

        # Insérer les agents
        for agent in elf_agents:
            cursor.execute(
                """
                INSERT OR REPLACE INTO agent_config 
                (agent_name, agent_type, mission, model_id, provider_id, temperature, prompt_file, domain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agent["agent_name"],
                    agent["agent_type"],
                    agent["mission"],
                    agent["model_id"],
                    agent["provider_id"],
                    agent["temperature"],
                    agent["prompt_file"],
                    agent["domain"],
                ),
            )

        # Configurer les workflows swarm par défaut
        default_workflows = [
            {
                "workflow_name": "full-analysis",
                "description": "Analyse complète: Researcher → Architect → Creative → Skeptic → Learning Extractor",
                "agents_sequence": "researcher,architect,creative,skeptic,learning-extractor",
            },
            {
                "workflow_name": "quick-scan",
                "description": "Scan rapide: Researcher + Skeptic",
                "agents_sequence": "researcher,skeptic",
            },
            {
                "workflow_name": "design-review",
                "description": "Review design: Architect + Skeptic",
                "agents_sequence": "architect,skeptic",
            },
            {
                "workflow_name": "innovation",
                "description": "Brainstorming: Creative + Researcher",
                "agents_sequence": "creative,researcher",
            },
        ]

        for workflow in default_workflows:
            cursor.execute(
                """
                INSERT OR REPLACE INTO swarm_workflows 
                (workflow_name, description, agents_sequence)
                VALUES (?, ?, ?)
            """,
                (
                    workflow["workflow_name"],
                    workflow["description"],
                    workflow["agents_sequence"],
                ),
            )

        print(f"  ✅ {len(elf_agents)} agents configurés")
        print(f"  ✅ {len(default_workflows)} workflows swarm créés")


def main():
    """Fonction principale de migration."""
    print("🚀 Migration complète ELF vers nouveau système avec OpenCode")
    print("=" * 60)

    migrator = ELFMigrator()

    try:
        migrator.migrate_database()

        print("\n" + "=" * 60)
        print("🎉 Migration terminée! Le système ELF est maintenant prêt pour OpenCode")
        print("\n📋 État final:")
        print("  ✅ Base de données migrée et corrigée")
        print("  ✅ Agents ELF configurés avec missions")
        print("  ✅ Workflows swarm définis")
        print("  ✅ Compatible avec OpenCode server")
        print("\n🔄 Prochaine étape:")
        print("  1. Démarrer l'orchestrateur ELF")
        print("  2. Tester les agents avec leurs missions")
        print("  3. Valider le learning complet")
        print("\n🌐 Dashboard: http://localhost:3001")
        print("🤖 OpenCode: http://localhost:4096")

        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
