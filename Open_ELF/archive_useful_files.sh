#!/bin/bash
# Archive des fichiers inutiles avant nettoyage définitif
# Usage: ./archive_useful_files.sh

ARCHIVE_DIR="/home/bamer/.opencode/emergent-learning/Open_ELF/archived_before_cleanup/$(date +%Y-%m-%d)"
mkdir -p "$ARCHIVE_DIR"

echo "📦 Archivage des fichiers inutiles vers: $ARCHIVE_DIR"

# Fichiers à archiver (déplacer, pas supprimer)
FILES_TO_ARCHIVE=(
    # Redondants avec event_bridge.py
    "orchestrator/async_opencode_client.py"

    # Redondants avec elf_logging.py
    "agents/logger.py"

    # Créent des sessions directement (ERADICATION!)
    "agents/opconnection.py"
    "agents/opencode_client.py"
    "agents/unified_orchestrator.py"  # (celui dans agents/, PAS dans orchestrator/)

    # API redondante (unified_orchestrator a déjà /status endpoint)
    "agents/agent_status_api.py"

    # Obsolètes
    "agents/orchestrator_state.py"
)

# Déplacer les fichiers
for file in "${FILES_TO_ARCHIVE[@]}"; do
    SRC="/home/bamer/.opencode/emergent-learning/Open_ELF/$file"
    DST="$ARCHIVE_DIR/$(basename $file)"

    if [ -f "$SRC" ]; then
        mkdir -p "$ARCHIVE_DIR/$(dirname $file)"
        mv "$SRC" "$DST"
        echo "✅ Archivé: $file → $DST"
    else
        echo "⚠️  Non trouvé (déjà archivé?): $file"
    fi
done

# Créer README dans archive
cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Fichiers Archivés - Avant Nettoyage Définitif

**Date**: $(date +%Y-%m-%d)
**Raison**: Restructuration architecture ELF

## Architecture Nouvelle

```
Open_ELF/
├── orchestrator/
│   ├── event_bridge.py                  ← Communication Layer (sessions, SSE)
│   └── unified_orchestrator.py          ← Orchestration Layer (workflows, décisions)
└── agents/
    └── elf_logging.py                    ← Infrastructure Layer (logs)
```

## Règle d'Or

> Toute fonction qui instancie ou tente d'ouvrir une session en direct sur le serveur opencode
> devrait être éradiquée.

## Fichiers Archivés

| Fichier | Raison |
|---------|--------|
| `orchestrator/async_opencode_client.py` | Redondant avec event_bridge.py (fusionné) |
| `agents/logger.py` | Redondant avec elf_logging.py (fusionné) |
| `agents/opconnection.py` | Crée sessions directes (éradiqué) |
| `agents/opencode_client.py` | Crée sessions directes (éradiqué) |
| `agents/unified_orchestrator.py` (agents/) | Crée sessions directes (éradiqué) |
| `agents/agent_status_api.py` | Redondant (unified_orchestrator a /status) |
| `agents/orchestrator_state.py` | Obsolète (non utilisé) |

## Migration des Appelants

### Avant (CRÉATION SESSION DIRECTE - MAUVAIS):
```python
response = requests.post(
    f"http://localhost:4096/session",
    json={"title": "Session"},
)
```

### Après (DÉLÉGATION - CORRECT):
```python
from orchestrator.event_bridge import EventBridge

bridge = EventBridge()
response = bridge.send_message("Message", agent="researcher")
```

## Tests à Effectuer Avant Suppression

- [ ] unified_orchestrator.py fonctionne sans ces fichiers
- [ ] event_bridge.py fonctionne
- [ ] Toutes les old sessions sont nettoyées
- [ ] Pas de nouvelle session créée directement
- [ ] RAM usage stable (~20-30 Go, pas 100 Go)

## Si Tout Est OK

Supprimer ce dossier après 7 jours:
```bash
rm -rf /home/bamer/.opencode/emergent-learning/Open_ELF/archived_before_cleanup/*/
```

## Si Problèmes

Restaurer les fichiers depuis ce dossier:
```bash
cp archived_before_cleanup/202X-XX-XX/* .
```
EOF

echo ""
echo "✅ Archivage terminé!"
echo "📄 README créé: $ARCHIVE_DIR/README.md"
echo ""
echo "📋 Étapes suivantes:"
echo "  1. Tester le système sans ces fichiers"
echo "  2. Vérifier qu'aucune session directe n'est créée"
echo "  3. Vérifier RAM usage stable"
echo "  4. Si OK → Supprimer ce dossier après 7 jours"
echo ""
echo "🔍 Pour voir les fichiers archivés:"
echo "  ls -la $ARCHIVE_DIR"
