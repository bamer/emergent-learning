#!/usr/bin/env python3
"""
Surveillance en temps réel des logs avec déclenchement automatique de rotation
Surveille la taille des fichiers et déclenche rotation quand seuils dépassés
"""

import os
import sys
import time
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Configuration
LOG_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
ROTATION_SCRIPT = "/home/bamer/.opencode/emergent-learning/scripts/auto_log_rotation.py"
WATCH_CONFIG = "/home/bamer/.opencode/emergent-learning/scripts/watch_config.json"
STATUS_FILE = Path("/home/bamer/.opencode/emergent-learning/logs/watcher_status.json")

# Seuils par fichier (taille en MB)
DEFAULT_THRESHOLDS = {
    "event-bridge.log": {"size_mb": 1, "interval_minutes": 5},  # Log très actif
    "watcher.log": {"size_mb": 2, "interval_minutes": 10},
    "orchestrator.log": {"size_mb": 2, "interval_minutes": 15},
    "backend.log": {"size_mb": 3, "interval_minutes": 20},
    "opencode-server.log": {"size_mb": 3, "interval_minutes": 20},
    "frontend.log": {"size_mb": 2, "interval_minutes": 15},
    "researcher.log": {"size_mb": 2, "interval_minutes": 15},
    "architect.log": {"size_mb": 2, "interval_minutes": 15},
    "creative.log": {"size_mb": 2, "interval_minutes": 15},
    "ceo.log": {"size_mb": 1, "interval_minutes": 10},
}

# Seuils globaux
GLOBAL_SIZE_THRESHOLD_MB = 5  # Rotation si TOUT le répertoire dépasse cette taille
GLOBAL_FILE_COUNT_THRESHOLD = 15  # Rotation si plus de 15 fichiers actifs


class LogWatcher:
    def __init__(self):
        self.log_dir = LOG_DIR
        self.config_file = Path(WATCH_CONFIG)
        self.status_file = STATUS_FILE
        self.running = True
        self.load_config()
        self.last_check = {}

    def load_config(self):
        """Charge ou crée la configuration des seuils"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.thresholds = config.get("thresholds", DEFAULT_THRESHOLDS)
                    self.global_size_mb = config.get(
                        "global_size_mb", GLOBAL_SIZE_THRESHOLD_MB
                    )
                    self.global_file_count = config.get(
                        "global_file_count", GLOBAL_FILE_COUNT_THRESHOLD
                    )
            except Exception as e:
                print(f"[Watch] Erreur chargement config: {e}")
                self.thresholds = DEFAULT_THRESHOLDS.copy()
                self.global_size_mb = GLOBAL_SIZE_THRESHOLD_MB
                self.global_file_count = GLOBAL_FILE_COUNT_THRESHOLD
        else:
            # Crée config par défaut
            self.thresholds = DEFAULT_THRESHOLDS.copy()
            self.global_size_mb = GLOBAL_SIZE_THRESHOLD_MB
            self.global_file_count = GLOBAL_FILE_COUNT_THRESHOLD
            self.save_config()

    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            config = {
                "thresholds": self.thresholds,
                "global_size_mb": self.global_size_mb,
                "global_file_count": self.global_file_count,
                "last_updated": datetime.now().isoformat(),
            }
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            print(f"[Watch] Configuration sauvegardée: {self.config_file}")
        except Exception as e:
            print(f"[Watch] Erreur sauvegarde config: {e}")

    def get_file_size_mb(self, file_path: Path) -> float:
        """Retourne la taille d'un fichier en MB"""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except:
            return 0.0

    def should_check_file(self, file_name: str) -> bool:
        """Vérifie si on doit vérifier ce fichier selon l'intervalle configuré"""
        if file_name not in self.last_check:
            return True

        last_check_time = self.last_check[file_name]
        interval_minutes = self.thresholds.get(file_name, {}).get(
            "interval_minutes", 15
        )

        time_since_check = (datetime.now() - last_check_time).total_seconds() / 60
        return time_since_check >= interval_minutes

    def get_directory_stats(self) -> Dict:
        """Retourne les statistiques du répertoire de logs"""
        try:
            log_files = list(self.log_dir.glob("*.log"))
            active_logs = [f for f in log_files if f.stat().st_size > 0]

            total_size = sum(f.stat().st_size for f in active_logs) / (1024 * 1024)

            return {
                "total_files": len(log_files),
                "active_files": len(active_logs),
                "total_size_mb": total_size,
                "files": [
                    {
                        "name": f.name,
                        "size_mb": self.get_file_size_mb(f),
                        "last_modified": datetime.fromtimestamp(
                            f.stat().st_mtime
                        ).isoformat(),
                    }
                    for f in active_logs
                ],
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_files": 0,
                "active_files": 0,
                "total_size_mb": 0,
            }

    def check_global_thresholds(self, stats: Dict) -> List[str]:
        """Vérifie les seuils globaux et retourne les raisons de rotation"""
        reasons = []

        if stats.get("total_size_mb", 0) > self.global_size_mb:
            reasons.append(
                f"Taille globale: {stats['total_size_mb']:.2f}MB > {self.global_size_mb}MB"
            )

        if stats.get("active_files", 0) > self.global_file_count:
            reasons.append(
                f"Nombre de fichiers: {stats['active_files']} > {self.global_file_count}"
            )

        return reasons

    def check_file_thresholds(self, file_path: Path) -> List[str]:
        """Vérifie les seuils spécifiques d'un fichier"""
        file_name = file_path.name
        size_mb = self.get_file_size_mb(file_path)

        reasons = []

        if file_name in self.thresholds:
            threshold = self.thresholds[file_name]
            size_limit = threshold.get("size_mb", 2)

            if size_mb > size_limit:
                reasons.append(f"Fichier {file_name}: {size_mb:.2f}MB > {size_limit}MB")

        return reasons

    def trigger_rotation(self, reason: str) -> bool:
        """Déclenche la rotation des logs"""
        try:
            import subprocess

            print(f"[Watch] 🚨 TRIGGER ROTATION: {reason}")

            result = subprocess.run(
                [sys.executable, ROTATION_SCRIPT, "run"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print(f"[Watch] ✅ Rotation réussie")
                self.log_event("rotation_success", reason, result.stdout)
                return True
            else:
                print(f"[Watch] ❌ Erreur rotation: {result.stderr}")
                self.log_event("rotation_error", reason, result.stderr)
                return False

        except Exception as e:
            print(f"[Watch] ❌ Erreur déclenchement rotation: {e}")
            self.log_event("rotation_exception", reason, str(e))
            return False

    def log_event(self, event_type: str, reason: str, details: str):
        """Enregistre un événement dans le fichier de statut"""
        try:
            status = self.get_status()
            if "events" not in status:
                status["events"] = []

            status["events"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": event_type,
                    "reason": reason,
                    "details": details[:500],  # Limite la taille des détails
                }
            )

            # Garde seulement les 100 derniers événements
            if len(status["events"]) > 100:
                status["events"] = status["events"][-100:]

            self.save_status(status)

        except Exception as e:
            print(f"[Watch] Erreur enregistrement événement: {e}")

    def get_status(self) -> Dict:
        """Récupère le statut actuel"""
        try:
            if self.status_file.exists():
                with open(self.status_file, "r") as f:
                    return json.load(f)
            return {
                "running": False,
                "start_time": None,
                "last_check": None,
                "checks_performed": 0,
                "rotations_triggered": 0,
                "events": [],
            }
        except:
            return {}

    def save_status(self, status: Dict):
        """Sauvegarde le statut"""
        try:
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"[Watch] Erreur sauvegarde statut: {e}")

    def run_monitoring(self):
        """Lance la surveillance en continu"""
        print(f"[Watch] 🚀 Démarrage surveillance logs...")
        print(f"[Watch] Répertoire: {self.log_dir}")
        print(
            f"[Watch] Seuils globaux: {self.global_size_mb}MB / {self.global_file_count} fichiers"
        )

        # Met à jour le statut
        status = self.get_status()
        status["running"] = True
        status["start_time"] = datetime.now().isoformat()
        self.save_status(status)

        while self.running:
            try:
                # Vérifie les statistiques globales
                stats = self.get_directory_stats()
                global_reasons = self.check_global_thresholds(stats)

                if global_reasons:
                    for reason in global_reasons:
                        self.trigger_rotation(f"Global: {reason}")

                # Vérifie chaque fichier individuellement
                log_files = list(self.log_dir.glob("*.log"))
                for log_file in log_files:
                    if not self.should_check_file(log_file.name):
                        continue

                    self.last_check[log_file.name] = datetime.now()
                    file_reasons = self.check_file_thresholds(log_file)

                    if file_reasons:
                        for reason in file_reasons:
                            self.trigger_rotation(reason)

                # Met à jour le statut
                status = self.get_status()
                status["last_check"] = datetime.now().isoformat()
                status["checks_performed"] = status.get("checks_performed", 0) + 1
                self.save_status(status)

                # Attend avant prochaine vérification (30 secondes)
                time.sleep(30)

            except KeyboardInterrupt:
                print("\n[Watch] Arrêt demandé par utilisateur")
                break
            except Exception as e:
                print(f"[Watch] Erreur surveillance: {e}")
                time.sleep(60)  # Attend plus longtemps en cas d'erreur

        # Arrêt
        status = self.get_status()
        status["running"] = False
        status["stop_time"] = datetime.now().isoformat()
        self.save_status(status)
        print("[Watch] 🛑 Surveillance arrêtée")


def signal_handler(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    print(f"\n[Watch] Signal {signum} reçu, arrêt en cours...")
    global watcher
    if watcher:
        watcher.running = False


def main():
    """Point d'entrée principal"""
    global watcher
    watcher = LogWatcher()

    # Gestion des signaux pour arrêt propre
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            # Affiche le statut actuel
            status = watcher.get_status()
            print(
                f"[Watch] Surveillance {'✅ active' if status.get('running') else '❌ inactive'}"
            )
            print(f"[Watch] Démarré: {status.get('start_time', 'Jamais')}")
            print(
                f"[Watch] Dernière vérification: {status.get('last_check', 'Jamais')}"
            )
            print(f"[Watch] Vérifications: {status.get('checks_performed', 0)}")
            print(
                f"[Watch] Rotations déclenchées: {status.get('rotations_triggered', 0)}"
            )

            stats = watcher.get_directory_stats()
            if "error" not in stats:
                print(
                    f"[Watch] Fichiers actifs: {stats['active_files']}/{stats['total_files']}"
                )
                print(f"[Watch] Taille totale: {stats['total_size_mb']:.2f}MB")
            return

        elif command == "config":
            # Affiche la configuration
            print(f"[Watch] Configuration des seuils:")
            for file_name, threshold in watcher.thresholds.items():
                print(
                    f"  {file_name}: {threshold['size_mb']}MB (intervalle: {threshold['interval_minutes']}min)"
                )
            print(
                f"[Watch] Seuils globaux: {watcher.global_size_mb}MB / {watcher.global_file_count} fichiers"
            )
            return

    # Lance la surveillance
    watcher.run_monitoring()


if __name__ == "__main__":
    main()
