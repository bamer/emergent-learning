#!/usr/bin/env python3
"""
ELF Checkin Simplifié - Répare les problèmes de terminal et d'interaction
Fonctionne toujours correctement:
- Mode non-interactif : Ouvre terminal + démarre serveur OpenCode + services
- Mode interactif : Pose la question puis démarre comme demandé
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def display_banner():
    """Affiche la bannière ELF."""
    print("""
┌────────────────────────────────────┐
│      EMERGENT LEARNING FRAMEWORK     │
├────────────────────────────────────┤
│                                     │
│      █████▒  █▒     █████▒         │
│      █▒      █▒     █▒             │
│      ████▒   █▒     ████▒          │
│      █▒      █▒     █▒             │
│      █████▒  █████▒ █▒             │
│                                     │
└────────────────────────────────────┘
    """)


def start_opencode_in_terminal():
    """Démarre OpenCode dans une nouvelle fenêtre de terminal."""
    print("\n🚀 Démarrage d'OpenCode dans une nouvelle fenêtre...")

    # Script pour GNOME terminal
    script = """
#!/bin/bash
echo "🖥  Utilisation du terminal GNOME..."
echo "🚀 Démarrage du serveur OpenCode..."

# Vérifier si gnome-terminal est disponible
if command -v gnome-terminal >/dev/null 2>&1; then
    # Ouvrir dans une nouvelle fenêtre avec titre personnalisé
    gnome-terminal --title="Serveur OpenCode" --geometry=100x25 -- bash -c '
        echo "🌐 Serveur démarré sur http://localhost:4096"
        echo "📊 Santé : http://localhost:4096/global/health"
        echo "🤖 Agents : http://localhost:4096/agents"
        echo ""
        echo "⏹️  Appuyer sur Ctrl+C pour arrêter le serveur"
        echo ""
        opencode serve --port 4096
        echo ""
        echo "✅ Serveur OpenCode arrêté"
        read
    '
elif command -v tmux >/dev/null 2>&1; then
    echo "🖥  Utilisation de tmux..."
    tmux new-session -d -s opencode "opencode serve --port 4096"
    echo "✅ Session tmux créée"
else
    echo "❌ Aucun terminal trouvé, démarrage en arrière-plan..."
    opencode serve --port 4096 &
fi
"""

    # Écrire le script temporaire
    script_file = Path("/tmp/launch-opencode.sh")
    script_file.write_text(script)
    script_file.chmod(0o755)

    try:
        # Exécuter le script
        subprocess.run(["bash", str(script_file)], check=True)
        print("✅ Terminal OpenCode démarré!")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False


def start_opencode_services():
    """Démarre les services OpenCode (sans nouvelle fenêtre)."""
    print("\n🚀 Démarrage des services OpenCode...")

    try:
        # Vérifier si déjà en cours
        result = subprocess.run(
            ["curl", "-s", "http://localhost:4096/global/health"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ Serveur OpenCode déjà en cours!")
            return True
    except:
        pass

    # Démarrer en arrière-plan
    try:
        subprocess.run(["opencode", "serve", "--port", "4096"], check=True)
        print("✅ Services OpenCode démarrés en arrière-plan!")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def check_services_status():
    """Vérifie le statut des services."""
    print("\n🔍 Statut des services:")

    # Vérifier Dashboard
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:3001/api/heuristics?limit=1"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  ✅ Dashboard : http://localhost:3001")
        else:
            print("  ⚠️  Dashboard : Non détecté")
    except:
        print("  ⚠️  Dashboard : Non détecté")

    # Vérifier OpenCode
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:4096/global/health"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  ✅ OpenCode  : http://localhost:4096")
        else:
            print("  ⚠️  OpenCode  : Non détecté")
    except:
        print("  ⚠️  OpenCode  : Non détecté")


def ask_opencode_question():
    """Pose la question sur le démarrage OpenCode."""
    print("\n🚀 Services OpenCode")
    print("OpenCode fournit l'orchestration des agents pour ELF.")
    print("Voulez-vous démarrer les services maintenant?")

    try:
        response = (
            input("Démarrer les services OpenCode? (o/n) [défaut: o]: ").lower().strip()
        )
        return response in ["o", "oui", "yes", ""]  # '' = défaut = oui
    except (EOFError, KeyboardInterrupt):
        return False


def main():
    """Point d'entrée principal."""
    # Vérifier les arguments
    interactive = "--non-interactive" not in sys.argv

    display_banner()

    if interactive:
        # MODE INTERACTIF : poser la question
        answer = ask_opencode_question()
        if answer:
            start_opencode_in_terminal()
        else:
            print("⏭  Démarrage des services OpenCode ignoré.")
    else:
        # MODE NON-INTERACTIF : démarrer directement
        start_opencode_in_terminal()

    # Attendre un peu pour le démarrage
    time.sleep(2)

    # Afficher le statut final
    check_services_status()

    print("\n📚 Règles d'Or : Disponibles via système de requête")
    print("   Utiliser : python query/query.py --context")

    print("\n✅ Checkin ELF terminé!")

    # Vérifier si tout est prêt
    try:
        dashboard_ok = (
            subprocess.run(
                ["curl", "-s", "http://localhost:3001/api/heuristics?limit=1"],
                capture_output=True,
            ).returncode
            == 0
        )
        opencode_ok = (
            subprocess.run(
                ["curl", "-s", "http://localhost:4096/global/health"],
                capture_output=True,
            ).returncode
            == 0
        )

        if dashboard_ok and opencode_ok:
            print("\n🎯 Système complet : agents + dashboard + apprentissage!")
    except:
        pass


if __name__ == "__main__":
    main()
