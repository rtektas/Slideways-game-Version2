"""Tests de l'interface (exécutés hors écran). Lancer : python -m unittest discover -s tests -v"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from pathlib import Path
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from projet3 import Window

app = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parent.parent


def wait_for(condition, ms=4000):
    for _ in range(ms // 20):
        if condition():
            return True
        QTest.qWait(20)
    return condition()


class Interface(unittest.TestCase):
    def setUp(self):
        QSettings.setDefaultFormat(QSettings.IniFormat)
        self.w = Window(splash=False, settings=QSettings('SlidewaysTests', 'ui'))
        self.w.settings.clear()
        self.w.animations = False
        self.w.show()
        app.processEvents()
        self.m = self.w.match

    def tearDown(self):
        self.w.close()
        app.processEvents()

    def press(self, widget, key):
        QTest.keyClick(widget, key)

    def label(self, screen):
        return screen.model.current().label

    def test_no_system_dialog_is_used(self):
        for path in ROOT.glob('*.py'):
            self.assertNotIn('QMessageBox', path.read_text(encoding='utf-8'), path.name)

    def test_menu_keyboard_and_pages(self):
        self.assertEqual(self.w.current, 'menu')
        self.assertEqual(self.label(self.w.menu_screen), 'Jouer')
        self.press(self.w.menu_screen, Qt.Key_Down)
        self.assertEqual(self.label(self.w.menu_screen), 'Comment jouer')
        self.press(self.w.menu_screen, Qt.Key_Return)
        self.assertEqual(self.w.current, 'rules')
        self.press(self.w.rules_screen, Qt.Key_Escape)
        self.assertEqual(self.w.current, 'menu')
        self.w.go('credits'); self.assertEqual(self.w.current, 'credits')
        self.press(self.w.credits_screen, Qt.Key_Escape)
        self.assertEqual(self.w.current, 'menu')

    def test_quit_asks_inside_the_window(self):
        self.press(self.w.menu_screen, Qt.Key_Escape)
        self.assertTrue(self.w.quit_overlay.isVisible())
        self.press(self.w.quit_overlay, Qt.Key_Escape)
        self.assertFalse(self.w.quit_overlay.isVisible())

    def test_difficulty_choice_reaches_the_ai(self):
        self.w.go('play')
        screen = self.w.play_screen
        self.press(screen, Qt.Key_Down)
        self.assertEqual(self.label(screen), 'Difficulté')
        self.w.level_item.set_value(3)
        self.w.start_game()
        self.assertEqual(self.m.level, 3)
        self.assertEqual(self.m.kinds, ['human', 'ai'])
        self.assertEqual(self.w.current, 'game')

    def test_duel_hides_difficulty(self):
        self.w.mode_item.set_value(1)
        self.assertFalse(self.w.level_item.is_visible())
        self.assertFalse(self.w.side_item.is_visible())

    def test_ai_replies_and_pause_blocks_it(self):
        self.w.level_item.set_value(0)
        self.m.delay = 100
        self.w.start_game()
        self.assertTrue(self.m.human_move('A1'))
        self.assertTrue(wait_for(lambda: len(self.m.game.history) == 2))
        self.press(self.w.game_screen, Qt.Key_Escape)
        self.assertTrue(self.w.pause_overlay.isVisible() and self.m.paused)
        self.assertFalse(self.m.human_move('B2'))
        self.press(self.w.pause_overlay, Qt.Key_Escape)
        self.assertFalse(self.m.paused)

    def test_continue_after_menu(self):
        self.w.mode_item.set_value(1)
        self.w.start_game()
        self.m.human_move('A1')
        self.w.to_menu()
        self.assertFalse(self.m.active)
        self.assertEqual(self.label(self.w.menu_screen), 'Continuer')
        self.w.resume()
        self.assertTrue(self.m.active)
        self.assertEqual(len(self.m.game.history), 1)

    def test_victory_shows_result_panel(self):
        self.w.mode_item.set_value(1)
        self.w.start_game()
        for move in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1']:
            self.assertTrue(self.m.human_move(move), move)
        self.assertEqual(self.m.game.result, 1)
        self.w.show_result(self.m.game)
        self.assertTrue(self.w.result_overlay.isVisible())
        self.assertIn('gagne', self.w.result_overlay.title)

    def test_board_hit_testing_and_extreme_shifts(self):
        self.w.mode_item.set_value(1)
        self.w.start_game()
        board = self.w.game_screen.board
        board.set_game(self.m.game, self.m.allowed(), animate=False)
        u, x0, y0 = board.geometry_info()
        self.assertEqual(board.hit(board.tile_rect(0, 0, u, x0, y0).center()), 'A1')
        self.assertEqual(board.hit(board.arrow_rect(1, -1, u, x0, y0).center()), '2-')
        self.assertEqual(board.hit(board.arrow_rect(3, 1, u, x0, y0).center()), '4+')
        self.m.game.shifts = [-3, 3, -3, 3]
        board.set_game(self.m.game, self.m.allowed(), animate=False)
        for r in range(4):
            for c in range(4):
                rect = board.tile_rect(r, c, u, x0, y0)
                self.assertGreaterEqual(rect.left(), x0)
                self.assertLessEqual(rect.right(), x0 + board.width())

    def test_options_volume_and_mute(self):
        self.w.go('options')
        screen = self.w.options_screen
        before = self.w.audio.volume
        self.press(screen, Qt.Key_Right)
        self.assertGreater(self.w.audio.volume, before)
        self.w.keyPressEvent(__import__('PyQt5.QtGui', fromlist=['QKeyEvent']).QKeyEvent(
            __import__('PyQt5.QtCore', fromlist=['QEvent']).QEvent.KeyPress, Qt.Key_M, Qt.NoModifier))
        self.assertTrue(self.w.audio.muted)
        self.assertTrue(self.w.mute_item.value)

    def test_audio_tracks(self):
        a = self.w.audio
        if not a.ready:
            self.skipTest(a.error)
        self.assertEqual(a.track, 'menu')
        self.w.mode_item.set_value(1)
        self.w.start_game()
        self.assertEqual(a.track, 'game')
        self.assertTrue(a.sounds)


if __name__ == '__main__':
    unittest.main()
