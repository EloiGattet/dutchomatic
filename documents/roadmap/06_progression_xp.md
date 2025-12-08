# Mission 06 : Progression & XP

**Agent** : Progression  
**Statut** : ⏳ En attente  
**Dépendances** : Mission 02 (Core), Mission 04 (Admin)  
**Durée estimée** : 2-3h

## Objectif
Implémenter le système de progression (XP, level-up, seuils configurables).

## Livrables

### 1. Module progression (`src/progression/`)
```
src/progression/
├── __init__.py
├── xp_manager.py      # Gestion XP et level-up
└── thresholds.py      # Seuils configurables
```

### 2. Gestion XP (`src/progression/xp_manager.py`)
- `add_xp(amount: int = 1) -> dict`
  - Incrémente XP
  - Vérifie level-up
  - Retourne `{"leveled_up": bool, "new_level": str, "xp": int}`
- `check_level_up() -> bool`
  - Compare XP actuel avec seuil niveau suivant
  - Met à jour `niveau_actuel` si seuil atteint

### 3. Seuils configurables (`src/progression/thresholds.py`)
- Fichier `config/levels.json` :
  ```json
  {
    "A1": {"min_xp": 0, "next": "A2"},
    "A2": {"min_xp": 100, "next": "B1"},
    "B1": {"min_xp": 250, "next": "B2"},
    "B2": {"min_xp": 500, "next": null}
  }
  ```
- Chargement depuis state ou fichier config
- Édition via interface admin

### 4. Ticket Level-up (optionnel)
- `format_level_up(new_level: str) -> str`
- Impression automatique après level-up
- Félicitations + mini-bonus (daily spécial)

### 5. Intégration
- Appelé depuis `state_manager.print_exercise()`
- Affichage dans dashboard admin
- Mise à jour state après level-up

## Tests à effectuer
- [ ] XP incrémenté correctement
- [ ] Level-up déclenché au bon seuil
- [ ] Seuils configurables (lecture/écriture)
- [ ] Ticket level-up généré (si implémenté)
- [ ] Gestion cas limites (niveau max atteint)

## Critères d'acceptation
- ✅ XP et level-up fonctionnent correctement
- ✅ Seuils configurables via admin
- ✅ State mis à jour après level-up
- ✅ Code ≤ 200 lignes par fichier
- ✅ Ticket level-up optionnel (bonus)

## Notes
- Seuils par défaut : A1→A2 à 100 XP (ajustable)
- Niveau max : B2 (ou configurable)
- Option ticket level-up : à décider si inclus dans MVP

