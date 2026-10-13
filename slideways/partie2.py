"""Slideways — projet original de Resul Tektas, moteur corrigé.
Les coordonnées A–D suivent les cases de leur rangée quand elle glisse.
"""
import random
from collections import Counter

# Niveaux de l'IA : profondeur = nombre de demi-coups regardés à l'avance,
# hasard = probabilité de jouer un coup au hasard au lieu du meilleur coup trouvé.
DIFFICULTES = [
    {'nom': 'Facile', 'profondeur': 1, 'hasard': 0.30,
     'desc': "Joue vite, regarde un seul coup à l'avance et se trompe souvent."},
    {'nom': 'Normal', 'profondeur': 2, 'hasard': 0.08,
     'desc': "Voit votre réponse immédiate et bloque les menaces évidentes, mais lui arrive de rater un coup."},
    {'nom': 'Difficile', 'profondeur': 3, 'hasard': 0.0,
     'desc': "Anticipe trois coups. Punit les erreurs de placement."},
    {'nom': 'Expert', 'profondeur': 4, 'hasard': 0.0,
     'desc': "Anticipe quatre coups. Peut réfléchir près de deux secondes."},
]


def nouveau_plateau():
    return [[0] * 4 for _ in range(4)]


def indice_plateau(coup):
    return [int(coup[1]) - 1, 'ABCD'.index(coup[0])]


def coup_possible(plateau, decalage, joueur, dernier_coup=''):
    moves = []
    for r in range(4):
        for c in range(4):
            move = f'{"ABCD"[c]}{r+1}'
            if plateau[r][c] != joueur and move != dernier_coup:
                moves.append(move)
        for direction, step in [('-', -1), ('+', 1)]:
            move = f'{r+1}{direction}'
            inverse = f'{r+1}{"+" if direction == "-" else "-"}'
            if -3 <= decalage[r] + step <= 3 and dernier_coup != inverse:
                moves.append(move)
    return moves


def coup_AI(plateau, decalage, joueur, coup):
    """Applique un coup déjà validé."""
    if coup[0] in '1234':
        decalage[int(coup[0])-1] += 1 if coup[1] == '+' else -1
    else:
        r, c = indice_plateau(coup)
        plateau[r][c] = joueur


def lignes(plateau, decalage):
    cells = {(r, c + decalage[r]): plateau[r][c]
             for r in range(4) for c in range(4)}
    result = [row[:] for row in plateau]
    for col in range(-3, 7):
        for slope in [-1, 0, 1]:
            coords = [(r, col + slope*r) for r in range(4)]
            if all(p in cells for p in coords):
                result.append([cells[p] for p in coords])
    return result


def fin(plateau, decalage):
    winners = {line[0] for line in lignes(plateau, decalage)
               if line[0] and len(set(line)) == 1}
    if len(winners) == 2:
        return 'égalité'
    return next(iter(winners), 0)


def cases_gagnantes(plateau, decalage):
    """Cases (rangée, colonne d'origine) qui font partie d'un alignement gagnant."""
    cells = {(r, c + decalage[r]): (r, c) for r in range(4) for c in range(4)}
    found = set()
    for r in range(4):
        if plateau[r][0] and len(set(plateau[r])) == 1:
            found.update((r, c) for c in range(4))
    for col in range(-3, 7):
        for slope in [-1, 0, 1]:
            coords = [(r, col + slope * r) for r in range(4)]
            if all(p in cells for p in coords):
                origins = [cells[p] for p in coords]
                values = [plateau[r][c] for r, c in origins]
                if values[0] and len(set(values)) == 1:
                    found.update(origins)
    return found


def choisir_coup_niveau(plateau, decalage, joueur, dernier_coup='', niveau=1):
    """Choisit un coup selon l'indice de difficulté (0 = Facile ... 3 = Expert)."""
    niveau = max(0, min(len(DIFFICULTES) - 1, int(niveau)))
    reglage = DIFFICULTES[niveau]
    return choisir_coup(plateau, decalage, joueur, dernier_coup,
                        profondeur=reglage['profondeur'], hasard=reglage['hasard'])


def choisir_coup(plateau, decalage, joueur, dernier_coup='', profondeur=2, hasard=0.0):
    """Minimax alpha-bêta, pour l'un ou l'autre joueur."""
    root = joueur
    def score(board, shifts):
        total = 0
        for line in lignes(board, shifts):
            own, other = line.count(root), line.count(3-root)
            total += (0, 1, 5, 30, 500)[own] - (0, 1, 5, 30, 500)[other]
        return total
    def search(board, shifts, turn, last, depth, alpha, beta):
        winner = fin(board, shifts)
        if winner:
            return 0 if winner == 'égalité' else (10000+depth if winner == root else -10000-depth)
        if depth == 0:
            return score(board, shifts)
        moves = coup_possible(board, shifts, turn, last)
        if not moves:
            return 0
        best = -float('inf') if turn == root else float('inf')
        for move in moves:
            b, s = [row[:] for row in board], shifts[:]
            coup_AI(b, s, turn, move)
            value = search(b, s, 3-turn, move, depth-1, alpha, beta)
            if turn == root:
                best = max(best, value); alpha = max(alpha, best)
            else:
                best = min(best, value); beta = min(beta, best)
            if beta <= alpha:
                break
        return best
    options = coup_possible(plateau, decalage, joueur, dernier_coup)
    if not options or fin(plateau, decalage):
        return None
    if hasard and random.random() < hasard:
        return random.choice(options)
    random.shuffle(options)
    best_move, best_score = options[0], -float('inf')
    for move in options:
        b, s = [row[:] for row in plateau], decalage[:]
        coup_AI(b, s, joueur, move)
        value = search(b, s, 3-joueur, move, max(0, profondeur-1), -float('inf'), float('inf'))
        if value > best_score:
            best_move, best_score = move, value
    return best_move


class Game:
    def __init__(self):
        self.board = nouveau_plateau()
        self.shifts = [0]*4
        self.turn = 1
        self.last = ''
        self.result = 0
        self.reason = ''
        self.history = []
        self.seen = Counter({self.key(): 1})

    def key(self):
        return (tuple(map(tuple, self.board)), tuple(self.shifts), self.turn, self.last)

    def legal(self):
        return [] if self.result else coup_possible(self.board, self.shifts, self.turn, self.last)

    def play(self, move):
        move = move.strip().upper()
        if move not in self.legal():
            raise ValueError('Coup interdit : choisissez une case ou une flèche disponible.')
        self.history.append((self.turn, move))
        coup_AI(self.board, self.shifts, self.turn, move)
        self.last = move
        self.turn = 3-self.turn
        self.result = fin(self.board, self.shifts)
        self.seen[self.key()] += 1
        if not self.result and self.seen[self.key()] >= 3:
            self.result, self.reason = 'égalité', 'Même position répétée trois fois.'
        if not self.result and not self.legal():
            self.result, self.reason = 'égalité', 'Aucun coup disponible.'
        if not self.result and len(self.history) >= 300:
            self.result, self.reason = 'égalité', 'Limite de 300 coups atteinte.'


def boucle_jeu():
    game = Game()
    noms = ' / '.join(f'{i+1} {d["nom"]}' for i, d in enumerate(DIFFICULTES))
    try:
        choix = input(f'Difficulté ({noms}) [2] > ').strip()
    except (EOFError, KeyboardInterrupt):
        return
    niveau = int(choix) - 1 if choix in {'1', '2', '3', '4'} else 1
    print(f'SLIDEWAYS — vous : X ; IA ({DIFFICULTES[niveau]["nom"]}) : O. Coups : A1, 2+, 3-. Q : quitter.')
    try:
        while not game.result:
            for r in reversed(range(4)):
                print(str(r+1)+'  '+'   '*(game.shifts[r]+3)+' '.join('.XO'[v] for v in game.board[r]))
            print('Décalages :', game.shifts)
            if game.turn == 1:
                move = input('Votre coup > ').strip().upper()
                if move == 'Q':
                    return
            else:
                move = choisir_coup_niveau(game.board, game.shifts, game.turn, game.last, niveau)
                print('IA :', move)
            try:
                game.play(move)
            except ValueError as e:
                print(e)
        print('Égalité.' if game.result == 'égalité' else f'Joueur {game.result} gagnant !')
        print(game.reason)
    except (EOFError, KeyboardInterrupt):
        print('\nPartie quittée.')


if __name__ == '__main__':
    boucle_jeu()
