# Slideways — Neon Arcade

**Slideways** est un jeu de stratégie local où les joueurs colorent des cases et déplacent des rangées pour aligner quatre symboles. Ce projet de **Resul Tektas** comprend un mode solo contre l'IA, un duel local et un mode spectateur.

![Slideways — menu principal](screenshots/menu.png)

## Captures d’écran

### Menu principal

Depuis le menu, lance une partie, consulte les règles, ouvre les options ou reprends ta partie. Le plateau en perspective et le fond animé sont dessinés directement par l'interface.

### Partie en cours

![Slideways — partie en cours](screenshots/gameplay.png)

## Lancer le jeu

### Windows

1. Installe **Python 3** si ce n'est pas déjà fait.
2. Télécharge le dépôt et extrais le ZIP.
3. Ouvre le dossier `slideways`.
4. Double-clique sur `LANCER_WINDOWS.bat`.

Au premier lancement, le script crée un environnement Python et installe PyQt5 et pygame-ce. Une connexion Internet est nécessaire uniquement pour cette installation. Les musiques sont incluses dans le projet.

Pour le lancer depuis PowerShell, dans le dossier `slideways` :

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe projet3.py
```

### Linux ou macOS

Python 3, `venv` et un environnement graphique sont nécessaires :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python projet3.py
```

### Version terminal

Le moteur du jeu peut aussi se lancer sans l’interface graphique :

```bash
python3 partie2.py
```

Sous Windows, remplace `python3` par `py`.

## Modes de jeu et options

- **Solo** : joue contre l’IA.
- **Duel local** : deux joueurs utilisent le même ordinateur.
- **Démo** : l’IA joue contre elle-même.
- Choisis la difficulté **Facile**, **Normal**, **Difficile** ou **Expert** avant de jouer. Tu peux aussi la changer dans les options ou pendant la partie.
- Le délai règle le temps d’attente avant que l’IA commence son calcul.
- La musique, le volume et le mode muet se règlent depuis la barre du bas.
- `Échap` ouvre le menu de pause ou revient à l’écran précédent ; `F11` bascule le plein écran.

## Règles

X commence. À chaque tour, tu peux soit colorer une case vide ou adverse, soit déplacer une rangée d’une case vers la gauche ou la droite à l’aide des flèches.

Aligne quatre symboles de ta couleur à l’horizontale, à la verticale ou en diagonale pour gagner. Les cases restent liées à leur rangée lorsqu’elle glisse. Une rangée ne peut pas dépasser trois cases de déplacement dans chaque direction.

Tu ne peux pas rejouer immédiatement la case du coup précédent ni annuler tout de suite le dernier déplacement de rangée. Si les deux couleurs gagnent au même tour, la partie est nulle.

## Musique et crédits

Le menu et les parties utilisent deux pistes d’**Empacotatron**, composé par **Fupi** et publié sous **CC0 1.0** sur OpenGameArt. Les fichiers et les crédits détaillés sont fournis dans `assets/music/` et [`CREDITS.md`](CREDITS.md).

## Tests

Les tests couvrent les règles, les limites de déplacement, les alignements, l’IA et ses difficultés. Les tests d’interface nécessitent les dépendances du fichier `requirements.txt`.

```bash
python -m unittest discover -s tests -v
```

## Dossiers principaux

- `projet3.py` : interface graphique et menu.
- `partie2.py` : règles, IA et version terminal.
- `controller.py` : tours de jeu et calcul de l’IA.
- `audio.py` : lecture des musiques.
- `assets/music/` : musiques du menu et de la partie.
- `screenshots/` : captures d’écran du jeu.
- `original/` : scripts et images d’origine.
