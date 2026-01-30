#!/bin/bash
#
# Emergent Learning Framework - Setup Script
# Supports: --mode fresh|merge|replace|skip
#           --core-only, --no-dashboard, --no-swarm
#
# Cross-platform: Works on Windows (Git Bash/MSYS2), Linux, and macOS
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.opencode"
ELF_DIR_DEFAULT="$CLAUDE_DIR/emergent-learning"
ELF_DIR="${ELF_BASE_PATH:-$ELF_DIR_DEFAULT}"
# SCRIPT_DIR is tools/setup, so repo root is two levels up
# Only set REPO_ROOT if not doing a custom install (ELF_BASE_PATH set to non-default)
if [ "$ELF_DIR" = "$ELF_DIR_DEFAULT" ]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
    REPO_ROOT=""
fi
BASE_DIR="$ELF_DIR"

MODE="interactive"
CORE_ONLY=false
NO_DASHBOARD=false
NO_SWARM=false

# Argument parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode=*)
            MODE="${1#--mode=}"
            shift
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --core-only)
            CORE_ONLY=true
            NO_DASHBOARD=true
            NO_SWARM=true
            shift
            ;;
        --no-dashboard)
            NO_DASHBOARD=true
            shift
            ;;
        --no-swarm)
            NO_SWARM=true
            shift
            ;;
        *)
            # Allow positional mode argument for backward compatibility if it matches known modes
            if [[ "$1" =~ ^(fresh|merge|replace|skip|interactive)$ ]]; then
                MODE="$1"
            fi
            shift
            ;;
    esac
done

if [ "$CORE_ONLY" = true ]; then
    NO_DASHBOARD=true
    NO_SWARM=true
fi

# Ensure .coordination exists in both Base Dir (active workspace) and ELF_DIR (installed location)
mkdir -p "$BASE_DIR/.coordination"
mkdir -p "$ELF_DIR/.coordination"

# Create directories
mkdir -p "$CLAUDE_DIR/commands"

# Detect Python command (python3 or python)
detect_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
}

PYTHON_CMD=$(detect_python)

db_has_user_data() {
    local db_path="$1"
    if [ -z "$PYTHON_CMD" ] || [ ! -f "$db_path" ]; then
        return 1
    fi

    local result
    set +e
    result=$("$PYTHON_CMD" - "$db_path" << 'PY'
import sqlite3
import sys

db_path = sys.argv[1]
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    if not tables:
        print("0")
        sys.exit(0)
    skip_tables = {"schema_version", "db_operations"}
    for table in tables:
        if table in skip_tables:
            continue
        cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
        if cursor.fetchone():
            print("1")
            sys.exit(0)
    print("0")
except Exception:
    print("1")
finally:
    try:
        conn.close()
    except Exception:
        pass
PY
    )
    local status=$?
    set -e
    if [ $status -ne 0 ]; then
        return 0
    fi

    [ "$result" = "1" ]
}

migrate_legacy_data() {
    local legacy_dir="$ELF_DIR_DEFAULT"
    local target_dir="$ELF_DIR"

    if [ ! -d "$legacy_dir" ]; then
        return
    fi

    if [ "$(cd "$legacy_dir" && pwd)" = "$(cd "$target_dir" && pwd)" ]; then
        return
    fi

    local legacy_db="$legacy_dir/memory/index.db"
    if [ ! -f "$legacy_db" ]; then
        return
    fi

    local target_db="$target_dir/memory/index.db"
    if db_has_user_data "$target_db"; then
        return
    fi

    mkdir -p "$(dirname "$target_db")"
    if [ -f "$target_db" ]; then
        cp "$target_db" "$target_db.pre-legacy-migration"
    fi

    cp "$legacy_db" "$target_db"

    local legacy_golden="$legacy_dir/memory/golden-rules.md"
    local target_golden="$target_dir/memory/golden-rules.md"
    if [ -f "$legacy_golden" ] && [ ! -f "$target_golden" ]; then
        cp "$legacy_golden" "$target_golden"
    fi

    echo "[ELF] Migrated legacy data to $target_dir"
}

if [ -n "$PYTHON_CMD" ]; then
    migrate_legacy_data
else
    echo "[ELF] Warning: Python not found; skipping legacy data migration."
fi

install_venv() {
    local venv_dir="$ELF_DIR/.venv"
    # requirements.txt is at root of repo, not in ELF_DIR
    local requirements="$SCRIPT_DIR/../../requirements.txt"
    # Fallback: check if it's in ELF_DIR (for in-place installs)
    if [ ! -f "$requirements" ]; then
        requirements="$ELF_DIR/requirements.txt"
    fi

    if [ -z "$PYTHON_CMD" ]; then
        echo "[ELF] Warning: Python not found. Skipping venv setup."
        echo "[ELF] Install Python 3.8+ and re-run setup for full functionality."
        return 1
    fi

    # Determine venv python path based on OS
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        VENV_PYTHON="$venv_dir/Scripts/python.exe"
    else
        VENV_PYTHON="$venv_dir/bin/python"
    fi

    # Check if existing venv is valid (python exists and works)
    local need_create=false
    if [ ! -d "$venv_dir" ]; then
        need_create=true
    elif [ ! -f "$VENV_PYTHON" ]; then
        echo "[ELF] Existing venv appears broken, recreating..."
        rm -rf "$venv_dir"
        need_create=true
    elif ! "$VENV_PYTHON" -c "import sys; sys.exit(0)" 2>/dev/null; then
        echo "[ELF] Existing venv Python not working, recreating..."
        rm -rf "$venv_dir"
        need_create=true
    fi

    # Create venv if needed
    if [ "$need_create" = true ]; then
        echo "[ELF] Creating Python virtual environment..."

        # Try to create venv, capture error for better diagnostics
        local venv_output
        venv_output=$($PYTHON_CMD -m venv "$venv_dir" 2>&1)
        local venv_exit=$?

        if [ $venv_exit -ne 0 ]; then
            echo "[ELF] Warning: Failed to create venv (exit code $venv_exit)"
            if echo "$venv_output" | grep -qi "ensurepip"; then
                echo "[ELF] Hint: On Debian/Ubuntu, run: sudo apt install python3-venv"
            elif echo "$venv_output" | grep -qi "permission"; then
                echo "[ELF] Hint: Permission denied. Check write access to $ELF_DIR"
            else
                echo "[ELF] Error: $venv_output"
            fi
            echo "[ELF] Falling back to system Python."
            VENV_PYTHON=""
            return 1
        fi
    fi

    # Verify venv python exists and works
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "[ELF] Warning: Venv python not found at $VENV_PYTHON"
        VENV_PYTHON=""
        return 1
    fi

    # Install/update requirements
    if [ -f "$requirements" ]; then
        echo "[ELF] Installing Python dependencies..."
        "$VENV_PYTHON" -m pip install --upgrade pip 2>&1 | grep -v "already satisfied" || true

        local pip_output
        pip_output=$("$VENV_PYTHON" -m pip install -r "$requirements" 2>&1)
        local pip_exit=$?

        if [ $pip_exit -ne 0 ]; then
            echo "[ELF] Warning: Some dependencies failed to install:"
            echo "$pip_output" | grep -i "error\|failed" | head -5
            echo "[ELF] Core features may still work."
        else
            echo "[ELF] Dependencies installed successfully."
        fi
    fi

    # Install project in editable mode
    echo "[ELF] Installing project in editable mode..."
    "$VENV_PYTHON" -m pip install -e "$SCRIPT_DIR/../.." 2>&1 || echo "[ELF] Warning: Failed to install editable package"

    # Final verification - can we import the core dependency?
    if ! "$VENV_PYTHON" -c "import peewee_aio" 2>/dev/null; then
        echo "[ELF] Warning: Core dependency peewee_aio not available."
        echo "[ELF] Try: $VENV_PYTHON -m pip install peewee-aio[aiosqlite]"
    fi

    echo "[ELF] Virtual environment ready at: $venv_dir"
    return 0
}

# Global variable for venv python path (set by install_venv)
VENV_PYTHON=""

install_commands() {
    local commands_dir="$SCRIPT_DIR/../../library/commands"
    local file filename dest
    local count=0

    if [ ! -d "$commands_dir" ]; then
        echo "[ELF] Warning: Commands directory not found"
        return 0
    fi

    for file in "$commands_dir"/*; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        dest="$CLAUDE_DIR/commands/$filename"

        if [ ! -f "$dest" ]; then
            if cp "$file" "$dest" 2>/dev/null; then
                echo "[ELF] Installed command: $filename"
                count=$((count + 1))
            else
                echo "[ELF] Error: Failed to install $filename" >&2
            fi
        elif ! cmp -s "$file" "$dest"; then
            if cp "$file" "$dest" 2>/dev/null; then
                echo "[ELF] Updated command: $filename"
                count=$((count + 1))
            else
                echo "[ELF] Error: Failed to update $filename" >&2
            fi
        fi
    done

    if [ $count -eq 0 ]; then
        echo "[ELF] Commands already up to date"
    fi
}

install_cli() {
    # Install elf.py CLI wrapper for easy command access
    # This allows users to run: python elf.py checkin, etc.
    local elf_cli_src="$SCRIPT_DIR/../../tools/scripts/elf.py"
    local elf_cli_dest="$ELF_DIR/elf.py"

    if [ -f "$elf_cli_src" ]; then
        mkdir -p "$ELF_DIR"
        cp "$elf_cli_src" "$elf_cli_dest"
        chmod +x "$elf_cli_dest"
    fi
}

install_core_files() {
    echo "[ELF] Installing core files to $ELF_DIR..."
    mkdir -p "$ELF_DIR"

    # Copy src contents (flattening)
    if [ -d "$SCRIPT_DIR/../../src" ]; then
        cp -r "$SCRIPT_DIR/../../src/"* "$ELF_DIR/"
    fi
    # Also copy elf_paths.py explicit check (though it is in src, ensuring presence)
    if [ -f "$SCRIPT_DIR/../../src/elf_paths.py" ]; then
        cp "$SCRIPT_DIR/../../src/elf_paths.py" "$ELF_DIR/"
    fi

    # Copy scripts
    mkdir -p "$ELF_DIR/scripts"
    if [ -d "$SCRIPT_DIR/../../tools/scripts" ]; then
        cp "$SCRIPT_DIR/../../tools/scripts/"*.sh "$ELF_DIR/scripts/" 2>/dev/null || true
        cp "$SCRIPT_DIR/../../tools/scripts/"*.py "$ELF_DIR/scripts/" 2>/dev/null || true
    fi

    # Copy golden rules template to memory directory
    mkdir -p "$ELF_DIR/memory"
    if [ -f "$SCRIPT_DIR/../../templates/golden-rules.md" ] && [ ! -f "$ELF_DIR/memory/golden-rules.md" ]; then
        cp "$SCRIPT_DIR/../../templates/golden-rules.md" "$ELF_DIR/memory/golden-rules.md"
        echo "[ELF] Copied golden-rules.md template"
    fi

    # Copy dashboard
    if [ "$NO_DASHBOARD" = false ] && [ -d "$SCRIPT_DIR/../../apps/dashboard" ]; then
        # Clean destination if exists to avoid merge issues
        rm -rf "$ELF_DIR/dashboard-app"
        cp -r "$SCRIPT_DIR/../../apps/dashboard" "$ELF_DIR/dashboard-app"
    fi

    # Copy swarm components
    if [ "$NO_SWARM" = false ]; then
        # Swarm agents are in src/agents, so they are copied with src/*
        # Conductor is in src/conductor, copied with src/*
        :
    fi
}

install_settings() {
    # Generate settings.json with hooks pointing to emergent-learning directory
    # Uses Python for cross-platform path handling
    # Pass VENV_PYTHON as environment variable for the script to use
    BASE_DIR="$BASE_DIR" VENV_PYTHON_PATH="$VENV_PYTHON" $PYTHON_CMD << 'PYTHON_SCRIPT'
import json
import os
import sys
from pathlib import Path

claude_dir = Path.home() / ".opencode"
base_dir_env = os.environ.get("ELF_BASE_PATH") or os.environ.get("BASE_DIR")
elf_dir = Path(base_dir_env).expanduser() if base_dir_env else (claude_dir / "emergent-learning")

# Hook paths: Prefer src/ (actual files) over hooks/ (symlinks may not work reliably)
hook_candidates = [
    elf_dir / "src" / "hooks" / "learning-loop",
    elf_dir / "hooks" / "learning-loop",
]
# Use the first existing path, defaulting to the post-installation location
elf_hooks = next((p for p in hook_candidates if p.exists()), hook_candidates[0])
settings_file = claude_dir / "settings.json"

# Get venv python path from environment, or detect it
venv_python = os.environ.get("VENV_PYTHON_PATH", "")

# If no venv python provided, try to detect it
if not venv_python:
    venv_dir = elf_dir / ".venv"
    if sys.platform == "win32":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"
    if candidate.exists():
        venv_python = str(candidate)

# Determine the python command to use in hooks
if venv_python and Path(venv_python).exists():
    python_cmd = f'"{venv_python}"'
else:
    # Fallback to system python3
    python_cmd = "python3"

# Detect platform and format paths appropriately
# Hook paths: learning-loop for pre/post, UserPromptSubmit for checkin detection
elf_hooks_main = elf_hooks.parent
checkin_hook_path = elf_hooks_main / "UserPromptSubmit" / "detect_checkin.py"

if sys.platform == "win32":
    # Windows: use escaped backslashes in JSON
    pre_hook = str(elf_hooks / "pre_tool_learning.py").replace("\\", "\\\\")
    post_hook = str(elf_hooks / "post_tool_learning.py").replace("\\", "\\\\")
    checkin_hook = str(checkin_hook_path).replace("\\", "\\\\")
    if venv_python:
        python_cmd = f'"{venv_python.replace(chr(92), chr(92)+chr(92))}"'
else:
    # Unix: forward slashes
    pre_hook = str(elf_hooks / "pre_tool_learning.py")
    post_hook = str(elf_hooks / "post_tool_learning.py")
    checkin_hook = str(checkin_hook_path)

settings = {
    "hooks": {
        "PreToolUse": [
            {
                "hooks": [
                    {
                        "command": f'{python_cmd} "{pre_hook}"',
                        "type": "command"
                    }
                ],
                "matcher": "Task"
            }
        ],
        "PostToolUse": [
            {
                "hooks": [
                    {
                        "command": f'{python_cmd} "{post_hook}"',
                        "type": "command"
                    }
                ],
                "matcher": "Task"
            }
        ]
    }
}

if checkin_hook_path.exists():
    settings["hooks"]["UserPromptSubmit"] = [
        {
            "hooks": [
                {
                    "command": f'{python_cmd} "{checkin_hook}"',
                    "type": "command"
                }
            ],
            "matcher": ""
        }
    ]

# Merge with existing settings if present
if settings_file.exists():
    try:
        with open(settings_file) as f:
            existing = json.load(f)
        # Only update hooks section, preserve other settings
        existing["hooks"] = settings["hooks"]
        settings = existing
    except (json.JSONDecodeError, KeyError):
        pass  # Use fresh settings if existing is corrupt

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=4)

print(f"[ELF] settings.json configured with hooks at: {elf_hooks}")
PYTHON_SCRIPT
}

install_git_hooks() {
    # Install git pre-commit hook enforcement
    # Priority: REPO_ROOT (dev env) -> ELF_DIR (if it happens to be a git repo)
    local git_hooks_dir=""

    if [ -d "$REPO_ROOT/.git/hooks" ]; then
        git_hooks_dir="$REPO_ROOT/.git/hooks"
    elif [ -d "$ELF_DIR/.git/hooks" ]; then
        git_hooks_dir="$ELF_DIR/.git/hooks"
    fi

    if [ -n "$git_hooks_dir" ] && [ -d "$git_hooks_dir" ] && [ -f "$SCRIPT_DIR/git-hooks/pre-commit" ]; then
        cp "$SCRIPT_DIR/git-hooks/pre-commit" "$git_hooks_dir/pre-commit"
        chmod +x "$git_hooks_dir/pre-commit"
        echo "[ELF] Git pre-commit hook installed to $git_hooks_dir"
    fi
}

install_ollama() {
    # Install Ollama and pull the embedding model
    echo "[ELF] Checking Ollama installation..."

    if command -v ollama &> /dev/null; then
        echo "[ELF] Ollama is already installed"

        # Check if nomic-embed-text model is available
        if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
            echo "[ELF] nomic-embed-text model is ready"
        else
            echo "[ELF] Pulling nomic-embed-text model (this may take a moment)..."
            if ollama pull nomic-embed-text 2>&1 | grep -v "pulling"; then
                echo "[ELF] nomic-embed-text model installed"
            else
                echo "[ELF] Warning: Could not pull nomic-embed-text model"
                echo "[ELF] You can install it manually with: ollama pull nomic-embed-text"
            fi
        fi
    else
        echo "[ELF] Ollama is not installed"
        echo "[ELF] For semantic search, install Ollama:"
        echo ""
        echo "    curl -fsSL https://ollama.com/install.sh | sh"
        echo ""
        echo "[ELF] Then pull the embedding model:"
        echo ""
        echo "    ollama pull nomic-embed-text"
        echo ""
        echo "[ELF] ELF will use keyword fallback until Ollama is available"
    fi
}

seed_golden_rules() {
    # Seed golden rules from markdown template into database
    # Look for golden_rules.md in repo first (source), then in ELF_DIR (deployed)
    local golden_rules_md=""
    if [ -f "$SCRIPT_DIR/../../memory/golden-rules.md" ]; then
        golden_rules_md="$SCRIPT_DIR/../../memory/golden-rules.md"
    elif [ -f "$ELF_DIR/memory/golden-rules.md" ]; then
        golden_rules_md="$ELF_DIR/memory/golden-rules.md"
    fi
    
    local seed_script="$ELF_DIR/scripts/seed_golden_rules.py"

    if [ -z "$PYTHON_CMD" ]; then
        echo "[ELF] Warning: Python not found, skipping golden rules seeding"
        return
    fi

    if [ ! -f "$golden_rules_md" ]; then
        echo "[ELF] Warning: golden-rules.md not found, skipping seeding"
        return
    fi

    if [ ! -f "$seed_script" ]; then
        # Try alternate location in repo
        seed_script="$SCRIPT_DIR/../../scripts/seed_golden_rules.py"
    fi

    if [ -f "$seed_script" ]; then
        # Use venv python if available, otherwise system python
        local python_to_use="${VENV_PYTHON:-$PYTHON_CMD}"
        echo "[ELF] Seeding golden rules into database..."
        echo "[ELF] Source: $golden_rules_md"
        echo "[ELF] Target DB: $ELF_DIR/memory/index.db"
        ELF_DIR="$ELF_DIR" "$python_to_use" "$seed_script" 2>&1 | grep -v "DeprecationWarning" || true
    else
        echo "[ELF] Warning: seed_golden_rules.py not found, skipping seeding"
    fi
}

apply_schema_migrations() {
    # Apply all database schema migrations to ensure schema is up-to-date
    local migrations_script="$SCRIPT_DIR/../../tools/scripts/apply_migrations.py"
    
    if [ ! -f "$migrations_script" ]; then
        # Try alternate location
        migrations_script="$SCRIPT_DIR/../scripts/apply_migrations.py"
    fi
    
    if [ -z "$PYTHON_CMD" ]; then
        echo "[ELF] Warning: Python not found, skipping schema migrations"
        return
    fi
    
    if [ ! -f "$migrations_script" ]; then
        # Create a simple inline migration script if not found
        local python_to_use="${VENV_PYTHON:-$PYTHON_CMD}"
        echo "[ELF] Applying schema migrations..."
        
        "$python_to_use" - "$ELF_DIR" << 'PYTHON_MIGRATIONS'
import sys
import sqlite3
from pathlib import Path

elf_dir = sys.argv[1]
db_path = Path(elf_dir) / "memory" / "index.db"
migrations_dir = Path(__file__).parent.parent / "src" / "query" / "migrations"

# For now, use a simple approach: ensure schema_version table exists
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Ensure schema_version table exists
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            description TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
except Exception as e:
    print(f"Warning: Could not create schema_version table: {e}")

conn.close()
print(f"[ELF] Schema migration setup complete at {db_path}")
PYTHON_MIGRATIONS
    else
        local python_to_use="${VENV_PYTHON:-$PYTHON_CMD}"
        echo "[ELF] Applying schema migrations..."
        ELF_DIR="$ELF_DIR" "$python_to_use" "$migrations_script"
    fi
}

copy_template() {
    local template_src="$SCRIPT_DIR/../../templates/AGENTS.md.template"
    local dest="$CLAUDE_DIR/AGENTS.md"
    
    if [ ! -f "$template_src" ]; then
        echo "[ELF] Warning: Template not found at $template_src"
        return
    fi
    
    cp "$template_src" "$dest"
    
    # Replace placeholder or hardcoded path with actual base directory
    # If ELF_BASE_PATH is set, replace default path with it
    if [ "$ELF_DIR" != "$ELF_DIR_DEFAULT" ]; then
         # Need to escape slashes for sed
         ESCAPED_TARGET=$(echo "$ELF_DIR" | sed 's/\//\\\//g')
         ESCAPED_DEFAULT="~\/.opencode\/emergent-learning"
         
         # Replace on Linux/Mac (sed -i works differently on Mac)
         if [[ "$OSTYPE" == "darwin"* ]]; then
             sed -i '' "s/$ESCAPED_DEFAULT/$ESCAPED_TARGET/g" "$dest"
         else
             sed -i "s/$ESCAPED_DEFAULT/$ESCAPED_TARGET/g" "$dest"
         fi
    fi
}

case "$MODE" in
    fresh)
        # New user - install everything
        copy_template
        install_commands
        install_core_files
        install_venv
        install_settings
        install_git_hooks
            seed_golden_rules
            apply_schema_migrations
            install_ollama
            echo "[ELF] Fresh install complete"
            ;;

    merge)
        # Merge: their config + ELF
        if [ -f "$CLAUDE_DIR/AGENTS.md" ]; then
            cp "$CLAUDE_DIR/AGENTS.md" "$CLAUDE_DIR/AGENTS.md.backup"
            {
                cat "$CLAUDE_DIR/AGENTS.md"
                echo ""
                echo ""
                echo "# =============================================="
                echo "# EMERGENT LEARNING FRAMEWORK - AUTO-APPENDED"
                echo "# =============================================="
                echo ""
                cat "$SCRIPT_DIR/../../templates/AGENTS.md.template"
            } > "$CLAUDE_DIR/AGENTS.md.new"
            mv "$CLAUDE_DIR/AGENTS.md.new" "$CLAUDE_DIR/AGENTS.md"
            echo "[ELF] Merged with existing config (backup: AGENTS.md.backup)"
        fi
        install_commands
        install_core_files
        install_venv
        install_settings
        install_git_hooks
        seed_golden_rules
        apply_schema_migrations
        install_ollama
        ;;

        replace)
        # Replace: backup theirs, use ELF only
        if [ -f "$CLAUDE_DIR/AGENTS.md" ]; then
            cp "$CLAUDE_DIR/AGENTS.md" "$CLAUDE_DIR/AGENTS.md.backup"
        fi
        copy_template
        install_commands
        install_core_files
        install_venv
        install_settings
        install_git_hooks
        seed_golden_rules
        apply_schema_migrations
        install_ollama
        echo "[ELF] Replaced config (backup: AGENTS.md.backup)"
        ;;

    skip)
        # Skip AGENTS.md but install commands/hooks
        echo "[ELF] Skipping AGENTS.md modification"
        echo "[ELF] Warning: ELF may not function correctly without AGENTS.md instructions"
        install_commands
        install_core_files
        install_venv
        install_settings
        install_git_hooks
        seed_golden_rules
        install_ollama
        ;;

    interactive|*)
        # Interactive mode - show menu
        echo "========================================"
        echo "Emergent Learning Framework - Setup"
        echo "========================================"
        echo ""

        if [ -f "$CLAUDE_DIR/AGENTS.md" ]; then
            if grep -q "Emergent Learning Framework" "$CLAUDE_DIR/AGENTS.md" 2>/dev/null; then
                echo "ELF already configured in AGENTS.md"
            else
                echo "Existing AGENTS.md found."
                echo ""
                echo "Options:"
                echo "  1) Merge - Keep yours, add ELF below"
                echo "  2) Replace - Use ELF only (yours backed up)"
                echo "  3) Skip - Don't modify AGENTS.md"
                echo ""
                read -p "Choice [1/2/3]: " choice
                case "$choice" in
                    1) bash "$0" --mode merge ;;
                    2) bash "$0" --mode replace ;;
                    3) bash "$0" --mode skip ;;
                    *) echo "Invalid choice"; exit 1 ;;
                esac
                exit 0
            fi
        else
            bash "$0" --mode fresh
            exit 0
        fi

        install_commands
        install_core_files
        install_venv
        install_settings
        install_git_hooks
        seed_golden_rules
        install_ollama
        echo ""
        echo "Setup complete!"
        ;;
esac
