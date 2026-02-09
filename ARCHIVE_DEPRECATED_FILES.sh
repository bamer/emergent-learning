#!/bin/bash
# Archive deprecated components after refactoring
# Run this script to move old files to archived_components/

set -e

ARCHIVE_DATE=$(date +%Y%m%d)
ARCHIVE_DIR="archived_components/${ARCHIVE_DATE}"

echo "📦 Archiving deprecated components to ${ARCHIVE_DIR}..."
mkdir -p "${ARCHIVE_DIR}"

# List of deprecated files to archive
declare -a DEPRECATED_FILES=(
    # Old Watcher (replaced by core/watcher.py)
    "Open_ELF/watcher/elf_watcher.py"
    
    # Sentinel (merged into core/watcher.py)
    "agents/sentinel_monitor.py"
    
    # Old EventBridge (replaced by core/event_bridge_v2.py)
    "Open_ELF/orchestrator/event_bridge.py"
    
    # Hook scripts (replaced by core/learning_processor.py)
    "hooks/learning-loop/post_tool_learning.py"
    "hooks/learning-loop/record_pheromone.py"
    "hooks/learning-loop/pre_tool_learning.py"
    "hooks/learning-loop/pre_tool_semantic_memory.py"
    "hooks/learning-loop/user_prompt_inject_context.py"
    
    # Conductor trails (moved to core/learning_processor.py)
    "conductor/conductor.py"
    
    # Old pattern handler (integrated into learning_processor)
    "pattern_response_handler.py"
)

# Archive each file
for file in "${DEPRECATED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  📁 Archiving: $file"
        
        # Create directory structure in archive
        dir=$(dirname "$file")
        mkdir -p "${ARCHIVE_DIR}/${dir}"
        
        # Move file to archive
        mv "$file" "${ARCHIVE_DIR}/${file}"
        
        # Create deprecation notice
        cat > "$file" << EOF
#!/usr/bin/env python3
"""
⚠️  DEPRECATED - FILE MOVED TO ARCHIVE

This file has been deprecated as part of the ELF refactoring (2026-02-09).

Original location: ${file}
Archived to: ${ARCHIVE_DIR}/${file}

Replacement:
  - Use core/watcher.py (merged Watcher + Sentinel)
  - Use core/learning_processor.py (all learning operations)
  - Use core/event_bridge_v2.py (simplified event routing)

See REFACTORING_SUMMARY.md for details.
"""

import sys
import warnings

warnings.warn(
    f"This module ({__file__}) has been deprecated. "
    "Use the new core/ components instead. "
    "See REFACTORING_SUMMARY.md",
    DeprecationWarning,
    stacklevel=2
)

if __name__ == "__main__":
    print("❌ This file is deprecated and no longer functional.")
    print("📁 Original file archived to: ${ARCHIVE_DIR}/${file}")
    print("✅ Use the new components instead:")
    print("   - core/watcher.py")
    print("   - core/learning_processor.py")
    print("   - core/event_bridge_v2.py")
    sys.exit(1)
EOF
        
        echo "     ✅ Archived + deprecation stub created"
    else
        echo "  ⚠️  File not found: $file"
    fi
done

# Create archive manifest
cat > "${ARCHIVE_DIR}/MANIFEST.md" << 'EOF'
# Archived Components Manifest

**Archive Date**: 2026-02-09
**Reason**: ELF Learning Workflow Refactoring

## Files Archived

### Monitoring Components (Merged)
- `Open_ELF/watcher/elf_watcher.py` → Replaced by `core/watcher.py`
- `agents/sentinel_monitor.py` → Merged into `core/watcher.py`

### Event Handling (Consolidated)
- `Open_ELF/orchestrator/event_bridge.py` → Replaced by `core/event_bridge_v2.py`

### Learning Operations (Centralized)
- `hooks/learning-loop/post_tool_learning.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/record_pheromone.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/pre_tool_learning.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/pre_tool_semantic_memory.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/user_prompt_inject_context.py` → Merged into `core/learning_processor.py`

### Workflow (Integrated)
- `conductor/conductor.py` → Trail functionality moved to `core/learning_processor.py`
- `pattern_response_handler.py` → Integrated into `core/learning_processor.py`

## New Architecture

```
Level 1: core/watcher.py (merged Watcher + Sentinel)
Level 2: Open_ELF/orchestrator/unified_orchestrator.py (service management)
Level 3: CEO agent (strategic decisions)

Supporting:
- core/learning_processor.py (all learning + trails)
- core/event_bridge_v2.py (event routing)
```

## Restoration

If you need to restore these files:
1. Copy from this archive directory back to original location
2. Update imports and dependencies
3. Test thoroughly before production use

## Documentation

See `../REFACTORING_SUMMARY.md` for complete refactoring details.
EOF

echo ""
echo "✅ Archive complete!"
echo "📁 Location: ${ARCHIVE_DIR}/"
echo "📄 Manifest: ${ARCHIVE_DIR}/MANIFEST.md"
echo ""
echo "📝 Deprecation stubs created in original locations"
echo "🔄 Old components are now disabled but can be restored from archive"
