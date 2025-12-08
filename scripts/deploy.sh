#!/bin/bash

# Script de déploiement pour Dutch-o-matic sur Raspberry Pi
# Usage: ./scripts/deploy.sh [--no-restart]
#   --no-restart : Ne pas redémarrer le service après le déploiement

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

echo "🚀 Déploiement de Dutch-o-matic sur $RASPBERRY_HOST"
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

# Création du répertoire distant
echo "📂 Création du répertoire distant..."
ssh "$RASPBERRY_HOST" "mkdir -p $REMOTE_DIR"
echo "✅ Répertoire créé"
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

# Installation des dépendances système
echo "📦 Vérification des dépendances système..."
ssh "$RASPBERRY_HOST" << 'ENDSSH'
    MISSING_DEPS=()
    DEPS=("python3-dev" "libjpeg-dev" "zlib1g-dev" "liblcms2-dev" "libopenjp2-7-dev" "libtiff5-dev" "libwebp-dev")
    
    for dep in "${DEPS[@]}"; do
        # Utiliser dpkg-query qui est plus fiable que dpkg -l | grep
        if ! dpkg-query -W -f='${Status}' "$dep" 2>/dev/null | grep -q "install ok installed"; then
            MISSING_DEPS+=("$dep")
        fi
    done
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo "📥 Installation des dépendances manquantes: ${MISSING_DEPS[*]}"
        sudo apt-get update > /dev/null 2>&1
        sudo apt-get install -y "${MISSING_DEPS[@]}" > /dev/null 2>&1
        echo "✅ Dépendances système installées"
    else
        echo "✅ Toutes les dépendances système sont déjà installées"
    fi
ENDSSH
echo ""

# Installation des dépendances Python
echo "📦 Vérification des dépendances Python..."
ssh "$RASPBERRY_HOST" << 'ENDSSH'
    cd ~/duch-o-matic
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 n'est pas installé"
        exit 1
    fi
    
    # Créer un environnement virtuel s'il n'existe pas
    if [ ! -d "venv" ]; then
        echo "🔧 Création de l'environnement virtuel..."
        python3 -m venv venv
        VENV_CREATED=true
    else
        echo "✅ Environnement virtuel déjà présent"
        VENV_CREATED=false
    fi
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Mettre à jour pip si nécessaire
    if [ "$VENV_CREATED" = true ] || ! pip list | grep -q "^pip "; then
        echo "📥 Mise à jour de pip..."
        pip install --upgrade pip > /dev/null 2>&1
    fi
    
    # Vérifier si les dépendances sont à jour
    if [ -f "requirements.txt" ]; then
        echo "📥 Vérification des packages Python..."
        pip install -q --upgrade -r requirements.txt
        echo "✅ Dépendances Python à jour"
    else
        echo "⚠️  Fichier requirements.txt non trouvé"
    fi
ENDSSH

# Installation du service systemd et nginx
echo "🔧 Vérification des services..."
SERVICE_INSTALLED=false
ssh "$RASPBERRY_HOST" << 'ENDSSH'
    cd ~/duch-o-matic
    
    # Vérifier et installer le service systemd si nécessaire
    if [ -f "scripts/install_service.sh" ]; then
        if systemctl list-unit-files | grep -q "^dutchomatic.service"; then
            echo "✅ Service systemd déjà installé"
        else
            echo "📋 Installation du service systemd..."
            cd scripts
            sudo ./install_service.sh
            cd ..
        fi
    else
        echo "⚠️  Script install_service.sh non trouvé, installation manuelle nécessaire"
    fi
    
    # Vérifier et installer nginx si nécessaire
    if [ -f "scripts/install_nginx.sh" ]; then
        if command -v nginx &> /dev/null && [ -f "/etc/nginx/sites-enabled/dutchomatic" ]; then
            echo "✅ nginx déjà installé et configuré"
        else
            echo "🌐 Installation de nginx..."
            cd scripts
            sudo ./install_nginx.sh
            cd ..
        fi
    else
        echo "⚠️  Script install_nginx.sh non trouvé, installation manuelle nécessaire"
    fi
ENDSSH

# Vérifier si le service systemd est installé
if ssh "$RASPBERRY_HOST" "systemctl list-unit-files | grep -q '^dutchomatic.service'" 2>/dev/null; then
    SERVICE_INSTALLED=true
fi

# Redémarrer le service si demandé
if [ "$NO_RESTART" = false ] && [ "$SERVICE_INSTALLED" = true ]; then
    echo ""
    echo "🔄 Redémarrage du service..."
    ssh "$RASPBERRY_HOST" "sudo systemctl restart dutchomatic" || {
        echo "⚠️  Erreur lors du redémarrage, vérifiez les logs"
    }
    
    # Attendre un peu et vérifier le statut
    sleep 2
    echo "📊 Vérification du statut..."
    ssh "$RASPBERRY_HOST" "sudo systemctl status dutchomatic --no-pager -l | head -10" || true
    echo ""
fi

echo ""
echo "✅ Déploiement terminé avec succès!"
echo ""
if [ "$SERVICE_INSTALLED" = true ]; then
    echo "Le service systemd est installé et activé."
    echo "Le serveur web démarrera automatiquement au boot."
else
    echo "⚠️  Le service systemd n'est pas installé."
    echo "   Pour l'installer: ssh $RASPBERRY_HOST 'cd ~/duch-o-matic && sudo ./scripts/install_service.sh'"
fi
echo ""
echo "Pour vous connecter au Raspberry Pi:"
echo "  ssh $RASPBERRY_HOST"
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl status dutchomatic    # Vérifier le statut"
echo "  sudo systemctl restart dutchomatic    # Redémarrer le service"
echo "  sudo journalctl -u dutchomatic -f     # Voir les logs"
if [ "$NO_RESTART" = true ]; then
    echo ""
    echo "ℹ️  Le service n'a pas été redémarré (--no-restart utilisé)"
    echo "   Pour redémarrer: ssh $RASPBERRY_HOST 'sudo systemctl restart dutchomatic'"
fi
