#!/usr/bin/env python3
"""
Détecteur d'état du système ELF
Détermine si ELF est actif ou inactif pour adapter le comportement
"""

import os
import sys
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class ELFStateDetector:
    def __init__(self):
        self.elf_dir = Path("/home/bamer/OPC_ELF")
        self.log_dir = Path("/home/bamer/OPC_ELF/Open_ELF/logs")
        self.dashboard_port = 3000  # Port du dashboard
        self.api_port = 8000  # Port de l'API backend
        self.state_file = Path(
            "/home/bamer/OPC_ELF/Open_ELF/logs/elf_state.json"
        )

        # Processus ELF typiques à surveiller
        self.elf_processes = [
            "python.*launcher.py",  # Sentinel
            "python.*event-bridge",  # Event bridge
            "npm.*dev",  # Dashboard
            "uvicorn.*backend",  # API backend
            "node.*server",  # Serveur OpenCode
        ]

        # Fichiers de logs critiques
        self.critical_logs = [
            "sentinel.log",
            "event_bridge.log",
            "backend.log",
            "orchestrator.log",
        ]

    def get_process_info(self, process_pattern: str) -> List[Dict]:
        """Trouve les processus correspondants au pattern"""
        matching_processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if process_pattern in cmdline and proc.is_running():
                        matching_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "cmdline": cmdline,
                                "status": proc.status(),
                                "create_time": proc.create_time(),
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"[StateDetect] Erreur détection processus: {e}")

        return matching_processes

    def check_elf_processes(self) -> Dict:
        """Vérifie si les processus ELF sont actifs"""
        active_processes = []
        process_summary = {}

        for pattern in self.elf_processes:
            processes = self.get_process_info(pattern)
            process_summary[pattern] = len(processes)
            active_processes.extend(processes)

        return {
            "total_processes": len(active_processes),
            "process_details": process_summary,
            "active": len(active_processes) > 0,
            "processes": active_processes,
        }

    def check_log_activity(self) -> Dict:
        """Vérifie l'activité récente des logs"""
        active_logs = []
        total_size = 0
        recent_activity = False

        for log_name in self.critical_logs:
            log_path = self.log_dir / log_name
            if log_path.exists():
                try:
                    stat = log_path.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)

                    # Considère "récent" si modifié dans les 5 dernières minutes
                    time_since_mod = (datetime.now() - modified_time).total_seconds()
                    is_recent = time_since_mod < 300  # 5 minutes

                    if is_recent:
                        recent_activity = True

                    log_info = {
                        "name": log_name,
                        "size_mb": size_mb,
                        "last_modified": modified_time.isoformat(),
                        "seconds_since_mod": time_since_mod,
                        "is_recent": is_recent,
                    }

                    active_logs.append(log_info)
                    total_size += size_mb

                except Exception as e:
                    print(f"[StateDetect] Erreur lecture log {log_name}: {e}")

        return {
            "total_logs": len(active_logs),
            "total_size_mb": total_size,
            "recent_activity": recent_activity,
            "active_logs": active_logs,
        }

    def check_dashboard_health(self) -> Dict:
        """Vérifie si le dashboard répond"""
        import requests
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        dashboard_status = {
            "reachable": False,
            "response_time": None,
            "status_code": None,
        }
        api_status = {"reachable": False, "response_time": None, "status_code": None}

        try:
            # Test dashboard
            start_time = time.time()
            response = requests.get(
                f"http://localhost:{self.dashboard_port}/health",
                timeout=5,
                verify=False,
            )
            dashboard_status["response_time"] = time.time() - start_time
            dashboard_status["status_code"] = response.status_code
            dashboard_status["reachable"] = response.status_code == 200

        except Exception:
            dashboard_status["reachable"] = False

        try:
            # Test API
            start_time = time.time()
            response = requests.get(
                f"http://localhost:{self.api_port}/api/v1/health",
                timeout=5,
                verify=False,
            )
            api_status["response_time"] = time.time() - start_time
            api_status["status_code"] = response.status_code
            api_status["reachable"] = response.status_code == 200

        except Exception:
            api_status["reachable"] = False

        return {
            "dashboard": dashboard_status,
            "api": api_status,
            "overall_healthy": dashboard_status["reachable"] or api_status["reachable"],
        }

    def detect_elf_state(self) -> Dict:
        """Détecte l'état global d'ELF"""
        detection_time = datetime.now()

        # Collecte toutes les métriques
        process_info = self.check_elf_processes()
        log_info = self.check_log_activity()
        health_info = self.check_dashboard_health()

        # Détermine l'état
        elf_active = (
            process_info["active"]  # Au moins un processus ELF
            or log_info["recent_activity"]  # Logs récents
            or health_info["overall_healthy"]  # Dashboard/API accessibles
        )

        # Score de confiance (0-100)
        confidence_score = 0
        if process_info["active"]:
            confidence_score += 40
        if log_info["recent_activity"]:
            confidence_score += 35
        if health_info["overall_healthy"]:
            confidence_score += 25

        # Détermine les recommandations
        if elf_active:
            recommendation = "surveillance_active"  # Surveiller intensivement
            interval_minutes = 5  # Vérifier toutes les 5 minutes
        else:
            recommendation = "surveillance_minimal"  # Surveiller轻度ment
            interval_minutes = 30  # Vérifier toutes les 30 minutes

        state_info = {
            "detection_time": detection_time.isoformat(),
            "elf_active": elf_active,
            "confidence_score": confidence_score,
            "recommendation": recommendation,
            "suggested_interval_minutes": interval_minutes,
            "processes": process_info,
            "logs": log_info,
            "health": health_info,
            "summary": {
                "active_processes": process_info["total_processes"],
                "active_logs": len(
                    [l for l in log_info["active_logs"] if l["is_recent"]]
                ),
                "dashboard_up": health_info["dashboard"]["reachable"],
                "api_up": health_info["api"]["reachable"],
            },
        }

        # Sauvegarde l'état
        self.save_state(state_info)

        return state_info

    def save_state(self, state_info: Dict):
        """Sauvegarde l'état détecté"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(state_info, f, indent=2)
        except Exception as e:
            print(f"[StateDetect] Erreur sauvegarde état: {e}")

    def get_current_state(self) -> Optional[Dict]:
        """Récupère le dernier état détecté"""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state_data = json.load(f)

                # Vérifie si l'état a moins de 10 minutes
                detection_time = datetime.fromisoformat(state_data["detection_time"])
                age_minutes = (datetime.now() - detection_time).total_seconds() / 60

                if age_minutes < 10:
                    return state_data

        except Exception as e:
            print(f"[StateDetect] Erreur lecture état: {e}")

        return None

    def print_status(self, state_info: Dict = None):
        """Affiche un résumé de l'état"""
        if state_info is None:
            state_info = self.get_current_state()
            if state_info is None:
                print("[StateDetect] Aucun état récent, détection en cours...")
                state_info = self.detect_elf_state()

        status_emoji = "✅" if state_info["elf_active"] else "⏸️"
        print(
            f"[StateDetect] {status_emoji} ELF {'ACTIF' if state_info['elf_active'] else 'INACTIF'}"
        )
        print(f"[StateDetect] Confiance: {state_info['confidence_score']}/100")
        print(f"[StateDetect] Recommandation: {state_info['recommendation']}")
        print(
            f"[StateDetect] Processus actifs: {state_info['summary']['active_processes']}"
        )
        print(f"[StateDetect] Logs récents: {state_info['summary']['active_logs']}")
        print(
            f"[StateDetect] Dashboard: {'✅' if state_info['summary']['dashboard_up'] else '❌'}"
        )
        print(f"[StateDetect] API: {'✅' if state_info['summary']['api_up'] else '❌'}")


def main():
    """Point d'entrée principal"""
    detector = ELFStateDetector()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            detector.print_status()
        elif command == "detect":
            state = detector.detect_elf_state()
            detector.print_status(state)
        elif command == "json":
            state = detector.detect_elf_state()
            print(json.dumps(state, indent=2))
        else:
            print(f"[StateDetect] Commande inconnue: {command}")
            print("Usage: python elf_state_detector.py {status|detect|json}")
    else:
        # Mode par défaut : affiche le statut
        detector.print_status()


if __name__ == "__main__":
    main()
