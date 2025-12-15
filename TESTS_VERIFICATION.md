# Liste de tests pour vérifier les améliorations

## Tests recommandés pour vérifier le travail

### Test 1 : Titres encadrés améliorés (priorité)
```bash
python tests/test_miniescpos.py --test 13
```
**Vérifie :**
- Nouveaux titres encadrés avec `print_boxed_title()` (séparateurs doubles visibles)
- Ancien format `_format_box()` amélioré avec séparateurs
- Visibilité des encadrements

### Test 2 : Accents avec Roboto 48px
```bash
python tests/test_miniescpos.py --test 8
```
**Vérifie :**
- Accents français avec Roboto-Bold en 48px
- Rendu des caractères accentués (é, è, à, ç, É, etc.)

### Test 3 : Support des emojis (économise le papier)
```bash
python tests/test_miniescpos.py --test 12
```
**Vérifie :**
- Détection automatique des fonts emoji
- Liste des emojis supportés/non supportés
- Affiche un résumé sans tout imprimer

### Test 4 : Emojis avec rendu visuel
```bash
python tests/test_miniescpos.py --test 9,11
```
**Vérifie :**
- Rendu visuel des emojis avec différentes fonts
- Test spécifique NotoEmoji (sans drapeaux)

### Test 5 : Rendu général et qualité
```bash
python tests/test_miniescpos.py --test 2,4,8,10
```
**Vérifie :**
- Séparateurs
- Fonts internes A et B
- Font custom Roboto
- Helpers haut niveau

## Test complet (tous les tests sauf ceux qui impriment beaucoup)
```bash
python tests/test_miniescpos.py --test 2,4,8,9,10,11,12,13
```

## Test minimal (essentiel pour vérifier les améliorations)
```bash
python tests/test_miniescpos.py --test 8,12,13
```
**Couvre :**
- Accents Roboto 48px (test 8)
- Support emojis sans impression (test 12)
- Titres encadrés améliorés (test 13)

## Notes
- Le test 12 (emoji_support_check) n'imprime qu'une seule ligne de résumé, très économique
- Le test 13 (format_box) teste les deux méthodes (nouvelle et ancienne améliorée)
- Le test 8 (custom_font) vérifie que les accents fonctionnent bien avec Roboto en 48px

