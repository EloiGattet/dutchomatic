# Roadmap MVP — Dutch-o-matic

## Statut global
- 🟡 **En cours** : Aucune mission démarrée
- ✅ **Terminé** : 4/7 missions
- ⏳ **En attente** : 3 missions

---

## Missions (par ordre d'exécution)

### Phase 1 : Fondations
| # | Mission | Agent | Statut | Description |
|---|---------|-------|--------|-------------|
| 01 | Structure & Storage | Storage | ✅ | Abstraction storage JSON, schémas, fichiers initiaux |
| 02 | Core Logic | Core | ✅ | Sélection exercices, formatage, gestion state |

### Phase 2 : Impression
| # | Mission | Agent | Statut | Description |
|---|---------|-------|--------|-------------|
| 03 | Formatage & Impression | Printer | ✅ | Formatage ASCII, simulation puis ESC/POS |

### Phase 3 : Interface Admin
| # | Mission | Agent | Statut | Description |
|---|---------|-------|--------|-------------|
| 04 | Interface Web Admin | Admin | ✅ | Dashboard, CRUD exercices/daily, paramètres |

### Phase 4 : Intégration Hardware
| # | Mission | Agent | Statut | Description |
|---|---------|-------|--------|-------------|
| 05 | Boutons Physiques | Hardware | ⏳ | GPIO, handlers boutons Exercice/Réponses |

### Phase 5 : Progression & Polish
| # | Mission | Agent | Statut | Description |
|---|---------|-------|--------|-------------|
| 06 | Progression & XP | Progression | ⏳ | XP, level-up, seuils configurables |
| 07 | Génération IA (optionnel) | AI | ⏳ | Génération exercices via IA, fallback offline |

---

## Légende statuts
- ⏳ **En attente** : Mission non démarrée
- 🟡 **En cours** : Mission en développement
- ✅ **Terminé** : Mission complète et testée
- 🔴 **Bloqué** : Blocage identifié, besoin d'aide

---

## Notes
- Chaque mission est **testable indépendamment**
- L'ordre respecte les dépendances (storage → core → impression → admin → hardware → progression)
- Les missions peuvent être assignées à différents agents selon leur spécialité
- Mettre à jour ce fichier après chaque mission terminée

