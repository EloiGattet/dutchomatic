# Mission 02 : Core Logic

**Agent** : Core  
**Statut** : ✅ Terminé  
**Dépendances** : Mission 01 (Structure & Storage)  
**Durée estimée** : 3-4h

## Objectif
Implémenter la logique métier : sélection d'exercices, formatage, gestion de la progression.

## Livrables

### 1. Sélection d'exercices (`src/core/selector.py`)
- `select_exercise(niveau_actuel: str, policy: str = "strict") -> dict`
  - **Politique "strict"** : uniquement exercices ≤ niveau actuel
  - **Politique "mix"** : 70% niveau actuel, 30% niveaux inférieurs (configurable)
- Pondération par type (diversité)
- Exclusion exercices récemment imprimés (optionnel, via history)
- Retourne `None` si aucun exercice disponible

### 2. Sélection daily (`src/core/daily_selector.py`)
- `select_daily() -> dict`
- Sélection aléatoire parmi tous les daily disponibles
- Gestion si aucun daily disponible

### 3. Formatage exercice (`src/core/formatter.py`)
- `format_exercise(exercise: dict, daily: dict = None) -> str`
- Format ASCII avec emojis
- Sections : titre, niveau, prompt, items (questions), daily (si fourni)
- Règles typographiques (séparateurs, alignement)
- Exemple sortie :
  ```
  ╔═══════════════════════════════╗
  ║  EXERCICE — Les animaux (A1)  ║
  ╚═══════════════════════════════╝
  
  Traduis en français (ou complète) :
  
  1. de hond 🐕
     le ____
  
  2. de kat 🐈
     le ____
  
  ───────────────────────────────
  💡 BONUS DU JOUR
  Dat klopt! → C'est exact !
  ───────────────────────────────
  ```

### 4. Formatage réponses (`src/core/formatter.py`)
- `format_answers(exercise: dict) -> str`
- Format "Corrections" avec Q→A et explications

### 5. Gestion state (`src/core/state_manager.py`)
- `print_exercise(exercise_id: str) -> bool`
  - Met à jour `last_exercise_id`
  - Incrémente `compteur_total`
  - Incrémente `xp`
  - Ajoute entrée dans `history`
- `print_answers(exercise_id: str) -> bool`
  - Ajoute entrée dans `history` avec `with_answers=1`

### 6. Structure
```
src/core/
├── __init__.py
├── selector.py
├── daily_selector.py
├── formatter.py
└── state_manager.py
```

## Tests à effectuer
- [ ] Sélection exercice (strict ≤ niveau)
- [ ] Sélection exercice (mix 70/30)
- [ ] Sélection daily aléatoire
- [ ] Formatage exercice (avec/sans daily)
- [ ] Formatage réponses
- [ ] Mise à jour state après impression
- [ ] Gestion cas limites (aucun exercice, aucun daily)

## Critères d'acceptation
- ✅ Sélection respecte politique configurée
- ✅ Formatage ASCII lisible et structuré
- ✅ State mis à jour correctement après chaque action
- ✅ Code ≤ 200 lignes par fichier
- ✅ Gestion erreurs (aucun exercice disponible, etc.)

## Notes
- Politique de tirage configurable via state ou fichier config séparé
- Formatage doit être optimisé pour impression ticket (largeur ~58 caractères typique)

