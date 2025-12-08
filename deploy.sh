#!/bin/bash

# Script de déploiement pour Dutch-o-matic sur Raspberry Pi
# Usage: ./deploy.sh

set -e

RASPBERRY_HOST="pi@dutchomatic.local"
REMOTE_DIR="~/duch-o-matic"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Synchronisation des fichiers (exclut venv, __pycache__, .DS_Store)
echo "📤 Synchronisation des fichiers..."
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude '.git/' \
    --exclude '*.pyc' \
    "$PROJECT_DIR/" "$RASPBERRY_HOST:$REMOTE_DIR/"
echo "✅ Fichiers synchronisés"
echo ""

# Installation des dépendances système
echo "📦 Installation des dépendances système..."
ssh "$RASPBERRY_HOST" "sudo apt-get update && sudo apt-get install -y python3-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7-dev libtiff5-dev libwebp-dev" > /dev/null 2>&1
echo "✅ Dépendances système installées"
echo ""

# Installation des dépendances Python
echo "📦 Installation des dépendances Python..."
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
    fi
    
    # Activer l'environnement virtuel et installer les dépendances
    echo "📥 Installation des packages Python..."
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    
    echo "✅ Dépendances Python installées"
ENDSSH

echo ""
echo "✅ Déploiement terminé avec succès!"
echo ""
echo "Pour vous connecter au Raspberry Pi:"
echo "  ssh $RASPBERRY_HOST"
echo ""
echo "Pour activer l'environnement virtuel:"
echo "  cd $REMOTE_DIR && source venv/bin/activate"
