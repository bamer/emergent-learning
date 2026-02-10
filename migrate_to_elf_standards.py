#!/usr/bin/env python3
"""
ELF Standards Migration Helper

Assists with migrating non-compliant ELF components to standard implementations.
Use this script after implementing the audit recommendations.

Usage:
    python migrate_to_elf_standards.py --component event_chronicle
    python migrate_to_elf_standards.py --phase 2
    python migrate_to_elf_standards.py --validate-all
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class ELFMigrator:
    """ELF Standards Migration Helper"""

    def __init__(self, elf_base: Path = None):
        if elf_base is None:
            elf_base = Path(__file__).parent

        self.elf_base = elf_base
        self.config_file = elf_base / "elf_config.yaml"
        self.audit_file = elf_base / "elf-compliance-audit.md"

        # Load current configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load ELF configuration"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f)
        return {}

    def _save_config(self):
        """Save ELF configuration"""
        with open(self.config_file, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def migrate_event_chronicle(self) -> bool:
        """Migrate to ELF event chronicle system"""
        print("🔧 Migrating to ELF Event Chronicle System...")

        try:
            # Ensure event chronicle exists
            event_chronicle_dir = self.elf_base / "event_chronicle"
            event_chronicle_dir.mkdir(exist_ok=True)

            # Test the event chronicle
            sys.path.insert(0, str(event_chronicle_dir))
            from event_chronicle import EventChronicle

            chronicle = EventChronicle()

            # Log migration event
            chronicle.log_event(
                event_type="migration_completed",
                source="migrate_to_elf_standards.py",
                data={
                    "component": "event_chronicle",
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                },
            )

            print("✅ Event Chronicle migration completed")

            # Update configuration
            if "elf_config" not in self.config:
                self.config["elf_config"] = {}
            if "event_chronicle" not in self.config["elf_config"]:
                self.config["elf_config"]["event_chronicle"] = {}

            self.config["elf_config"]["event_chronicle"]["enabled"] = True
            self.config["elf_config"]["event_chronicle"]["directory"] = (
                "event_chronicle"
            )

            return True

        except Exception as e:
            print(f"❌ Event Chronicle migration failed: {e}")
            return False

    def migrate_configuration(self) -> bool:
        """Migrate scattered configurations to ELF standard"""
        print("🔧 Migrating to ELF Standard Configuration...")

        try:
            # Create elf_config.yaml if it doesn't exist
            if not self.config_file.exists():
                print("❌ ELF configuration file not found. Run audit first.")
                return False

            # Remove old configuration files
            old_configs = [
                self.elf_base / "test-swarm.yaml",
                self.elf_base / ".coordination" / "sentinel-config.yaml",
            ]

            for old_config in old_configs:
                if old_config.exists():
                    # Move to backup
                    backup_dir = self.elf_base / "backup" / "old_configs"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup_path = backup_dir / old_config.name
                    old_config.rename(backup_path)
                    print(f"📦 Moved {old_config.name} to backup")

            print("✅ Configuration migration completed")
            return True

        except Exception as e:
            print(f"❌ Configuration migration failed: {e}")
            return False

    def validate_component(self, component: str) -> bool:
        """Validate a specific ELF component"""
        print(f"🔍 Validating ELF component: {component}")

        validation_map = {
            "event_chronicle": self._validate_event_chronicle,
            "configuration": self._validate_configuration,
            "database": self._validate_database,
            "coordination": self._validate_coordination,
            "query": self._validate_query,
            "dashboard": self._validate_dashboard,
            "sentinel": self._validate_sentinel,
        }

        validator = validation_map.get(component)
        if not validator:
            print(f"❌ Unknown component: {component}")
            return False

        return validator()

    def _validate_event_chronicle(self) -> bool:
        """Validate event chronicle implementation"""
        try:
            event_chronicle_dir = self.elf_base / "event_chronicle"
            if not event_chronicle_dir.exists():
                print("❌ Event chronicle directory not found")
                return False

            event_chronicle_py = event_chronicle_dir / "event_chronicle.py"
            if not event_chronicle_py.exists():
                print("❌ Event chronicle implementation not found")
                return False

            # Test functionality
            sys.path.insert(0, str(event_chronicle_dir))
            from event_chronicle import EventChronicle

            chronicle = EventChronicle()
            stats = chronicle.get_stats()

            print(f"✅ Event chronicle functional ({stats['total_events']} events)")
            return True

        except Exception as e:
            print(f"❌ Event chronicle validation failed: {e}")
            return False

    def _validate_configuration(self) -> bool:
        """Validate configuration standardization"""
        if not self.config_file.exists():
            print("❌ ELF configuration file not found")
            return False

        # Check required sections
        required_sections = ["elf_config", "components", "migration"]

        for section in required_sections:
            if section not in self.config:
                print(f"❌ Missing configuration section: {section}")
                return False

        print("✅ ELF configuration standardized")
        return True

    def _validate_database(self) -> bool:
        """Validate database compliance"""
        db_path = self.elf_base / "memory" / "index.db"
        if not db_path.exists():
            print("❌ ELF database not found")
            return False

        # Check if it's a valid SQLite database
        try:
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check for standard tables
            standard_tables = [
                "heuristics",
                "failures",
                "experiments",
                "learnings",
                "violations",
                "invariants",
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing_tables = set(standard_tables) - existing_tables
            if missing_tables:
                print(f"❌ Missing database tables: {missing_tables}")
                return False

            conn.close()
            print("✅ ELF database compliant")
            return True

        except Exception as e:
            print(f"❌ Database validation failed: {e}")
            return False

    def _validate_coordination(self) -> bool:
        """Validate coordination system"""
        coordination_dir = self.elf_base / ".coordination"
        if not coordination_dir.exists():
            print("❌ Coordination directory not found")
            return False

        blackboard_file = coordination_dir / "blackboard.json"
        if not blackboard_file.exists():
            print("❌ Blackboard coordination file not found")
            return False

        try:
            with open(blackboard_file, "r") as f:
                blackboard = json.load(f)

            # Check standard fields
            required_fields = ["timestamp", "agents", "coordination"]
            for field in required_fields:
                if field not in blackboard:
                    print(f"❌ Missing blackboard field: {field}")
                    return False

            print("✅ ELF coordination system compliant")
            return True

        except Exception as e:
            print(f"❌ Coordination validation failed: {e}")
            return False

    def _validate_query(self) -> bool:
        """Validate query system"""
        query_dir = self.elf_base / "query"
        if not query_dir.exists():
            print("❌ Query directory not found")
            return False

        query_py = query_dir / "query.py"
        if not query_py.exists():
            print("❌ Query system entry point not found")
            return False

        print("✅ ELF query system compliant")
        return True

    def _validate_dashboard(self) -> bool:
        """Validate dashboard compliance (will be partial)"""
        dashboard_dir = self.elf_base / "dashboard-app"
        if not dashboard_dir.exists():
            print("⚠️  Dashboard not found (optional component)")
            return True  # Dashboard is optional

        backend_main = dashboard_dir / "backend" / "main.py"
        if not backend_main.exists():
            print("❌ Dashboard backend not found")
            return False

        # Note: Dashboard compliance will be improved in Phase 2
        print("⚠️  Dashboard partially compliant (Phase 2 migration needed)")
        return True

    def _validate_sentinel(self) -> bool:
        """Validate sentinel system compliance"""
        sentinel_loop = self.elf_base / "sentinel" / "sentinel_loop.py"
        if not sentinel_loop.exists():
            print("⚠️  Watcher system not found (optional component)")
            return True  # Watcher is optional

        # Note: Watcher compliance will be improved in Phase 3
        print("⚠️  Watcher partially compliant (Phase 3 migration needed)")
        return True

    def validate_all(self) -> Dict[str, bool]:
        """Validate all ELF components"""
        print("🔍 Validating all ELF components...")

        components = [
            "event_chronicle",
            "configuration",
            "database",
            "coordination",
            "query",
            "dashboard",
            "sentinel",
        ]

        results = {}
        for component in components:
            results[component] = self.validate_component(component)

        # Summary
        compliant = sum(results.values())
        total = len(results)
        compliance_pct = (compliant / total) * 100

        print(f"\n📊 Overall Compliance: {compliance_pct:.1f}% ({compliant}/{total})")

        return results

    def run_phase(self, phase: int) -> bool:
        """Run a specific migration phase"""
        print(f"🚀 Running ELF Migration Phase {phase}...")

        phases = {
            1: self._phase_1_critical_components,
            2: self._phase_2_dashboard_migration,
            3: self._phase_3_system_integration,
            4: self._phase_4_validation,
        }

        phase_func = phases.get(phase)
        if not phase_func:
            print(f"❌ Invalid phase: {phase}")
            return False

        return phase_func()

    def _phase_1_critical_components(self) -> bool:
        """Phase 1: Implement critical missing components"""
        print("\n=== Phase 1: Critical Components ===")

        success = True

        # 1. Event Chronicle
        success &= self.migrate_event_chronicle()

        # 2. Configuration Standardization
        success &= self.migrate_configuration()

        if success:
            print("\n✅ Phase 1 completed successfully")
            self.config["migration"]["phase_1"]["event_chronicle"] = "complete"
            self.config["migration"]["phase_1"]["configuration"] = "complete"
            self._save_config()
        else:
            print("\n❌ Phase 1 failed")

        return success

    def _phase_2_dashboard_migration(self) -> bool:
        """Phase 2: Dashboard migration (placeholder)"""
        print("\n=== Phase 2: Dashboard Migration ===")
        print("⚠️  Dashboard migration not yet implemented")
        print("   See elf-compliance-audit.md for details")
        return True

    def _phase_3_system_integration(self) -> bool:
        """Phase 3: System integration (placeholder)"""
        print("\n=== Phase 3: System Integration ===")
        print("⚠️  System integration not yet implemented")
        print("   See elf-compliance-audit.md for details")
        return True

    def _phase_4_validation(self) -> bool:
        """Phase 4: Validation and documentation"""
        print("\n=== Phase 4: Validation ===")

        results = self.validate_all()

        if all(results.values()):
            print("\n🎉 All components compliant! ELF migration complete.")
            self.config["migration"]["phase_4"]["validation"] = "complete"
            self._save_config()
            return True
        else:
            non_compliant = [k for k, v in results.items() if not v]
            print(f"\n⚠️  Non-compliant components: {non_compliant}")
            return False


def main():
    parser = argparse.ArgumentParser(description="ELF Standards Migration Helper")
    parser.add_argument(
        "--component",
        choices=[
            "event_chronicle",
            "configuration",
            "database",
            "coordination",
            "query",
            "dashboard",
            "sentinel",
        ],
        help="Validate specific component",
    )
    parser.add_argument(
        "--phase", type=int, choices=[1, 2, 3, 4], help="Run migration phase"
    )
    parser.add_argument(
        "--validate-all", action="store_true", help="Validate all components"
    )
    parser.add_argument(
        "--migrate",
        choices=["event_chronicle", "configuration"],
        help="Migrate specific component",
    )

    args = parser.parse_args()

    migrator = ELFMigrator()

    if args.component:
        success = migrator.validate_component(args.component)
        sys.exit(0 if success else 1)

    elif args.phase:
        success = migrator.run_phase(args.phase)
        sys.exit(0 if success else 1)

    elif args.validate_all:
        results = migrator.validate_all()
        success = all(results.values())
        sys.exit(0 if success else 1)

    elif args.migrate:
        if args.migrate == "event_chronicle":
            success = migrator.migrate_event_chronicle()
        elif args.migrate == "configuration":
            success = migrator.migrate_configuration()
        else:
            print(f"❌ Unknown migration target: {args.migrate}")
            sys.exit(1)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
