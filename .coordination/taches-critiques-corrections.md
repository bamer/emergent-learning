# TÂCHES CRITIQUES - CORRECTIONS SÉCURITÉ

## 🚨 TÂCHE #1: Supprimer les utilisations d'exec() dangereuses
**Priorité:** CRITIQUE  
**Estimation:** 2-3 heures  
**Impact:** Sécurité critique  
**Emplacements:**
- `/hooks/learning-loop/add_debug.py` (ligne~37)
- `/hooks/learning-loop/add_minimal_logging.py` (ligne~30)
- `/hooks/learning-loop/patch_all_logging.py` (lignes~55, 89)

**Action:** Remplacer par des alternatives sécurisées (fonctions de logging paramétriques)

---

## 🚨 TÂCHE #2: Sécuriser les appels HTTP externes
**Priorité:** CRITIQUE  
**Estimation:** 1-2 heures  
**Impact:** Sécurité critique  
**Emplacement:** `/dashboard-app/backend/routers/monitoring.py`

**Problèmes identifiés:**
- URL hardcodée ligne 388: `status_url = "http://localhost:9999/status"`
- Pas de vérification TLS ligne 396: `requests.get(status_url, timeout=3)`

**Actions:**
1. Externaliser l'URL dans la configuration
2. Ajouter `verify=True` pour TLS verification
3. Implémenter timeout dynamique
4. Ajouter validation des réponses JSON

---

## 🚨 TÂCHE #3: Corriger la gestion d'expiration des tokens
**Priorité:** CRITIQUE  
**Estimation:** 1 heure  
**Impact:** Sécurité critique  
**Emplacement:** `/dashboard-app/backend/routers/auth.py`

**Problème:** Pas de vérification d'expiration des tokens de session

**Actions:**
1. Ajouter la vérification de l'expiration des tokens
2. Implémenter la rotation automatique des tokens
3. Ajouter la validation de session à chaque requête

---

## 🔶 TÂCHE #4: Optimiser les requêtes SQL
**Priorité:** IMPORTANT  
**Estimation:** 3-4 heures  
**Impact:** Performance critique  
**Emplacements:** `/dashboard-app/backend/routers/analytics.py`, autres routers

**Problèmes:**
- SELECT * non optimisés
- Indexes manquants
- Pas de pagination sur les gros datasets

**Actions:**
1. Remplacer SELECT * par colonnes spécifiques
2. Ajouter indexes sur colonnes frequently queried
3. Implémenter pagination pour résultats volumineux

---

## 🔶 TÂCHE #5: Éliminer les dépendances circulaires
**Priorité:** IMPORTANT  
**Estimation:** 2-3 heures  
**Impact:** Maintenabilité  
**Emplacement:** `/dashboard-app/backend/main.py` (lignes 38-60)

**Problème:** Import circulaire avec elf_logging

**Actions:**
1. Restructurer l'ordre des imports
2. Implémenter une architecture de plugins propre
3. Séparer les utilitaires de logging

---

## 📅 PLANNING RECOMMANDÉ

### Semaine 1:
- Jour 1-2: Tâches #1 et #2 (Sécurité critique)
- Jour 3: Tâche #3 (Gestion tokens)
- Jour 4-5: Tâche #4 (Optimisation SQL)

### Semaine 2:
- Jour 1-2: Tâche #5 (Dépendances circulaires)
- Jour 3-5: Tests et validation

---

## ✅ CRITÈRES DE VALIDATION

### Sécurité:
- [ ] Aucune utilisation d'exec() trouvée par grep
- [ ] Tous les appels HTTP avec TLS verification
- [ ] Tokens avec expiration validée

### Performance:
- [ ] Requêtes SQL optimisées (< 100ms)
- [ ] Pagination sur résultats > 1000 éléments
- [ ] Indexes sur colonnes frequently queried

### Architecture:
- [ ] Dépendances circulaires éliminées
- [ ] Imports restructurés
- [ ] Tests unitaires passent à 100%

---

## 🎯 OBJECTIFS DE SUCCÈS

**Avant corrections:**
- Score sécurité: 6.5/10
- Score performance: 6.0/10

**Après corrections:**
- Score sécurité: 9.0/10 (objectif)
- Score performance: 8.5/10 (objectif)
- Score architecture: 8.0/10 → 9.0/10

**Score global cible:** 8.5/10 (vs 7.2/10 actuel)