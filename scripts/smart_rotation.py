#!/usr/bin/env python3
"""
Rotation intelligente des logs
Adapte son comportement selon l'état d'ELF détecté
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from elf_state_detector import ELFStateDetector
from auto_log_rotation import AutoLogRotator


class SmartLogRotator:
    def __init__(self):
        self.detector = ELFStateDetector()
        self.rotator = AutoLogRotator()

    def should_rotate(self, force: bool = False) -> tuple[bool, str]:
        """Détermine si rotation nécessaire selon l'état d'ELF"""

        # Force rotation si demandé
        if force:
            return True, "Rotation forcée demandée"

        # Récupère l'état d'ELF
        state = self.detector.get_current_state()
        if not state:
            # Pas d'état récent, fait une détection rapide
            state = self.detector.detect_elf_state()

        # Si ELF inactif, rotation minimale (seulement si logs vraiment anciens)
        if not state["elf_active"]:
            # Vérifie si logs vraiment anciens (>24h)
            stats = self.detector.check_log_activity()
            for log in stats["active_logs"]:
                if log["seconds_since_mod"] > 86400:  # >24h
                    return (
                        True,
                        f"ELF inactif mais log ancien: {log['name']} ({log['seconds_since_mod'] / 3600:.1f}h)",
                    )
            return False, "ELF inactif, logs récents"

        # Si ELF actif, rotation plus agressive
        stats = self.detector.check_log_activity()
        for log in stats["active_logs"]:
            if log["size_mb"] > 2.0:  # Rotation si >2MB quand ELF actif
                return (
                    True,
                    f"ELF actif, log volumineux: {log['name']} ({log['size_mb']:.2f}MB)",
                )

        # Si processus ELF mais pas de logs récents - rotation préventive
        if state["summary"]["active_processes"] > 0 and not stats["recent_activity"]:
            return True, "ELF actif mais logs stagnants"

        return False, f"ELF actif, logs normaux ({stats['total_size_mb']:.2f}MB total)"

    def run_smart_rotation(self, force: bool = False) -> dict:
        """Lance rotation intelligente"""
        start_time = datetime.now()

        print(f"[SmartRotation] 🚀 Rotation intelligente démarrée")
        print(f"[SmartRotation] Mode: {'Forcé' if force else 'Intelligent'}")

        # Détermine si rotation nécessaire
        should_rotate, reason = self.should_rotate(force)

        if not should_rotate:
            print(f"[SmartRotation] ⏭️  Rotation ignorée: {reason}")
            return {
                "rotated": False,
                "reason": reason,
                "execution_time_seconds": 0,
                "files_processed": 0,
            }

        print(f"[SmartRotation] ✅ Rotation décidée: {reason}")

        # Lance la rotation
        status = self.rotator.run_rotation_check()
        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "rotated": True,
            "reason": reason,
            "execution_time_seconds": execution_time,
            "files_processed": status.get("files_processed", 0),
            "files_rotated": status.get("files_rotated", 0),
            "archives_deleted": status.get("archives_deleted", 0),
        }

        print(f"[SmartRotation] 📊 Résultat: {result}")
        return result


def main():
    """Point d'entrée principal"""
    rotator = SmartLogRotator()

    force = len(sys.argv) > 1 and sys.argv[1] == "force"

    result = rotator.run_smart_rotation(force=force)

    # Retourne le résultat pour le crontab
    print(json.dumps(result, indent=2))

    return 0 if result["rotated"] else 0


if __name__ == "__main__":
    main()
