#!/bin/bash
# Script to install systemd service for Dutch-o-matic

set -e

SERVICE_NAME="dutchomatic"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_FILE="$PROJECT_DIR/systemd/${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🔧 Installation du service systemd pour Dutch-o-matic"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Fichier service non trouvé: $SERVICE_FILE"
    exit 1
fi

# Check if service is already installed
if [ -f "$SYSTEMD_DIR/${SERVICE_NAME}.service" ]; then
    # Compare files to see if update is needed
    if ! cmp -s "$SERVICE_FILE" "$SYSTEMD_DIR/${SERVICE_NAME}.service"; then
        echo "📋 Mise à jour du fichier service..."
        cp "$SERVICE_FILE" "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        echo "🔄 Rechargement de systemd..."
        systemctl daemon-reload
    else
        echo "✅ Service déjà installé et à jour"
    fi
else
    echo "📋 Installation du fichier service..."
    cp "$SERVICE_FILE" "$SYSTEMD_DIR/${SERVICE_NAME}.service"
    echo "🔄 Rechargement de systemd..."
    systemctl daemon-reload
fi

# Enable service (idempotent)
if ! systemctl is-enabled "${SERVICE_NAME}.service" > /dev/null 2>&1; then
    echo "✅ Activation du service au démarrage..."
    systemctl enable "${SERVICE_NAME}.service"
else
    echo "✅ Service déjà activé au démarrage"
fi

echo ""
echo "✅ Service installé avec succès!"
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl start ${SERVICE_NAME}    # Démarrer le service"
echo "  sudo systemctl stop ${SERVICE_NAME}     # Arrêter le service"
echo "  sudo systemctl status ${SERVICE_NAME}   # Vérifier le statut"
echo "  sudo systemctl restart ${SERVICE_NAME}  # Redémarrer le service"
echo "  sudo journalctl -u ${SERVICE_NAME} -f   # Voir les logs"
