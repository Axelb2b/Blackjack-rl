# Publier le projet sur GitHub (depuis un Mac)

Le dossier livré est **prêt à être publié**, mais il n'a pas été envoyé sur ton compte GitHub : aucune connexion à ton dépôt n'était autorisée dans cette session.

## Méthode Terminal (macOS)

1. Décompresse l'archive ZIP. Ouvre Terminal puis déplace-toi dans le dossier extrait (tu peux taper `cd ` et glisser-déposer le dossier dans Terminal).
2. Sur github.com, crée un dépôt vide (par exemple `blackjack-reinforcement-learning`), **sans ajouter de README ou de `.gitignore`** car ils sont déjà présents.
3. Exécute les commandes suivantes depuis le dossier contenant `README.md` :

```bash
# Vérification et préparation
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q

git init -b main
git add .
git status --short
# Inspecte la liste avant de confirmer : pas de .venv, BJEngine, .DS_Store.
git commit -m "Publish blackjack simulation and reinforcement learning portfolio"

# Remplace l'URL par celle du dépôt vide créé sur TON compte GitHub.
git remote add origin https://github.com/TON-COMPTE/blackjack-reinforcement-learning.git
git push -u origin main
```

Pour éviter de saisir un mot de passe GitHub dans Terminal, utilise un authentificateur compatible (par exemple `gh auth login` si GitHub CLI est installé), une clé SSH ou un jeton d'accès personnel selon ta configuration.

Si ce dossier est **déjà** un dépôt Git, ne lance pas `git init` et n'ajoute pas aveuglément une seconde origine : vérifie d'abord `git remote -v` et fais un commit sur la branche souhaitée.

## Contrôles après push

- Le README s'affiche correctement, avec le graphique.
- `Actions` indique l'exécution des tests ; **2 xfail** sont documentés, pas des erreurs masquées.
- `.venv`, `BJEngine` et les caches ne figurent pas dans le dépôt.
- Tu peux exécuter le benchmark avec `python3 -m scripts.benchmark --rounds 10000 --seed 42`.
- Vérifie la confidentialité de toute donnée ajoutée ultérieurement et choisis une licence si tu souhaites autoriser la réutilisation par des tiers.
