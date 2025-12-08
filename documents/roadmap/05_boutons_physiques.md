# Mission 05 : Boutons Physiques

**Agent** : Hardware  
**Statut** : ⏳ En attente  
**Dépendances** : Mission 03 (Impression), Mission 02 (Core)  
**Durée estimée** : 3-4h

## Objectif
Implémenter la gestion des boutons physiques GPIO sur Raspberry Pi.

## Livrables

### 1. Module GPIO (`src/hardware/`)
```
src/hardware/
├── __init__.py
├── buttons.py          # Gestion boutons GPIO
└── simulator.py        # Simulation (clavier/clics)
```

### 2. Gestion boutons (`src/hardware/buttons.py`)
- `ButtonHandler` class
- Bouton 1 (GPIO X) → `print_exercise()`
- Bouton 2 (GPIO Y) → `print_answers()`
- Debounce (éviter doubles déclenchements)
- Gestion erreurs (GPIO indisponible, permissions)

### 3. Intégration
- Appel `printer.print_exercise()` et `printer.print_answers()`
- Appel `state_manager` pour mise à jour
- Logs (bouton pressé, timestamp, succès/échec)

### 4. Simulateur (`src/hardware/simulator.py`)
- Mode simulation (pas de GPIO)
- Clavier : `E` pour Exercice, `R` pour Réponses
- Ou interface simple (boutons web/cli)

### 5. Configuration
- Fichier `config/hardware.json` :
  ```json
  {
    "mode": "gpio",
    "button_exercise": 17,
    "button_answers": 27,
    "debounce_ms": 200
  }
  ```

## Tests à effectuer
- [ ] Simulation boutons (clavier)
- [ ] Debounce fonctionne (pas de doubles déclenchements)
- [ ] Intégration avec printer et state_manager
- [ ] Gestion erreurs (GPIO indisponible)
- [ ] Logs corrects

## Critères d'acceptation
- ✅ Simulation fonctionne (tests sans Raspberry Pi)
- ✅ Debounce implémenté
- ✅ Intégration complète (bouton → impression → state)
- ✅ Code ≤ 200 lignes par fichier
- ✅ Compatible Raspberry Pi (test si matériel disponible)

## Bibliothèque
- `RPi.GPIO` pour Raspberry Pi
- Fallback simulation si bibliothèque absente

## Notes
- Pour MVP : simulation suffit pour tests
- GPIO réel à tester sur Raspberry Pi
- Gestion permissions (sudo ou groupe gpio)

