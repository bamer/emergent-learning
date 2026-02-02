#!/usr/bin/env python3
"""
Script d'automatisation avancée pour la rotation des logs
- Rotation basée sur taille ET temps
- Notifications et alertes
- Nettoyage intelligent des archives
- Monitoring de santé du système
"""

import os
import sys
import time
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
LOG_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
CONFIG_FILE = Path(
    "/home/bamer/.opencode/emergent-learning/scripts/log_rotation_config.json"
)
MAX_SIZE_MB = 5  # Rotation quand fichier dépasse 5MB
MAX_AGE_HOURS = 24  # Rotation quand fichier plus vieux que 24h
MAX_ARCHIVES = 10  # Nombre maximum d'archives à garder
CRITICAL_SIZE_MB = 20  # Taille critique pour alerte
STATUS_FILE = Path(
    "/home/bamer/.opencode/emergent-learning/logs/auto_rotation_status.json"
)


class AutoLogRotator:
    def __init__(self):
        self.log_dir = LOG_DIR
        self.status_file = STATUS_FILE
        self.load_config()

    def load_config(self):
        """Charge la configuration depuis fichier"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.max_size_mb = config.get("max_size_mb", MAX_SIZE_MB)
                    self.max_age_hours = config.get("max_age_hours", MAX_AGE_HOURS)
                    self.max_archives = config.get("max_archives", MAX_ARCHIVES)
                    self.critical_size_mb = config.get(
                        "critical_size_mb", CRITICAL_SIZE_MB
                    )
            except Exception as e:
                print(f"[AutoRotate] Erreur chargement config: {e}")
                self.max_size_mb = MAX_SIZE_MB
                self.max_age_hours = MAX_AGE_HOURS
                self.max_archives = MAX_ARCHIVES
                self.critical_size_mb = CRITICAL_SIZE_MB
        else:
            # Crée config par défaut
            default_config = {
                "max_size_mb": MAX_SIZE_MB,
                "max_age_hours": MAX_AGE_HOURS,
                "max_archives": MAX_ARCHIVES,
                "critical_size_mb": CRITICAL_SIZE_MB,
                "auto_cleanup": True,
                "notifications": True,
            }
            try:
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CONFIG_FILE, "w") as f:
                    json.dump(default_config, f, indent=2)
                print(f"[AutoRotate] Configuration créée: {CONFIG_FILE}")
            except Exception as e:
                print(f"[AutoRotate] Erreur création config: {e}")

            self.max_size_mb = MAX_SIZE_MB
            self.max_age_hours = MAX_AGE_HOURS
            self.max_archives = MAX_ARCHIVES
            self.critical_size_mb = CRITICAL_SIZE_MB

    def get_file_info(self, file_path: Path) -> Dict:
        """Retourne informations détaillées sur un fichier"""
        try:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600

            return {
                "path": str(file_path),
                "name": file_path.name,
                "size_mb": size_mb,
                "size_bytes": stat.st_size,
                "age_hours": age_hours,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "needs_rotation": size_mb > self.max_size_mb
                or age_hours > self.max_age_hours,
                "critical": size_mb > self.critical_size_mb,
            }
        except Exception as e:
            return {
                "path": str(file_path),
                "name": file_path.name,
                "error": str(e),
                "needs_rotation": False,
                "critical": False,
            }

    def rotate_file(self, file_path: Path) -> bool:
        """Effectue la rotation d'un fichier"""
        try:
            # Vérifie que le fichier existe et a du contenu
            if not file_path.exists() or file_path.stat().st_size == 0:
                return False

            # Nom du fichier d'archive avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{file_path.stem}.{timestamp}.gz"
            archive_path = self.log_dir / archive_name

            # Compression du fichier
            with open(file_path, "rb") as f_in:
                with gzip.open(archive_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Vide le fichier original
            with open(file_path, "w") as f:
                f.write(
                    f"=== Log rotation performed at {datetime.now().isoformat()} ===\n"
                )

            print(f"[AutoRotate] Fichier rotation: {file_path.name} -> {archive_name}")
            return True

        except Exception as e:
            print(f"[AutoRotate] Erreur rotation {file_path.name}: {e}")
            return False

    def cleanup_archives(self, log_name: str) -> int:
        """Nettoie les anciennes archives (garde seulement les MAX_ARCHIVES plus récentes)"""
        try:
            pattern = f"{log_name}.*.gz"
            archive_files = sorted(
                self.log_dir.glob(pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            # Supprime les archives en trop
            deleted_count = 0
            for old_archive in archive_files[self.max_archives :]:
                old_archive.unlink()
                print(f"[AutoRotate] Archive supprimée: {old_archive.name}")
                deleted_count += 1

            return deleted_count

        except Exception as e:
            print(f"[AutoRotate] Erreur nettoyage {log_name}: {e}")
            return 0

    def send_notification(self, message: str, level: str = "INFO"):
        """Envoie notification (logs + fichier de statut)"""
        timestamp = datetime.now().isoformat()
        log_message = f"[{timestamp}] [{level}] {message}"

        # Log la notification
        print(log_message)

        # Sauvegarde dans fichier de statut
        try:
            status = self.get_status()
            if "notifications" not in status:
                status["notifications"] = []

            status["notifications"].append(
                {"timestamp": timestamp, "level": level, "message": message}
            )

            # Garde seulement les 50 dernières notifications
            if len(status["notifications"]) > 50:
                status["notifications"] = status["notifications"][-50:]

            self.save_status(status)

        except Exception as e:
            print(f"[AutoRotate] Erreur sauvegarde notification: {e}")

    def get_status(self) -> Dict:
        """Récupère le statut depuis fichier"""
        try:
            if self.status_file.exists():
                with open(self.status_file, "r") as f:
                    return json.load(f)
            return {
                "last_run": None,
                "files_processed": 0,
                "files_rotated": 0,
                "archives_deleted": 0,
                "errors": [],
                "notifications": [],
            }
        except Exception:
            return {}

    def save_status(self, status: Dict):
        """Sauvegarde le statut dans fichier"""
        try:
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"[AutoRotate] Erreur sauvegarde statut: {e}")

    def run_rotation_check(self) -> Dict:
        """Lance une vérification complète et rotation automatique"""
        start_time = datetime.now()
        status = self.get_status()

        # Met à jour dernière exécution
        status["last_run"] = start_time.isoformat()
        status["files_processed"] = 0
        status["files_rotated"] = 0
        status["archives_deleted"] = 0
        status["errors"] = []

        # Parcourt tous les fichiers de log
        for log_file in self.log_dir.glob("*.log"):
            if log_file.name.startswith("."):
                continue

            status["files_processed"] += 1
            file_info = self.get_file_info(log_file)

            if "error" in file_info:
                status["errors"].append(f"{log_file.name}: {file_info['error']}")
                continue

            # Vérifie si rotation nécessaire
            if file_info["needs_rotation"]:
                if self.rotate_file(log_file):
                    status["files_rotated"] += 1

                    # Notification de rotation
                    if file_info["critical"]:
                        self.send_notification(
                            f"ROTATION CRITIQUE: {log_file.name} ({file_info['size_mb']:.2f}MB) - Size/age threshold",
                            "WARN",
                        )
                    else:
                        self.send_notification(
                            f"Rotation: {log_file.name} ({file_info['size_mb']:.2f}MB, {file_info['age_hours']:.1f}h)",
                            "INFO",
                        )

                # Nettoie les anciennes archives
                deleted = self.cleanup_archives(log_file.stem)
                status["archives_deleted"] += deleted

            # Alerte taille critique même sans rotation
            elif file_info["critical"]:
                self.send_notification(
                    f"ALERTE TAILLE CRITIQUE: {log_file.name} ({file_info['size_mb']:.2f}MB > {self.critical_size_mb}MB)",
                    "WARN",
                )

        # Sauvegarde le statut final
        execution_time = (datetime.now() - start_time).total_seconds()
        status["execution_time_seconds"] = execution_time
        self.save_status(status)

        # Notification de fin
        self.send_notification(
            f"Rotation automatique terminée: {status['files_processed']} fichiers, {status['files_rotated']} rotations, {status['archives_deleted']} archives supprimées ({execution_time:.1f}s)",
            "INFO",
        )

        return status


def main():
    """Point d'entrée principal"""
    rotator = AutoLogRotator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            # Affiche statut détaillé
            status = rotator.get_status()
            print(
                f"[AutoRotate] Dernière exécution: {status.get('last_run', 'Jamais')}"
            )
            print(f"[AutoRotate] Fichiers traités: {status.get('files_processed', 0)}")
            print(f"[AutoRotate] Rotations: {status.get('files_rotated', 0)}")
            print(
                f"[AutoRotate] Archives supprimées: {status.get('archives_deleted', 0)}"
            )
            print(
                f"[AutoRotate] Temps exécution: {status.get('execution_time_seconds', 0):.1f}s"
            )

            if status.get("errors"):
                print(f"[AutoRotate] Erreurs: {len(status['errors'])}")
                for error in status["errors"][-5:]:  # Affiche 5 dernières erreurs
                    print(f"  - {error}")

            return

        elif command == "run":
            # Lance rotation immédiatement
            print(f"[AutoRotate] === LANCEMENT ROTATION AUTOMATIQUE ===")
            status = rotator.run_rotation_check()
            print(f"[AutoRotate] === TERMINÉ ===")
            return

    # Par défaut, lance la vérification
    rotator.run_rotation_check()


if __name__ == "__main__":
    main()
