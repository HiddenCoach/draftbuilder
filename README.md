# LoL Draft Lab — Draft Room PRO

Application Streamlit de préparation de drafts League of Legends pour le coaching compétitif.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Fonctionnalités

- 40 drafts et 8 archétypes avec bans, plans early/mid/late, win conditions et pivots.
- Analyse approfondie, checklist et notes de scrim.
- Draft Room PRO : **10 bans et 10 picks** dans l'ordre compétitif (Blue / Red), verrouillage progressif, annulation, nouvelle simulation et export JSON.
- Chronomètre de pick/ban configurable, avec pause et reprise.
- Portraits de champions récupérés depuis **Riot Data Dragon** ; connexion internet requise pour les images et le catalogue complet.
- Suggestions de bans anti-counter recalculées à chaque action, avec exclusion des picks/bans verrouillés et de tous les champions de notre draft de départ.
- Signalement des contres adverses déjà sélectionnés et pivots par rôle encore disponibles.
- Scouting, bibliothèque personnalisée et export/import de sauvegarde.

## Limites

Les suggestions de counter sont des **heuristiques de coaching** (pas des statistiques live ni une optimisation garantie). Elles sont recalculées à partir des champions de la composition initiale et des slots déjà joués. L'application ne peut pas deviner les rôles des picks adverses ni générer automatiquement une draft parfaite.

Les données Worlds/LCK du playbook sont des inspirations tactiques ; aucune synchronisation automatique des statistiques professionnelles n'est incluse. Les données de session Streamlit sont à exporter en JSON pour les conserver durablement. Le chronomètre fonctionne pendant que l'onglet de l'application est ouvert.

## Déploiement

Pousser `app.py`, `draft_room_pro.py`, `drafts.json` et `requirements.txt` sur GitHub, puis créer une application sur https://share.streamlit.io avec `app.py` comme fichier principal.

## V3 — Remplacements automatiques après un ban adverse
Dans Draft Room PRO, si l'équipe adverse bannit un champion prévu dans la composition, une alerte affiche le rôle concerné et jusqu'à cinq remplaçants disponibles. La meilleure alternative est présélectionnée et proposée automatiquement dans les prochains picks de notre équipe. Il est possible de sélectionner puis confirmer une autre alternative. Les suggestions respectent le rôle, les champions déjà pick/ban, les synergies simples et les pools de pivots de la fiche. Le plan adapté est inclus dans l'export JSON. Les recommandations restent heuristiques et ne reposent pas sur des winrates live.

## V4 — Galerie de champions et interface modernisée

La Draft Room propose un sélecteur déroulant visuel avec recherche, portraits officiels Riot Data Dragon, filtre « suggestions prioritaires », exclusion des champions déjà pris/bannis et sélection par clic. Le Draft Builder présente également les portraits des cinq champions. Le thème sombre et les cartes ont été modernisés.

Les portraits et le catalogue complet nécessitent une connexion Internet au démarrage ; en cas d'indisponibilité de Riot Data Dragon, le sélecteur utilise un catalogue local réduit. L'outil n'a pas encore été testé de bout en bout dans un navigateur.

## V5 — Draft Room façon client LoL

- Tableau central Blue / Red avec 10 emplacements de picks, portraits officiels Riot Data Dragon et 10 bans grisés/barrés.
- Mise en évidence de l'action en cours et barre de progression (20 actions).
- Recommandations de bans anti-counter et picks prévus affichées directement sous le tableau, mises à jour à chaque action.
- Vue texte accessible en complément, interface responsive sur écran étroit.
- Les fonctions V4 sont conservées : galerie de champions, timer, annulation, pivots automatiques en cas de ban adverse et export JSON.

Les portraits et le catalogue complet nécessitent une connexion à Riot Data Dragon. Les recommandations restent des heuristiques de coaching et non des statistiques live.

## V7 — données statistiques actualisées
Dans le panneau latéral **Statistiques actualisées**, connectez un flux HTTPS JSON/CSV autorisé contenant `champion,role,games,wins` et, optionnellement, `picks,bans,total_games`. JSON : `{ "patch":"16.22", "updated_at":"2026-11-13T18:00:00Z", "source":"Fournisseur", "rows":[{"champion":"Vi","role":"JGL","games":1000,"wins":520}] }`. Les statistiques sont mises en cache 5 minutes. La Draft Room utilise les taux de victoire par rôle avec pondération de la taille d'échantillon pour réordonner les suggestions structurelles. Sans flux valide, elle garde les recommandations qualitatives. Les icônes et le catalogue de champions proviennent de Data Dragon, qui ne fournit pas les winrates. Une clé Riot API seule ne fournit pas de statistiques agrégées prêtes à l'emploi : elles doivent être calculées à partir des matchs ou obtenues auprès d'un fournisseur autorisé. L'application ne prétend pas disposer de statistiques live tant qu'un flux n'est pas connecté.

## V7 — Statistiques réelles pendant la simulation

- **Data Dragon** : liste et icônes des champions mises à jour depuis le CDN officiel.
- **Flux JSON/CSV** : importer un fournisseur autorisé avec `champion,role,games,wins` et éventuellement `picks,bans,total_games`. Le flux HTTPS est mis en cache 5 minutes et peut être actualisé manuellement.
- **Riot Match-v5** : saisir une clé Riot et des Riot IDs pour collecter un **échantillon réel** de parties classées terminées. La clé n'est pas sauvegardée dans les exports. Les statistiques ne représentent PAS l'ensemble de la méta.
- Les recommandations de picks/bans sont recalculées à chaque action de draft. Les statistiques disponibles ajustent légèrement leur score ; les règles de matchup restent le signal principal.
- **Limites** : Riot ne fournit pas de winrates globaux via Data Dragon, et Match-v5 ne fournit pas des statistiques live de champion select. Pour des statistiques professionnelles Worlds/LCK réellement mises à jour, brancher un flux autorisé adapté. Ne pas utiliser les winrates d'un petit échantillon comme des vérités globales.
- Pour un déploiement public utilisant l'API Riot, vérifier les conditions et le type de clé Riot (une clé de développement expire généralement en 24 h).
