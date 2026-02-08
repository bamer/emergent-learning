# PLAN DE REPRISE ET FINITION DU REFACTORING Open_ELF

## ÉTAT ACTUEL (75% complété)

### ✅ CE QUI A ÉTÉ FAIT
1. Structure Open_ELF créée avec répertoires de base
2. Fichiers copiés depuis la racine vers Open_ELF
3. Orchestrateur de base fonctionnel
4. Dashboard-app partiellement migré

### ❌ PROBLÈMES IDENTIFIÉS

#### 1. DOUBLONS MASSIFS (CRITIQUE)
- **agents/** : 22 fichiers dupliqués entre `/agents/` et `/Open_ELF/agents/`
- **query/** : 60+ fichiers identiques dans les deux emplacements
- **scripts/** : Non migré mais présent uniquement à la racine
- **dashboard-app/** : Présent dans les deux emplacements

#### 2. STRUCTURE INCOMPLÈTE
Manque dans Open_ELF :
- `scripts/` (114 scripts non migrés)
- `memory/` (système de mémoire)
- `skills/` (compétences ELF)
- `golden-rules/` (règles constitutionnelles)
- `config/` (configuration)
- `docs/` (documentation)
- `database/` (base de données SQLite)
- `workflows/` (workflows TDD)

#### 3. RÉFÉRENCES CASSÉES
- Les imports Python pointent encore vers la racine
- Les chemins de fichiers sont absolus et incorrects
- Scripts shell avec chemins durs codés

#### 4. ORCHESTRATEUR INCOMPLÈT
- Orchestrateur.py existe mais n'est pas le "vrai" orchestrateur unifié
- Manque l'intégration avec l'API OpenCode
- Pas de gestion de session persistante

---

## PLAN DE FINITION DÉTAILLÉ

### PHASE 1: AUDIT ET SAUVEGARDE (Jour 1)

#### 1.1 Inventaire complet
```bash
# Créer une liste exhaustive de tous les fichiers
find /home/bamer/.opencode/emergent-learning -type f \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.venv/*" \
  -not -path "*/Open_ELF/*" > /tmp/root_files.txt

find /home/bamer/.opencode/emergent-learning/Open_ELF -type f \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.venv/*" > /tmp/open_elf_files.txt
```

#### 1.2 Identifier les fichiers essentiels vs doublons
- Comparer les checksums MD5 des fichiers
- Identifier quels fichiers sont sources de vérité
- Marquer les fichiers à supprimer après migration

#### 1.3 Sauvegarde complète
```bash
# Créer une sauvegarde avant toute modification
cd /home/bamer/.opencode/emergent-learning
git add -A
git commit -m "Pre-refactoring backup - état avant nettoyage"
```

---

### PHASE 2: MIGRATION DES COMPOSANTS MANQUANTS (Jours 2-3)

#### 2.1 Migrer scripts/ essentiels
Copier vers `/Open_ELF/scripts/` :
- ✅ record-failure.sh
- ✅ record-heuristic.py
- ✅ record-success.sh
- ✅ query/query.py (adapté)
- ✅ self-test.sh
- ✅ learning-metrics.sh
- ✅ bootstrap-recovery.sh
- ✅ suggest-heuristics.sh
- ✅ deduplicate-failures.sh

**Action** : Ne copier que les scripts critiques, pas les 114 entiers

#### 2.2 Migrer infrastructure mémoire
Copier vers `/Open_ELF/memory/` :
- Structure de répertoires complète
- Templates de succès/échecs
- Sessions récentes
- Fichiers de contexte

#### 2.3 Migrer skills/
Copier vers `/Open_ELF/skills/` :
- Tous les skills existants
- Adapter les chemins dans SKILL.md

#### 2.4 Migrer golden-rules/
Copier vers `/Open_ELF/golden-rules/` :
- Règles constitutionnelles
- Conserver hiérarchie core/domain-specific

#### 2.5 Migrer config/
Copier vers `/Open_ELF/config/` :
- elf.conf
- agent-config.yaml
- parties.yaml (si pas déjà présent)

---

### PHASE 3: CONSOLIDATION DES DOUBLONS (Jours 4-5)

#### 3.1 Définir la source de vérité
Règle : **Open_ELF/ devient la source de vérité**

#### 3.2 Consolidation agents/
```bash
# Comparer et fusionner
cd /home/bamer/.opencode/emergent-learning

# Garder dans Open_ELF/agents/ :
# - unified_orchestrator.py (nouveau)
# - test_orchestration.py
# - test_agent_execution_integration.py

# Supprimer doublons de la racine après vérification
```

#### 3.3 Consolidation query/
Stratégie :
- Garder query.py adapté dans Open_ELF/query/
- Supprimer ancien query/ de la racine
- Créer lien symbolique temporaire pour compatibilité

#### 3.4 Consolidation dashboard-app/
Problème : deux dashboard-app existent
Solution :
- Analyser lesquels sont utilisés
- Fusionner les fonctionnalités
- Supprimer l'ancien

---

### PHASE 4: CORRECTION DES RÉFÉRENCES (Jours 6-7)

#### 4.1 Mettre à jour les imports Python
Dans tous les fichiers .py de Open_ELF/ :
```python
# AVANT (incorrect)
from legacy.helpers import LegacyAgent

# APRÈS (correct)
from Open_ELF.agents.agent_manager import get_agent_manager
```

#### 4.2 Mettre à jour les chemins dans les scripts shell
```bash
# AVANT
ELF_DIR="/home/bamer/.opencode/emergent-learning"

# APRÈS
ELF_DIR="/home/bamer/.opencode/emergent-learning/Open_ELF"
```

#### 4.3 Créer __init__.py manquants
Ajouter dans tous les packages Python pour imports propres.

---

### PHASE 5: TEST ET VALIDATION (Jour 8)

#### 5.1 Tests unitaires
```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF
python -m pytest tests/ -v
```

#### 5.2 Test d'intégration
```bash
# Vérifier que query fonctionne
python query/query.py --context

# Vérifier que record-failure fonctionne
scripts/record-failure.sh "Test" "Test domain"

# Vérifier l'orchestrateur
python orchestrator/orchestrator.py status
```

#### 5.3 Test end-to-end
Exécuter une mission complète via le nouvel orchestrateur.

---

### PHASE 6: NETTOYAGE FINAL (Jour 9)

#### 6.1 Supprimer les doublons de la racine
Après validation complète :
```bash
# Supprimer les répertoires migrés
cd /home/bamer/.opencode/emergent-learning
rm -rf agents/          # Doublon
rm -rf query/           # Doublon
rm -rf dashboard-app/   # Doublon
rm -rf orchestrator/    # Doublon (si présent à la racine)
```

#### 6.2 Créer liens symboliques (optionnel)
Pour rétro-compatibilité temporaire :
```bash
ln -s Open_ELF/agents agents
ln -s Open_ELF/query query
ln -s Open_ELF/scripts scripts
```

#### 6.3 Mettre à jour .gitignore
Ajouter les répertoires obsolètes si nécessaire.

---

### PHASE 7: DOCUMENTATION (Jour 10)

#### 7.1 Mettre à jour README.md principal
Documenter la nouvelle structure et comment migrer.

#### 7.2 Créer guide de migration
```markdown
# Guide de Migration Open_ELF

## Anciens chemins → Nouveaux chemins
- ~/agents/* → ~/Open_ELF/agents/*
- ~/query/* → ~/Open_ELF/query/*
- ~/scripts/* → ~/Open_ELF/scripts/*

## Commandes à mettre à jour
- Avant: python query/query.py
- Après: python Open_ELF/query/query.py
```

#### 7.3 Mettre à jour CLAUDE.md
Modifier les instructions pour pointer vers Open_ELF.

---

## CHECKLIST DE VALIDATION

### Avant de commencer
- [ ] Sauvegarde git créée
- [ ] Liste complète des fichiers générée
- [ ] Tests de base passent

### Pendant la migration
- [ ] Chaque fichier copié est vérifié
- [ ] Pas de perte de données
- [ ] Checksums comparés

### Après migration
- [ ] Tous les imports Python fonctionnent
- [ ] Tous les scripts shell s'exécutent
- [ ] Query fonctionne normalement
- [ ] Record-failure fonctionne
- [ ] Orchestrateur démarre
- [ ] Dashboard fonctionne

### Nettoyage
- [ ] Doublons supprimés
- [ ] Liens symboliques créés (si besoin)
- [ ] Documentation à jour
- [ ] Tests passent

---

## RISQUES ET MITIGATIONS

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Perte de données | Faible | Critique | Sauvegarde git complète |
| Scripts cassés | Élevé | Élevé | Tests exhaustifs, liens symboliques |
| ImportError Python | Élevé | Moyen | Vérifier tous les __init__.py |
| Références absolues | Moyen | Élevé | Recherche/grep systématique |
| Boucle infinie | Faible | Critique | Pas de liens symboliques circulaires |

---

## ESTIMATION TEMPS

- Phase 1 (Audit) : 4h
- Phase 2 (Migration) : 16h
- Phase 3 (Consolidation) : 12h
- Phase 4 (Corrections) : 12h
- Phase 5 (Tests) : 8h
- Phase 6 (Nettoyage) : 4h
- Phase 7 (Documentation) : 4h

**TOTAL : ~60 heures (7-8 jours plein)**

---

## PROCHAINS PAS IMMÉDIATS

1. **Maintenant** : Créer une branche git pour le refactoring
2. **Aujourd'hui** : Exécuter Phase 1 (Audit)
3. **Demain** : Commencer Phase 2 (Migration scripts critiques)
4. **Cette semaine** : Terminer Phases 2-3

---

## COMMANDES UTILES POUR LE DÉBOGAGE

```bash
# Trouver toutes les références à l'ancien chemin
grep -r "/home/bamer/.opencode/emergent-learning" \
  --include="*.py" --include="*.sh" --include="*.md" \
  Open_ELF/ | grep -v "Open_ELF"

# Trouver les imports absolus problématiques
grep -r "from agents\." Open_ELF/ --include="*.py"
grep -r "from query\." Open_ELF/ --include="*.py"

# Vérifier les liens symboliques
find Open_ELF/ -type l

# Comparer deux fichiers
diff /home/bamer/.opencode/emergent-learning/agents/base_agent.py \
     /home/bamer/.opencode/emergent-learning/Open_ELF/agents/base_agent.py
```

---

## NOTES SPÉCIFIQUES

### Architecture cible

```
/home/bamer/.opencode/emergent-learning/
├── Open_ELF/                    ← SEUL POINT D'ENTRÉE
│   ├── agents/                  ← Personas et orchestration
│   ├── orchestrator/            ← Orchestrateur unifié
│   ├── query/                   ← Système de requête
│   ├── scripts/                 ← Scripts utilitaires
│   ├── dashboard-app/           ← Dashboard (source unique)
│   ├── memory/                  ← Mémoire persistante
│   ├── skills/                  ← Compétences ELF
│   ├── golden-rules/            ← Règles constitutionnelles
│   ├── config/                  ← Configuration
│   └── README.md                ← Documentation
│
├── .coordination/               ← Coordination multi-agent (reste à la racine)
├── .logs/                       ← Logs système (reste à la racine)
├── memory/                      ← À migrer vers Open_ELF/
├── scripts/                     ← À migrer vers Open_ELF/
├── skills/                      ← À migrer vers Open_ELF/
└── [autres fichiers de config]  ← À évaluer un par un
```

### Principes directeurs

1. **Single Source of Truth** : Tout dans Open_ELF/
2. **Pas de doublons** : Un seul exemplaire de chaque fichier
3. **Chemins relatifs** : Éviter les chemins absolus hardcodés
4. **Imports propres** : Utiliser les imports Python standards
5. **Rétro-compatibilité** : Liens symboliques pendant la transition
6. **Tests continus** : Vérifier à chaque étape

---

*Document créé le : 2026-02-05*
*Dernière mise à jour : 2026-02-05*
*Statut : Plan de reprise validé, en attente d'exécution*
