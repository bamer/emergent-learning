#!/usr/bin/env python3
"""
Démonstration du AgentManager

Ce fichier montre comment utiliser le nouveau AgentManager pour interroger
les agents IA avec leurs vrais prompts système chargés depuis les fichiers .md

Usage:
    python examples/agent_manager_demo.py
"""

import sys
import json
from pathlib import Path

# Ajouter le parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_manager import AgentManager, get_agent_manager


def demo_basic_usage():
    """Démonstration de l'utilisation de base"""
    print("\n" + "=" * 70)
    print("DÉMONSTRATION 1: Utilisation de base")
    print("=" * 70)
    
    # Créer le manager
    manager = AgentManager()
    
    # Lister les agents disponibles
    print("\n📋 Agents disponibles:")
    for agent_name in manager.list_agents():
        info = manager.get_agent_info(agent_name)
        print(f"  • {agent_name:20s} - {info['description'][:50]}...")
    
    print(f"\n✅ Total: {len(manager.list_agents())} agents chargés")


def demo_agent_info():
    """Affiche les informations détaillées d'un agent"""
    print("\n" + "=" * 70)
    print("DÉMONSTRATION 2: Informations sur un agent")
    print("=" * 70)
    
    manager = get_agent_manager()
    
    # Info sur le watcher
    info = manager.get_agent_info("watcher")
    if info:
        print(f"\n🔍 Agent: watcher")
        print(f"  Description: {info['description']}")
        print(f"  Modèle: {info['model']}")
        print(f"  Tags: {', '.join(info['tags']) if info['tags'] else 'Aucun'}")
        print(f"  Session active: {'Oui' if info['has_session'] else 'Non'}")


def demo_ask_agent():
    """Démontre comment interroger un agent"""
    print("\n" + "=" * 70)
    print("DÉMONSTRATION 3: Interroger un agent")
    print("=" * 70)
    
    manager = get_agent_manager()
    
    # Note: Cette démo ne fait pas de vrai appel API pour éviter de consommer des tokens
    # mais montre la syntaxe correcte
    
    print("\n📝 Exemple de requête au Watcher:")
    print("-" * 70)
    
    example_request = "Analyze the current system state and identify any anomalies"
    
    print(f"\nCode:")
    print(f"  result = manager.watcher(\"{example_request}\")")
    print(f"  # ou: manager.ask_agent(\"watcher\", \"{example_request}\")")
    
    print(f"\nStructure de la réponse:")
    example_response = {
        "success": True,
        "agent": "watcher",
        "request": example_request,
        "response": "[Réponse de l'agent Watcher avec son vrai prompt système]",
        "session_id": "abc123...",
        "timestamp": "2026-02-07T15:30:00",
        "model_used": "nvidia/minimaxai/minimax-m2"
    }
    print(json.dumps(example_response, indent=2))


def demo_with_context():
    """Montre comment utiliser le contexte"""
    print("\n" + "=" * 70)
    print("DÉMONSTRATION 4: Utiliser le contexte")
    print("=" * 70)
    
    manager = get_agent_manager()
    
    print("\n📝 Exemple avec contexte:")
    print("-" * 70)
    
    context = {
        "system_state": {
            "event_bridge_healthy": True,
            "services": {
                "dashboard": True,
                "watcher": True,
                "sentinel": False  # Problème ici!
            }
        },
        "timestamp": "2026-02-07T15:30:00",
        "urgency": "high"
    }
    
    print("\nContext:")
    print(json.dumps(context, indent=2))
    
    print("\nCode:")
    print('  result = manager.sentinel(')
    print('      "Analyze system health and recommend actions",')
    print('      context=context')
    print('  )')
    
    print("\nL'agent reçoit le contexte + la requête, mais utilise SON vrai prompt système")
    print("(chargé depuis sentinel.md, pas un prompt hardcodé!)")


def demo_convenience_methods():
    """Montre les méthodes de convenance"""
    print("\n" + "=" * 70)
    print("DÉMONSTRATION 5: Méthodes de convenance")
    print("=" * 70)
    
    print("\nLe AgentManager fournit des méthodes pratiques pour chaque agent:")
    print()
    
    methods = [
        ('manager.watcher("Check services")', "Agent de monitoring"),
        ('manager.sentinel("Detect anomalies")', "Agent de surveillance"),
        ('manager.ceo("Make strategic decision")', "Agent décisionnaire"),
        ('manager.orchestrator("Coordinate mission")', "Agent orchestrateur"),
        ('manager.researcher("Investigate issue")', "Agent de recherche"),
        ('manager.architect("Design solution")', "Agent architecte"),
        ('manager.skeptic("Review proposal")', "Agent critique"),
        ('manager.creative("Generate ideas")', "Agent créatif"),
    ]
    
    for method, description in methods:
        print(f"  {method:45s} # {description}")


def demo_session_management():
    """Montre la gestion des sessions"""
    print("\n" + "=" * 70)
    print("DÉMONSTRATION 6: Gestion des sessions persistantes")
    print("=" * 70)
    
    manager = get_agent_manager()
    
    print("\n💡 Concept clé:")
    print("  Chaque agent a SA PROPRE SESSION persistante avec son vrai prompt système!")
    print()
    
    print("📊 Statistiques des sessions:")
    stats = manager.get_session_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n🔄 Cycle de vie d'une session:")
    print("  1. Premier appel → Création automatique de la session")
    print("  2. Appels suivants → Réutilisation de la session existante")
    print("  3. Session invalide → Recréation automatique")
    print("  4. Cleanup manuel → manager.cleanup_session('watcher')")


def demo_comparison_old_vs_new():
    """Compare l'ancien vs nouveau système"""
    print("\n" + "=" * 70)
    print("COMPARAISON: Ancien système vs Nouveau AgentManager")
    print("=" * 70)
    
    print("\n❌ ANCIEN SYSTÈME (dans Event Bridge):")
    print("-" * 70)
    old_code = '''
# Dans event_bridge.py - Prompt hardcodé!
prompt = f"""ELF System Analysis Request from {component.upper()} Agent

{prompt}

You are analyzing system state as the {component} agent. 
Provide agent-specific insights and recommendations."""

# Envoie le tout comme un seul message
response = requests.post(
    f"{base_url}/session/{session_id}/message",
    json={
        "parts": [{"type": "text", "text": enhanced_prompt}],
        "model": model_config,
    }
)
'''
    print(old_code)
    
    print("\n✅ NOUVEAU SYSTÈME (AgentManager):")
    print("-" * 70)
    new_code = '''
# Charge le vrai prompt système depuis watcher.md
agent_config = manager.agents["watcher"]
# Prompt système = contenu complet de watcher.md

# Envoie seulement la requête utilisateur
result = manager.watcher("Analyze system health")
# Le prompt système est déjà dans la session!
'''
    print(new_code)
    
    print("\n✨ Avantages du nouveau système:")
    print("  • Utilise les vrais prompts système des fichiers .md")
    print("  • Sessions persistantes par agent (contexte conservé)")
    print("  • Séparation des responsabilités (Event Bridge ≠ AI)")
    print("  • API simple et standard OpenCode")
    print("  • Facile à étendre avec de nouveaux agents")


def demo_migration_example():
    """Montre un exemple concret de migration"""
    print("\n" + "=" * 70)
    print("EXEMPLE DE MIGRATION: ElfWatcher")
    print("=" * 70)
    
    print("\n📝 AVANT (dans elf_watcher.py):")
    print("-" * 70)
    before = '''
def analyze_with_event_bridge(self, system_state):
    """Analyser l'état du système via l'Event Bridge."""
    event_bridge_response = self.ask_event_bridge(
        "system_analysis",
        {
            "system_state": system_state,
            "analysis_type": "watcher_cycle",
        },
    )
    # Event Bridge construit un prompt hardcodé
    # et appelle OpenCode...
'''
    print(before)
    
    print("\n✅ APRÈS (avec AgentManager):")
    print("-" * 70)
    after = '''
from Open_ELF.agents.agent_manager import get_agent_manager

class ElfWatcher:
    def __init__(self):
        self.agent_manager = get_agent_manager()
    
    def analyze_system(self, system_state):
        """Analyser l'état du système via l'agent Watcher."""
        context = {
            "system_state": system_state,
            "analysis_type": "watcher_cycle",
            "timestamp": datetime.now().isoformat()
        }
        
        # Appelle directement l'agent Watcher avec son vrai prompt système!
        result = self.agent_manager.watcher(
            "Perform Tier 2 analysis on the provided system state",
            context=context
        )
        
        if result["success"]:
            return result["response"]
        else:
            return self.fallback_analysis(system_state)
'''
    print(after)


def main():
    """Point d'entrée principal"""
    print("\n" + "🚀 " * 35)
    print("AGENT MANAGER - DÉMONSTRATION")
    print("🚀 " * 35)
    
    try:
        demo_basic_usage()
        demo_agent_info()
        demo_ask_agent()
        demo_with_context()
        demo_convenience_methods()
        demo_session_management()
        demo_comparison_old_vs_new()
        demo_migration_example()
        
        print("\n" + "=" * 70)
        print("RÉSUMÉ")
        print("=" * 70)
        print("""
✅ Le AgentManager est prêt à l'emploi!

📁 Emplacement: emergent-learning/Open_ELF/agents/agent_manager.py

🔑 Points clés:
   • Charge les agents depuis les fichiers .md
   • Maintient des sessions persistantes par agent
   • Utilise les vrais prompts système (pas hardcodés)
   • API simple: manager.watcher("request") ou manager.ask_agent("name", "request")

🚀 Prochaines étapes:
   1. Tester: python agent_manager.py
   2. Migrer les composants (watcher, sentinel, etc.)
   3. Nettoyer OpenCodeAIClient de event_bridge.py

📚 Documentation:
   • Voir MIGRATION_GUIDE.md pour les étapes détaillées
   • Voir agent_manager.py pour la documentation complète
""")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
