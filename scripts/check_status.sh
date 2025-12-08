#!/bin/bash
# Script pour vérifier le statut du serveur et du watcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Statut du serveur Dutch-o-matic ==="
echo ""

# Vérifier si systemd est utilisé
if systemctl list-unit-files 2>/dev/null | grep -q "^dutchomatic.service"; then
    echo "📦 Service systemd détecté"
    echo ""
    echo "Statut du service:"
    sudo systemctl status dutchomatic --no-pager -l | head -15
    echo ""
    echo "Pour redémarrer: sudo systemctl restart dutchomatic"
    echo "Pour voir les logs: sudo journalctl -u dutchomatic -f"
else
    echo "📦 Service systemd non installé"
    echo ""
    
    # Vérifier le processus serveur
    SERVER_PID=$(ps aux | grep "[r]un_server.py" | awk '{print $2}')
    if [ -n "$SERVER_PID" ]; then
        echo "✅ Serveur en cours d'exécution (PID: $SERVER_PID)"
    else
        echo "❌ Serveur arrêté"
    fi
    
    # Vérifier le watcher
    WATCHER_PID=$(ps aux | grep "[w]atch_restart.sh" | awk '{print $2}')
    if [ -n "$WATCHER_PID" ]; then
        echo "✅ Watcher actif (PID: $WATCHER_PID)"
        echo "   Vous pouvez utiliser './scripts/touch_restart.sh' pour redémarrer"
    else
        echo "❌ Watcher non actif"
        echo "   Pour l'activer: ./scripts/watch_restart.sh"
        echo "   Ou redémarrer directement: ./scripts/restart.sh restart"
    fi
fi

echo ""
echo "=== Méthodes de redémarrage ==="
echo ""
echo "1. Si systemd est installé:"
echo "   sudo systemctl restart dutchomatic"
echo ""
echo "2. Si le watcher est actif:"
echo "   ./scripts/touch_restart.sh"
echo ""
echo "3. Redémarrage direct:"
echo "   ./scripts/restart.sh restart"
echo ""
