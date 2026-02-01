#!/usr/bin/env bash
"""
ELF OpenCode - Script de démarrage complet

Démarrage de tous les services nécessaires pour ELF OpenCode:
1. OpenCode Server (port 4096)
2. Dashboard Backend (port 8888) 
3. Event Bridge (port 9998)
4. Dashboard Frontend (port 3001)

Usage:
    ./start-elf-system.sh [mode]
    
Modes:
    all     - Démarre tout (défaut)
    minimal - Démarre seulement OpenCode + Backend
    test    - Mode test rapide
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="${SCRIPT_DIR}"
OPENCODE_DIR="${HOME}/.opencode"
LOGS_DIR="${ELF_DIR}/Open_ELF/logs"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_success() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }

# Variables globales
OPENCODE_PID=""
BACKEND_PID=""
EVENT_BRIDGE_PID=""
FRONTEND_PID=""

# Nettoyage à la sortie
cleanup() {
    log "🧹 Nettoyage des processus..."
    
    # Tuer les processus enfants
    if [[ -n "${OPENCODE_PID:-}" ]]; then
        kill "${OPENCODE_PID}" 2>/dev/null || true
    fi
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi
    if [[ -n "${EVENT_BRIDGE_PID:-}" ]]; then
        kill "${EVENT_BRIDGE_PID}" 2>/dev/null || true
    fi
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi
    
    # Attendre la fin des processus
    [[ -n "${OPENCODE_PID:-}" ]] && wait "${OPENCODE_PID}" 2>/dev/null || true
    [[ -n "${BACKEND_PID:-}" ]] && wait "${BACKEND_PID}" 2>/dev/null || true
    [[ -n "${EVENT_BRIDGE_PID:-}" ]] && wait "${EVENT_BRIDGE_PID}" 2>/dev/null || true
    [[ -n "${FRONTEND_PID:-}" ]] && wait "${FRONTEND_PID}" 2>/dev/null || true
    
    log_success "✅ Nettoyage terminé"
}
trap cleanup EXIT INT TERM

# Vérifier si un service est en cours d'exécution
is_running() {
    local pid=$1
    if [[ -n "${pid:-}" ]] && kill -0 "${pid}" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Attendre qu'un service soit prêt
wait_for_service() {
    local url=$1
    local name=$2
    local timeout=${3:-30}
    local count=0
    
    log "⏳ Attente de ${name} (${url})..."
    
    while [[ $count -lt $timeout ]]; do
        if curl -s "${url}" >/dev/null 2>&1; then
            log_success "✅ ${name} est prêt"
            return 0
        fi
        sleep 1
        ((count++))
    done
    
    log_error "❌ ${name} n'est pas prêt après ${timeout}s"
    return 1
}

# Démarrer OpenCode Server
start_opencode_server() {
    log "🚀 Démarrage d'OpenCode Server (port 4096)..."
    
    # Vérifier si OpenCode est installé
    if ! command -v opencode >/dev/null 2>&1; then
        log_error "❌ OpenCode n'est pas installé. Installez-le avec:"
        log_error "curl -fsSL https://get.opencde.ai | sh"
        exit 1
    fi
    
    # Démarrer le serveur en arrière-plan
    opencode serve --port 4096 --hostname 127.0.0.1 >"${LOGS_DIR}/opencode-server.log" 2>&1 &
    OPENCODE_PID=$!
    
    # Attendre que le serveur soit prêt
    if wait_for_service "http://localhost:4096/global/health" "OpenCode Server" 30; then
        log_success "✅ OpenCode Server démarré (PID: ${OPENCODE_PID})"
        return 0
    else
        log_error "❌ Impossible de démarrer OpenCode Server"
        return 1
    fi
}

# Démarrer le Dashboard Backend
start_backend() {
    log "🚀 Démarrage du Dashboard Backend (port 8888)..."
    
    local backend_dir="${ELF_DIR}/dashboard-app/backend"
    
    # Vérifier que le répertoire existe
    if [[ ! -d "${backend_dir}" ]]; then
        log_error "❌ Répertoire backend introuvable: ${backend_dir}"
        return 1
    fi
    
    # Activer l'environnement virtuel
    if [[ -f "${backend_dir}/venv/bin/activate" ]]; then
        source "${backend_dir}/venv/bin/activate"
    else
        log_warning "⚠️ Environnement virtuel non trouvé, utilisation de Python système"
    fi
    
    # Démarrer le backend en arrière-plan
    cd "${backend_dir}"
    uvicorn main:app --host 0.0.0.0 --port 8888 >"${LOGS_DIR}/backend.log" 2>&1 &
    BACKEND_PID=$!
    cd - >/dev/null
    
    # Attendre que le backend soit prêt
    if wait_for_service "http://localhost:8888/api/v1/agents/status" "Dashboard Backend" 30; then
        log_success "✅ Dashboard Backend démarré (PID: ${BACKEND_PID})"
        return 0
    else
        log_error "❌ Impossible de démarrer le Dashboard Backend"
        return 1
    fi
}

# Démarrer l'Event Bridge
start_event_bridge() {
    log "🚀 Démarrage de l'Event Bridge (port 9998)..."
    
    local orchestrator_dir="${ELF_DIR}/Open_ELF/orchestrator"
    
    # Vérifier que le répertoire existe
    if [[ ! -d "${orchestrator_dir}" ]]; then
        log_error "❌ Répertoire orchestrator introuvable: ${orchestrator_dir}"
        return 1
    fi
    
    # Démarrer l'Event Bridge en arrière-plan
    cd "${orchestrator_dir}"
    python3 event_bridge.py start >"${LOGS_DIR}/event-bridge.log" 2>&1 &
    EVENT_BRIDGE_PID=$!
    cd - >/dev/null
    
    # Attendre que l'Event Bridge soit prêt
    if wait_for_service "http://localhost:9998/status" "Event Bridge" 20; then
        log_success "✅ Event Bridge démarré (PID: ${EVENT_BRIDGE_PID})"
        return 0
    else
        log_warning "⚠️ Event Bridge démarré mais non prêt (PID: ${EVENT_BRIDGE_PID})"
        return 0  # Continuer même si non prêt
    fi
}

# Démarrer le Dashboard Frontend
start_frontend() {
    log "🚀 Démarrage du Dashboard Frontend (port 3001)..."
    
    local frontend_dir="${ELF_DIR}/dashboard-app/frontend"
    
    # Vérifier que le répertoire existe
    if [[ ! -d "${frontend_dir}" ]]; then
        log_error "❌ Répertoire frontend introuvable: ${frontend_dir}"
        return 1
    fi
    
    # Vérifier que npm/node est installé
    if ! command -v npm >/dev/null 2>&1; then
        log_error "❌ Node.js/npm n'est pas installé"
        return 1
    fi
    
    # Installer les dépendances si nécessaire
    if [[ ! -d "${frontend_dir}/node_modules" ]]; then
        log "📥 Installation des dépendances frontend..."
        cd "${frontend_dir}"
        npm install >/dev/null 2>&1
        cd - >/dev/null
    fi
    
    # Démarrer le frontend en arrière-plan
    cd "${frontend_dir}"
    npm run dev >"${LOGS_DIR}/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd - >/dev/null
    
    # Attendre que le frontend soit prêt
    if wait_for_service "http://localhost:3001" "Dashboard Frontend" 60; then
        log_success "✅ Dashboard Frontend démarré (PID: ${FRONTEND_PID})"
        return 0
    else
        log_warning "⚠️ Dashboard Frontend démarré mais non prêt (PID: ${FRONTEND_PID})"
        return 0  # Continuer même si non prêt
    fi
}

# Afficher le statut des services
show_status() {
    log "📊 Statut des services:"
    
    echo "----------------------------------------"
    if is_running "${OPENCODE_PID}"; then
        echo "✅ OpenCode Server (PID: ${OPENCODE_PID})"
    else
        echo "❌ OpenCode Server"
    fi
    
    if is_running "${BACKEND_PID}"; then
        echo "✅ Dashboard Backend (PID: ${BACKEND_PID})"
    else
        echo "❌ Dashboard Backend"
    fi
    
    if is_running "${EVENT_BRIDGE_PID}"; then
        echo "✅ Event Bridge (PID: ${EVENT_BRIDGE_PID})"
    else
        echo "❌ Event Bridge"
    fi
    
    if is_running "${FRONTEND_PID}"; then
        echo "✅ Dashboard Frontend (PID: ${FRONTEND_PID})"
    else
        echo "❌ Dashboard Frontend"
    fi
    echo "----------------------------------------"
}

# Afficher les URLs
show_urls() {
    log "🌐 URLs des services:"
    echo "----------------------------------------"
    echo "🏠 Dashboard:     http://localhost:3001"
    echo "📡 Backend API:   http://localhost:8888"
    echo "🔌 Event Bridge:  http://localhost:9998/status"
    echo "🖥️ OpenCode:      http://localhost:4096"
    echo "----------------------------------------"
}

# Mode test rapide
test_mode() {
    log "🧪 Mode test rapide"
    
    # Ne démarrer que les services essentiels
    start_opencode_server || return 1
    start_backend || return 1
    start_event_bridge || return 1
    
    show_status
    show_urls
    
    log_success "✅ Mode test terminé"
    return 0
}

# Mode minimal
minimal_mode() {
    log "🔽 Mode minimal"
    
    # Ne démarrer que les services essentiels
    start_opencode_server || return 1
    start_backend || return 1
    
    show_status
    show_urls
    
    log_success "✅ Mode minimal terminé"
    return 0
}

# Mode complet
all_mode() {
    log "🚀 Mode complet"
    
    # Démarrer tous les services
    start_opencode_server || return 1
    start_backend || return 1
    start_event_bridge || return 1
    start_frontend || return 1
    
    show_status
    show_urls
    
    log_success "✅ Tous les services démarrés!"
    return 0
}

# Fonction principale
main() {
    local mode="all"
    
    # Parser les arguments
    if [[ $# -gt 0 ]]; then
        mode="$1"
    fi
    
    # Créer le répertoire de logs si nécessaire
    mkdir -p "${LOGS_DIR}"
    
    log "🎯 Démarrage du système ELF OpenCode (mode: ${mode})"
    
    # Exécuter selon le mode
    case "${mode}" in
        "test")
            test_mode
            ;;
        "minimal")
            minimal_mode
            ;;
        "all"|*)
            all_mode
            ;;
    esac
    
    local result=$?
    
    if [[ $result -eq 0 ]]; then
        log_success "🎉 Démarrage terminé avec succès!"
        log "💡 Pour arrêter: Ctrl+C ou kill $$"
        log "📝 Logs dans: ${LOGS_DIR}"
        
        # Boucle infinie pour garder le script en vie
        while true; do
            sleep 60
        done
    else
        log_error "💥 Échec du démarrage"
        exit 1
    fi
}

# Exécuter la fonction principale
main "$@"