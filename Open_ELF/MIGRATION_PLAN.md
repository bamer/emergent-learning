# Plan de Migration vers Orchestrator Unifié

## 📋 Fichiers à Migrer/Archiver

### Fichiers Obsolètes (à archiver)
- `orchestrator/event_bridge.py` → Remplacé par `enhanced_event_bridge.py`
- `orchestrator/orchestrator.py` → Remplacé par `enhanced_event_bridge.py`  
- `orchestrator/unified_orchestrator.py` → Fonctionnalités intégrées dans `enhanced_event_bridge.py`

### Fichiers à Conserver
- `orchestrator/enhanced_event_bridge.py` → **Nouveau orchestrator central**
- `orchestrator/opencode_client.py` → Peut être utile pour certaines fonctionnalités
- `orchestrator/mission_bridge.py` → À migrer vers API orchestrator
- `orchestrator/event_bridge_sdk.py` → À migrer vers API orchestrator

## 🚀 Actions Immédiates

### 1. Archiver les fichiers obsolètes
```bash
mkdir -p archived/orchestrator
mv orchestrator/event_bridge.py archived/orchestrator/
mv orchestrator/orchestrator.py archived/orchestrator/
mv orchestrator/unified_orchestrator.py archived/orchestrator/
```

### 2. Mettre à jour la documentation
Mettre à jour tous les fichiers de documentation pour référencer le nouvel orchestrator.

### 3. Migrer les composants existants
Utiliser le guide de migration pour adapter les composants restants.

## 📝 Mise à jour de la Documentation

Mettons à jour le README principal :