# Mission 01 : Structure & Storage

**Agent** : Storage  
**Statut** : ✅ Terminé  
**Dépendances** : Aucune  
**Durée estimée** : 2-3h

## Objectif
Créer la structure de base du projet avec l'abstraction storage JSON et les schémas de données.

## Livrables

### 1. Structure du projet
```
duch-o-matic/
├── src/
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── json_storage.py      # Implémentation JSON
│   │   └── interface.py         # Interface abstraite (future SQLite)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── exercise.py          # Schéma exercice
│   │   ├── daily.py             # Schéma daily
│   │   └── state.py             # Schéma state
│   └── utils/
│       ├── __init__.py
│       └── validators.py        # Validation JSON
├── data/
│   ├── exercises.json           # Fichier initial (vide ou exemples)
│   ├── daily.json               # Fichier initial (vide ou exemples)
│   └── state.json               # Fichier initial avec valeurs par défaut
├── requirements.txt
└── README.md
```

### 2. Abstraction storage (`src/storage/interface.py`)
Interface Python avec méthodes :
- `get_exercise(exercise_id: str) -> dict`
- `get_all_exercises(filters: dict = None) -> list`
- `add_exercise(exercise: dict) -> str`
- `update_exercise(exercise_id: str, exercise: dict) -> bool`
- `delete_exercise(exercise_id: str) -> bool`
- `get_daily(daily_id: str) -> dict`
- `get_all_daily(kind: str = None) -> list`
- `add_daily(daily: dict) -> str`
- `get_state() -> dict`
- `update_state(key: str, value: any) -> bool`
- `add_history_entry(entry: dict) -> bool`

### 3. Implémentation JSON (`src/storage/json_storage.py`)
- Lecture/écriture atomique (lock fichier si besoin)
- Gestion erreurs (fichier absent, JSON invalide)
- Auto-création fichiers si absents

### 4. Schémas de données (`src/models/`)
- `Exercise` : validation selon PRD (id, niveau, type, title, prompt, items, explanations, tags)
- `Daily` : validation (id, kind, nl, fr, extra_json)
- `State` : structure (history, last_exercise_id, niveau_actuel, xp, compteur_total)

### 5. Validateurs (`src/utils/validators.py`)
- Validation schéma exercice (types, champs requis)
- Validation schéma daily
- Validation state

### 6. Fichiers JSON initiaux (`data/`)
- `exercises.json` : `[]` ou 2-3 exemples A1 (vocabulary)
- `daily.json` : `[]` ou 2-3 exemples (expression, fact, quote)
- `state.json` : valeurs par défaut
  ```json
  {
    "history": [],
    "last_exercise_id": null,
    "niveau_actuel": "A1",
    "xp": 0,
    "compteur_total": 0
  }
  ```

## Tests à effectuer
- [ ] Création fichiers JSON si absents
- [ ] Lecture/écriture exercices (CRUD complet)
- [ ] Lecture/écriture daily (CRUD complet)
- [ ] Gestion state (get/update/add_history)
- [ ] Validation schémas (rejet données invalides)
- [ ] Gestion erreurs (fichier corrompu, permissions)

## Critères d'acceptation
- ✅ Tous les tests passent
- ✅ Code ≤ 200 lignes par fichier
- ✅ Interface abstraite permet future migration SQLite sans changer le reste
- ✅ Fichiers JSON initialisés correctement

## Notes
- Utiliser `json` standard library
- Pour locks : `fcntl` (Linux) ou `msvcrt` (Windows) ou simple retry
- Pas de dépendances externes pour cette mission

