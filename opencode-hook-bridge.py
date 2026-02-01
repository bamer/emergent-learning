#!/usr/bin/env python3
"""
Opencode Hook Bridge - Intègre les hooks ELF dans Opencode CLI

Ce script doit être appelé par Opencode à chaque utilisation d'outil.
À configurer dans ~/.config/opencode/config.json ou via la commande /config
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def main():
    """Point d'entrée principal appelé par Opencode."""

    # Lire les données depuis stdin (passées par Opencode)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    # Extraire les informations de l'outil
    tool_name = input_data.get("tool", "unknown")
    tool_input = input_data.get("input", {})
    tool_output = input_data.get("output", {})
    success = input_data.get("success", True)
    session_id = input_data.get("session_id", "unknown")

    # Préparer les données pour les hooks ELF
    hook_data = {
        "event_type": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "success": success,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
    }

    # Chemins
    elf_base = Path.home() / ".opencode" / "emergent-learning"
    hooks_dir = Path.home() / ".opencode" / "hooks"

    # Définir l'environnement
    env = dict(os.environ)
    env["ELF_BASE_PATH"] = str(elf_base)
    env["PYTHONPATH"] = str(elf_base)

    # Exécuter les hooks PostToolUse
    post_tool_dir = hooks_dir / "PostToolUse"
    if post_tool_dir.exists():
        for hook_file in sorted(post_tool_dir.glob("*.py")):
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(hook_file)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(elf_base),
                    env=env,
                )
                stdout, stderr = proc.communicate(
                    input=json.dumps(hook_data).encode(), timeout=30
                )

                if proc.returncode == 0:
                    print(f"✅ Hook {hook_file.name} exécuté", file=sys.stderr)
                else:
                    print(
                        f"⚠️ Hook {hook_file.name} a échoué: {stderr.decode()[:200]}",
                        file=sys.stderr,
                    )

            except Exception as e:
                print(f"❌ Erreur hook {hook_file.name}: {e}", file=sys.stderr)

    # Si échec, déclencher aussi learning-loop
    if not success:
        learning_dir = hooks_dir / "learning-loop"
        if learning_dir.exists():
            failure_data = {
                **hook_data,
                "event_type": "ToolFailure",
                "failure_reason": tool_output.get("error", "Unknown error"),
            }

            for hook_file in sorted(learning_dir.glob("*.py")):
                try:
                    proc = subprocess.Popen(
                        [sys.executable, str(hook_file)],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=str(elf_base),
                        env=env,
                    )
                    proc.communicate(
                        input=json.dumps(failure_data).encode(), timeout=30
                    )
                except:
                    pass

    # Retourner le résultat à Opencode
    result = {
        "status": "ok",
        "hooks_triggered": True,
        "timestamp": datetime.now().isoformat(),
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
