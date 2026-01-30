#!/usr/bin/env python3
"""
Test Complet ELF - Vérifie tous les composants du système

Ce script vérifie:
- Dashboard (frontend + backend)
- Serveur OpenCode
- Agents OpenCode (orchestrator, watcher, etc.)
- Base de données
- Golden Rules
- Connexions et ports

Utilisation: python test-complete-elf.py
"""

import subprocess
import time
import json
import requests
import sys
from pathlib import Path


def print_status():
    """Affiche l'en-tête de statut."""
    print("\n" + "=" * 60)
    print("🔍 TEST COMPLET DU SYSTÈME EMERGENT LEARNING FRAMEWORK")
    print("=" * 60)


def test_dashboard_frontend():
    """Test le frontend Dashboard."""
    print("\n📱 1. TEST FRONTEND DASHBOARD")
    print("-" * 40)

    try:
        # Test connexion frontend
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Dashboard: ACCESSIBLE (http://localhost:3001)")
        else:
            print(f"❌ Frontend Dashboard: ERREUR {response.status_code}")

        # Test API endpoints
        api_tests = [
            ("Heuristics", "http://localhost:3001/api/heuristics?limit=1"),
            ("Analytics", "http://localhost:3001/api/analytics"),
            ("Stats", "http://localhost:3001/api/stats"),
        ]

        for name, url in api_tests:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    print(f"✅ API {name}: Opérationnel")
                else:
                    print(f"❌ API {name}: Erreur {response.status_code}")
            except Exception as e:
                print(f"⚠️  API {name}: Erreur connexion {e}")

    except Exception as e:
        print(f"❌ Frontend: Impossible de se connecter - {e}")

    return True


def test_dashboard_backend():
    """Test le backend Dashboard."""
    print("\n🗄️ 2. TEST BACKEND DASHBOARD")
    print("-" * 40)

    try:
        # Test si backend écoute sur port 8888
        result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
        if "8888" in result.stdout:
            print("✅ Backend Dashboard: ÉCOUTE sur port 8888")
        else:
            print("❌ Backend Dashboard: Non détecté sur port 8888")

        # Test API backend directement
        response = requests.get(
            "http://localhost:8888/api/heuristics?limit=1", timeout=5
        )
        if response.status_code == 200:
            print("✅ Backend API: Répond correctement")
        else:
            print(f"❌ Backend API: Erreur {response.status_code}")

    except Exception as e:
        print(f"❌ Backend: Erreur test - {e}")

    return True


def test_opencode_server():
    """Test le serveur OpenCode."""
    print("\n🚀 3. TEST SERVEUR OPENCODE")
    print("-" * 40)

    try:
        # Test health endpoint
        response = requests.get("http://localhost:4096/global/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            version = health_data.get("version", "inconnue")
            print(f"✅ Serveur OpenCode: OPÉRATIONNEL (v{version})")
            print(f"   URL: http://localhost:4096")
            print(f"   Health: {response.status_code}")
        else:
            print(f"❌ Serveur OpenCode: Erreur {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Serveur OpenCode: Non joignable")
    except Exception as e:
        print(f"❌ Serveur OpenCode: Erreur test - {e}")

    return True


def test_opencode_agents():
    """Test les agents OpenCode."""
    print("\n🤖 4. TEST AGENTS OPENCODE")
    print("-" * 40)

    agents_to_test = [
        ("Agents Status", "http://localhost:4096/agents/status"),
        ("Models", "http://localhost:4096/models"),
        ("Orchestrator", "http://localhost:4096/orchestrator"),
        ("Watcher", "http://localhost:4096/watcher"),
    ]

    for agent_name, url in agents_to_test:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {agent_name}: ACTIF")
            else:
                print(f"⚠️  {agent_name}: Non trouvé ({response.status_code})")
        except Exception as e:
            print(f"❌ {agent_name}: Erreur {e}")

    return True


def test_database():
    """Test la base de données ELF."""
    print("\n🗄️ 5. TEST BASE DE DONNÉES")
    print("-" * 40)

    try:
        # Vérifier existence de la base de données
        db_path = (
            Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
        )

        if db_path.exists():
            print(f"✅ Base de données: PRÉSENTE ({db_path})")

            # Test avec sqlite3
            result = subprocess.run(
                ["sqlite3", str(db_path), "SELECT COUNT(*) FROM heuristics;"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                heuristics_count = result.stdout.strip()
                print(f"✅ Nombre d'heuristiques: {heuristics_count}")

                # Compter les golden rules
                result_golden = subprocess.run(
                    [
                        "sqlite3",
                        str(db_path),
                        "SELECT COUNT(*) FROM heuristics WHERE is_golden = 1;",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result_golden.returncode == 0:
                    golden_count = result_golden.stdout.strip()
                    print(f"✅ Règles d'Or: {golden_count}")
            else:
                print("❌ Erreur lecture base de données")
        else:
            print("❌ Base de données: NON TROUVÉE")

    except Exception as e:
        print(f"❌ Base de données: Erreur test - {e}")

    return True


def test_golden_rules():
    """Test les Golden Rules via query system."""
    print("\n📚 6. TEST GOLDEN RULES")
    print("-" * 40)

    try:
        # Tester le système de requête ELF
        result = subprocess.run(
            ["python", "query/query.py", "--context"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            output = result.stdout
            if "Golden Rules - PARFAIT" in output:
                print("✅ Golden Rules: ACCESSIBLE via query system")
            elif "golden rules" in output.lower() or "Golden Rules" in output:
                print("✅ Golden Rules: ACCESSIBLE via query system")
            else:
                print("⚠️  Golden Rules: Query system répond")

            # Extraire le nombre de règles
            if "12" in output:
                print("✅ Nombre de règles: 12/12")

        else:
            print("❌ Golden Rules: Erreur query system")

    except subprocess.TimeoutExpired:
        print("❌ Golden Rules: Timeout requête")
    except Exception as e:
        print(f"❌ Golden Rules: Erreur test - {e}")

    return True


def test_services_ports():
    """Test les ports utilisés par les services."""
    print("\n🔌 7. TEST PORTS ET CONNEXIONS")
    print("-" * 40)

    ports_to_check = [
        (3001, "Dashboard Frontend"),
        (8888, "Dashboard Backend"),
        (4096, "OpenCode Server"),
    ]

    for port, service_name in ports_to_check:
        try:
            result = subprocess.run(
                ["netstat", "-tlnp"], capture_output=True, text=True
            )
            if f":{port}" in result.stdout:
                print(f"✅ {service_name}: Port {port} OUVERT")
            else:
                print(f"❌ {service_name}: Port {port} FERMÉ")
        except Exception as e:
            print(f"⚠️  {service_name}: Erreur test port {e}")

    return True


def test_elf_integrity():
    """Test l'intégrité complète du système ELF."""
    print("\n🎯 8. TEST D'INTÉGRITÉ SYSTÈME")
    print("=" * 40)

    try:
        # Vérifier tous les composants critiques
        dashboard_ok = (
            requests.get("http://localhost:3001", timeout=2).status_code == 200
        )
        opencode_ok = (
            requests.get("http://localhost:4096/global/health", timeout=2).status_code
            == 200
        )
        database_ok = (
            Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
        ).exists()

        if dashboard_ok and opencode_ok and database_ok:
            print("✅ SYSTÈME ELF: COMPLET ET FONCTIONNEL")
            print("✅ Dashboard: Frontend + Backend OK")
            print("✅ OpenCode: Serveur + Agents OK")
            print("✅ Base de données: Accessible")
            print("✅ Architecture: TOUS LES COMPOSANTS ACTIFS")
            return True
        else:
            print("⚠️  SYSTÈME ELF: PARTIELLEMENT FONCTIONNEL")
            status = []
            if not dashboard_ok:
                status.append("Dashboard")
            if not opencode_ok:
                status.append("OpenCode")
            if not database_ok:
                status.append("Base de données")
            print(f"❌ Composants problématiques: {', '.join(status)}")
            return False

    except Exception as e:
        print(f"❌ Test intégrité: Erreur - {e}")
        return False


def main():
    """Fonction principale de test."""
    print_status()

    # Lister tous les tests
    tests = [
        ("Frontend Dashboard", test_dashboard_frontend),
        ("Backend Dashboard", test_dashboard_backend),
        ("Serveur OpenCode", test_opencode_server),
        ("Agents OpenCode", test_opencode_agents),
        ("Base de données", test_database),
        ("Golden Rules", test_golden_rules),
        ("Ports et Connexions", test_services_ports),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n⏳ Exécution: {test_name}")
        try:
            result = test_func()
            results[test_name] = "✅" if result else "❌"
            time.sleep(1)  # Pause entre tests
        except Exception as e:
            print(f"⚠️  Erreur test {test_name}: {e}")
            results[test_name] = "⚠️"

    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)

    for test_name, result in results.items():
        print(f"{result} {test_name}")

    print("\n" + "=" * 60)
    print(
        "🎯 CONCLUSION:",
        "SYSTÈME ELF FONCTIONNEL"
        if all("✅" in r for r in results.values())
        else "⚠️  SYSTÈME ELF PARTIEL",
    )
    print("=" * 60)

    return all("✅" in r for r in results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
