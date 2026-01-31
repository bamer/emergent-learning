# Open_ELF - Orchestrateur Unifié

## Structure

```
/home/bamer/.opencode/emergent-learning/Open_ELF/
├── orchestrator/
│   ├── orchestrator.py      # Orchestrateur principal
│   ├── test.py              # Tests
│   └── __init__.py
├── agents/
│   └── (personas ELF)       # Personas spécifiques ELF
├── logs/
│   ├── orchestrator.log     # Logs principaux
│   ├── architect.log        # Logs par agent
│   ├── researcher.log
│   ├── heuristics.log       # Heuristiques extraites
│   └── ...
└── README.md
```

## 🚀 Fonctionnalités Clés

### 1. **Sélection Automatique d'Agent** 🤖

L'orchestrateur analyse la mission et choisit automatiquement le meilleur agent :

```bash
# Détection automatique basée sur les mots-clés
python3 orchestrator.py auto --mission "Design a new API endpoint"
→ Sélectionne: architect (confiance: 100%)

python3 orchestrator.py auto --mission "Investigate database performance issues"
→ Sélectionne: researcher (confiance: 100%)
```

**Mots-clés détectés :**
- **architect** : design, architecture, structure, pattern, blueprint
- **researcher** : investigate, research, analyze, explore, debug
- **skeptic** : review, audit, security, risk, validate, test
- **creative** : innovate, creative, brainstorm, new feature, ui, ux
- **ceo** : decide, strategy, prioritize, plan, coordinate

### 2. **Mode Swarm (Multi-Agents Parallèles)** 🐝

Déclenché automatiquement par les mots-clés `swarm`, `parallel`, `multi-agent` :

```bash
# Détection automatique du mode swarm
python3 orchestrator.py smart --mission "swarm: Design and implement authentication"

# Ou forcer le mode swarm
python3 orchestrator.py swarm --mission "Parallel analysis of the codebase"
```

**Processus :**
1. Décompose la mission en sous-tâches
2. Assigne chaque sous-tâche à l'agent approprié
3. Exécute toutes les sous-tâches en parallèle
4. Synthétise les résultats avec le CEO

**Exemple de décomposition :**
```
Mission: "Design and implement a new feature"
→ Sous-tâche 1: [architect] Design phase
→ Sous-tâche 2: [creative] Implementation planning
→ Sous-tâche 3: [skeptic] Validation
```

### 3. **Mode Smart (Auto-Detection)** 🎯

Analyse la mission et choisit automatiquement entre :
- **Mode Swarm** : Si mots-clés swarm/parallel détectés
- **Mode Single Agent** : Sinon, avec sélection automatique

```bash
# Détection intelligente du mode
python3 orchestrator.py smart --mission "Your mission here"
```

## Architecture

L'orchestrateur utilise l'**API OpenCode** (HTTP sur port 4096) pour :

1. **Créer des sessions** pour chaque agent (architect, researcher, etc.)
2. **Envoyer des missions** comme messages aux sessions
3. **Récupérer les réponses** de l'IA (Claude, etc.)
4. **Logger tout** dans le système unifié
5. **Extraire les heuristiques** des réponses
6. **Gérer l'escalade** au CEO si nécessaire

## Utilisation

### Démarrer l'orchestrateur

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python3 orchestrator.py start
```

### Voir le statut

```bash
python3 orchestrator.py status
```

### Exécuter une mission (mode manuel)

```bash
python3 orchestrator.py run --agent architect --mission "Design API auth"
```

### Exécuter avec sélection automatique

```bash
python3 orchestrator.py auto --mission "Investigate slow queries"
```

### Mode Swarm (multi-agents)

```bash
python3 orchestrator.py swarm --mission "swarm: Design and implement new feature"
```

### Mode Smart (auto-détection)

```bash
python3 orchestrator.py smart --mission "Your mission here"
```

### Exécution parallèle (dans le code)

```python
from orchestrator import UnifiedOrchestrator

orch = UnifiedOrchestrator()
orch.start()

# Missions en parallèle
missions = [
    ("researcher", "Investigate the database schema"),
    ("architect", "Design the API structure"),
    ("skeptic", "Review security implications"),
]

results = orch.run_parallel_missions(missions)
```

## Logs Unifiés

Tous les logs sont centralisés dans `/Open_ELF/logs/` :

- `orchestrator.log` - Logs principaux
- `architect.log` - Réponses de l'agent architect
- `researcher.log` - Réponses de l'agent researcher
- `heuristics.log` - Heuristiques extraites automatiquement

## Extraction d'Heuristiques

Les patterns suivants sont automatiquement extraits des réponses :

```
[LEARNED:architecture] Always validate user input
[HEURISTIC:security] Use parameterized queries
[PATTERN:performance] Cache frequently accessed data
```

## Différence avec l'ancien système

| Ancien | Nouveau |
|--------|---------|
| Processus Python vides | Sessions OpenCode avec IA réelle |
| Pas de traitement de mission | Missions envoyées comme messages |
| Logs dispersés | Logs unifiés dans Open_ELF/logs/ |
| Pas d'extraction | Heuristiques extraites automatiquement |
| Pas d'escalade | Escalade au CEO intégrée |
| Pas de sélection auto | Sélection automatique par mots-clés |
| Pas de parallélisme | Mode swarm multi-agents |

## Intégration Dashboard

L'orchestrateur expose une API simple que le dashboard peut utiliser :

```python
# Dashboard → Orchestrateur
orch = UnifiedOrchestrator()
status = orch.get_status()  # Statut de tous les agents

# Mode smart (auto-détection)
result = orch.run_smart("Your mission here")

# Mode swarm explicite
result = orch.execute_swarm_mission("swarm: Complex mission")
```

## Tests

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python3 test.py
```

## Prochaines étapes de migration

1. [ ] Connecter le dashboard au nouvel orchestrateur
2. [ ] Créer les personas ELF spécifiques (fichiers .md)
3. [ ] Implémenter le système de tâches persistantes
4. [ ] Ajouter la visualisation temps réel (SSE)
5. [ ] Supprimer l'ancien orchestrateur une fois stable
