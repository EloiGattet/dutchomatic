# Mission 04 : Interface Web Admin

**Agent** : Admin  
**Statut** : ⏳ En attente  
**Dépendances** : Mission 01 (Storage), Mission 02 (Core)  
**Durée estimée** : 6-8h

## Objectif
Créer l'interface web admin locale pour gérer exercices, daily, paramètres et stats.

## Livrables

### 1. Framework web
- **Choix** : Flask (léger, Python natif) ou FastAPI (moderne, async)
- **Recommandation** : Flask pour simplicité MVP
- Structure :
```
src/web/
├── __init__.py
├── app.py              # Application Flask
├── routes/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── exercises.py
│   ├── daily.py
│   ├── settings.py
│   └── stats.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── exercises.html
│   ├── daily.html
│   └── settings.html
└── static/
    └── style.css
```

### 2. Dashboard (`/`)
- Affichage : niveau actuel, XP, compteur total, dernier exercice, derniers tirages (10 derniers)
- Graphique simple (optionnel) : XP sur 7 jours

### 3. Gestion Exercices (`/exercices`)
- Liste avec filtres (niveau, type, tag)
- Détail exercice (modal ou page dédiée)
- CRUD : créer, modifier, supprimer
- Import/export JSON (boutons)
- Validation côté serveur (schémas)

### 4. Gestion Daily (`/daily`)
- Liste avec filtre par kind (expression/fact/quote)
- CRUD complet
- Import/export JSON

### 5. Paramètres (`/settings`)
- Politique de tirage (strict / mix avec %)
- Seuils de level-up (A1→A2, A2→B1, etc.)
- Activation/désactivation IA (sans impacter offline)
- Configuration imprimante (type, device)

### 6. Stats (`/stats`)
- Distribution par type/niveau (graphique simple)
- Tickets/jour (7 derniers jours)
- Taux de réponses imprimées (%)

### 7. API REST (optionnel pour MVP)
- Endpoints JSON pour futures intégrations
- `/api/v1/exercises`, `/api/v1/daily`, `/api/v1/state`

## Tests à effectuer
- [ ] Dashboard affiche données correctes
- [ ] CRUD exercices fonctionne (création, modification, suppression)
- [ ] CRUD daily fonctionne
- [ ] Filtres fonctionnent
- [ ] Import/export JSON fonctionne
- [ ] Paramètres sauvegardés
- [ ] Stats calculées correctement

## Critères d'acceptation
- ✅ Interface accessible sur `http://localhost:5000` (ou port configuré)
- ✅ Toutes les fonctionnalités CRUD opérationnelles
- ✅ Validation données côté serveur
- ✅ Design simple mais lisible (CSS basique)
- ✅ Code ≤ 200 lignes par fichier (routes séparées)

## Configuration
- Port configurable (défaut : 5000)
- Host : `0.0.0.0` pour accès réseau local (Raspberry Pi)
- Pas d'authentification pour MVP (admin local uniquement)

## Notes
- Interface minimaliste mais fonctionnelle
- Pas besoin de framework JS lourd (HTML/CSS/vanilla JS si besoin)
- Templates Jinja2 (Flask) ou équivalent

