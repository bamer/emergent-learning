# 🧹 Nettoyage Open_ELF - Migration vers AgentManager

## Résumé des Modifications

Ce document résume les changements effectués pour standardiser l'utilisation de **AgentManager** comme SEUL point d'entrée pour les appels IA.

---

## ✅ Modifications Effectuées

### 1. Fichiers Dépréciés (avec warnings)

#### `agents/base_agent.py` ➜ DÉPRÉCIÉ
- **Statut**: Marqué comme obsolète avec warnings Python
- **Migration**:
  ```python
  # AVANT (déprécié)
  from agents.base_agent import BaseAgent, ResearcherAgent
  researcher = ResearcherAgent()
  result = researcher.analyze("task")
  
  # APRÈS (standard)
  from agents.agent_manager import get_agent_manager
  manager = get_agent_manager()
  result = manager.researcher("Analyze this task")
  ```

#### `agents/elf_ai_client.py` ➜ DÉPRÉCIÉ
- **Statut**: Marqué comme obsolète avec warnings Python
- **Migration**:
  ```python
  # AVANT (déprécié)
  from agents.elf_ai_client import ELFAIClient
  client = ELFAIClient()
  response = client.call("prompt")
  
  # APRÈS (standard)
  from agents.agent_manager import get_agent_manager
  manager = get_agent_manager()
  result = manager.ask_agent("experiment-analyzer", "Analyze this experiment...")
  ```

### 2. Dashboard Monitoring - Nouveaux Endpoints

#### `/api/v1/escalations` - Liste complète des escalades
**Fonctionnalités**:
- Filtres par agent: `?agent=watcher|sentinel|ceo`
- Filtres par sévérité: `?severity=info|warning|critical`
- Période configurable: `?hours=24` (défaut)
- Limite de résultats: `?limit=50` (défaut)

**Réponse**:
```json
{
  "status": "ok",
  "escalations": [
    {
      "id": 123,
      "timestamp": "2026-02-07T10:30:00",
      "agent": "sentinel",
      "severity": "warning",
      "summary": "Service instability detected",
      "display_message": "🟡 Sentinel: Service instability detected",
      "requires_action": true
    }
  ],
  "stats": {
    "total": 45,
    "by_agent": {"sentinel": 30, "watcher": 15},
    "by_severity": {"info": 20, "warning": 15, "critical": 10},
    "requiring_action": 25
  }
}
```

#### `/api/v1/escalations/summary` - Résumé des escalades
**Fonctionnalités**:
- Statistiques par agent
- Comptage par sévérité
- Liste des escalades critiques récentes

---

## 🎯 Standard Recommandé

Tous les appels IA doivent maintenant passer par **AgentManager**:

```python
from agents.agent_manager import get_agent_manager

# Obtenir l'instance singleton
manager = get_agent_manager()

# Agents disponibles
response = manager.watcher("Check system health")
response = manager.sentinel("Monitor services")
response = manager.ceo("Review critical decisions")
response = manager.researcher("Research topic")
response = manager.architect("Design system")
response = manager.skeptic("Review proposal")
response = manager.creative("Brainstorm ideas")

# Ou méthode générique
response = manager.ask_agent("watcher", "Your request here")
```

---

## 📊 Architecture Actuelle

```
┌─────────────────────────────────────────────────────────┐
│                    Application Code                      │
│                                                          │
│  from agents.agent_manager import get_agent_manager     │
│  manager = get_agent_manager()                          │
│  result = manager.watcher("check system")               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    AgentManager                         │
│  - Charge agents depuis .md files                       │
│  - Maintient sessions persistantes                      │
│  - Gère les appels OpenCode API                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              OpenCode Server (port 4096)                │
│  - API REST /session/{id}/message                       │
│  - Gestion des modèles IA                               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Event Bridge (port 9998)                   │
│  - SSE events                                           │
│  - Journalisation des événements                        │
│  - Séparé des appels IA                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Fichiers Modifiés

1. ✅ `agents/base_agent.py` - Déprécié avec warnings
2. ✅ `agents/elf_ai_client.py` - Déprécié avec warnings
3. ✅ `dashboard-app/backend/routers/monitoring.py` - Ajout endpoints escalades

---

## 🚀 Prochaines Étapes (Optionnel)

1. **Tests**: Vérifier que tous les agents fonctionnent correctement
2. **Documentation**: Mettre à jour la documentation utilisateur
3. **Suppression**: Retirer les fichiers dépréciés dans une future version
4. **Frontend**: Mettre à jour le dashboard pour afficher les escalades

---

## ⚠️ Notes Importantes

- Les fichiers dépréciés continuent de fonctionner mais affichent des warnings
- Les warnings invitent les développeurs à migrer vers AgentManager
- Les endpoints d'escalades sont disponibles immédiatement
- Aucun fichier n'utilise plus les classes dépréciées (vérifié)

---

## 🔍 Vérification

Pour tester les nouveaux endpoints:

```bash
# Vérifier les escalades
curl http://localhost:8888/api/v1/escalations

# Filtrer par agent
curl "http://localhost:8888/api/v1/escalations?agent=sentinel&hours=12"

# Résumé des escalades
curl http://localhost:8888/api/v1/escalations/summary

# Status des agents
curl http://localhost:8888/api/v1/watcher/status
curl http://localhost:8888/api/v1/sentinel/status
```

---

**Date**: 2026-02-07  
**Version**: 1.0  
**Statut**: ✅ Terminé
