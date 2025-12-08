# Dutch-o-matic — PRD logiciel (V1.1)

## 1) Vision & Principes
- Boîte d’exercices NL: 1 bouton **Exercice**, 1 bouton **Réponses**.
- **Offline-first** (packs JSON locaux). **Online** toujours activé pour l’admin (génération IA), avec **fallback** automatique si réseau KO.
- **Progression par niveaux** (A1→A2…), compteur de tickets, interface **web admin** locale sur le Pi.
- Python only, modules courts (**≤ 200 lignes**/fichier).

## 2) Public & Scénarios
### Utilisateur (apprenant)
- Bouton 1 → imprime un ticket **Exercice** (1–3 minis exos) + **bonus du jour** (expression / anecdote / citation).
- Bouton 2 → imprime **Réponses** du **dernier exercice**.

### Admin (toi)
- Interface web locale → gérer exercices/daily, niveaux, paramètres, stats, packs JSON, génération IA (création de nouveaux exercices), import/export.

## 3) Données & Stockage
Deux stratégies compatibles (au choix ou combinées) :

### Option A — **SQLite** (recommandé pour historique propre)
**Avantages** : requêtes simples, stats fiables, suivi d’historique, intégrité.

**Tables (proposition minimale)**
- `exercises(id TEXT PK, niveau TEXT, type TEXT, title TEXT, payload_json TEXT, tags TEXT, created_at DATETIME)`
- `daily(id TEXT PK, kind TEXT, nl TEXT, fr TEXT, extra_json TEXT, created_at DATETIME)`  
  *(kind ∈ {expression, fact, quote})*
- `prints(id INTEGER PK AUTOINCREMENT, exercise_id TEXT, printed_at DATETIME, with_answers INTEGER DEFAULT 0)`
- `state(key TEXT PK, value TEXT)`  
  *(ex: niveau_actuel, xp, compteur_total, last_exercise_id)*

**Suivi “déjà fait”** :
- via `prints` (exercices imprimés). Un exercice peut être réimprimé (révision) → pas de flag destructif.
- Dernier exercice pour le bouton Réponses = valeur `state.last_exercise_id` (ou `last_print_id`).

### Option B — **Fichiers JSON** only (simple & portable)
- Un `exercises.json` + `daily.json` + `state.json`.
- Chaque entrée d’exo **ne porte pas** un booléen “déjà imprimé” (pour éviter de salir le contenu).  
  À la place : `state.json` contient un tableau d’historique :
  ```json
  {
    "history": [
      {"exercise_id": "ex_0001", "printed_at": "2025-12-08T08:00:00Z", "with_answers": false}
    ],
    "last_exercise_id": "ex_0001",
    "niveau_actuel": "A1",
    "xp": 17,
    "compteur_total": 23
  }
  ```
- **Avantage** : lecture/édition à la main faciles, backups simples.

**Recommandation (décidée)** : **JSON-only par défaut** pour V1 (exercises.json, daily.json, state.json), avec une **couche d’abstraction `storage` obligatoire** afin de pouvoir, plus tard, remplacer le backend par SQLite sans toucher au reste du code applicatif.

## 4) Format des Exos & Daily (schémas)

### Exercice (générique)
```json
{
  "id": "ex_0001",
  "niveau": "A1",
  "type": "vocabulary",          
  "title": "Les animaux",
  "prompt": "Traduis en français (ou complète) :",
  "items": [
    { "qid": "q1", "question_nl": "de hond", "question_fr": "le ____", "answer": "chien", "img": "🐕" },
    { "qid": "q2", "question_nl": "de kat",  "question_fr": "le ____", "answer": "chat",  "img": "🐈" }
  ],
  "explanations": "‘de’ est l’article défini commun (m./f.)",
  "tags": ["animaux", "base", "A1"]
}
```

### Variantes de type
- `grammar` → `rules`, `examples`, `questions` (conjugaison, accords, ordre des mots)
- `reading` → petit `text_nl`, `questions` (V/F, trous)
- `quiz` → `mcq` (QCM), `true_false`

### Daily
```json
{
  "id": "exp_001",
  "kind": "expression",
  "nl": "Dat klopt!",
  "fr": "C’est exact !"
}
```
*(pour fact/quote, même structure avec `kind` différent et champs adaptés)*

## 5) Flux Boutons & Impression

### Bouton 1 — Exercice
1) Sélection aléatoire **pondérée** par niveau (≤ niveau actuel) et diversité de type.  
2) Sélection d’un **daily** (expression/fact/quote).  
3) Formatage ASCII + emojis (sections, règles typographiques, séparateurs).  
4) Impression ESC/POS.  
5) Mise à jour `state` : `last_exercise_id`, `compteur_total++`, `xp++`, ajout entrée d’historique.

### Bouton 2 — Réponses
1) Charger `last_exercise_id`.  
2) Générer **ticket “Corrections”** (titre, niveau, puis liste Q→A, explications).  
3) Impression.  
4) Historiser event `with_answers=1`.

## 6) Progression
- **XP**: +1 par ticket Exercice.  
- **Seuils** : `A1→A2` à N points (configurable).  
- **Niveau actuel** stocké dans `state`.  
- **Option**: ticket “Level up” automatique (félicitations + mini-bonus).

## 7) Interface Web Admin (local)
- **Dashboard** : niveau actuel, XP, compteur total, dernier exo, derniers tirages.  
- **Exercices** : liste/filtre (niveau, type, tag), détail, CRUD, import/export JSON.  
- **Daily** : CRUD des expressions/facts/quotes.  
- **IA** : formulaire (niveau, type, thème) → génération → preview → **validation** → enregistrement.  
- **Paramètres** : politique de tirage (strict ≤ niveau / mix), seuils de niveau, activer/désactiver IA (sans impacter le offline).  
- **Stats** : distribution par type/niveau, tickets/jour, taux de réponses imprimées.

## 8) Robustesse & Non-fonctionnel
- **Offline-first** pour le tirage.  
- Timeouts & retries côté IA (admin).  
- Validation stricte schema JSON (exercices/daily).  
- Démarrage au boot (systemd).  
- Logs fichier (erreurs, tirages, IA).  
- Temps bouton→impression visée < 2 s.

## 9) Évolutions possibles
- QR codes & audio, profils multiples, mode révision/spaced repetition, écran OLED, synchronisation cloud, analytics avancés.

---

# Décisions (état actuel)
1) **Stockage** : ✅ JSON-only par défaut (V1), avec abstraction `storage` compatible future migration SQLite.
2) **Politique de tirage** : à définir (strict ≤ niveau, ou mix contrôlé, ex: 70% niveau courant, 30% en-dessous).
3) **Seuils de level-up** : à paramétrer (valeurs par défaut à fixer, p.ex. A1→A2 à N XP).
4) **Réimpression** : à décider si l’admin peut forcer des sessions de révision (réimpression ciblée de certains exos).

---

*Fin du document.* (à valider)
1) **Stockage par défaut** : JSON-only avec abstraction, et bascule SQLite quand on voudra des stats longues durée ?
2) **Politique de tirage** : strict ≤ niveau, ou mix contrôlé (ex: 70% niveau courant, 30% en-dessous) ?
3) **Seuils de level-up** : valeurs par défaut (p.ex. A1→A2 à 100 XP), ajustables via Admin.
4) **Réimpression** : autoriser explicitement la réimpression d’un même exo (mode révision) dans l’admin ?

---

*Fin du document.*

