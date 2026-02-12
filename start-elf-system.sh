#!/usr/bin/env bash

# ELF OpenCode - Script de démarrage complet
#
# Démarrage de tous les services nécessaires pour ELF OpenCode:
# 1. OpenCode Server (port 4096) - Optionnel si déjà démarré manuellement
# 2. Dashboard Backend (port 8888) - CEO, Missions, System Services routers
# 3. Event Bridge (port 9998) - SSE event streaming
# 4. Unified Orchestrator (port 9998) - Central decision-making
# 5. Semantic Search Daemon (port 5001) - MANDATORY - Semantic search
# 6. Sentinel v3.0 (Level 1 Agent - Monitoring + Pattern Detection)
# 7. Dashboard Frontend (port 3001)
# 8. Learning Capture Service - Auto-extraction des heuristiques
# 9. CEO Inbox Monitor - Autonomous escalation processing
#
# Usage:
#     ./start-elf-system.sh [mode]
#     
# Modes:
#     all       - Démarre tout (défaut)
#     minimal   - Démarre seulement OpenCode + Backend
#     test      - Mode test rapide
#     no-opencode - Démarre tout sauf OpenCode (si vous le gérez manuellement)
#
# REFACTORED v0.5.5 (2026-02-11):
# - Added Semantic Search Daemon (port 5001) - MANDATORY
# - Implemented 3-mechanism auto-learning system (explicit, error-context, anti-pattern)
# - Semantic daemon now uses unified ELF logging system
# - Fixed FTS5 table corruption handling after crashes
# - EventBridge port corrected (was 9999, actually 9998)
#
# REFACTORED v0.5.4 (2026-02-09):
# - Sentinel merged into Sentinel v3.0 (removed start_sentinel function)
# - Added CEO, Missions, System services routers to backend
# - Fixed orchestrator port 9998 (was 9999)
# - AI analysis corrected (Sentinel 5min vs old Sentinel 5min)

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

# Fonction d'aide
show_help() {
    echo -e "${CYAN}≡≡≡ ELF OpenCode System - Startup Script (v0.5.5) ≡≡≡${NC}"
    echo ""
    echo -e "${GREEN}USAGE:${NC}"
    echo "  $0 [MODE]"
    echo ""
    echo -e "${GREEN}MODES:${NC}"
    echo "  test      Quick test mode (OpenCode, Dashboard, Orchestrator, Sentinel only)"
    echo "  minimal   Minimal services (Backend + Frontend only, for development)"
    echo "  no-opencode All services except OpenCode (for production use)"
    echo "  all       Full system startup (default)"
    echo "  --help    Show this help message"
    echo ""
    echo -e "${GREEN}SERVICES (Full Mode):${NC}"
    echo "  • OpenCode Server (port 4096)"
    echo "  • Dashboard Backend (port 8888) - with CEO, Missions, System Services routers"
    echo "  • EventBridge (port 9998)"
    echo "  • Unified Orchestrator (port 9998)"
    echo "  • Sentinel v3.0 (Level 1 Agent - Monitoring + Pattern Detection + AI Analysis)"
    echo "  • Semantic Search Daemon (port 5001) - MANDATORY"
    echo "  • Dashboard Frontend (port 3001)"
    echo "  • Learning Capture Service"
    echo "  • CEO Inbox Monitor"
    echo ""
    echo -e "${GREEN}NEW IN v0.5.5:${NC}"
    echo "  • Semantic Search Daemon integrated (unified logging)"
    echo "  • 3-mechanism auto-learning system implemented"
    echo "  • FTS5 corruption handling improved"
    echo ""
    echo -e "${GREEN}NEW IN v0.5.4:${NC}"
    echo "  • CEO Monitoring (/api/v1/ceo/* - 8 endpoints)"
    echo "  • Mission Engine Monitoring (/api/v1/missions/* - 7 endpoints)"
    echo "  • System Services Health Checks (/api/v1/system/* - 4 endpoints)"
    echo "  • Coordinator Monitoring (/api/v1/monitoring/coordinator/* - 6 endpoints)"
    echo "  • AI Analysis Schedule (/api/v1/monitoring/ai-analysis/* - 2 endpoints)"
    echo "  • Pheromone Trails (/api/v1/monitoring/trails/* - 2 endpoints)"
    echo "  • Orchestrator port corrected: 9999 → 9998"
    echo "  • Sentinel merged into Sentinel v3.0 (no longer separate service)"
    echo ""
    echo -e "${YELLOW}NOTES:${NC}"
    echo "  • Sentinel has been merged into Sentinel v3.0 - no longer a separate service"
    echo "  • Orchestrator is now Unified Orchestrator on port 9998"
    echo "  • Press Ctrl+C to stop all services cleanly"
    echo ""
    echo -e "${GREEN}EXAMPLES:${NC}"
    echo "  $0              # Start full system"
    echo "  $0 test         # Quick test mode"
    echo "  $0 no-opencode  # Production mode (skip OpenCode)"
    echo ""
}

# Variables globales
OPENCODE_PID=""
BACKEND_PID=""
EVENT_BRIDGE_PID=""
FRONTEND_PID=""
SENTINEL_PID=""
ORCHESTRATOR_PID=""
LEARNING_CAPTURE_PID=""
CEO_MONITOR_PID=""
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
    if [[ -n "${SENTINEL_PID:-}" ]]; then
        kill "${SENTINEL_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${SENTINEL_PID}"  2>/dev/null || true
    fi
    if [[ -n "${ORCHESTRATOR_PID:-}" ]]; then
        kill "${ORCHESTRATOR_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${ORCHESTRATOR_PID}"  2>/dev/null || true
    fi
    if [[ -n "${LEARNING_CAPTURE_PID:-}" ]]; then
        kill "${LEARNING_CAPTURE_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${LEARNING_CAPTURE_PID}" 2>/dev/null || true
    fi
    if [[ -n "${CEO_MONITOR_PID:-}" ]]; then
        kill "${CEO_MONITOR_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${CEO_MONITOR_PID}" 2>/dev/null || true
    fi
    if [[ -n "${SEMANTIC_DAEMON_PID:-}" ]]; then
        kill "${SEMANTIC_DAEMON_PID}" 2>/dev/null || true
        sleep 1
        kill -9 "${SEMANTIC_DAEMON_PID}" 2>/dev/null || true
    fi

    # Kill tous les processus liés à Open_ELF et dashboard
    pkill -f "opencode serve" 2>/dev/null || true
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "event_bridge.py" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "semantic.daemon" 2>/dev/null || true

    pkill -f "background-learning-capture.py" 2>/dev/null || true
    pkill -f "Open_ELF/agents/ceo_inbox_monitor.py" 2>/dev/null || true
    pkill -f "Open_ELF/orchestrator/unified_orchestrator.py" 2>/dev/null || true
    # NOTE: Removed pkill for sentinel_monitor.py - Sentinel merged into Sentinel v3.0
    
    log_success "✅ Nettoyage terminé"
    log "👋 Au revoir!"
    exit 0
}

# Check for help flag early (before trap is set)
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

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
all_services_running() {
    # Vérifier seulement les services que nous avons démarrés
    if is_running "${BACKEND_PID}" && \
       is_running "${EVENT_BRIDGE_PID}" && \
       is_running "${FRONTEND_PID}" && \
       is_running "${SENTINEL_PID}" && \
       is_running "${ORCHESTRATOR_PID}"; then
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
        log_warning "⚠️ Le script va continuer sans OpenCode Server"
        OPENCODE_EXTERNAL=true
        return 0  # Ne pas bloquer le démarrage
    fi
}

# Démarrer le Dashboard Backend (port 8888)
#    NOTE: Now includes new routers: CEO, Missions, System Services monitoring
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
        log_info "   (Nouveaux routers: CEO, Missions, System Services monitoring activés)"
        return 0
    else
        log_error "❌ Impossible de démarrer le Dashboard Backend"
        return 1
    fi
}

# Démarrer l'Event Bridge v2 (refactored)
start_event_bridge() {
    log "🌉 Démarrage de l'Event Bridge v2.0 (port 9998)..."
    
    # Nettoyer les anciens processus et lockfiles
    pkill -f "event_bridge" 2>/dev/null || true
    rm -f "${LOGS_DIR}/.event_bridge.lock" 2>/dev/null || true
    sleep 1
    
    local event_bridge_script="${SCRIPT_DIR}/core/event_bridge_v2.py"
    
    # Vérifier que le script existe (nouveau emplacement)
    if [[ ! -f "${event_bridge_script}" ]]; then
        log_warning "⚠️ Script Event Bridge v2 introuvable: ${event_bridge_script}"
        # Essayer l'ancien emplacement
        if [[ -f "${ELF_DIR}/orchestrator/event_bridge.py" ]]; then
            event_bridge_script="${ELF_DIR}/orchestrator/event_bridge.py"
        else
            log_error "❌ Event Bridge script not found at either location"
            return 1
        fi
    fi
    
    # Démarrer le Event Bridge
    cd "$(dirname "${event_bridge_script}")"
    python3 "$(basename "${event_bridge_script}")" start >"${LOGS_DIR}/event_bridge.log" 2>&1 &
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

# Démarrer le Sentinel v3.0 (refactored - merged Sentinel + Sentinel)
start_sentinel() {
    log "👁️ Démarrage du Sentinel  (Level 1 Agent )..."
    
    local sentinel_script="${SCRIPT_DIR}/core/sentinel.py"
    
    # Vérifier que le script existe (nouveau emplacement)
    if [[ ! -f "${sentinel_script}" ]]; then
        log_warning "⚠️ Script sentinel v3.0 introuvable: ${sentinel_script}"
        log_error "⚠️ Sentinel v3.0 script not found, continuing without it"
        return 0
    fi
    
    # Tuer tout processus sentinel existant avant de lancer (force restart)
    log "🔄 Arrêt des anciennes instances du sentinel..."
    pkill -f "core/sentinel.py" 2>/dev/null || true
    pkill -f "Open_ELF/sentinel/elf_sentinel.py" 2>/dev/null || true
    pkill -f "Open_ELF/agents/sentinel_monitor.py" 2>/dev/null || true
    sleep 1  # Attendre que les processus se terminent
    
    # Démarrer le sentinel en arrière-plan
    cd "${SCRIPT_DIR}"
    python3 "${sentinel_script}" >"${LOGS_DIR}/sentinel.log" 2>&1 &
    SENTINEL_PID=$!
    cd - >/dev/null
    
    # Attendre quelques secondes pour laisser le sentinel démarrer
    sleep 2
    
    # Vérifier qu'il tourne
    if is_running "${SENTINEL_PID}"; then
        log_success "✅ Sentinel v3.0 démarré (PID: ${SENTINEL_PID})"
        log_info "   Level 1 Agent: Monitoring + Pattern Detection + AI Analysis"
        log_info "   (includes Sentinel capabilities merged)"
        return 0
    else
        log_warning "⚠️ Sentinel v3.0 démarré mais non prêt (PID: ${SENTINEL_PID})"
        return 0  # Continuer même si non prêt
    fi
}

# Démarrer le Learning Capture Service
start_learning_capture() {
    log "🧠 Démarrage du Learning Capture Service..."
    
    local capture_script="${SCRIPT_DIR}/scripts/background-learning-capture.py"
    
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
        log_info   "   Capture automatique des heuristiques activée"
        return 0
    else
        log_warning "⚠️ Learning Capture Service non démarré"
        return 0
    fi
}

# Démarrer le CEO Inbox Monitor
start_ceo_monitor() {
    log "👔 Démarrage du CEO Inbox Monitor..."
    
    local ceo_monitor_script="${ELF_DIR}/agents/ceo_inbox_monitor.py"
    
    # Vérifier que le script existe
    if [[ ! -f "${ceo_monitor_script}" ]]; then
        log_warning "⚠️ Script CEO Inbox Monitor introuvable: ${ceo_monitor_script}"
        return 0  # Continuer sans le monitor
    fi
    
    # Tuer tout processus existant avant de lancer
    log "🔄 Arrêt des anciennes instances du CEO monitor..."
    pkill -f "Open_ELF/agents/ini_ceo_monitor.py" 2>/dev/null || true
    sleep 1
    
    # Démarrer le monitor en arrière-plan
    cd "${SCRIPT_DIR}"
    python3 "${ceo_monitor_script}" start >"${LOGS_DIR}/ceo-monitor.log" 2>&1 &
    CEO_MONITOR_PID=$!
    cd - >/dev/null
    
    # Attendre quelques secondes pour laisser démarrer
    sleep 3
    
    # Vérifier qu'il tourne
    if is_running "${CEO_MONITOR_PID}"; then
        log_success "✅ CEO Inbox Monitor démarré (PID: ${CEO_MONITOR_PID})"
        log_info   "Traitement autonome des escalations"
        return 0
    else
        log_warning "⚠️ CEO Inbox Monitor non démarré"
        return 0  # Continuer même si non prêt
    fi
}

# Démarrer l'Unified Orchestrator
start_orchestrator() {
    log "🧠 Démarrage de l'Unified Orchestrator..."
    
    local orchestrator_script="${ELF_DIR}/orchestrator/unified_orchestrator.py"
    
    # Vérifier que le script existe
    if [[ ! -f "${orchestrator_script}" ]]; then
        log_warning "⚠️ Script Orchestrator introuvable: ${orchestrator_script}"
        return 0  # Continuer sans l'orchestrator
    fi
    
    # Tuer tout processus existant avant de lancer
    log "🔄 Arrêt des anciennes instances de l'orchestrator..."
    pkill -f "unified_orchestrator.py" 2>/dev/null || true
    sleep 1
    
    # Démarrer l'orchestrator en arrière-plan
    cd "${ELF_DIR}/orchestrator"
    python3 "$(basename "${orchestrator_script}")" start >"${LOGS_DIR}/orchestrator.log" 2>&1 &
    ORCHESTRATOR_PID=$!
    cd - >/dev/null
    
    # Attendre quelques secondes pour laisser démarrer
    sleep 3
    
    # Vérifier qu'il tourne
    if is_running "${ORCHESTRATOR_PID}"; then
        log_success "✅ Unified Orchestrator démarré (PID: ${ORCHESTRATOR_PID})"
        log_info   "Decision-making centralisé"
        return 0
    else
        log_warning "⚠️ Unified Orchestrator non démarré"
        return 0  # Continuer même si non prêt
    fi
}

# Démarrer la Dashboard Frontend
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
        log_success "✅ Dashboard  démarré (PID: ${FRONTEND_PID})"
        return 0
    else
        log_warning "⚠️ Dashboard  démarré mais non prêt (PID: ${FRONTEND_PID})"
        return 0  # Continuer même si non prêt
    fi
}

# Start Semantic Search Daemon
start_semantic_daemon() {
    log "🔍 Démarrage du Semantic Search Daemon (port 5001)..."

    # Kill any existing semantic daemon
    pkill -f "semantic/daemon.py" 2>/dev/null || true
    pkill -f "semantic.daemon" 2>/dev/null || true
    sleep 1

    # Start semantic daemon from the correct location
    cd "${SCRIPT_DIR}/semantic"
    python3 daemon.py > "${LOGS_DIR}/semantic-daemon.log" 2>&1 &
    SEMANTIC_DAEMON_PID=$!
    cd - >/dev/null

    # Wait for it to start
    sleep 3

    # Check if it's running
    if is_running "${SEMANTIC_DAEMON_PID}"; then
        log_success "✅ Semantic Search Daemon démarré (PID: ${SEMANTIC_DAEMON_PID})"
        log_info   "   Port: 5001 - Semantic search activée"
        return 0
    else
        log_warning "⚠️ Semantic Search Daemon non démarré"
        # Try to read the error
        if [[ -f "${LOGS_DIR}/semantic-daemon.log" ]]; then
            log_error "$(head -20 "${LOGS_DIR}/semantic-daemon.log")"
        fi
        return 0  # Continue even if not started (non-blocking)
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
    
    # Event Bridge - check PID ou fallback pgrep
    if is_running "${EVENT_BRIDGE_PID}"; then
        echo "✅ Event Bridge (PID: ${EVENT_BRIDGE_PID})"
    elif pgrep -f "event_bridge_v2.py" >/dev/null 2>&1; then
        EVENT_BRIDGE_PID=$(pgrep -f "event_bridge_v2.py" | head -1)
        echo "✅ Event Bridge (PID: ${EVENT_BRIDGE_PID}) [détecté]"
    else
        echo "❌ Event Bridge"
    fi
    
    if is_running "${FRONTEND_PID}"; then
        echo "✅ Dashboard Frontend (PID: ${FRONTEND_PID})"
    else
        echo "❌ Dashboard Frontend"
    fi
    
    if is_running "${SENTINEL_PID}"; then
        echo "✅ Sentinel v3.0 (PID: ${SENTINEL_PID})"
        echo "   Level 1: Monitoring + Pattern Detection + AI Analysis"
        echo "   includes Sentinel capabilities (merged)"
    else
        echo "❌ Sentinel"
    fi
    
    # Unified Orchestrator - check PID ou fallback pgrep
    if pgrep -f "unified_orchestrator.py" >/dev/null 2>&1; then
        ORCHESTRATOR_PID=$(pgrep -f "unified_orchestrator.py" | head -1)
        echo "🧠 Unified Orchestrator (PID: ${ORCHESTRATOR_PID}) [détecté]"
    else
        echo "⚪ Unified Orchestrator (non actif)"
    fi
    
    if is_running "${LEARNING_CAPTURE_PID}"; then
        echo "✅ Learning Capture (PID: ${LEARNING_CAPTURE_PID})"
        echo "   Capture automatique des heuristiques activée"
    else
        echo "⚪ Learning Capture (non actif)"
    fi
    
    if is_running "${CEO_MONITOR_PID}"; then
        echo "✅ CEO Monitor (PID: ${CEO_MONITOR_PID})"
        echo "   Traitement autonome des escalations"
    else
        echo "⚪ CEO Monitor (non actif)"
    fi

    if is_running "${SEMANTIC_DAEMON_PID}"; then
        echo "✅ Semantic Daemon (PID: ${SEMANTIC_DAEMON_PID})"
        echo "   Port: 5001 - Semantic search activée"
    else
        echo "⚪ Semantic Daemon (non actif)"
    fi

    echo ""
    log "💡 Nouveaux endpoints de monitoring disponibles:"
    echo "   /api/v1/ceo/* - CEO inbox metrics, monitor status"
    echo "   /api/v1/missions/* - Mission Engine monitoring"
    echo "   /api/v1/system/* - System services health checks"
    echo "   /api/v1/monitoring/coordinator/* - Agent coordination"
    echo "   /api/v1/monitoring/ai-analysis/* - AI analysis tracking"
    echo "   /api/v1/monitoring/trails/* - Pheromone trails"
    echo "   :5001/health - Semantic daemon health check"
    echo "   :5001/stats - Semantic daemon statistics"
    echo "   :5001/search - Semantic search API"
    echo "----------------------------------------"
}

# Afficher les URLs
show_urls() {
    log "🌐 URLs des services:"
    echo "----------------------------------------"
    echo "🏠 Dashboard:     http://localhost:3001"
    echo "📡 Backend API:   http://localhost:8888"
    echo "🔌 Event Bridge: http://localhost:9998/status"
    echo "🔍 Semantic:      http://localhost:5001/health"
    echo "🖥️ OpenCode:      http://localhost:4096"
    echo "----------------------------------------"
}

# Mode test rapide
test_mode() {
    log "🧪 Mode test rapide"
    
    # Ne démarrer que les services essentiels
    start_opencode_server || return 1
    start_semantic_daemon || return 1  # START FIRST - Required by learning_processor
    start_backend || return 1
    start_event_bridge || return 1
    start_orchestrator || return 1  # Unified Orchestrator
    start_sentinel || return 1               # Sentinel
    start_learning_capture || return 0 # Ne pas bloquer si échec
    start_ceo_monitor || return 0    # CEO Inbox Monitor

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
    start_semantic_daemon || return 0  # Optional in minimal mode but useful
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
    start_orchestrator || return 1    # Unified Orchestrator
    start_sentinel || return 1               # Sentinel v3.0 (merged Sentinel + Sentinel)
    start_semantic_daemon || return 0    # Semantic Search Daemon
    start_frontend || return 1
    start_learning_capture || return 0 # Ne pas bloquer si échec
    start_ceo_monitor || return 0    # CEO Inbox Monitor

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
    start_orchestrator || return 1 # Unified Orchestrator
    start_sentinel || return 1               # Sentinel v3.0 (merged Sentinel + Sentinel)
    start_semantic_daemon || return 0  # Semantic Search Daemon
    start_frontend || return 1
    start_learning_capture || return 0 # Ne pas bloquer si échec
    start_ceo_monitor || return 0    # CEO Inbox Monitor

    show_status
    show_urls

    log_success "✅ Services démarrés (sans gestion d'OpenCode)!"
    return 0
}

# Fonction principale - VERSION CORRECTÉE
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
            
            # Attendre 5 secondes mais interrompe si signal reçu
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