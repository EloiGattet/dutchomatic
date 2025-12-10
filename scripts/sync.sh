#!/bin/bash

# Script de synchronisation rapide pour Dutch-o-matic sur Raspberry Pi
# Usage: ./scripts/sync.sh [--no-restart]
#   --no-restart : Ne pas redémarrer le service après la synchronisation

set -e

RASPBERRY_HOST="pi@dutchomatic.local"
REMOTE_DIR="~/duch-o-matic"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Option pour éviter le redémarrage
NO_RESTART=false
if [[ "$1" == "--no-restart" ]]; then
    NO_RESTART=true
fi

echo "🔄 Synchronisation de Dutch-o-matic sur $RASPBERRY_HOST"
echo "📁 Répertoire local: $PROJECT_DIR"
echo "📁 Répertoire distant: $REMOTE_DIR"
echo ""

# Test de connexion SSH
echo "🔌 Test de connexion SSH..."
if ! ssh -o ConnectTimeout=5 "$RASPBERRY_HOST" "echo 'Connexion OK'" > /dev/null 2>&1; then
    echo "❌ Erreur: Impossible de se connecter à $RASPBERRY_HOST"
    echo "   Vérifiez que:"
    echo "   - Le Raspberry Pi est allumé et accessible"
    echo "   - La clé SSH est configurée"
    echo "   - Le hostname 'dutchomatic.local' est résolu"
    exit 1
fi
echo "✅ Connexion SSH réussie"
echo ""

# Synchronisation des fichiers (exclut venv, __pycache__, .DS_Store, logs, etc.)
echo "📤 Synchronisation des fichiers..."
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude '.git/' \
    --exclude 'logs/' \
    --exclude '.restart' \
    --exclude '.server.pid' \
    --exclude 'output/' \
    --exclude '*.log' \
    "$PROJECT_DIR/" "$RASPBERRY_HOST:$REMOTE_DIR/"
echo "✅ Fichiers synchronisés"
echo ""

# Rendre les scripts exécutables
echo "🔧 Configuration des permissions..."
ssh "$RASPBERRY_HOST" << 'ENDSSH'
    cd ~/duch-o-matic
    chmod +x run_server.py
    chmod +x scripts/*.sh 2>/dev/null || true
ENDSSH
echo "✅ Permissions configurées"
echo ""

# Redémarrer le service si demandé
if [ "$NO_RESTART" = false ]; then
    echo "🔄 Redémarrage du service..."
    if ssh "$RASPBERRY_HOST" "systemctl list-unit-files | grep -q '^dutchomatic.service'" 2>/dev/null; then
        ssh "$RASPBERRY_HOST" "sudo systemctl restart dutchomatic" || {
            echo "⚠️  Erreur lors du redémarrage, vérifiez les logs"
        }
        
        # Attendre un peu et vérifier le statut
        sleep 2
        echo "📊 Vérification du statut..."
        ssh "$RASPBERRY_HOST" "sudo systemctl status dutchomatic --no-pager -l | head -10" || true
        echo ""
        echo "✅ Synchronisation terminée avec succès!"
    else
        echo "⚠️  Le service systemd n'est pas installé."
        echo "   Utilisez ./scripts/deploy.sh pour une installation complète"
        echo "✅ Synchronisation terminée (sans redémarrage)"
    fi
else
    echo "✅ Synchronisation terminée (sans redémarrage)"
    echo "   Pour redémarrer: ssh $RASPBERRY_HOST 'sudo systemctl restart dutchomatic'"
fi

echo ""
echo "Commandes utiles:"
echo "  ssh $RASPBERRY_HOST 'sudo systemctl status dutchomatic'    # Vérifier le statut"
echo "  ssh $RASPBERRY_HOST 'sudo systemctl restart dutchomatic'  # Redémarrer le service"
echo "  ssh $RASPBERRY_HOST 'sudo journalctl -u dutchomatic -f'    # Voir les logs"



