"""Contenu du tutoriel « Comment jouer » : textes et parties scriptées (sans Qt)."""

RULES_SLIDES = [
    {'title': 'Le but du jeu',
     'text': ["Alignez quatre symboles de votre couleur : en ligne, en colonne ou en diagonale.",
              "X commence. À chaque tour, vous faites une seule action : colorer une case ou faire glisser une rangée."],
     'script': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1']},
    {'title': 'Colorer une case',
     'text': ["Touchez une case vide ou adverse pour la colorer à votre couleur.",
              "Une case déjà à vous ne peut pas être rejouée, et vous ne pouvez pas reprendre aussitôt la case qui vient d'être jouée."],
     'script': ['B2', 'A1', 'C3', 'B2']},
    {'title': 'Faire glisser une rangée',
     'text': ["Les flèches sur les côtés déplacent une rangée entière d'une case, à gauche ou à droite.",
              "Une rangée s'éloigne d'au plus trois cases de sa position de départ, et le glissement précédent ne peut pas être annulé tout de suite."],
     'script': ['A1', '1+', 'C2', '1+', '2-', '1+']},
    {'title': 'Les rangées comptent',
     'text': ["Les cases restent solidaires de leur rangée : en glissant, vous créez des colonnes et des diagonales.",
              "Deux couleurs gagnantes en même temps, trois répétitions d'une même position ou 300 coups : égalité."],
     'script': ['A1', 'D1', 'B2', 'D3', '2-', 'C4', 'A3', 'D2', 'A4']},
]
