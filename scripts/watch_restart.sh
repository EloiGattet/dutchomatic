#!/bin/bash
# Script pour surveiller le fichier .restart et redémarrer automatiquement

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESTART_FILE="$PROJECT_ROOT/.restart"
RESTART_SCRIPT="$SCRIPT_DIR/restart.sh"

cd "$PROJECT_ROOT"

# Crée le fichier s'il n'existe pas
touch "$RESTART_FILE"

echo "Surveillance du fichier $RESTART_FILE"
echo "Utilisez './scripts/touch_restart.sh' pour déclencher un redémarrage"
echo "Appuyez sur Ctrl+C pour arrêter la surveillance"
echo ""

LAST_MODIFIED=$(stat -f %m "$RESTART_FILE" 2>/dev/null || stat -c %Y "$RESTART_FILE" 2>/dev/null)

while true; do
    sleep 1
    CURRENT_MODIFIED=$(stat -f %m "$RESTART_FILE" 2>/dev/null || stat -c %Y "$RESTART_FILE" 2>/dev/null)
    
    if [ "$CURRENT_MODIFIED" != "$LAST_MODIFIED" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Fichier .restart modifié, redémarrage du serveur..."
        "$RESTART_SCRIPT" restart
        LAST_MODIFIED=$CURRENT_MODIFIED
    fi
done
