#!/usr/bin/env bash

# ELF OpenCode - Script de démarrage complet
#
# Démarrage de tous les services nécessaires pour ELF OpenCode:
# 1. OpenCode Server (port 4096) - Optionnel si déjà démarré manuellement
# 2. Dashboard Backend (port 8888) 
# 3. Event Bridge (port 9998)
# 4. Dashboard Frontend (port 3001)
# 5. Watcher (continuous monitoring)
# 6. Learning Capture Service (auto-extraction des heuristiques)

# Usage:
#     ./start-elf-system.sh [mode]
#     
# Modes:
#     all       - Démarre tout (défaut)
#     minimal   - Démarre seulement OpenCode + Backend
#     test      - Mode test rapide
#     no-opencode - Démarre tout sauf OpenCode (si vous le gérez manuellement)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="${SCRIPT_DIR}/Open_ELF"
OPENCODE_DIR="${HOME}/.opencode"
LOGS_DIR="${ELF_DIR}/logs"

# Create logs directory
mkdir -p "${LOGS_DIR}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_success() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_info() { echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }

# Variables globales
OPENCODE_PID=""
BACKEND_PID=""
EVENT_BRIDGE_PID=""
FRONTEND_PID=""
WATCHER_PID=""
LEARNING_CAPTURE_PID=""
RUNNING=true
OPENCODE_EXTERNAL=false  # true si OpenCode est déjà démarré manuellement

# Nettoyage à la sortie - Version améliorée avec kill -9 si nécessaire
cleanup() {
    log "🧹 Nettoyage des processus..."
    RUNNING=false
    
    # Tuer les processus enfants avec kill -9 si nécessaire
    if [[ -n "${OPENCODE_PID:-}" ]]; then
        kill "${OPENCODE_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${OPENCODE_PID}" 2>/dev/null || true
    fi
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill "${BACKEND_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${BACKEND_PID}" 2>/dev/null || true
    fi
    if [[ -n "${EVENT_BRIDGE_PID:-}" ]]; then
        kill "${EVENT_BRIDGE_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${EVENT_BRIDGE_PID}" 2>/dev/null || true
    fi
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${FRONTEND_PID}" 2>/dev/null || true
    fi
    if [[ -n "${WATCHER_PID:-}" ]]; then
        kill "${WATCHER_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${WATCHER_PID}" 2>/dev/null || true
    fi
    if [[ -n "${LEARNING_CAPTURE_PID:-}" ]]; then
        kill "${LEARNING_CAPTURE_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${LEARNING_CAPTURE_PID}" 2>/dev/null || true
    fi
    
    # Kill tous les processus liés à Open_ELF et dashboard
    pkill -f "opencode serve" 2>/dev/null || true
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "event_bridge.py" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "Open_ELF/watcher/launcher.py" 2>/dev/null || true
    pkill -f "background-learning-capture.py" 2>/dev/null || true
    
    log_success "✅ Nettoyage terminé"
    log "👋 Au revoir!"
    exit 0
}

# Trap tous les signaux d'arrêt
trap cleanup EXIT INT TERM HUP

# Vérifier si un service est en cours d'exécution
is_running() {
    local pid=$1
    if [[ -n "${pid:-}" ]] && kill -0 "${pid}" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Vérifier si tous les services tournent encore
# Note: OpenCode n'est pas vérifié si son PID est vide (démarré manuellement par l'utilisateur)
all_services_running() {
    # Vérifier seulement les services que nous avons démarrés
    if is_running "${BACKEND_PID}" && \
       is_running "${EVENT_BRIDGE_PID}" && \
       is_running "${FRONTEND_PID}" && \
       is_running "${WATCHER_PID}"; then
        return 0
    fi
    return 1
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
# Retourne 0 si démarré avec succès OU si déjà démarré manuellement
start_opencode_server() {
    log "🚀 Démarrage d'OpenCode Server (port 4096)..."
    
    # Vérifier si OpenCode tourne déjà (démarré manuellement par l'utilisateur)
    if pgrep -f "opencode serve" >/dev/null 2>&1; then
        log_info "ℹ️ OpenCode Server est déjà en cours d'exécution (démarré manuellement)"
        log_info "   Le script ne gérera pas ce processus"
        OPENCODE_EXTERNAL=true
        return 0  # Considéré comme succès
    fi
    
    # Vérifier si OpenCode est installé
    if ! command -v opencode >/dev/null 2>&1; then
        log_error "❌ OpenCode n'est pas installé. Installez-le avec:"
        log_error "curl -fsSL https://get.opencde.ai | sh"
        log_warning "⚠️ Continuation sans OpenCode Server"
        OPENCODE_EXTERNAL=true
        return 0  # Ne pas bloquer le démarrage
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
        log_warning "⚠️ Le script va continuer sans OpenCode"
        OPENCODE_EXTERNAL=true
        return 0  # Ne pas bloquer le démarrage
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
    
    local orchestrator_dir="${ELF_DIR}/orchestrator"
    
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

# Démarrer le Watcher
start_watcher() {
    log "👁️ Démarrage du Watcher..."
    
    local watcher_script="${ELF_DIR}/Open_ELF/watcher/launcher.py"
    
    # Vérifier que le script existe
    if [[ ! -f "${watcher_script}" ]]; then
        log_warning "⚠️ Script watcher introuvable: ${watcher_script}"
        return 0  # Continuer sans le watcher
    fi
    
    # Tuer tout processus watcher existant avant de lancer (force restart)
    log "🔄 Arrêt des anciennes instances du watcher..."
    pkill -f "Open_ELF/watcher/launcher.py" 2>/dev/null || true
    sleep 1  # Attendre que les processus se terminent
    
    # Démarrer le watcher en arrière-plan
    cd "${ELF_DIR}"
    python3 "${watcher_script}" >"${LOGS_DIR}/watcher.log" 2>&1 &
    WATCHER_PID=$!
    cd - >/dev/null
    
    # Attendre quelques secondes pour laisser le watcher démarrer
    sleep 2
    
    # Vérifier qu'il tourne
    if is_running "${WATCHER_PID}"; then
        log_success "✅ Watcher démarré (PID: ${WATCHER_PID})"
        return 0
    else
        log_warning "⚠️ Watcher démarré mais non prêt (PID: ${WATCHER_PID})"
        return 0  # Continuer même si non prêt
    fi
}

# Démarrer le Learning Capture Service
start_learning_capture() {
    log "🧠 Démarrage du Learning Capture Service..."
    
    local capture_script="${ELF_DIR}/scripts/background-learning-capture.py"
    
    # Vérifier que le script existe
    if [[ ! -f "${capture_script}" ]]; then
        log_warning "⚠️ Script learning capture introuvable: ${capture_script}"
        return 0  # Continuer sans le service
    fi
    
    # Tuer tout processus existant avant de lancer
    pkill -f "background-learning-capture.py" 2>/dev/null || true
    sleep 1
    
    # Démarrer le service en arrière-plan
    cd "${ELF_DIR}"
    nohup python3 "${capture_script}" >"${LOGS_DIR}/learning-capture.log" 2>&1 &
    LEARNING_CAPTURE_PID=$!
    cd - >/dev/null
    
    # Attendre quelques secondes
    sleep 2
    
    # Vérifier qu'il tourne
    if is_running "${LEARNING_CAPTURE_PID}"; then
        log_success "✅ Learning Capture Service démarré (PID: ${LEARNING_CAPTURE_PID})"
        log_info "   📊 Capture automatique des heuristiques activée"
        return 0
    else
        log_warning "⚠️ Learning Capture Service non démarré"
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
    # Si OpenCode PID est défini, on l'a démarré nous-mêmes
    if [[ -n "${OPENCODE_PID:-}" ]]; then
        if is_running "${OPENCODE_PID}"; then
            echo "✅ OpenCode Server (PID: ${OPENCODE_PID})"
        else
            echo "❌ OpenCode Server (arrêté)"
        fi
    elif [[ "${OPENCODE_EXTERNAL}" == true ]]; then
        # OpenCode géré manuellement par l'utilisateur
        if pgrep -f "opencode serve" >/dev/null 2>&1; then
            echo "🔌 OpenCode Server (externe - géré manuellement)"
        else
            echo "⚪ OpenCode Server (non démarré)"
        fi
    else
        echo "⚪ OpenCode Server (non démarré)"
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
    
    if is_running "${WATCHER_PID}"; then
        echo "✅ Watcher (PID: ${WATCHER_PID})"
    else
        echo "❌ Watcher"
    fi
    
    if is_running "${LEARNING_CAPTURE_PID}"; then
        echo "✅ Learning Capture (PID: ${LEARNING_CAPTURE_PID})"
    else
        echo "⚪ Learning Capture (non actif)"
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
    start_watcher || return 1
    start_learning_capture || return 0  # Ne pas bloquer si échec
    
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
    start_watcher || return 1
    start_frontend || return 1
    start_learning_capture || return 0  # Ne pas bloquer si échec
    
    show_status
    show_urls
    
    log_success "✅ Tous les services démarrés!"
    return 0
}

# Mode sans OpenCode (si vous le gérez manuellement)
no_opencode_mode() {
    log "🔧 Mode sans OpenCode (gestion manuelle)"
    OPENCODE_EXTERNAL=true
    
    # Vérifier quand même si OpenCode tourne
    if pgrep -f "opencode serve" >/dev/null 2>&1; then
        log_info "ℹ️ OpenCode Server détecté (démarré manuellement)"
    else
        log_warning "⚠️ OpenCode Server n'est pas démarré"
        log_info "   Démarrez-le manuellement avec: opencode serve --port 4096"
    fi
    
    # Démarrer les autres services
    start_backend || return 1
    start_event_bridge || return 1
    start_watcher || return 1
    start_frontend || return 1
    start_learning_capture || return 0  # Ne pas bloquer si échec
    
    show_status
    show_urls
    
    log_success "✅ Services démarrés (sans gestion d'OpenCode)!"
    return 0
}

# Fonction principale - VERSION CORRIGÉE
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
        "no-opencode")
            no_opencode_mode
            ;;
        "all"|*)
            all_mode
            ;;
    esac
    
    local result=$?
    
    if [[ $result -eq 0 ]]; then
        log_success "🎉 Démarrage terminé avec succès!"
        log "💡 Pour arrêter: Ctrl+C"
        log "📝 Logs dans: ${LOGS_DIR}"
        
        if [[ "${OPENCODE_EXTERNAL}" == true ]]; then
            log_info "ℹ️ OpenCode n'est pas géré par ce script"
            log_info "   Il ne sera pas arrêté lors de l'arrêt du script"
        fi
        
        # Boucle principale corrigée - vérifie les processus et répond à Ctrl+C
        log "🔄 Surveillance des services (Ctrl+C pour arrêter)..."
        
        # Vérifier les processus toutes les 5 secondes mais répondre aux signaux
        while [[ $RUNNING == true ]]; do
            # Vérifier si les processus sont encore en vie
            if ! all_services_running; then
                log_warning "⚠️ Un ou plusieurs services se sont arrêtés"
                show_status
            fi
            
            # Attendre 5 secondes mais interrompre si signal reçu
            if ! timeout 5 sleep 5; then
                # Si timeout interrompu, c'est probablement un signal
                if [[ $RUNNING == false ]]; then
                    break
                fi
            fi
        done
        
        # Sortie normale
        cleanup
    else
        log_error "💥 Échec du démarrage"
        exit 1
    fi
}

# Exécuter la fonction principale
main "$@"
