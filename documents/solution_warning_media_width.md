# Solution : Warning "media.width.pixel" — python-escpos

## Problème

Lors de l'utilisation de `python-escpos`, un warning apparaît :

```
The media.width.pixel field of the printer profile is not set. 
The center flag will have no effect.
```

Ce warning indique que le profil d'imprimante ne connaît pas la largeur en pixels du média, ce qui empêche le centrage automatique de fonctionner.

## Cause

Le module `python-escpos` utilise un système de "profils" d'imprimante pour connaître les caractéristiques du média (largeur, hauteur, etc.). Si le champ `media.width.pixels` n'est pas renseigné dans le profil, le centrage ne peut pas fonctionner car le module ne sait pas combien de pixels fait la largeur.

## Solution

### Spécifications de l'imprimante

- **Résolution** : 8 dots/mm
- **Largeur papier** : 57.5 ±0.5mm
- **Largeur utile** : 384 pixels (8 dots/mm × 48mm)

### Code de patch

À appliquer **immédiatement après** la création de l'objet `Serial` :

```python
from escpos.printer import Serial

# Création de l'imprimante
printer = Serial(
    devfile='/dev/serial0',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

# Patch du profil pour éviter le warning et permettre le centrage
try:
    if hasattr(printer, "profile") and hasattr(printer.profile, "media"):
        printer.profile.media.setdefault("width", {})
        printer.profile.media["width"]["pixels"] = 384  # largeur utile
        printer.profile.media["width"]["mm"] = 48       # largeur en mm
except Exception as e:
    # Silently fail if patch doesn't work
    pass
```

### Où appliquer la solution

#### ✅ Dans la codebase principale

**Fichier** : `src/printer/escpos.py`  
**Méthode** : `_init_printer()`

Le patch est déjà appliqué automatiquement lors de l'initialisation de l'imprimante.

#### ✅ Dans les scripts de test

**Fichiers** :
- `test_vitesse_imprimante.py` ✅ (déjà appliqué)
- `test_reglages_imprimante.py` ✅ (déjà appliqué)

#### ✅ Pour tout nouveau script

Copier-coller le code de patch après la création de l'objet `Serial`.

## Résultat

- ✅ Le warning disparaît
- ✅ Le centrage automatique fonctionne correctement
- ✅ Pas d'impact sur les performances

## Références

- Rapport complet des essais : `documents/rapport_essais_impression.md`
- Section 1.1 : Problèmes initiaux et solutions

---

*Document créé le : Décembre 2024*  
*Basé sur les essais d'impression Dutch-o-matic*

