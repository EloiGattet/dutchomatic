#!/bin/bash
# Script pour redémarrer le serveur Dutch-o-matic

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/.server.pid"
RESTART_FILE="$PROJECT_ROOT/.restart"

cd "$PROJECT_ROOT"

# Fonction pour trouver le PID du serveur
find_server_pid() {
    # Cherche le processus run_server.py
    ps aux | grep "[r]un_server.py" | awk '{print $2}'
}

# Fonction pour arrêter le serveur
stop_server() {
    PID=$(find_server_pid)
    if [ -n "$PID" ]; then
        echo "Arrêt du serveur (PID: $PID)..."
        kill "$PID" 2>/dev/null
        sleep 2
        # Force kill si toujours en vie
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force kill du serveur..."
            kill -9 "$PID" 2>/dev/null
        fi
        echo "Serveur arrêté."
    else
        echo "Aucun serveur en cours d'exécution."
    fi
    
    # Supprime le fichier PID s'il existe
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
}

# Fonction pour démarrer le serveur
start_server() {
    echo "Démarrage du serveur..."
    
    # Active le venv s'il existe
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Démarre le serveur en arrière-plan
    nohup python3 run_server.py > /dev/null 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"
    echo "Serveur démarré (PID: $SERVER_PID)"
    echo "Logs disponibles dans: logs/dutchomatic.log"
}

# Fonction pour redémarrer
restart_server() {
    stop_server
    sleep 1
    start_server
}

# Gestion des arguments
case "${1:-restart}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        PID=$(find_server_pid)
        if [ -n "$PID" ]; then
            echo "Serveur en cours d'exécution (PID: $PID)"
        else
            echo "Serveur arrêté"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
