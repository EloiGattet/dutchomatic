# Guide de gestion du serveur

## Logging

Le serveur enregistre automatiquement tous les logs dans `logs/dutchomatic.log` avec rotation automatique (10MB par fichier, 5 fichiers de backup).

Les logs incluent :
- Toutes les requêtes HTTP (méthode, chemin, IP, statut)
- Toutes les erreurs avec stack traces
- Les opérations importantes (création, modification, suppression d'exercices)

### Consulter les logs

```bash
# Voir les dernières lignes
tail -f logs/dutchomatic.log

# Voir les erreurs uniquement
grep ERROR logs/dutchomatic.log

# Voir les dernières 50 lignes
tail -n 50 logs/dutchomatic.log
```

## Redémarrage du serveur

### Méthode 1 : Script de redémarrage direct

```bash
# Redémarrer le serveur
./scripts/restart.sh restart

# Démarrer le serveur
./scripts/restart.sh start

# Arrêter le serveur
./scripts/restart.sh stop

# Vérifier le statut
./scripts/restart.sh status
```

### Méthode 2 : Système "touch" (comme Node.js)

1. Démarrer le watcher dans un terminal séparé :
```bash
./scripts/watch_restart.sh
```

2. Pour redémarrer, touchez simplement le fichier :
```bash
./scripts/touch_restart.sh
# ou simplement
touch .restart
```

Le watcher détectera automatiquement le changement et redémarrera le serveur.

### Méthode 3 : Redémarrage manuel

```bash
# Trouver le processus
ps aux | grep run_server.py

# Arrêter le processus
kill <PID>

# Redémarrer
python3 run_server.py
```

## Variables d'environnement

- `PORT` : Port du serveur (défaut: 5000)
- `HOST` : Host du serveur (défaut: 0.0.0.0)
- `FLASK_DEBUG` : Active les logs console (défaut: False)
- `SECRET_KEY` : Clé secrète Flask (défaut: dev-secret-key-change-in-production)

## En production (systemd)

Si le serveur est géré par systemd :

```bash
# Redémarrer
sudo systemctl restart dutchomatic

# Voir les logs
sudo journalctl -u dutchomatic -f

# Vérifier le statut
sudo systemctl status dutchomatic
```
