# Mission 03 : Formatage & Impression

**Agent** : Printer  
**Statut** : ✅ Terminé  
**Dépendances** : Mission 02 (Core Logic)  
**Durée estimée** : 3-4h

## Objectif
Implémenter le formatage final et l'impression ESC/POS (avec simulation pour tests).

## Livrables

### 1. Module impression (`src/printer/`)
```
src/printer/
├── __init__.py
├── escpos.py          # Commandes ESC/POS
├── printer.py         # Interface abstraite
└── simulator.py       # Simulation (écriture fichier)
```

### 2. Interface abstraite (`src/printer/printer.py`)
- `print_text(text: str) -> bool`
- `print_exercise(exercise: dict, daily: dict = None) -> bool`
- `print_answers(exercise_id: str) -> bool`
- Gestion erreurs (imprimante absente, papier, etc.)

### 3. Implémentation ESC/POS (`src/printer/escpos.py`)
- Utiliser bibliothèque `python-escpos` ou implémentation basique
- Commandes : reset, bold, underline, feed, cut
- Support USB/Serial/Network (selon imprimante disponible)
- Configuration via fichier config ou variables d'environnement

### 4. Simulateur (`src/printer/simulator.py`)
- Écriture dans fichier `output/ticket_YYYYMMDD_HHMMSS.txt`
- Permet tester sans imprimante physique
- Format identique à impression réelle

### 5. Intégration avec Core
- Utiliser `formatter.py` de Mission 02
- Appeler `state_manager` après impression réussie
- Logs (succès/échec, timestamp)

## Tests à effectuer
- [ ] Simulation impression exercice (fichier généré)
- [ ] Simulation impression réponses (fichier généré)
- [ ] Formatage respecte largeur ticket (58 chars)
- [ ] Gestion erreurs (imprimante absente)
- [ ] Logs corrects

## Critères d'acceptation
- ✅ Simulation fonctionne (fichiers générés lisibles)
- ✅ Formatage optimisé pour ticket (pas de débordement)
- ✅ Gestion erreurs robuste
- ✅ Code ≤ 200 lignes par fichier
- ✅ Compatible imprimantes ESC/POS courantes (test si matériel disponible)

## Configuration
- Fichier `config/printer.json` ou variables d'environnement :
  ```json
  {
    "type": "simulator",
    "output_dir": "output",
    "device": "/dev/usb/lp0",
    "width": 58
  }
  ```

## Notes
- Pour MVP : simulation suffit pour tests
- ESC/POS réel à tester sur Raspberry Pi avec imprimante
- Bibliothèque recommandée : `python-escpos` (si disponible) ou implémentation basique

