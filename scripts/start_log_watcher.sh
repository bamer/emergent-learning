#!/bin/bash
"""
Script de démarrage du système de surveillance des logs
- Démarre le sentinel en arrière-plan
- Gère les processus avec PID file
- Intégration avec le dashboard
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHER_SCRIPT="$SCRIPT_DIR/log_sentinel.py"
PID_FILE="/tmp/log_sentinel.pid"
LOG_FILE="/home/bamer/.opencode/emergent-learning/logs/sentinel_daemon.log"

# Fonction de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Vérifier si le sentinel est déjà en cours d'exécution
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # En cours d'exécution
        else
            rm -f "$PID_FILE"  # PID file orphelin
            return 1
        fi
    fi
    return 1
}

# Démarrer le sentinel
start_sentinel() {
    if is_running; then
        log_message "⚠️  Le sentinel est déjà en cours d'exécution (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    log_message "🚀 Démarrage du sentinel de logs..."
    
    # Démarre le sentinel en arrière-plan
    nohup python3 "$WATCHER_SCRIPT" > /dev/null 2>&1 &
    local sentinel_pid=$!
    
    # Sauvegarde le PID
    echo $sentinel_pid > "$PID_FILE"
    
    # Vérifie que le processus a bien démarré
    sleep 2
    if kill -0 "$sentinel_pid" 2>/dev/null; then
        log_message "✅ Watcher démarré avec succès (PID: $sentinel_pid)"
        return 0
    else
        log_message "❌ Échec du démarrage du sentinel"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Arrêter le sentinel
stop_sentinel() {
    if ! is_running; then
        log_message "ℹ️  Le sentinel n'est pas en cours d'exécution"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    log_message "🛑 Arrêt du sentinel (PID: $pid)..."
    
    # Arrêt propre du processus
    kill -TERM "$pid"
    
    # Attend 10 secondes max
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force l'arrêt si nécessaire
    if kill -0 "$pid" 2>/dev/null; then
        log_message "⚠️  Arrêt forcé du sentinel"
        kill -KILL "$pid"
    fi
    
    rm -f "$PID_FILE"
    log_message "✅ Watcher arrêté"
    return 0
}

# Redémarrer le sentinel
restart_sentinel() {
    log_message "🔄 Redémarrage du sentinel..."
    stop_sentinel
    sleep 2
    start_sentinel
}

# Afficher le statut
status_sentinel() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log_message "✅ Watcher en cours d'exécution (PID: $pid)"
        
        # Affiche les infos détaillées du processus
        if command -v ps >/dev/null 2>&1; then
            echo ""
            echo "=== Détails du processus ==="
            ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || echo "Impossible d'obtenir les détails"
        fi
        
        # Affiche le statut depuis le script
        echo ""
        echo "=== Statut du sentinel ==="
        python3 "$WATCHER_SCRIPT" status
        
        return 0
    else
        log_message "❌ Watcher non en cours d'exécution"
        return 1
    fi
}

# Afficher les logs
logs_sentinel() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Logs du sentinel ($LOG_FILE) ==="
        tail -n 50 "$LOG_FILE"
    else
        echo "Aucun fichier de log trouvé: $LOG_FILE"
    fi
    
    echo ""
    echo "=== Statut actuel ==="
    python3 "$WATCHER_SCRIPT" status
}

# Installation du démarrage automatique
install_autostart() {
    log_message "📦 Installation du démarrage automatique..."
    
    # Ajoute au crontab pour démarrage au boot
    (crontab -l 2>/dev/null; echo "@reboot $SCRIPT_DIR/start_log_sentinel.sh start") | crontab -
    
    # Démarre maintenant
    start_sentinel
    
    log_message "✅ Démarrage automatique configuré"
}

# Désinstallation
uninstall_autostart() {
    log_message "🗑️  Désinstallation du démarrage automatique..."
    
    # Arrête le sentinel
    stop_sentinel
    
    # Retire du crontab
    crontab -l | grep -v "start_log_sentinel.sh" | crontab -
    
    log_message "✅ Démarrage automatique désinstallé"
}

# Aide
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|install|uninstall|help}"
    echo ""
    echo "Commandes:"
    echo "  start     - Démarre le sentinel"
    echo "  stop      - Arrête le sentinel"
    echo "  restart   - Redémarre le sentinel"
    echo "  status    - Affiche le statut du sentinel"
    echo "  logs      - Affiche les logs du sentinel"
    echo "  install   - Configure le démarrage automatique"
    echo "  uninstall - Retire le démarrage automatique"
    echo "  help      - Affiche cette aide"
    echo ""
    echo "Fichiers:"
    echo "  Script: $WATCHER_SCRIPT"
    echo "  PID file: $PID_FILE"
    echo "  Log file: $LOG_FILE"
}

# Point d'entrée principal
case "${1:-help}" in
    start)
        start_sentinel
        ;;
    stop)
        stop_sentinel
        ;;
    restart)
        restart_sentinel
        ;;
    status)
        status_sentinel
        ;;
    logs)
        logs_sentinel
        ;;
    install)
        install_autostart
        ;;
    uninstall)
        uninstall_autostart
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_message "❌ Commande inconnue: $1"
        show_help
        exit 1
        ;;
esac

exit $?