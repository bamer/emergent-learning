#!/usr/bin/env python3
"""
Test simplifié de l'API Orchestrator
"""

import requests
import json


def test_simple_api():
    """Test simple de l'API orchestrator"""

    print("🧪 Test de l'API Orchestrator Unifié")
    print("=" * 50)

    # Test statut de base
    print("1. Test du endpoint /status")
    try:
        response = requests.get("http://localhost:9998/status")
        print(f"   ✅ Statut: {response.status_code}")
        print(f"   📊 Données: {response.json()}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print("\n2. Test du endpoint /api/v1/ask avec données simplifiées")
    try:
        # Données simplifiées sans datetime
        test_data = {
            "component": "test_component",
            "request_type": "health_check",
            "data": {
                "component": "database",
                "test_timestamp": "2025-02-05T19:30:00",  # Chaîne au lieu de datetime
            },
        }

        response = requests.post("http://localhost:9998/api/v1/ask", json=test_data)
        print(f"   ✅ Statut: {response.status_code}")
        if response.status_code == 200:
            print(f"   📊 Réponse: {response.json()}")
        else:
            print(f"   ❌ Erreur: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print("\n3. Test de soumission de mission")
    try:
        mission_data = {
            "agent_type": "researcher",
            "mission": "Test de l'orchestrator unifié",
            "priority": 5,
        }

        response = requests.post(
            "http://localhost:9998/api/v1/mission", json=mission_data
        )
        print(f"   ✅ Statut: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 Mission ID: {result.get('mission_id', 'N/A')}")
            print(f"   📊 Statut: {result.get('status', 'N/A')}")
        else:
            print(f"   ❌ Erreur: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print("\n" + "=" * 50)
    print("🎯 Tests de l'API Orchestrator terminés")


if __name__ == "__main__":
    test_simple_api()
