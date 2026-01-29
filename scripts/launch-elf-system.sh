#!/bin/bash
#
# ELF Multi-Agent System Launcher - Enhanced avec Terminal Séparée
# Usage:
#   ./launch-elf-system.sh [--daemon]       # Lancement normal du système
#   ./launch-elf-system.sh --opencode       # Démarrer serveur OpenCode dans terminal séparée
#   ./launch-elf-system.sh --stop-opencode  # Arrêter serveur OpenCode
#   ./launch-elf-system.sh --check          # Vérification santé système
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Détecter la commande Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Erreur: Python non trouvé. Installez depuis https://python.org${NC}"
    exit 1
fi

# Fonction pour vérifier si le serveur OpenCode fonctionne
check_opencode() {
    if curl -s http://localhost:4096/global/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Serveur OpenCode: DÉMARRÉ${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Serveur OpenCode: NON DÉMARRÉ${NC}"
        echo -e "   Démarrez avec: ${BLUE}opencode server --port 4096${NC}"
        return 1
    fi
}

# Fonction pour vérifier le dashboard
check_dashboard() {
    if curl -s http://localhost:8888/api/stats >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Dashboard: DÉMARRÉ${NC}"
    else
        echo -e "${YELLOW}⚠️  Dashboard: NON DÉMARRÉ${NC}"
        echo -e "   Démarrez avec: ${BLUE}cd dashboard-app && bash run-dashboard.sh${NC}"
        return 1
    fi
}

# Fonction pour démarrer le serveur OpenCode dans une fenêtre séparée
start_opencode_separated_terminal() {
    echo -e "${PURPLE}🌐 Démarrage du Serveur OpenCode dans Terminal Séparée...${NC}"
    echo ""
    
    # Vérifier si déjà en cours
    if check_opencode; then
        echo -e "${YELLOW}⚠️  Le serveur OpenCode est déjà en cours d'exécution${NC}"
        return 0
    fi
    
    # Détecter le type de terminal disponible
    TERMINAL_CMD=""
    TERMINAL_NAME=""
    
    if command -v gnome-terminal >/dev/null 2>&1; then
        # GNOME Terminal
        TERMINAL_CMD="gnome-terminal --title='OpenCode Server - Fermez avec Ctrl+C'"
        TERMINAL_NAME="GNOME Terminal"
        
    elif command -v konsole >/dev/null 2>&1; then
        # KDE Konsole
        TERMINAL_CMD="konsole --title 'OpenCode Server - Fermez avec Ctrl+C'"
        TERMINAL_NAME="KDE Konsole"
        
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        # XFCE Terminal
        TERMINAL_CMD="xfce4-terminal --title 'OpenCode Server - Fermez avec Ctrl+C'"
        TERMINAL_NAME="XFCE Terminal"
        
    elif command -v xterm >/dev/null 2>&1; then
        # xterm (fallback)
        TERMINAL_CMD="xterm -title 'OpenCode Server - Fermez avec Ctrl+C'"
        TERMINAL_NAME="xterm"
        
    else
        # Dernière option: terminal standard
        TERMINAL_CMD="x-terminal-emulator -title 'OpenCode Server - Fermez avec Ctrl+C'"
        TERMINAL_NAME="terminal standard"
    fi
    
    if [ -n "$TERMINAL_CMD" ]; then
        echo -e "${GREEN}📱 Terminal détecté: ${TERMINAL_NAME}${NC}"
        
        # Préparer le script à exécuter dans la nouvelle fenêtre
        SERVER_SCRIPT="
echo -e '${GREEN}🌐 SERVEUR OPENCODE - TERMINAL SÉPARÉE${NC}'
echo -e '${GREEN}=============================================${NC}'
echo -e '${BLUE}Port: 4096${NC}'
echo -e '${BLUE}État: Démarrage en cours...${NC}'
echo -e '${BLUE}Terminal: ${TERMINAL_NAME}${NC}'
echo -e '${BLUE}Arrêt: Fermez cette fenêtre (Ctrl+C)${NC}'
echo -e '${GREEN}=============================================${NC}'
echo ''
echo -e '${YELLOW}⚡ Lancement du serveur...${NC}'
cd '$ELF_DIR'
opencode server --port 4096
        "
        
        # Exécuter dans la nouvelle fenêtre
        if command -v gnome-terminal >/dev/null 2>&1; then
            # GNOME Terminal
            gnome-terminal -- bash -c "$SERVER_SCRIPT" &
        elif command -v konsole >/dev/null 2>&1; then
            # KDE Konsole  
            konsole --hold -e bash -c "$SERVER_SCRIPT" &
        elif command -v xfce4-terminal >/dev/null 2>&1; then
            # XFCE Terminal
            xfce4-terminal -e bash -c "$SERVER_SCRIPT" &
        else
            # Autre terminal
            x-terminal-emulator -e bash -c "$SERVER_SCRIPT" &
        fi
        
        OPENCODE_PID=$!
        echo -e "${GREEN}✅ Serveur OpenCode démarré (PID: $OPENCODE_PID)${NC}"
        echo -e "${BLUE}   🖥️  Terminal ${TERMINAL_NAME} ouverte avec le serveur${NC}"
        echo ""
        echo -e "${PURPLE}💡 CONTRÔLE DU SERVEUR:${NC}"
        echo -e "${BLUE}   • Monitorer: ${GREEN}curl http://localhost:4096/global/health${NC}"
        echo -e "${BLUE}   • Arrêter: ${RED}./launch-elf-system.sh --stop-opencode${NC}"
        echo -e "${BLUE}   • Logs: ${YELLOW}.coordination/watcher-log.md${NC}"
        
        # Attendre que le serveur soit prêt
        echo -e "${BLUE}⏳ Attente de disponibilité du serveur...${NC}"
        for i in {1..10}; do
            if curl -s http://localhost:4096/global/health >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Serveur OpenCode prêt et disponible!${NC}"
                return 0
            fi
            echo -e "${YELLOW}⏳ Attente... ($i/10)${NC}"
            sleep 1
        done
        
        echo -e "${RED}❌ Timeout: Le serveur n'a pas démarré rapidement${NC}"
        return 1
    else
        echo -e "${RED}❌ Aucun terminal approprié trouvé${NC}"
        echo -e "${YELLOW}🔄 Lancement en arrière-plan à la place...${NC}"
        
        # Lancer en arrière-plan
        cd "$ELF_DIR"
        opencode server --port 4096 &
        OPENCODE_PID=$!
        echo -e "${GREEN}✅ Serveur OpenCode démarré en arrière-plan (PID: $OPENCODE_PID)${NC}"
        
        # Attendre un peu pour le démarrage
        sleep 3
        
        if curl -s http://localhost:4096/global/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Serveur prêt!${NC}"
        else
            echo -e "${YELLOW}⚠️  Vérification du serveur impossible${NC}"
        fi
        
        return 0
    fi
}

# Fonction pour arrêter proprement le serveur OpenCode
stop_opencode_server() {
    echo -e "${BLUE}🛑 Arrêt du serveur OpenCode...${NC}"
    
    # Chercher et tuer les processus OpenCode
    if pgrep -f "opencode server" >/dev/null; then
        # Obtenir la liste des PIDs
        PIDS=$(pgrep -f "opencode server")
        echo -e "${YELLOW}📋 Processus trouvés: $PIDS${NC}"
        
        # Tuer proprement chaque processus
        for PID in $PIDS; do
            echo -e "${BLUE}   Arrêt du processus $PID...${NC}"
            kill $PID 2>/dev/null
        done
        
        # Attendre un peu et vérifier
        sleep 2
        
        if pgrep -f "opencode server" >/dev/null; then
            echo -e "${RED}   Forcer l'arrêt...${NC}"
            pkill -9 -f "opencode server"
        fi
        
        echo -e "${GREEN}✅ Serveur OpenCode arrêté${NC}"
    else
        echo -e "${YELLOW}⚠️  Aucun serveur OpenCode en cours d'exécution${NC}"
    fi
}

# Fonction pour démarrer le watcher daemon
start_watcher_daemon() {
    echo -e "${PURPLE}👁️ Démarrage du Watcher Daemon...${NC}"
    
    cd "$ELF_DIR"
    
    # Démarrer en arrière-plan
    $PYTHON_CMD watcher/enhanced_watcher.py --daemon --interval 30 &
    WATCHER_PID=$!
    
    echo -e "${GREEN}✅ Watcher démarré (PID: $WATCHER_PID)${NC}"
    echo -e "   📝 Logs: ${BLUE}$ELF_DIR/.coordination/watcher-log.md${NC}"
    echo -e "   🛑 Contrôle: ${BLUE}touch $ELF_DIR/.coordination/watcher-stop${NC}"
    
    # Sauvegarder le PID pour la gestion
    echo $WATCHER_PID > "$ELF_DIR/.watcher.pid"
}

# Fonction pour effectuer une vérification de santé
run_health_check() {
    echo -e "${PURPLE}🔍 Vérification Santé Système ELF${NC}"
    echo -e "${PURPLE}=================================${NC}"
    echo ""
    
    check_opencode
    OPENCODE_STATUS=$?
    
    echo ""
    check_dashboard
    DASHBOARD_STATUS=$?
    
    echo ""
    
    # Vérifier le répertoire de coordination
    if [ -d "$ELF_DIR/.coordination" ]; then
        echo -e "${GREEN}✅ Répertoire coordination: EXISTE${NC}"
        echo -e "   Tableau noir: ${BLUE}$ELF_DIR/.coordination/blackboard.json${NC}"
        echo -e "   Logs watcher: ${BLUE}$ELF_DIR/.coordination/watcher-log.md${NC}"
    else
        echo -e "${YELLOW}⚠️  Répertoire coordination: MANQUANT${NC}"
        echo -e "   Création: $ELF_DIR/.coordination"
        mkdir -p "$ELF_DIR/.coordination"
    fi
    
    echo ""
    echo -e "${PURPLE}📊 Résumé État Système${NC}"
    
    if [ $OPENCODE_STATUS -eq 0 ] && [ $DASHBOARD_STATUS -eq 0 ]; then
        echo -e "${GREEN}🎉 Tous les systèmes opérationnels!${NC}"
        return 0
    elif [ $OPENCODE_STATUS -ne 0 ] || [ $DASHBOARD_STATUS -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Certains services nécessitent attention${NC}"
        return 1
    else
        echo -e "${RED}❌ Problèmes multiples détectés${NC}"
        return 2
    fi
}

# Fonction pour afficher l'aide
show_usage() {
    echo -e "${PURPLE}ELF Multi-Agent System Launcher - Enhanced${NC}"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --check          Vérifier santé système uniquement"
    echo "  --daemon         Démarrer système complet avec watcher daemon"
    echo "  --opencode       Démarrer serveur OpenCode dans terminal séparée"
    echo "  --stop-opencode  Arrêter serveur OpenCode"
    echo "  --help, -h      Afficher cette aide"
    echo ""
    echo "Composants:"
    echo "  🤖 ELF Orchestrator  - Coordination multi-agent"
    echo "  👁️ ELF Watcher     - Cycles surveillance 30s"
    echo "  🌐 OpenCode Server   - API spawn agents"
    echo "  📊 Dashboard        - Interface web"
    echo ""
    echo "Nouvelles fonctionnalités:"
    echo "  🖥️  Terminal séparée pour serveur OpenCode"
    echo "  🛑  Arrêt propre du serveur OpenCode"
    echo "  🧠  Détection automatique type terminal"
    echo "  🌍  Support multilingue (français)"
    echo ""
    echo "Exemples:"
    echo "  $0 --check                    # Vérifier santé"
    echo "  $0 --opencode                  # Démarrer serveur séparé"
    echo "  $0 --daemon                    # Démarrer système complet"
    echo ""
}

# Analyser les arguments
case "${1:-}" in
    --check|-c)
        run_health_check
        exit $?
        ;;
    --daemon|-d)
        echo -e "${PURPLE}🚀 Démarrage ELF Multi-Agent System...${NC}"
        echo -e "${PURPLE}=======================================${NC}"
        
        # Vérifier les prérequis
        echo -e "${BLUE}🔍 Vérification prérequis...${NC}"
        
        if ! check_opencode; then
            echo -e "${RED}❌ Serveur OpenCode requis mais non démarré${NC}"
            echo -e "   Démarrez: ${BLUE}opencode server --port 4096${NC}"
            echo -e "   Ou: ${BLUE}$0 --opencode${NC}"
            exit 1
        fi
        
        if ! check_dashboard; then
            echo -e "${RED}❌ Dashboard requis mais non démarré${NC}"
            echo -e "   Démarrez: ${BLUE}cd dashboard-app && bash run-dashboard.sh${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}✅ Prérequis vérifiés${NC}"
        echo ""
        
        start_watcher_daemon
        exit 0
        ;;
    --opencode|--opencode)
        start_opencode_separated_terminal
        exit 0
        ;;
    --stop-opencode|--stop-opencode)
        stop_opencode_server
        exit 0
        ;;
    --help|-h|"")
        show_usage
        exit 0
        ;;
    *)
        echo -e "${RED}Erreur: Option '$1' inconnue${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac