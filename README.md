# Dutch-o-matic

Boîte d'exercices de néerlandais avec impression de tickets.

## Structure du projet

```
duch-o-matic/
├── src/
│   ├── storage/          # Abstraction storage (JSON/SQLite)
│   ├── models/           # Modèles de données
│   └── utils/            # Utilitaires (validateurs)
├── data/                 # Fichiers JSON de données
└── documents/            # Documentation et roadmap
```

## Installation

```bash
# Pas de dépendances externes pour l'instant
python3 -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` sur Windows
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

## Roadmap

Voir `documents/roadmap/00_index.md` pour le statut des missions.
