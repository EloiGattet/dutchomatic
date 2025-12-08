#!/bin/bash
# Script to install and configure nginx for Dutch-o-matic

set -e

echo "🔧 Installation et configuration de nginx pour Dutch-o-matic"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

# Install nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installation de nginx..."
    apt-get update
    apt-get install -y nginx
else
    echo "✅ nginx est déjà installé"
fi

# Copy nginx configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
NGINX_CONF="$PROJECT_DIR/nginx/dutchomatic.conf"
NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"

if [ ! -f "$NGINX_CONF" ]; then
    echo "❌ Fichier de configuration nginx non trouvé: $NGINX_CONF"
    exit 1
fi

# Check if configuration needs update
NGINX_UPDATED=false
if [ -f "$NGINX_SITES_DIR/dutchomatic" ]; then
    if ! cmp -s "$NGINX_CONF" "$NGINX_SITES_DIR/dutchomatic"; then
        echo "📋 Mise à jour de la configuration nginx..."
        cp "$NGINX_CONF" "$NGINX_SITES_DIR/dutchomatic"
        NGINX_UPDATED=true
    else
        echo "✅ Configuration nginx déjà à jour"
    fi
else
    echo "📋 Installation de la configuration nginx..."
    cp "$NGINX_CONF" "$NGINX_SITES_DIR/dutchomatic"
    NGINX_UPDATED=true
fi

# Remove default site if it exists
if [ -f "$NGINX_ENABLED_DIR/default" ]; then
    echo "🗑️  Suppression du site par défaut..."
    rm "$NGINX_ENABLED_DIR/default"
    NGINX_UPDATED=true
fi

# Enable site
if [ ! -L "$NGINX_ENABLED_DIR/dutchomatic" ]; then
    echo "🔗 Activation du site..."
    ln -s "$NGINX_SITES_DIR/dutchomatic" "$NGINX_ENABLED_DIR/dutchomatic"
    NGINX_UPDATED=true
fi

# Test nginx configuration
echo "🧪 Test de la configuration nginx..."
if nginx -t; then
    echo "✅ Configuration nginx valide"
else
    echo "❌ Erreur dans la configuration nginx"
    exit 1
fi

# Restart nginx only if configuration was updated
if [ "$NGINX_UPDATED" = true ]; then
    echo "🔄 Redémarrage de nginx..."
    systemctl restart nginx
else
    echo "✅ nginx déjà configuré, pas de redémarrage nécessaire"
fi

# Enable nginx (idempotent)
if ! systemctl is-enabled nginx > /dev/null 2>&1; then
    echo "✅ Activation de nginx au démarrage..."
    systemctl enable nginx
else
    echo "✅ nginx déjà activé au démarrage"
fi

echo ""
echo "✅ nginx configuré avec succès!"
echo ""
echo "L'interface est maintenant accessible sur:"
echo "  http://dutchomatic.local/"
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl status nginx    # Vérifier le statut"
echo "  sudo systemctl restart nginx   # Redémarrer nginx"
echo "  sudo nginx -t                  # Tester la configuration"
