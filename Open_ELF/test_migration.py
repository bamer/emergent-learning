#!/usr/bin/env python3
"""
Test de migration - Vérifie que tout fonctionne après le grand ménage
"""

import sys
from pathlib import Path

# Ajouter le chemin pour les imports
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_manager():
    """Test que AgentManager fonctionne"""
    print("🧪 Test 1: AgentManager...")
    try:
        from agents.agent_manager import AgentManager, get_agent_manager
        
        # Créer une instance
        manager = AgentManager()
        agents = manager.list_agents()
        
        print(f"   ✅ AgentManager chargé avec {len(agents)} agents")
        print(f"   📋 Agents disponibles: {', '.join(agents[:5])}...")
        
        # Vérifier les méthodes de convenance
        methods = ['watcher', 'sentinel', 'ceo', 'researcher', 'architect', 'skeptic', 'creative']
        for method in methods:
            if hasattr(manager, method):
                print(f"   ✅ Méthode {method}() disponible")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_deprecated_files_removed():
    """Test que les fichiers obsolètes sont supprimés"""
    print("\n🧪 Test 2: Fichiers obsolètes supprimés...")
    
    elf_dir = Path(__file__).parent
    deprecated_files = [
        elf_dir / "agents" / "base_agent.py",
        elf_dir / "agents" / "elf_ai_client.py"
    ]
    
    all_removed = True
    for file_path in deprecated_files:
        if file_path.exists():
            print(f"   ⚠️  {file_path.name} existe encore")
            all_removed = False
        else:
            print(f"   ✅ {file_path.name} supprimé")
    
    return all_removed


def test_escalation_endpoints():
    """Test que les endpoints d'escalades existent"""
    print("\n🧪 Test 3: Endpoints d'escalades...")
    
    try:
        monitoring_file = Path(__file__).parent / "dashboard-app" / "backend" / "routers" / "monitoring.py"
        
        if not monitoring_file.exists():
            print(f"   ❌ Fichier monitoring.py non trouvé")
            return False
        
        content = monitoring_file.read_text()
        
        # Vérifier les endpoints
        endpoints = [
            '@router.get("/escalations")',
            '@router.get("/escalations/summary")',
            'async def get_escalations(',
            'async def get_escalations_summary('
        ]
        
        all_present = True
        for endpoint in endpoints:
            if endpoint in content:
                print(f"   ✅ Endpoint trouvé: {endpoint[:50]}...")
            else:
                print(f"   ❌ Endpoint manquant: {endpoint}")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_no_deprecated_usage():
    """Test qu'aucun fichier n'utilise les imports obsolètes"""
    print("\n🧪 Test 4: Vérification des imports obsolètes...")
    
    import subprocess
    
    elf_dir = Path(__file__).parent
    
    # Rechercher les imports obsolètes
    patterns = [
        r"from.*base_agent.*import",
        r"import.*BaseAgent",
        r"from.*elf_ai_client.*import",
        r"import.*ELFAIClient"
    ]
    
    found_deprecated = False
    
    for pattern in patterns:
        result = subprocess.run(
            ["grep", "-r", "-l", pattern, str(elf_dir)],
            capture_output=True,
            text=True
        )
        
        # Ignorer les fichiers de backup et __pycache__
        files = [f for f in result.stdout.strip().split('\n') 
                 if f and '__pycache__' not in f and '.pyc' not in f]
        
        if files and files[0]:
            print(f"   ⚠️  Pattern '{pattern[:30]}...' trouvé dans:")
            for f in files[:3]:  # Limiter l'affichage
                if f:
                    print(f"      - {f}")
            found_deprecated = True
    
    if not found_deprecated:
        print("   ✅ Aucun import obsolète trouvé")
    
    return not found_deprecated


def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("🧪 TESTS DE MIGRATION Open_ELF")
    print("=" * 60)
    
    tests = [
        test_agent_manager,
        test_deprecated_files_removed,
        test_escalation_endpoints,
        test_no_deprecated_usage
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n   ❌ Test échoué avec exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passés: {passed}/{total}")
    
    if passed == total:
        print("\n✅ TOUS LES TESTS PASSENT - Migration réussie!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(main())
