#!/usr/bin/env bash
# ELF OpenCode - Script de Check-in Complet
#
# Effectue un check-in complet du système ELF OpenCode:
# 1. Vérifie l'état de tous les services
# 2. Teste la connectivité
# 3. Vérifie les hooks et le learning system
# 4. Affiche un rapport de santé
#
# Usage:
#     ./checkin-elf.sh

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
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_success() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_info() { echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }

# Vérifier la connectivité à un service
check_service() {
    local url=$1
    local name=$2
    local timeout=${3:-5}
    
    if curl -s --max-time "${timeout}" "${url}" >/dev/null 2>&1; then
        log_success "✅ ${name} est accessible"
        return 0
    else
        log_error "❌ ${name} est inaccessible (${url})"
        return 1
    fi
}

# Vérifier les processus en cours
check_processes() {
    log "🔍 Vérification des processus..."
    
    local found_services=0
    
    # OpenCode Server
    if pgrep -f "opencode.*serve.*4096" >/dev/null 2>&1; then
        log_success "✅ OpenCode Server en cours d'exécution"
        ((found_services++))
    else
        log_warning "⚠️ OpenCode Server non trouvé"
    fi
    
    # Dashboard Backend
    if pgrep -f "uvicorn.*8888" >/dev/null 2>&1; then
        log_success "✅ Dashboard Backend en cours d'exécution"
        ((found_services++))
    else
        log_warning "⚠️ Dashboard Backend non trouvé"
    fi
    
    # Event Bridge
    if pgrep -f "event_bridge.py" >/dev/null 2>&1; then
        log_success "✅ Event Bridge en cours d'exécution"
        ((found_services++))
    else
        log_warning "⚠️ Event Bridge non trouvé"
    fi
    
    # Dashboard Frontend
    if pgrep -f "npm.*dev" >/dev/null 2>&1; then
        log_success "✅ Dashboard Frontend en cours d'exécution"
        ((found_services++))
    else
        log_warning "⚠️ Dashboard Frontend non trouvé"
    fi
    
    log_info "📈 ${found_services}/4 services trouvés"
    return 0
}

# Tester les APIs
test_apis() {
    log "🧪 Test des APIs..."
    
    local api_tests=0
    local api_success=0
    
    # Test OpenCode Health
    ((api_tests++))
    if curl -s "http://localhost:4096/global/health" | grep -q "healthy"; then
        log_success "✅ OpenCode API (health)"
        ((api_success++))
    else
        log_error "❌ OpenCode API (health)"
    fi
    
    # Test Backend Agents Status
    ((api_tests++))
    if curl -s "http://localhost:8888/api/v1/agents/status" | grep -q "timestamp"; then
        log_success "✅ Backend API (agents status)"
        ((api_success++))
    else
        log_error "❌ Backend API (agents status)"
    fi
    
    # Test Event Bridge Status
    ((api_tests++))
    if curl -s "http://localhost:9998/status" | grep -q "running"; then
        log_success "✅ Event Bridge API"
        ((api_success++))
    else
        log_error "❌ Event Bridge API"
    fi
    
    # Test Backend Models
    ((api_tests++))
    if curl -s "http://localhost:8888/api/v1/agents/models" | grep -q "models"; then
        log_success "✅ Backend API (models)"
        ((api_success++))
    else
        log_error "❌ Backend API (models)"
    fi
    
    log_info "📈 ${api_success}/${api_tests} APIs fonctionnelles"
    return 0
}

# Vérifier les agents
check_agents() {
    log "🤖 Vérification des agents..."
    
    local agents_response
    agents_response=$(curl -s "http://localhost:8888/api/v1/agents/list" 2>/dev/null || echo "{}")
    
    if echo "${agents_response}" | grep -q "agents"; then
        local agent_count
        agent_count=$(echo "${agents_response}" | grep -o '"id"' | wc -l)
        log_success "✅ ${agent_count} agents disponibles"
        
        # Afficher quelques agents
        echo "${agents_response}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    agents = data.get('agents', [])[:5]
    print('  Agents disponibles:')
    for agent in agents:
        print(f'    • {agent.get(\"name\", \"unknown\")} - {agent.get(\"description\", \"\")[:60]}...')
    if len(data.get('agents', [])) > 5:
        print(f'    ... et {len(data.get(\"agents\", [])) - 5} autres')
except:
    pass
" 2>/dev/null || true
        
        return 0
    else
        log_error "❌ Impossible de récupérer la liste des agents"
        return 1
    fi
}

# Vérifier les hooks
check_hooks() {
    log "🎣 Vérification des hooks..."
    
    local hooks_dir="${OPENCODE_DIR}/hooks"
    if [[ ! -d "${hooks_dir}" ]]; then
        log_error "❌ Répertoire des hooks introuvable: ${hooks_dir}"
        return 1
    fi
    
    local hook_types=("PostToolUse" "PreToolUse" "learning-loop" "dashboard" "talkinhead")
    local total_hooks=0
    
    for hook_type in "${hook_types[@]}"; do
        local type_dir="${hooks_dir}/${hook_type}"
        if [[ -d "${type_dir}" ]]; then
            local hook_count
            hook_count=$(find "${type_dir}" -name "*.py" -type f 2>/dev/null | wc -l)
            if [[ $hook_count -gt 0 ]]; then
                log_success "✅ ${hook_type}: ${hook_count} hooks"
                ((total_hooks += hook_count))
            else
                log_info "ℹ️ ${hook_type}: 0 hooks"
            fi
        else
            log_warning "⚠️ ${hook_type}: répertoire introuvable"
        fi
    done
    
    log_info "🎣 ${total_hooks} hooks au total"
    return 0
}

# Tester un hook manuellement
test_hook() {
    log "🔧 Test d'un hook PostToolUse..."
    
    # Créer des données de test
    local test_data='{"tool_name": "Read", "tool_input": {"path": "/tmp/test.txt"}, "tool_output": {"content": "test"}, "success": true, "session_id": "test123", "timestamp": "'$(date -Iseconds)'"}'
    
    # Exporter les variables d'environnement
    export ELF_BASE_PATH="${ELF_DIR}"
    export PYTHONPATH="${ELF_DIR}"
    
    # Tester le hook principal
    local hook_file="${OPENCODE_DIR}/hooks/PostToolUse/post_tool_learning.py"
    if [[ -f "${hook_file}" ]]; then
        if echo "${test_data}" | python3 "${hook_file}" >/dev/null 2>&1; then
            log_success "✅ Hook post_tool_learning.py fonctionne"
            return 0
        else
            log_error "❌ Hook post_tool_learning.py a échoué"
            return 1
        fi
    else
        log_warning "⚠️ Hook post_tool_learning.py introuvable"
        return 1
    fi
}

# Vérifier le système d'apprentissage
check_learning_system() {
    log "🧠 Vérification du système d'apprentissage..."
    
    local db_file="${ELF_DIR}/memory/index.db"
    if [[ ! -f "${db_file}" ]]; then
        log_warning "⚠️ Base de données introuvable: ${db_file}"
        return 1
    fi
    
    # Compter les entrées dans la base
    local heuristics_count=0
    local embeddings_count=0
    local trails_count=0
    
    if command -v sqlite3 >/dev/null 2>&1; then
        heuristics_count=$(sqlite3 "${db_file}" "SELECT COUNT(*) FROM heuristics;" 2>/dev/null || echo "0")
        embeddings_count=$(sqlite3 "${db_file}" "SELECT COUNT(*) FROM embeddings;" 2>/dev/null || echo "0")
        trails_count=$(sqlite3 "${db_file}" "SELECT COUNT(*) FROM pheromone_trails;" 2>/dev/null || echo "0")
        
        log_success "✅ Base de données OK"
        log_info "📊 Statistiques:"
        log_info "   Heuristiques: ${heuristics_count}"
        log_info "   Embeddings: ${embeddings_count}"
        log_info "   Trails: ${trails_count}"
    else
        log_warning "⚠️ sqlite3 non disponible, impossible de vérifier la base"
        return 1
    fi
    
    return 0
}

# Vérifier les logs
check_logs() {
    log "📋 Vérification des logs..."
    
    if [[ ! -d "${LOGS_DIR}" ]]; then
        log_warning "⚠️ Répertoire des logs introuvable: ${LOGS_DIR}"
        return 1
    fi
    
    # Vérifier les fichiers de log récents
    local recent_logs
    recent_logs=$(find "${LOGS_DIR}" -name "*.log" -mtime -1 2>/dev/null | wc -l)
    if [[ $recent_logs -gt 0 ]]; then
        log_success "✅ ${recent_logs} fichiers de log récents trouvés"
    else
        log_info "ℹ️ Aucun log récent trouvé"
    fi
    
    # Vérifier s'il y a des erreurs dans les logs récents
    local error_logs
    error_logs=$(find "${LOGS_DIR}" -name "*.log" -mtime -1 -exec grep -l "ERROR\|error\|Error" {} \; 2>/dev/null | wc -l)
    if [[ $error_logs -gt 0 ]]; then
        log_warning "⚠️ ${error_logs} fichiers de log contiennent des erreurs"
    fi
    
    return 0
}

# Rapport final
generate_report() {
    log "📊 Rapport de santé du système..."
    echo "=================================================="
    
    # Services
    echo "サービ Services:"
    if check_service "http://localhost:4096/global/health" "OpenCode Server" 2; then
        echo "  ✅ OpenCode Server"
    else
        echo "  ❌ OpenCode Server"
    fi
    
    if check_service "http://localhost:8888/api/v1/agents/status" "Dashboard Backend" 2; then
        echo "  ✅ Dashboard Backend"
    else
        echo "  ❌ Dashboard Backend"
    fi
    
    if check_service "http://localhost:9998/status" "Event Bridge" 2; then
        echo "  ✅ Event Bridge"
    else
        echo "  ❌ Event Bridge"
    fi
    
    if check_service "http://localhost:3001" "Dashboard Frontend" 2; then
        echo "  ✅ Dashboard Frontend"
    else
        echo "  ❌ Dashboard Frontend"
    fi
    
    echo ""
    
    # Agents
    local agents_response
    agents_response=$(curl -s "http://localhost:8888/api/v1/agents/list" 2>/dev/null || echo "{}")
    if echo "${agents_response}" | grep -q "agents"; then
        local agent_count
        agent_count=$(echo "${agents_response}" | grep -o '"id"' | wc -l)
        echo "🤖 Agents: ${agent_count} disponibles"
    else
        echo "🤖 Agents: ❌ Indisponibles"
    fi
    
    echo ""
    
    # Hooks
    local hooks_dir="${OPENCODE_DIR}/hooks"
    if [[ -d "${hooks_dir}" ]]; then
        local hook_count
        hook_count=$(find "${hooks_dir}" -name "*.py" -type f 2>/dev/null | wc -l)
        echo "🎣 Hooks: ${hook_count} installés"
    else
        echo "🎣 Hooks: ❌ Non installés"
    fi
    
    echo ""
    
    # Learning System
    local db_file="${ELF_DIR}/memory/index.db"
    if [[ -f "${db_file}" ]] && command -v sqlite3 >/dev/null 2>&1; then
        local heuristics_count
        heuristics_count=$(sqlite3 "${db_file}" "SELECT COUNT(*) FROM heuristics;" 2>/dev/null || echo "0")
        echo "🧠 Learning: ${heuristics_count} heuristiques"
    else
        echo "🧠 Learning: ❌ Indisponible"
    fi
    
    echo "=================================================="
    
    return 0
}

# Fonction principale
main() {
    log "🎯 Check-in complet du système ELF OpenCode"
    echo "=================================================="
    
    # Vérifications
    check_processes
    echo ""
    
    test_apis
    echo ""
    
    check_agents
    echo ""
    
    check_hooks
    echo ""
    
    test_hook
    echo ""
    
    check_learning_system
    echo ""
    
    check_logs
    echo ""
    
    # Rapport final
    generate_report
    
    log_success "✅ Check-in terminé!"
    
    # URLs utiles
    log_info "🌐 URLs utiles:"
    echo "  Dashboard:     http://localhost:3001"
    echo "  Backend API:   http://localhost:8888/api/v1/agents/status"
    echo "  Event Bridge:  http://localhost:9998/status"
    echo "  OpenCode:      http://localhost:4096/global/health"
    
    return 0
}

# Exécuter la fonction principale
main "$@"
