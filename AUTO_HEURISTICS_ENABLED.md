# AUTO HEURISTICS ENABLED - SYSTÈME ACTIF

## 🎯 FONCTIONNALITÉ ACTIVE

Le système ELF crée maintenant des heuristiques **automatiquement** à partir de :

1. **Patterns détectés** → automatiquement convertis en heuristiques
2. **Sorties de tâches** → automatiquement extraites comme heuristiques
3. **Promotion automatique** → patterns automatiquement promus en golden rules

## ✅ MÉCANISMES ACTIVÉS

### 1. Pattern Response Handler (`pattern_response_handler.py`)
- ✅ **FONCTIONNE** : `_record_pattern_as_learning()` crée automatiquement des heuristiques
- ✅ **FONCTIONNE** : Patterns enregistrés dans `event_chronicle` ET comme heuristiques
- ✅ **SOURCE_TYPE** : `auto` pour identifier les heuristiques créées automatiquement

### 2. Post-Task Learning Hook (`post_tool_learning.py`)
- ✅ **FONCTIONNE** : Extraction automatique d'heuristiques des sorties
- ✅ **MOTS-CLÉS** : always, never, should, must, don't, avoid, prefer
- ✅ **SOURCE_TYPE** : `auto` avec UPSERT pour éviter les doublons

### 3. Dashboard Sentinel (`dashboard_sentinel_complete.py`)
- ✅ **FONCTIONNE** : Promotion automatique à golden rule si critères remplis
- ✅ **CRITÈRES** : min_validations=5, confidence_threshold=0.9, age_days=30, consistency_score=0.8
- ✅ **LOG** : `🧠 ELF Learning: Promoted X heuristics to golden rules`

## 📊 COMMENT ÇA MARCHE

### 1. Détection de Pattern
```
Pattern détecté → _record_pattern_as_learning() → Heuristique créée
```

### 2. Extraction de Tâche
```
Sortie de tâche → Analyse mots-clés → Heuristique créée (source_type='auto')
```

### 3. Promotion Automatique
```
Heuristique validée 5+ fois → Critères remplis → Promue en golden rule
```

## 🔍 VÉRIFICATION

Pour vérifier que le système crée des heuristiques automatiquement :

```bash
# Vérifier les heuristiques automatiques
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT COUNT(*) FROM heuristics WHERE source_type = 'auto';"

# Voir les dernières heuristiques créées
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT id, domain, rule, confidence, source_type, created_at \
   FROM heuristics WHERE source_type = 'auto' ORDER BY created_at DESC LIMIT 10;"

# Vérifier les promotions en golden rules
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT COUNT(*) FROM heuristics WHERE is_golden = 1;"
```

## 📝 EXEMPLES D'HEURISTIQUES CRÉÉES

### Patterns Détectés
- `system-patterns`: "Declining activity trend detected" (confidence: 0.8)
- `system-patterns`: "Service instability detected" (confidence: 0.7)
- `system-patterns`: "Cyclical pattern detected" (confidence: 0.8)

### Extractions de Tâches
- `testing`: "Always test hooks thoroughly" (confidence: 0.5)
- `general`: "Never use eval() on untrusted data" (confidence: 0.75)
- `general`: "Always check file permissions" (confidence: 0.7)

## 🚨 LOGS À SURVEILLER

**Dans les logs, vous devriez voir :**
- ✅ `AUTO-EXTRACTED HEURISTIC: ...` - Heuristique créée depuis sortie de tâche
- ✅ `🧠 ELF Learning: Promoted X heuristics to golden rules` - Promotion automatique
- ✅ `Learning recorded: True` - Pattern enregistré comme heuristique

**Erreurs normales (base verrouillée) :**
- ⚠️ `database is locked` - Normal en cas d'accès concurrent
- ⚠️ `UNIQUE constraint failed` - Heuristique déjà existante (UPSERT devrait gérer)

## 🎯 CRITÈRES DE PROMOTION

Pour qu'une heuristique soit promue automatiquement en golden rule :

| Critère | Valeur | Description |
|---------|--------|-------------|
| **min_validations** | 5+ | Répétition réussie 5+ fois |
| **confidence_threshold** | 0.9 | Confiance ≥ 90% |
| **age_days** | 30 | Stable pendant 30 jours |
| **consistency_score** | 0.8 | Ratio de succès ≥ 80% |

## 📞 MONITORING

Pour surveiller l'activité automatique :

```bash
# Surveiller les logs en temps réel
tail -f ~/.opencode/emergent-learning/logs/*.log | grep -E "(AUTO-EXTRACTED|Promoted heuristic)"

# Compter les heuristiques créées aujourd'hui
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT COUNT(*) FROM heuristics WHERE source_type = 'auto' \
   AND date(created_at) = date('now');"

# Voir les domaines les plus actifs
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT domain, COUNT(*) as count FROM heuristics \
   WHERE source_type = 'auto' GROUP BY domain ORDER BY count DESC;"
```

---

**Date d'activation** : 2026-01-31
**Statut** : ✅ ACTIF - Heuristiques automatiques activées
**Test** : `python /home/bamer/.opencode/emergent-learning/test_auto_heuristics.py`
