"""Slideways — Neon Arcade. Projet de Resul Tektas. Lancement : python projet3.py"""
import sys
import math
from PyQt5.QtCore import Qt, QTimer, QElapsedTimer, QPointF, QRectF, QSettings
from PyQt5.QtGui import QPainter, QPen, QLinearGradient, QRadialGradient, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout
from audio import Audio
from controller import Match
from game_screen import GameScreen
from menu_model import Item, ListModel
from partie2 import DIFFICULTES
from screens import Fade, ListScreen, MainMenu, Splash, RulesScreen, CreditsScreen
from theme import (BG_TOP, BG_BOTTOM, CYAN, PINK, MUTED, DIM, FAINT, INK, color, mix, font,
                   draw_text, draw_keycap, approach, app_icon, WRAP_TOP_LEFT)

MODES = ['Solo', 'Duel à deux', 'Démo IA']
MODE_TEXT = [
    "Vous affrontez l’ordinateur. Choisissez son niveau, puis votre symbole.",
    "Deux joueurs sur le même écran. X (cyan) commence, O (rose) répond. En cours de partie, "
    "cliquez sur un joueur pour confier sa place à l’ordinateur.",
    "Deux ordinateurs s’affrontent au niveau choisi. Cliquez sur un joueur à tout moment pour reprendre la main.",
]
SIDES = ['X, je commence', 'O, je joue en second']
SPEEDS = [('Lente', 900), ('Normale', 500), ('Rapide', 150)]
TRACKS = [(0.16, 14.0), (0.31, -22.0), (0.52, 18.0), (0.70, -12.0), (0.86, 26.0)]
SHORTCUTS = [('Échap', 'Pause ou retour'), ('← →', 'Modifier un réglage'), ('M', 'Couper le son'),
             ('F11', 'Plein écran'), ('R', 'Rejouer en partie')]


class Window(QWidget):
    def __init__(self, splash=True, settings=None):
        super().__init__()
        self.setWindowTitle('Slideways')
        self.setWindowIcon(app_icon())
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self.settings = settings or QSettings('ResulTektas', 'SlidewaysArcade')
        self.t = 0.0
        self.energy = 1.0
        self.energy_target = 1.0
        self.current = ''
        self.animations = True
        self.options_return = 'menu'
        self.mode = self.get_int('mode', 0, 0, 2)
        self.level = self.get_int('level', 1, 0, len(DIFFICULTES) - 1)
        self.side = self.get_int('side', 0, 0, 1)
        self.speed = self.get_int('ai_speed', 1, 0, len(SPEEDS) - 1)
        self.bars = [0.0] * len(DIFFICULTES)

        self.audio = Audio()
        self.audio.volume = self.get_int('volume', 30, 0, 100) / 100
        self.audio.muted = self.get_bool('muted', False)
        self.audio.sfx_on = self.get_bool('sfx', True)

        self.match = Match(self)
        self.match.level = self.level
        self.match.delay = SPEEDS[self.speed][1]
        self.match.moved.connect(self.on_moved)
        self.match.ended.connect(self.on_ended)
        self.match.failed.connect(self.on_ai_failed)

        # --- pages -------------------------------------------------------------
        self.stack = QStackedWidget(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)
        self.splash_screen = Splash()
        self.splash_screen.finished.connect(lambda: self.go('menu'))
        self.menu_screen = self.build_menu()
        self.play_screen = self.build_play()
        self.options_screen = self.build_options()
        self.rules_screen = RulesScreen()
        self.rules_screen.backRequested.connect(self.close_rules)
        self.credits_screen = CreditsScreen()
        self.credits_screen.backRequested.connect(self.to_menu)
        self.game_screen = GameScreen(self.match)
        self.game_screen.pauseRequested.connect(self.show_pause)
        self.game_screen.restartRequested.connect(self.restart)
        self.pages = {'splash': self.splash_screen, 'menu': self.menu_screen, 'play': self.play_screen,
                      'options': self.options_screen, 'rules': self.rules_screen,
                      'credits': self.credits_screen, 'game': self.game_screen}
        for page in self.pages.values():
            self.stack.addWidget(page)

        # --- fenêtres internes (jamais de boîte de dialogue système) --------------
        self.pause_overlay = self.build_overlay('Pause', [
            Item('action', 'Reprendre', action=self.hide_pause),
            Item('action', 'Recommencer', action=self.restart),
            Item('action', 'Options', action=lambda: self.open_options('game')),
            Item('action', 'Menu principal', action=self.to_menu)], self.hide_pause)
        self.result_overlay = self.build_overlay('', [
            Item('action', 'Rejouer', action=self.restart),
            Item('action', 'Réglages de la partie', action=self.to_play),
            Item('action', 'Menu principal', action=self.to_menu)], self.to_menu)
        self.quit_overlay = self.build_overlay('Quitter Slideways ?', [
            Item('action', 'Rester', action=self.hide_quit),
            Item('action', 'Quitter', action=self.close)], self.hide_quit)
        self.fade = Fade(self)
        self.overlays = [self.pause_overlay, self.result_overlay, self.quit_overlay]

        for page in self.pages.values():
            if hasattr(page, 'sfx'):
                page.sfx.connect(self.audio.sfx)

        self.clock = QElapsedTimer()
        self.clock.start()
        self.ticker = QTimer(self)
        self.ticker.setTimerType(Qt.PreciseTimer)
        self.ticker.timeout.connect(self.tick)
        self.ticker.start(16)
        self.switch('splash' if splash else 'menu')

    # --- réglages ----------------------------------------------------------------
    def get_int(self, key, default, lo, hi):
        try:
            value = int(self.settings.value(key, default))
        except (TypeError, ValueError):
            value = default
        return max(lo, min(hi, value))

    def get_bool(self, key, default):
        return str(self.settings.value(key, default)).lower() in ('true', '1')

    def save(self, key, value):
        self.settings.setValue(key, value)

    # --- construction -----------------------------------------------------------
    def build_menu(self):
        items = [
            Item('action', 'Continuer', action=self.resume, visible=self.match.in_progress),
            Item('action', 'Jouer', action=lambda: self.go('play')),
            Item('action', 'Comment jouer', action=lambda: self.go('rules')),
            Item('action', 'Options', action=lambda: self.open_options('menu')),
            Item('action', 'Crédits', action=lambda: self.go('credits')),
            Item('action', 'Quitter', action=self.ask_quit)]
        screen = MainMenu(ListModel(items))
        screen.backRequested.connect(self.ask_quit)
        return screen

    def build_play(self):
        self.mode_item = Item('choice', 'Mode de jeu', options=MODES, index=self.mode, on_change=self.set_mode)
        self.level_item = Item('choice', 'Difficulté', options=[d['nom'] for d in DIFFICULTES],
                               index=self.level, on_change=self.set_level, visible=lambda: self.mode != 1)
        self.side_item = Item('choice', 'Votre symbole', options=SIDES, index=self.side,
                              on_change=self.set_side, visible=lambda: self.mode == 0)
        launch = Item('action', 'Lancer la partie', action=self.start_game)
        launch.accent = True
        items = [self.mode_item, self.level_item, self.side_item, launch,
                 Item('action', 'Retour', action=lambda: self.go('menu'))]
        screen = ListScreen(ListModel(items), 'Nouvelle partie', 'Choisissez votre adversaire.')
        screen.right_painter = self.paint_play_side
        screen.advance_hook = self.play_hook
        screen.backRequested.connect(lambda: self.go('menu'))
        return screen

    def build_options(self):
        self.mute_item = Item('toggle', 'Couper tout le son', value=self.audio.muted, on_change=self.on_mute)
        self.fs_item = Item('toggle', 'Plein écran', value=False, on_change=self.set_fullscreen)
        items = [
            Item('slider', 'Volume de la musique', value=int(round(self.audio.volume * 100)), step=5,
                 on_change=self.on_volume),
            Item('toggle', 'Effets sonores', value=self.audio.sfx_on, on_change=self.on_sfx),
            self.mute_item,
            Item('choice', 'Vitesse de l’ordinateur', options=[s[0] for s in SPEEDS], index=self.speed,
                 on_change=self.on_speed, hint='Temps d’attente avant que l’ordinateur joue son coup.'),
            self.fs_item,
            Item('action', 'Retour', action=self.close_options)]
        screen = ListScreen(ListModel(items), 'Options', 'Son, rythme et affichage.')
        screen.right_painter = self.paint_options_side
        screen.backRequested.connect(self.close_options)
        return screen

    def build_overlay(self, title, items, on_back):
        overlay = ListScreen(ListModel(items), title, overlay=True, parent=self)
        overlay.backRequested.connect(on_back)
        overlay.sfx.connect(self.audio.sfx)
        overlay.hide()
        return overlay

    # --- changements de réglages ------------------------------------------------
    def set_mode(self, value):
        self.mode = value
        self.save('mode', value)
        self.play_screen.model.snap()

    def set_level(self, value):
        self.level = value
        self.save('level', value)

    def set_side(self, value):
        self.side = value
        self.save('side', value)

    def on_volume(self, value):
        self.audio.set_volume(value)
        self.save('volume', int(value))

    def on_sfx(self, value):
        self.audio.sfx_on = bool(value)
        self.save('sfx', bool(value))
        self.audio.sfx('select')

    def on_mute(self, value):
        if bool(value) != self.audio.muted:
            self.audio.toggle()
        self.save('muted', self.audio.muted)

    def on_speed(self, value):
        self.speed = value
        self.match.delay = SPEEDS[value][1]
        self.save('ai_speed', value)

    def set_fullscreen(self, on):
        on = bool(on)
        if on and not self.isFullScreen():
            self.showFullScreen()
        elif not on and self.isFullScreen():
            self.showNormal()
        self.fs_item.value = on

    # --- navigation ---------------------------------------------------------------
    def go(self, name, then=None, instant=False):
        def apply():
            self.switch(name)
            if then:
                then()
        if instant or not self.animations or not self.isVisible():
            apply()
        else:
            self.fade.start(apply)

    def switch(self, name):
        page = self.pages[name]
        self.current = name
        self.stack.setCurrentWidget(page)
        self.energy_target = 0.35 if name == 'game' else 1.0
        self.audio.play('game' if name == 'game' else 'menu')
        if name == 'menu':
            self.menu_screen.reset_selection()
        elif name in ('play', 'options'):
            page.reset_selection()
        for overlay in self.overlays:
            overlay.hide()
        self.fade.raise_()
        page.setFocus()

    def start_game(self):
        m = self.match
        m.invalidate()
        m.level = self.level
        if self.mode == 0:
            m.kinds = ['human', 'ai'] if self.side == 0 else ['ai', 'human']
        elif self.mode == 1:
            m.kinds = ['human', 'human']
        else:
            m.kinds = ['ai', 'ai']
        m.active = True
        m.new_game()
        self.game_screen.reset_view()
        self.go('game')

    def resume(self):
        self.match.set_active(True)
        self.game_screen.reset_view()
        self.go('game')

    def restart(self):
        for overlay in self.overlays:
            overlay.hide()
        self.match.active = True
        self.match.new_game()
        self.game_screen.reset_view()
        self.game_screen.setFocus()

    def to_menu(self):
        for overlay in self.overlays:
            overlay.hide()
        self.match.set_active(False)
        self.go('menu')

    def to_play(self):
        for overlay in self.overlays:
            overlay.hide()
        self.match.set_active(False)
        self.go('play')

    def close_rules(self):
        self.go('menu')

    def open_options(self, origin):
        self.options_return = origin
        self.pause_overlay.hide()
        self.go('options')

    def close_options(self):
        if self.options_return == 'game':
            self.go('game', then=self.show_pause)
        else:
            self.go('menu')

    # --- fenêtres internes ----------------------------------------------------------
    def show_overlay(self, overlay):
        overlay.setGeometry(self.rect())
        overlay.reset_selection()
        overlay.show()
        overlay.raise_()
        self.fade.raise_()
        overlay.setFocus()

    def show_pause(self):
        if self.current != 'game' or self.result_overlay.isVisible():
            return
        self.match.set_paused(True)
        self.pause_overlay.subtitle = ''
        self.show_overlay(self.pause_overlay)

    def hide_pause(self):
        self.pause_overlay.hide()
        self.match.set_paused(False)
        self.game_screen.setFocus()

    def show_result(self, game):
        if self.current != 'game' or self.match.game is not game or not game.result:
            return
        if any(o.isVisible() for o in self.overlays):
            return
        m = self.match
        res = game.result
        if res == 'égalité':
            title, col = 'Égalité', MUTED
        else:
            col = CYAN if res == 1 else PINK
            if m.kinds.count('human') == 1:
                title = 'Victoire !' if m.kinds[res - 1] == 'human' else 'Défaite'
            else:
                title = f'Joueur {res} gagne !'
        self.result_overlay.title = title
        self.result_overlay.title_color = col
        self.result_overlay.subtitle = game.reason or f'{len(game.history)} coups joués'
        self.show_overlay(self.result_overlay)

    def ask_quit(self):
        self.show_overlay(self.quit_overlay)

    def hide_quit(self):
        self.quit_overlay.hide()
        self.pages[self.current].setFocus()

    # --- événements de partie ---------------------------------------------------------
    def on_moved(self, move, player):
        self.audio.sfx('slide' if move[-1] in '+-' else 'place')

    def on_ended(self):
        g = self.match.game
        humans = self.match.kinds.count('human')
        if g.result == 'égalité':
            self.audio.sfx('draw')
        elif humans != 1 or self.match.kinds[g.result - 1] == 'human':
            self.audio.sfx('win')
        else:
            self.audio.sfx('draw')
        QTimer.singleShot(1500, lambda: self.show_result(g))

    def on_ai_failed(self, message):
        sys.stderr.write('Erreur IA : ' + message + '\n')
        self.show_pause()
        self.pause_overlay.subtitle = 'L’ordinateur a rencontré une erreur.'

    # --- animation et dessin -------------------------------------------------------------
    def tick(self):
        dt = min(0.05, self.clock.restart() / 1000.0)
        self.t += dt
        self.energy = approach(self.energy, self.energy_target, dt, 4.0)
        page = self.pages.get(self.current)
        if page is not None and hasattr(page, 'advance'):
            page.advance(dt)
        for overlay in self.overlays:
            if overlay.isVisible():
                overlay.advance(dt)
        self.fade.advance(dt)
        self.update()

    def play_hook(self, dt):
        for i in range(len(self.bars)):
            target = 1.0 if (i <= self.level and self.mode != 1) else 0.0
            self.bars[i] = approach(self.bars[i], target, dt, 12.0)

    def resizeEvent(self, event):
        if hasattr(self, 'fade'):
            for overlay in self.overlays:
                overlay.setGeometry(self.rect())
            self.fade.setGeometry(self.rect())
        super().resizeEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        e = self.energy
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.0, color(BG_TOP))
        bg.setColorAt(1.0, color(BG_BOTTOM))
        p.fillRect(self.rect(), QBrush(bg))
        for cx, cy, col, k in [(0.82, 0.22, '#5a1e5c', 0.0), (0.12, 0.72, '#08405a', 2.1)]:
            x = w * cx + math.sin(self.t * 0.15 + k) * w * 0.03
            y = h * cy + math.cos(self.t * 0.12 + k) * h * 0.03
            glow = QRadialGradient(QPointF(x, y), w * 0.5)
            glow.setColorAt(0.0, color(col, 110 * (0.5 + 0.5 * e)))
            glow.setColorAt(1.0, color(col, 0))
            p.fillRect(self.rect(), QBrush(glow))
        spacing, size = 96.0, 30.0
        for k, (fy, speed) in enumerate(TRACKS):
            y = h * fy
            p.setPen(QPen(color(FAINT, 110 * e), 1))
            p.drawLine(QPointF(0, y), QPointF(w, y))
            shift = self.t * speed
            base = math.floor(shift / spacing)
            off = shift - base * spacing
            for i in range(-1, int(w / spacing) + 3):
                ident = i - base + k * 3
                tint = int(ident) % 5
                col = CYAN if tint == 0 else PINK if tint == 3 else DIM
                alpha = (80 if tint in (0, 3) else 40) * e
                p.setPen(QPen(color(col, alpha), 1.2))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(QRectF(i * spacing + off, y - size / 2, size, size), 6, 6)
        vignette = QRadialGradient(QPointF(w / 2, h / 2), max(w, h) * 0.75)
        vignette.setColorAt(0.55, color('#000000', 0))
        vignette.setColorAt(1.0, color('#000000', 150))
        p.fillRect(self.rect(), QBrush(vignette))
        p.end()

    def paint_play_side(self, p, screen):
        w, h = screen.width(), screen.height()
        x = w * 0.62
        width = w - x - screen.margin()
        card = QRectF(x, h * 0.30, width, 350)
        p.setPen(QPen(color('#3a2d5e'), 1.2))
        p.setBrush(color('#ffffff', 6))
        p.drawRoundedRect(card, 14, 14)
        inner = card.adjusted(28, 26, -28, -20)
        if self.mode == 1:
            title, tint = 'Deux joueurs', MUTED
        else:
            title = DIFFICULTES[self.level]['nom']
            tint = mix(CYAN, PINK, self.level / max(1, len(DIFFICULTES) - 1)).name()
        draw_text(p, inner.left(), inner.top() + 38, title, font(38, QFont.DemiBold, 0.5), color(INK))
        bar_w = min(54.0, (inner.width() - 30) / len(DIFFICULTES))
        for i, amount in enumerate(self.bars):
            rect = QRectF(inner.left() + i * (bar_w + 10), inner.top() + 62, bar_w, 8)
            p.setPen(Qt.NoPen)
            p.setBrush(color('#2c2347'))
            p.drawRoundedRect(rect, 4, 4)
            if amount > 0.01:
                p.setBrush(color(tint))
                p.drawRoundedRect(QRectF(rect.left(), rect.top(), rect.width() * amount, 8), 4, 4)
        text = MODE_TEXT[self.mode]
        if self.mode != 1:
            text = DIFFICULTES[self.level]['desc'] + '\n\n' + text
        p.setFont(font(16))
        p.setPen(color(MUTED))
        p.drawText(QRectF(inner.left(), inner.top() + 92, inner.width(), 240), WRAP_TOP_LEFT, text)

    def paint_options_side(self, p, screen):
        w, h = screen.width(), screen.height()
        x = w * 0.64
        y = h * 0.30
        draw_text(p, x, y + 4, 'Raccourcis', font(20, QFont.DemiBold), color(INK))
        for i, (key, label) in enumerate(SHORTCUTS):
            draw_keycap(p, x, y + 52 + i * 44, key, label, 14)

    # --- clavier global ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_M:
            self.audio.toggle()
            self.mute_item.value = self.audio.muted
            self.save('muted', self.audio.muted)
        elif event.key() == Qt.Key_F11:
            self.set_fullscreen(not self.isFullScreen())
            self.save('fullscreen', self.isFullScreen())
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.match.shutdown()
        self.audio.close()
        self.settings.sync()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Slideways')
    window = Window()
    if window.get_bool('fullscreen', False):
        window.showFullScreen()
        window.fs_item.value = True
    else:
        window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
