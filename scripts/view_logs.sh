#!/bin/bash
# Script pour consulter les logs du serveur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/dutchomatic.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "Aucun fichier de log trouvé: $LOG_FILE"
    exit 1
fi

case "${1:-tail}" in
    tail)
        echo "Affichage des dernières lignes (Ctrl+C pour quitter)..."
        tail -f "$LOG_FILE"
        ;;
    errors)
        echo "Affichage des erreurs uniquement:"
        grep -i error "$LOG_FILE" | tail -50
        ;;
    last)
        lines="${2:-50}"
        echo "Dernières $lines lignes:"
        tail -n "$lines" "$LOG_FILE"
        ;;
    search)
        if [ -z "$2" ]; then
            echo "Usage: $0 search <terme>"
            exit 1
        fi
        echo "Recherche de '$2' dans les logs:"
        grep -i "$2" "$LOG_FILE" | tail -50
        ;;
    *)
        echo "Usage: $0 {tail|errors|last [n]|search <terme>}"
        echo ""
        echo "  tail      - Suivre les logs en temps réel (défaut)"
        echo "  errors    - Afficher uniquement les erreurs"
        echo "  last [n]  - Afficher les n dernières lignes (défaut: 50)"
        echo "  search    - Rechercher un terme dans les logs"
        exit 1
        ;;
esac
