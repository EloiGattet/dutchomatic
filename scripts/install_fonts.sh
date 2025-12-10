#!/bin/bash
# Installation des fonts sur Raspberry Pi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FONTS_DIR="$PROJECT_DIR/fonts"
FONTS_SYSTEM="/usr/share/fonts/truetype/dutchomatic"
FONTS_PROJECT="$PROJECT_DIR"

echo "Installation des fonts pour Dutch-o-matic..."

# Vérifier que les fonts existent
if [ ! -d "$FONTS_DIR" ] || [ -z "$(ls -A "$FONTS_DIR"/*.ttf 2>/dev/null)" ]; then
    echo "Erreur: Aucune font trouvée dans $FONTS_DIR"
    exit 1
fi

# 1. Installation système (pour que toutes les applications puissent les utiliser)
echo "Installation système des fonts..."
sudo mkdir -p "$FONTS_SYSTEM"
sudo cp "$FONTS_DIR"/*.ttf "$FONTS_SYSTEM/"
sudo chmod 644 "$FONTS_SYSTEM"/*.ttf
sudo fc-cache -fv

# 2. Copie dans le répertoire du projet (pour les chemins relatifs dans le code)
echo "Copie des fonts dans le répertoire du projet..."
cp "$FONTS_DIR"/*.ttf "$FONTS_PROJECT/"

echo ""
echo "✓ Fonts installées avec succès!"
echo "  - Système: $FONTS_SYSTEM"
echo "  - Projet: $FONTS_PROJECT"
echo ""
echo "Fonts disponibles:"
ls -lh "$FONTS_DIR"/*.ttf
