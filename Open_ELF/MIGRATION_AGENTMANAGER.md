# Migration vers AgentManager - Guide Complet

## Vue d'ensemble

Cette migration remplace l'ancien système hybride (Event Bridge + OpenCodeAIClient) par un nouveau système standardisé utilisant **AgentManager**.

### Ancien système (OBSOLÈTE)
- **Event Bridge** : Gestion des événements SSE + appels IA avec prompts hardcodés
- **OpenCodeAIClient** : Client IA embarqué dans Event Bridge
- **Problème** : L'Event Bridge avait deux responsabilités, prompts hardcodés au lieu des fichiers .md

### Nouveau système (ACTUEL)
- **Event Bridge** : Gestion des événements SSE uniquement
- **AgentManager** : Gestion dédiée des appels IA avec vrais prompts système depuis les fichiers .md
- **Avantage** : Séparation des responsabilités, utilisation des agents définis dans les fichiers .md

## Changements effectués

### 1. Fichiers modifiés

#### `emergent-learning/Open_ELF/watcher/elf_watcher.py`
**Changements majeurs :**
- Suppression de `ask_event_bridge()` pour l'analyse IA
- Suppression de `analyze_with_event_bridge()`
- Ajout de `analyze_with_agent_manager()`
- Import de `AgentManager` et `get_agent_manager`
- Fallback vers analyse basique si AgentManager indisponible

**Nouvelle API :**
```python
from Open_ELF.agents.agent_manager import get_agent_manager

manager = get_agent_manager()
result = manager.watcher("Analyze system health", context={"system_state": state})
```

#### `emergent-learning/Open_ELF/orchestrator/event_bridge.py`
**Changements majeurs :**
- Suppression complète de la classe `OpenCodeAIClient`
- Suppression de `_ask_opencode()` et `_generate_analysis_prompt()`
- Simplification de la configuration (suppression de `ai_analysis`)
- `/api/v1/ask` retourne maintenant un message indiquant que l'API est dépréciée
- `/api/v1/mission` conservé pour les escalades (pas d'appel IA)

## Comment utiliser le nouveau système

### Exemple 1 : Watcher avec analyse IA

```python
from Open_ELF.agents.agent_manager import get_agent_manager

# Obtenir le manager (singleton)
manager = get_agent_manager()

# Appeler l'agent Watcher avec son vrai prompt système
context = {
    "system_state": {...},
    "analysis_type": "watcher_cycle",
    "tier": 2
}

result = manager.watcher(
    request="Analyze current system state and identify anomalies",
    context=context
)

if result["success"]:
    print(result["response"])  # Réponse de l'agent Watcher
    print(f"Session: {result['session_id']}")
    print(f"Model: {result['model_used']}")
else:
    print(f"Error: {result['error']}")
```

### Exemple 2 : Utiliser d'autres agents

```python
from Open_ELF.agents.agent_manager import get_agent_manager

manager = get_agent_manager()

# Agent Sentinel (surveillance)
result = manager.sentinel(
    "Detect security anomalies in the last hour",
    context={"logs": [...]}
)

# Agent CEO (décision)
result = manager.ceo(
    "Should we escalate this critical issue?",
    context={"issue": {...}}
)

# Agent Orchestrator
result = manager.orchestrator(
    "Coordinate the next system maintenance window",
    context={"maintenance_plan": {...}}
)
```

### Exemple 3 : Agent générique

```python
from Open_ELF.agents.agent_manager import get_agent_manager

manager = get_agent_manager()

# Appeler n'importe quel agent par son nom
result = manager.ask_agent(
    agent_name="researcher",  # ou "architect", "skeptic", "creative"
    user_request="Research best practices for...",
    context={"topic": "..."}
)
```

## Fichiers des agents

Les agents sont définis dans :
```
agents/OPC_ELF_System_Agents/
├── watcher.md              # Agent de monitoring
├── sentinel.md             # Agent de surveillance
├── ceo.md                  # Agent décisionnaire
├── unified-orchestrator.md # Agent orchestrateur
├── researcher.md           # Agent de recherche
├── architect.md            # Agent architecte
├── skeptic.md              # Agent critique
└── creative.md             # Agent créatif
```

Chaque fichier .md contient :
- **Métadonnées YAML** (nom, description, modèle, tags)
- **Prompt système complet** (le vrai prompt utilisé par l'agent)

## Architecture du nouveau système

```
┌─────────────────────────────────────────────────────────────┐
│                        ElfWatcher                           │
│  (cycle de monitoring tous les 60s/5min)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐              ┌────────────────┐
│ Basic Check   │              │ AgentManager   │
│ (sans IA)     │              │ (avec IA)      │
└───────────────┘              └───────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌──────────┐      ┌──────────┐      ┌──────────┐
            │ Watcher  │      │ Sentinel │      │   CEO    │
            │  Agent   │      │  Agent   │      │  Agent   │
            └──────────┘      └──────────┘      └──────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │      Session persistante par        │
                    │      agent avec prompt système      │
                    │      depuis fichier .md             │
                    └─────────────────────────────────────┘
```

## Points importants

### Sessions persistantes
- Chaque agent a sa **propre session persistante**
- Le prompt système est chargé **une seule fois** depuis le fichier .md
- Les messages suivants utilisent la même session (contexte conservé)

### Fallback
- Si AgentManager n'est pas disponible, le Watcher utilise une analyse basique
- Pas de dépendance critique sur AgentManager pour le fonctionnement de base

### Event Bridge
- Conserve sa fonction principale : gestion des événements SSE
- API `/api/v1/mission` conservée pour les escalades
- API `/api/v1/ask` dépréciée (renvoie un message d'information)

## Tests et vérification

### 1. Vérifier que AgentManager fonctionne

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/agents
python agent_manager.py
```

Sortie attendue :
```
🧪 Test du AgentManager
============================================================

📋 Agents chargés (8):
  - watcher: Enhanced ELF monitoring system with tiered analysis...
  - sentinel: System monitoring and pattern detection...
  - ceo: CEO/CTO decision maker...
  ...

✅ AgentManager prêt à l'emploi!
```

### 2. Vérifier que le Watcher fonctionne

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/watcher
python elf_watcher.py
```

Sortie attendue :
```
🚀 ELF Watcher v2.0 starting continuous monitoring
   Basic checks: every 60s
   AI analysis: every 300s (5 minutes)
   ✅ AgentManager: ENABLED
   📁 Agents loaded: 8
```

### 3. Vérifier que Event Bridge fonctionne

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python event_bridge.py start
```

Sortie attendue :
```
======================================================================
🌉 OpenCode Event Bridge Starting
======================================================================
✅ Connected to OpenCode server
✅ Status server starting on port 9998
👂 Listening to OpenCode events...
```

## Dépannage

### Problème : "AgentManager not available"
**Solution :** Vérifier que le fichier `agent_manager.py` existe :
```bash
ls -la /home/bamer/.opencode/emergent-learning/Open_ELF/agents/agent_manager.py
```

### Problème : "No module named 'Open_ELF.agents.agent_manager'"
**Solution :** Vérifier le PYTHONPATH :
```bash
export PYTHONPATH="/home/bamer/.opencode/emergent-learning:$PYTHONPATH"
```

### Problème : Event Bridge ne démarre pas
**Solution :** Vérifier qu'OpenCode est en cours d'exécution :
```bash
curl http://localhost:4096/
```

## Rétrocompatibilité

- L'ancienne API `ask_event_bridge()` n'existe plus dans elf_watcher.py
- L'ancienne classe `OpenCodeAIClient` n'existe plus dans event_bridge.py
- Les composants qui utilisaient ces API doivent migrer vers AgentManager
- Les endpoints API de l'Event Bridge retournent des messages de dépréciation

## Prochaines étapes

1. **Tester** le nouveau système avec des scénarios réels
2. **Migrer** d'autres composants (Sentinel, etc.) vers AgentManager
3. **Supprimer** définitivement le code obsolète après validation
4. **Documenter** les nouveaux patterns d'utilisation

## Résumé des avantages

✅ **Séparation des responsabilités** : Event Bridge = événements, AgentManager = IA  
✅ **Prompts système réels** : Utilisation des fichiers .md au lieu de prompts hardcodés  
✅ **Sessions persistantes** : Chaque agent conserve son contexte  
✅ **Standard OpenCode** : Architecture alignée avec les meilleures pratiques  
✅ **Extensibilité** : Facile d'ajouter de nouveaux agents  
✅ **Fallback robuste** : Fonctionnement sans IA si nécessaire  

---

**Date de migration** : 2026-02-07  
**Version** : ELF Watcher v2.0 + AgentManager v1.0  
**Auteur** : Système ELF
