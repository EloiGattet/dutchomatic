#!/bin/bash
# Script pour déclencher un redémarrage en touchant le fichier .restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESTART_FILE="$PROJECT_ROOT/.restart"

touch "$RESTART_FILE"
echo "Fichier de redémarrage touché: $RESTART_FILE"
echo "Le serveur devrait redémarrer automatiquement si le watcher est actif."
