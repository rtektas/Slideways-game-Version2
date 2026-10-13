# SLIDEWAYS — Neon Arcade

Projet de **Resul Tektas**. Un jeu de stratégie à deux couleurs : alignez quatre symboles, en faisant glisser les rangées.

## Lancer sur Windows

1. Installer Python 3 si nécessaire.
2. Extraire **tout** le ZIP dans un nouveau dossier.
3. Ouvrir `slideways` et double-cliquer sur **LANCER_WINDOWS.bat**.

Au premier lancement, le script crée `.venv` et télécharge PyQt5 et pygame-ce (Internet nécessaire une seule fois). Les musiques sont dans le ZIP, le jeu fonctionne ensuite hors ligne.

Linux / macOS : `python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt && .venv/bin/python projet3.py`

Version terminal sans dépendances : `python3 partie2.py`

## Ce qui change dans cette version

- **Menu principal de jeu** : lancement avec écran de titre, titre découpé en bandes qui glissent, démonstration jouée en direct à droite, sélection animée, navigation clavier et souris, sons de menu, fondus entre les écrans.
- **Niveaux de difficulté** : Facile, Normal, Difficile, Expert (voir ci-dessous), choisis dans « Jouer ».
- **Aucune fenêtre pop-up** : « Comment jouer », « Crédits », « Options », la pause, la fin de partie et la confirmation pour quitter sont des écrans du jeu lui-même.
- **Comment jouer** : 4 diapositives, chacune avec une démonstration jouée sur un vrai plateau.
- **Plateau animé** : les rangées glissent, les cases apparaissent, l'alignement gagnant pulse.
- **Pause en jeu** (Échap), écran de fin de partie (Rejouer / Réglages / Menu), reprise d'une partie depuis le menu.
- **Options** : volume, effets sonores, coupure du son, vitesse de l'ordinateur, plein écran. Tout est mémorisé.
- **Effets sonores** générés par le jeu (aucun fichier à ajouter).

## Difficulté de l'IA

| Niveau | Anticipation | Erreurs volontaires |
| --- | --- | --- |
| Facile | 1 coup | 30 % de coups au hasard |
| Normal | 2 coups | 8 % |
| Difficile | 3 coups | aucune |
| Expert | 4 coups | aucune (jusqu'à 2 s de réflexion) |

L'IA utilise toujours minimax avec élagage alpha-bêta ; elle n'est pas imbattable. La réflexion se fait en arrière-plan, l'interface ne se fige pas.

## Commandes

| Touche | Action |
| --- | --- |
| ↑ ↓ / souris | Naviguer |
| ← → | Modifier un réglage |
| Entrée / clic | Valider |
| Échap | Retour, pause, ou quitter depuis le menu |
| R | Rejouer (en partie) |
| M | Couper le son |
| F11 | Plein écran |

En partie, cliquez sur la carte d'un joueur pour passer de **Humain** à **Ordinateur** (ou l'inverse).

## Règles

X commence. À chaque tour, une seule action :

1. Colorer une case vide ou adverse ; ou
2. Faire glisser une rangée d'une case à gauche ou à droite.

Une case déjà à vous ne peut pas être jouée. La case venant d'être jouée ne peut pas être immédiatement retournée. Le dernier glissement ne peut pas être immédiatement annulé. Chaque rangée reste entre −3 et +3 cases de sa position initiale.

**Quatre symboles alignés (ligne, colonne, diagonale) gagnent**, en tenant compte de la position réelle des rangées. Deux couleurs gagnantes en même temps : égalité. Égalité aussi après trois répétitions d'une même position, 300 coups, ou si aucun coup n'est disponible.

## Fichiers

- `projet3.py` : fenêtre, décor animé, enchaînement des écrans, réglages.
- `screens.py` : menus, intro, « Comment jouer », crédits, fondu.
- `board_view.py` : plateau dessiné et animé.
- `game_screen.py` : écran de partie (bandeau des joueurs).
- `menu_model.py`, `rules_data.py` : logique des menus et contenu du tutoriel (sans Qt).
- `controller.py` : tours, joueurs humains / IA, calcul en arrière-plan.
- `partie2.py` : règles, IA, niveaux, version terminal.
- `audio.py`, `theme.py` : sons et style.
- `assets/music/` : deux pistes OGG (Empacotatron, Fupi, CC0 — voir `CREDITS.md`).
- `original/` : scripts et images d'origine, et l'ancienne interface (`projet3_arcade_v1.py`).
- `tests/` : tests automatisés.

## Tests

```bash
python -m unittest discover -s tests -v
```

`test_game.py` et `test_menu_model.py` n'ont besoin d'aucune bibliothèque. `test_ui.py` exige PyQt5 et pygame-ce.

## Vérifications faites

- Moteur, niveaux, scripts du tutoriel et modèle de menu : tests réussis (20).
- Toute l'interface a été exécutée (navigation, partie complète à chaque niveau, pause, reprise, fin de partie, options) contre une maquette de PyQt5, sans écran réel.
- **L'interface n'a pas encore été lancée avec le vrai PyQt5 ni vue à l'écran**, et le son n'a pas été écouté. Si quelque chose s'affiche mal ou plante, le message d'erreur dans la console suffit pour corriger.
