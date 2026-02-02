#!/bin/bash
"""
Installation du système intelligent de rotation des logs
- Crontab adaptatif selon état ELF
- Surveillance intelligente
- Rotation conditionnelle
"""

echo "[SmartInstall] 🔧 Installation du système intelligent..."

# 1. Remplace le crontab par un système intelligent
cat > /tmp/smart_crontab << 'EOF'
# Système intelligent de rotation ELF - Adaptatif selon état ELF
# Détecte si ELF actif et adapte la surveillance

# Détection d'état toutes les 5 minutes
*/5 * * * * /usr/bin/python3 /home/bamer/.opencode/emergent-learning/scripts/elf_state_detector.py detect >/dev/null 2>&1

# Rotation intelligente si ELF actif (toutes les 15 min)
*/15 * * * * /usr/bin/python3 /home/bamer/.opencode/emergent-learning/scripts/smart_rotation.py >/dev/null 2>&1

# Rotation quotidienne force si ELF inactif
0 4 * * * /usr/bin/python3 /home/bamer/.opencode/emergent-learning/scripts/smart_rotation.py force >/dev/null 2>&1

# Statut quotidien
0 9 * * * /usr/bin/python3 /home/bamer/.opencode/emergent-learning/scripts/elf_state_detector.py status >/dev/null 2>&1
EOF

(crontab -l 2>/dev/null; cat /tmp/smart_crontab) | crontab -
rm /tmp/smart_crontab

echo "[SmartInstall] ✅ Crontab intelligent installé"

# 2. Test du système
echo "[SmartInstall] 🧪 Test du système..."
python3 /home/bamer/.opencode/emergent-learning/scripts/elf_state_detector.py status
python3 /home/bamer/.opencode/emergent-learning/scripts/auto_log_rotation.py status

echo "[SmartInstall] ✅ Installation terminée!"
echo "[SmartInstall] 📋 Nouveau crontab:"
crontab -l | grep -E "(elf_state|smart_rotation)"