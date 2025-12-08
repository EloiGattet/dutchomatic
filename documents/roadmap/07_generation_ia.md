# Mission 07 : Génération IA (Optionnel)

**Agent** : AI  
**Statut** : ⏳ En attente  
**Dépendances** : Mission 01 (Storage), Mission 04 (Admin)  
**Durée estimée** : 4-5h

## Objectif
Implémenter la génération d'exercices via IA avec fallback offline.

## Livrables

### 1. Module IA (`src/ai/`)
```
src/ai/
├── __init__.py
├── generator.py        # Génération via API IA
├── fallback.py         # Templates offline
└── validator.py        # Validation exercice généré
```

### 2. Génération IA (`src/ai/generator.py`)
- `generate_exercise(niveau: str, type: str, theme: str) -> dict`
- API : OpenAI, Anthropic, ou autre (configurable)
- Prompt structuré selon schéma exercice
- Retry avec timeout (3 tentatives, 5s timeout)
- Gestion erreurs (réseau KO, quota, etc.)

### 3. Fallback offline (`src/ai/fallback.py`)
- Templates d'exercices par type/niveau
- Sélection aléatoire si IA indisponible
- Message à l'admin : "IA indisponible, exercice généré depuis template"

### 4. Validation (`src/ai/validator.py`)
- Validation schéma exercice généré
- Rejet si invalide (retry ou fallback)

### 5. Interface admin
- Formulaire : niveau, type, thème
- Bouton "Générer"
- Preview exercice généré
- Boutons "Valider" / "Rejeter"
- Si validé : enregistrement dans storage

### 6. Configuration
- Fichier `config/ai.json` :
  ```json
  {
    "enabled": true,
    "provider": "openai",
    "api_key": "env:OPENAI_API_KEY",
    "model": "gpt-4",
    "timeout": 5,
    "retries": 3
  }
  ```

## Tests à effectuer
- [ ] Génération IA fonctionne (si API configurée)
- [ ] Fallback offline fonctionne (si réseau KO)
- [ ] Validation exercice généré
- [ ] Preview et validation dans admin
- [ ] Gestion erreurs (timeout, quota, etc.)

## Critères d'acceptation
- ✅ Génération IA opérationnelle (si API configurée)
- ✅ Fallback offline fonctionne
- ✅ Validation stricte
- ✅ Interface admin intuitive
- ✅ Code ≤ 200 lignes par fichier
- ✅ Offline-first : système fonctionne sans IA

## Notes
- **Optionnel pour MVP** : peut être reporté après MVP
- Fallback obligatoire : système doit fonctionner sans IA
- API key via variable d'environnement (sécurité)
- Coût API à considérer (limites, quotas)

## Décision MVP
- [ ] Inclure dans MVP
- [ ] Reporter après MVP

