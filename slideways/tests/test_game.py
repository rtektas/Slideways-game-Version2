import unittest
from partie2 import (Game, nouveau_plateau, fin, coup_possible, choisir_coup, choisir_coup_niveau,
                     cases_gagnantes, DIFFICULTES)

class Rules(unittest.TestCase):
    def test_boundaries(self):
        for shift in [-3, 3]:
            moves = coup_possible(nouveau_plateau(), [shift]*4, 1)
            for r in range(1, 5):
                self.assertNotIn(str(r)+('-' if shift == -3 else '+'), moves)

    def test_no_immediate_reverse(self):
        g = Game(); g.play('A1')
        self.assertNotIn('A1', g.legal())
        g.play('2+'); self.assertNotIn('2-', g.legal())
        with self.assertRaises(ValueError): g.play('2-')

    def test_recolor(self):
        g = Game(); g.play('A1'); g.play('B1'); g.play('C1'); g.play('A1')
        self.assertEqual(g.board[0][0], 2)

    def test_multiple_lines_same_winner(self):
        b = nouveau_plateau(); b[0] = [1]*4; b[1] = [1]*4
        self.assertEqual(fin(b, [0]*4), 1)
        b[2] = [2]*4
        self.assertEqual(fin(b, [0]*4), 'égalité')

    def test_shifted_columns_and_diagonals(self):
        b = nouveau_plateau()
        for r in range(4): b[r][r] = 1
        self.assertEqual(fin(b, [0, -1, -2, -3]), 1)
        self.assertEqual(fin(b, [0]*4), 1)
        self.assertEqual(fin(b, [0, 1, 2, 3]), 0)

    def test_ai_win_and_block_both_players(self):
        for player in [1, 2]:
            b = nouveau_plateau(); b[0] = [player]*3+[0]
            self.assertEqual(choisir_coup(b, [0]*4, player, 'B2'), 'D1')
            b = nouveau_plateau(); b[0] = [3-player]*3+[0]
            m = choisir_coup(b, [0]*4, player, 'C1')
            self.assertIn(m, ['A1', 'B1', 'D1'])

    def test_complete_ai_game(self):
        g = Game()
        while not g.result:
            m = choisir_coup(g.board, g.shifts, g.turn, g.last)
            self.assertIn(m, g.legal()); g.play(m)
            self.assertTrue(all(-3 <= x <= 3 for x in g.shifts))
        self.assertLessEqual(len(g.history), 300)
        with self.assertRaises(ValueError): g.play('A1')

class Difficulty(unittest.TestCase):
    def test_four_levels_with_increasing_depth(self):
        self.assertEqual([d['nom'] for d in DIFFICULTES], ['Facile', 'Normal', 'Difficile', 'Expert'])
        depths = [d['profondeur'] for d in DIFFICULTES]
        self.assertEqual(depths, sorted(depths))
        self.assertGreater(DIFFICULTES[0]['hasard'], DIFFICULTES[1]['hasard'])
        self.assertEqual(DIFFICULTES[3]['hasard'], 0)

    def test_every_level_plays_legal_moves(self):
        for level in range(4):
            g = Game()
            g.play('A1')
            move = choisir_coup_niveau(g.board, g.shifts, g.turn, g.last, level)
            self.assertIn(move, g.legal())

    def test_strong_levels_take_immediate_win(self):
        for level in (1, 2, 3):
            b = nouveau_plateau(); b[0] = [1, 1, 1, 0]
            for _ in range(3):
                self.assertEqual(choisir_coup_niveau(b, [0] * 4, 1, 'B2', 3), 'D1')

    def test_easy_level_can_blunder(self):
        b = nouveau_plateau(); b[0] = [1, 1, 1, 0]
        answers = {choisir_coup(b, [0] * 4, 1, 'B2', profondeur=1, hasard=1.0) for _ in range(60)}
        self.assertGreater(len(answers), 3)

    def test_out_of_range_level_is_clamped(self):
        self.assertIn(choisir_coup_niveau(nouveau_plateau(), [0] * 4, 1, '', 99), coup_possible(nouveau_plateau(), [0] * 4, 1))
        self.assertIn(choisir_coup_niveau(nouveau_plateau(), [0] * 4, 1, '', -5), coup_possible(nouveau_plateau(), [0] * 4, 1))

    def test_winning_cells(self):
        b = nouveau_plateau()
        for r in range(4): b[r][r] = 1
        self.assertEqual(cases_gagnantes(b, [0] * 4), {(0, 0), (1, 1), (2, 2), (3, 3)})
        self.assertEqual(cases_gagnantes(b, [0, 1, 2, 3]), set())

    def test_tutorial_scripts_are_legal(self):
        from rules_data import RULES_SLIDES
        for slide in RULES_SLIDES:
            g = Game()
            for move in slide['script']:
                g.play(move)


if __name__ == '__main__': unittest.main()
