#!/usr/bin/env python3
"""
Exemple d'utilisation du Mission Engine

Ce fichier montre comment utiliser le composant mission-engine
pour créer et gérer des missions, notamment pour l'onglet Live.
"""

import time
from mission_engine import (
    MissionEngine,
    LiveMissionHandler,
    MissionPriority,
    get_mission_engine,
)


def example_basic_mission():
    """Exemple basique : créer et exécuter une mission"""
    print("\n" + "="*70)
    print("📝 EXEMPLE 1: Mission basique")
    print("="*70)
    
    # Créer le moteur
    engine = MissionEngine()
    
    # Créer une mission
    mission = engine.create_mission(
        title="Vérification système",
        description="Vérifier que tous les services fonctionnent correctement",
        agent="sentinel",
        priority=MissionPriority.HIGH,
    )
    
    print(f"✅ Mission créée: {mission.id}")
    print(f"   Titre: {mission.title}")
    print(f"   Status: {mission.status.value}")
    
    # Afficher les stats
    stats = engine.get_stats()
    print(f"\n📊 Stats: {stats['total_missions']} missions au total")
    
    return engine, mission


def example_live_mission():
    """Exemple : mission pour l'onglet Live"""
    print("\n" + "="*70)
    print("📺 EXEMPLE 2: Mission Live")
    print("="*70)
    
    engine = MissionEngine()
    handler = LiveMissionHandler(engine)
    
    # Créer une mission Live
    mission = handler.create_live_mission(
        title="🔍 Analyse de sécurité",
        description="Analyse complète de la sécurité du système",
        agent="sentinel",
        priority="HIGH",
        auto_execute=False,  # Ne pas exécuter automatiquement pour l'exemple
    )
    
    print(f"✅ Mission Live créée: {mission.live_tab_id}")
    
    # Afficher le dashboard
    dashboard = handler.get_live_dashboard()
    print(f"\n📊 Dashboard Live:")
    print(f"   Total: {dashboard['stats']['total']}")
    print(f"   En attente: {dashboard['stats']['pending']}")
    print(f"   En cours: {dashboard['stats']['running']}")
    
    # Afficher les missions
    print(f"\n📋 Missions Live:")
    for live_mission in handler.get_live_missions():
        print(f"   - {live_mission.title} ({live_mission.status})")
    
    return engine, handler, mission


def example_pattern_response():
    """Exemple : réponse à un pattern détecté"""
    print("\n" + "="*70)
    print("⚡ EXEMPLE 3: Réponse à un pattern")
    print("="*70)
    
    engine = MissionEngine()
    handler = LiveMissionHandler(engine)
    
    # Simuler un pattern détecté
    pattern = "High memory usage detected"
    recommendations = [
        "Investigate memory leaks",
        "Check running processes",
        "Review recent changes"
    ]
    context = {
        "memory_usage": "85%",
        "timestamp": "2026-02-07T10:00:00",
    }
    
    # Créer une mission de réponse
    mission = handler.create_pattern_response_mission(
        pattern=pattern,
        agent="sentinel",
        recommendations=recommendations,
        context=context,
    )
    
    print(f"✅ Mission de réponse créée: {mission.id}")
    print(f"   Pattern: {pattern}")
    print(f"   Agent: {mission.agent}")
    print(f"   Auto-exécution: désactivée pour l'exemple")
    
    return engine, handler, mission


def example_callbacks():
    """Exemple : utilisation des callbacks"""
    print("\n" + "="*70)
    print("📡 EXEMPLE 4: Callbacks et événements")
    print("="*70)
    
    engine = MissionEngine()
    
    # Enregistrer des callbacks
    def on_created(mission):
        print(f"   📢 Callback: Mission créée {mission.id}")
    
    def on_started(mission):
        print(f"   📢 Callback: Mission démarrée {mission.id}")
    
    def on_completed(mission):
        print(f"   📢 Callback: Mission terminée {mission.id}")
    
    engine.on("mission_created", on_created)
    engine.on("mission_started", on_started)
    engine.on("mission_completed", on_completed)
    
    print("✅ Callbacks enregistrés")
    
    # Créer une mission (déclenchera on_created)
    mission = engine.create_mission(
        title="Test callbacks",
        description="Mission pour tester les callbacks",
        auto_execute=False,
    )
    
    print(f"\n✅ Mission créée avec callbacks")
    
    return engine, mission


def example_singleton():
    """Exemple : utilisation du pattern singleton"""
    print("\n" + "="*70)
    print("🔧 EXEMPLE 5: Pattern Singleton")
    print("="*70)
    
    # Récupérer l'instance singleton
    engine1 = get_mission_engine()
    engine2 = get_mission_engine()
    
    print(f"✅ Instance 1: {id(engine1)}")
    print(f"✅ Instance 2: {id(engine2)}")
    print(f"   Même instance: {engine1 is engine2}")
    
    # Créer une mission avec l'instance 1
    mission = engine1.create_mission(
        title="Test singleton",
        description="Vérifier que le singleton fonctionne",
    )
    
    # Vérifier avec l'instance 2
    stats = engine2.get_stats()
    print(f"\n📊 Stats depuis instance 2: {stats['total_missions']} missions")
    
    return engine1


def example_dashboard_export():
    """Exemple : export du dashboard"""
    print("\n" + "="*70)
    print("📊 EXEMPLE 6: Export Dashboard")
    print("="*70)
    
    engine = MissionEngine()
    handler = LiveMissionHandler(engine)
    
    # Créer quelques missions
    handler.create_live_mission(
        title="Mission 1",
        description="Description 1",
        auto_execute=False,
    )
    handler.create_live_mission(
        title="Mission 2",
        description="Description 2",
        priority="HIGH",
        auto_execute=False,
    )
    
    # Récupérer le dashboard
    dashboard = handler.get_live_dashboard()
    
    print("✅ Dashboard récupéré:")
    print(f"   Stats: {dashboard['stats']}")
    print(f"   Nombre de missions: {len(dashboard['missions'])}")
    print(f"   Dernière mise à jour: {dashboard['last_updated']}")
    
    # Export JSON
    json_export = handler.export_live_missions_json()
    print(f"\n✅ Export JSON: {len(json_export)} caractères")
    
    return engine, handler, dashboard


def main():
    """Exécute tous les exemples"""
    print("\n" + "🚀"*35)
    print("🚀 MISSION ENGINE - DÉMONSTRATION 🚀")
    print("🚀"*35)
    
    try:
        # Exemple 1: Mission basique
        engine1, mission1 = example_basic_mission()
        
        # Exemple 2: Mission Live
        engine2, handler2, mission2 = example_live_mission()
        
        # Exemple 3: Réponse pattern
        engine3, handler3, mission3 = example_pattern_response()
        
        # Exemple 4: Callbacks
        engine4, mission4 = example_callbacks()
        
        # Exemple 5: Singleton
        engine5 = example_singleton()
        
        # Exemple 6: Dashboard
        engine6, handler6, dashboard = example_dashboard_export()
        
        print("\n" + "="*70)
        print("✅ TOUS LES EXEMPLES ONT RÉUSSI!")
        print("="*70)
        print("\n📚 Résumé:")
        print("   - Création de missions basiques")
        print("   - Gestion des missions Live")
        print("   - Réponse aux patterns détectés")
        print("   - Système de callbacks")
        print("   - Pattern singleton")
        print("   - Export dashboard")
        print("\n💡 Prochaines étapes:")
        print("   - Intégrer avec votre interface Live Tab")
        print("   - Utiliser start_background_processing() pour l'auto-exécution")
        print("   - Personnaliser les callbacks pour votre UI")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
