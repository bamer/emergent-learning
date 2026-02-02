#!/bin/bash
"""
Script d'installation du crontab pour la rotation automatique des logs
- Configure rotation toutes les 4 heures
- Rotation de vérification toutes les 30 minutes
- Logs des exécutions crontab
"""

# Configuration
SCRIPT_PATH="/home/bamer/.opencode/emergent-learning/scripts/auto_log_rotation.py"
CRON_LOG="/home/bamer/.opencode/emergent-learning/logs/cron_rotation.log"
USER="bamer"

echo "[InstallCron] Installation du crontab pour rotation automatique des logs..."

# Crée le répertoire de logs s'il n'existe pas
mkdir -p "$(dirname "$CRON_LOG")"

# Sauvegarde l'ancien crontab s'il existe
echo "[InstallCron] Sauvegarde de l'ancien crontab..."
crontab -l > /tmp/old_crontab_$(date +%Y%m%d_%H%M%S).backup 2>/dev/null || echo "Aucun crontab existant"

# Supprime les anciennes entrées de rotation automatique
echo "[InstallCron] Suppression des anciennes entrées de rotation..."
crontab -l | grep -v "auto_log_rotation" | crontab -

# Ajoute les nouvelles entrées de rotation
echo "[InstallCron] Ajout des nouvelles entrées de rotation..."

# Rotation principale toutes les 4 heures (0,4,8,12,16,20 heures)
# Rotation de vérification toutes les 30 minutes
# Log des exécutions dans un fichier séparé

# Crée un fichier temporaire avec les nouvelles entrées
cat > /tmp/new_crontab_entries << EOF
# Rotation automatique des logs ELF - Généré automatiquement
# Vérification toutes les 30 minutes (rotation si nécessaire)
*/30 * * * * /usr/bin/python3 "$SCRIPT_PATH" run >> "$CRON_LOG" 2>&1

# Rotation forcée quotidienne à 3h00 (nettoie les fichiers vieux)
0 3 * * * /usr/bin/python3 "$SCRIPT_PATH" run >> "$CRON_LOG" 2>&1

# Statut quotidien à 9h00 (pour monitoring)
0 9 * * * /usr/bin/python3 "$SCRIPT_PATH" status >> "$CRON_LOG" 2>&1
EOF

# Ajoute les entrées au crontab existant
(crontab -l 2>/dev/null; cat /tmp/new_crontab_entries) | crontab -

# Nettoie le fichier temporaire
rm /tmp/new_crontab_entries

echo "[InstallCron] Crontab installé avec succès!"

# Affiche le nouveau crontab
echo "[InstallCron] Nouveau crontab :"
echo "─────────────────────────────────────────"
crontab -l | grep -E "(auto_log_rotation|# Rotation)"
echo "─────────────────────────────────────────"

echo "[InstallCron] Installation terminée!"
echo "[InstallCron] Logs des exécutions : $CRON_LOG"
echo "[InstallCron] Vérification du statut : python3 $SCRIPT_PATH status"
echo "[InstallCron] Test manuel : python3 $SCRIPT_PATH run"

# Test immédiat
echo ""
echo "[InstallCron] Test immédiat de l'installation..."
/usr/bin/python3 "$SCRIPT_PATH" status

exit 0