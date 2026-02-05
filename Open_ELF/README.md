# Open_ELF - Emergent Learning Framework

## 🏗️ Structure Complète

```
/home/bamer/.opencode/emergent-learning/Open_ELF/
├── agents/                    # Personas et agents ELF
├── config/                    # Configuration système
├── coordinator/               # Coordination multi-agent
├── dashboard-app/             # Application dashboard
├── database/                  # Base de données SQLite
├── docs/                      # Documentation
├── golden-rules/              # Règles constitutionnelles
├── logs/                      # Logs système
├── memory/                    # Mémoire persistante
├── orchestrator/              # Orchestrateur principal
├── query/                     # Système de requête
├── scripts/                   # Scripts utilitaires
├── skills/                    # Compétences ELF
├── timeline_dashboard/        # Dashboard timeline
├── watcher/                   # Watcher système
├── workflows/                 # Workflows TDD
├── init.sh                    # Script d'initialisation
├── README.md                  # Ce fichier
└── REFACTORING_PLAN.md        # Plan de refactoring
```

## 🚀 Démarrage Rapide

### Initialisation

```bash
# Charger l'environnement
source /home/bamer/.opencode/emergent-learning/Open_ELF/init.sh

# Ou manuellement
export ELF_ROOT="/home/bamer/.opencode/emergent-learning/Open_ELF"
```

### Commandes Essentielles

```bash
# Interroger le building
python3 query/query.py --context

# Enregistrer un échec
scripts/record-failure.sh "Titre" "domaine"

# Enregistrer une heuristique
python3 scripts/record-heuristic.py "Règle" "domaine"

# Auto-test
scripts/self-test.sh

# Métriques d'apprentissage
scripts/learning-metrics.sh
```

## 🧪 Tests

```bash
# Vérifier l'installation
python3 query/query.py --context

# Tester les scripts
scripts/self-test.sh --quick

# Test complet
cd /home/bamer/.opencode/emergent-learning/Open_ELF
find . -name "test*.py" -exec python3 {} \;
```

## 📝 Migration depuis l'ancienne structure

Si vous utilisiez l'ancienne structure à la racine :

```bash
# Anciens chemins → Nouveaux chemins
~/query/query.py              → ~/Open_ELF/query/query.py
~/scripts/record-failure.sh   → ~/Open_ELF/scripts/record-failure.sh
~/memory/                     → ~/Open_ELF/memory/
~/skills/                     → ~/Open_ELF/skills/
```

## 🔧 Développement

### Ajouter un nouveau skill

1. Créer un répertoire dans `skills/`
2. Ajouter un fichier `SKILL.md`
3. Tester avec `python3 query/query.py --domain votre-domaine`

### Modifier l'orchestrateur

1. Éditer `orchestrator/orchestrator.py`
2. Tester avec `python3 orchestrator/orchestrator.py status`
3. Valider avec les tests unitaires

## 📊 Architecture

```
┌─────────────────────────────────────┐
│           Open_ELF                  │
├─────────────────────────────────────┤
│  orchestrator/  │  agents/          │
│  query/         │  coordinator/     │
│  scripts/       │  dashboard-app/   │
├─────────────────────────────────────┤
│  memory/  │  skills/  │  docs/      │
│  database/│  config/  │  workflows/ │
└─────────────────────────────────────┘
```

## 🤝 Contribution

Voir `REFACTORING_PLAN.md` pour l'historique du refactoring.

## 📄 Licence

MIT - Emergent Learning Framework
