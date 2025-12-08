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
