# LoL Draft Lab

Application Streamlit de préparation de drafts compétitives.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Déposez `app.py`, `drafts.json` et `requirements.txt` dans un dépôt GitHub, puis créez une application sur https://share.streamlit.io avec `app.py` comme fichier principal.

## Fonctionnalités

- 40 drafts de coaching / 8 archétypes
- Bans contre la composition (aucun auto-ban), justifications et contrôles de cohérence
- Plans de jeu early / mid / late et conditions de victoire
- Simulation des 10 picks, des deux phases de bans, avec édition libre
- Analyse des counters et pivots par rôle
- Scouting d'équipe adverse et notes
- Bibliothèque personnalisée, import/export JSON et fiche Markdown
- Données locales sans connexion Riot ; statistiques professionnelles non revendiquées

Les modifications de session sont exportables via JSON. Streamlit Cloud n'offre pas de stockage local persistant garanti entre redémarrages.
