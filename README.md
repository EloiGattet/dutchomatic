<div align="center">
  <img src="documents/Logo_dutchomatic.png" alt="Dutch-o-matic Logo" width="200"/>
  
  # Dutch-o-matic
  
  Boîte d'exercices de néerlandais avec impression de tickets.
  
  ![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
  ![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Armv6-red?logo=raspberry-pi&logoColor=white)
  ![ESC/POS](https://img.shields.io/badge/ESC%2FPOS-Printer-green)
  ![License](https://img.shields.io/badge/License-MIT-yellow)
</div>

## Technologies

- **Python 3.8+** - Langage principal
- **python-escpos** - Communication avec imprimantes ESC/POS
- **Raspberry Pi** - Plateforme matérielle (Armv6)
- **JSON** - Stockage des données (exercices, état, daily)

## Structure du projet

```
duch-o-matic/
├── src/
│   ├── storage/          # Abstraction storage (JSON/SQLite)
│   ├── models/           # Modèles de données
│   └── utils/            # Utilitaires (validateurs)
├── data/                 # Fichiers JSON de données
├── scripts/              # Scripts de déploiement et installation
│   ├── deploy.sh         # Déploiement sur Raspberry Pi
│   ├── install_service.sh # Installation du service systemd
│   └── install_nginx.sh  # Installation et configuration nginx
├── systemd/              # Configuration systemd
├── nginx/                # Configuration nginx
└── documents/            # Documentation et roadmap
```

## Installation

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` sur Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

```python
from src.storage import JSONStorage

storage = JSONStorage(data_dir='data')

# Exemples
exercise = storage.get_exercise('ex_0001')
all_exercises = storage.get_all_exercises({'niveau': 'A1'})
state = storage.get_state()
```

## Utilitaires

### Conversion d'images avec dithering

Le projet inclut des utilitaires pour convertir des images en noir et blanc avec dithering error diffusion, optimisées pour l'impression thermique (384px de large).

#### Interface graphique interactive

Lancez l'interface graphique pour convertir des images avec prévisualisation en temps réel :

```bash
python -m utils.image_converter_gui
```

Fonctionnalités :
- **Sélection d'image** : Bouton "Parcourir" pour choisir une image
- **Prévisualisation en temps réel** : Affichage côte à côte de l'original et du résultat
- **Contrôles ajustables** :
  - **Algorithme de dithering** : Atkinson+, Atkinson, Floyd-Steinberg, Sierra24A, Stucki
  - **Luminosité** : Curseur de -100 à +100
  - **Contraste** : Curseur de 0.0 à 2.0
- **Sauvegarde** : Enregistre automatiquement dans `data/surprise_photos` en PNG compressé

#### Conversion par lots

Pour convertir un dossier entier d'images :

```bash
python -m utils.batch_convert /chemin/vers/dossier
```

Options disponibles :
- `--output-dir` : Dossier de sortie (défaut: `data/surprise_photos`)
- `--width` : Largeur de sortie en pixels (défaut: 384)
- `--algorithm` : Algorithme de dithering (défaut: `atkinson_plus`)
  - Options : `atkinson_plus`, `atkinson`, `floyd_steinberg`, `sierra24a`, `stucki`
- `--brightness` : Ajustement de luminosité -100 à +100 (défaut: 0.0)
- `--contrast` : Ajustement de contraste 0.0 à 2.0 (défaut: 1.0)

Exemple :
```bash
python -m utils.batch_convert ~/Photos/vacances --algorithm sierra24a --brightness 10 --contrast 1.2
```

#### Algorithmes de dithering disponibles

- **Atkinson+** (recommandé) : Variante améliorée d'Atkinson, bon compromis qualité/vitesse
- **Atkinson** : Algorithme classique, diffusion d'erreur sur 6 pixels
- **Floyd-Steinberg** : Algorithme historique, très répandu
- **Sierra24A** : Variante Sierra, bonne qualité pour les détails
- **Stucki** : Haute qualité, traitement plus lent mais meilleur rendu

Les images converties sont automatiquement :
- Redimensionnées à 384px de large (proportionnellement)
- Converties en noir et blanc avec dithering error diffusion
- Sauvegardées en PNG compressé dans `data/surprise_photos`

## Déploiement

### Déploiement sur Raspberry Pi

Le script de déploiement automatise l'installation sur un Raspberry Pi :

```bash
# Depuis la racine du projet
./scripts/deploy.sh
```

Ce script :
- Synchronise les fichiers vers le Raspberry Pi
- Installe les dépendances système et Python
- Configure le service systemd
- Configure nginx comme reverse proxy

### Installation manuelle

Si vous préférez installer manuellement :

```bash
# Installation du service systemd
sudo ./scripts/install_service.sh

# Installation de nginx
sudo ./scripts/install_nginx.sh
```

## Gestion du serveur web

Pour la gestion du serveur web (logging, redémarrage, etc.), voir [README_SERVER.md](README_SERVER.md).

## Roadmap

Voir `documents/roadmap/00_index.md` pour le statut des missions.
