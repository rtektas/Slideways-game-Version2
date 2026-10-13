"""Écran de partie : bandeau des joueurs, plateau animé, indications de touches."""
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from board_view import BoardView, draw_symbol
from partie2 import DIFFICULTES
from theme import (INK, MUTED, DIM, CYAN, PINK, GOLD, color, mix, font, text_width,
                   draw_text, draw_keycap, approach)

CARD_W = 300.0
CARD_H = 84.0


class Hud(QWidget):
    kindToggled = pyqtSignal(int)
    pauseRequested = pyqtSignal()

    def __init__(self, match, parent=None):
        super().__init__(parent)
        self.match = match
        self.setFixedHeight(128)
        self.setMouseTracking(True)
        self.glow = [0.0, 0.0]
        self.time = 0.0
        self.card_rects = [QRectF(), QRectF()]
        self.pause_rect = QRectF()
        self.setToolTip('Cliquez sur un joueur pour le passer de Humain à Ordinateur')

    def margin(self):
        return max(40.0, self.width() * 0.04)

    def advance(self, dt):
        self.time += dt
        g = self.match.game
        for i in range(2):
            target = 1.0 if (not g.result and g.turn == i + 1) else 0.0
            self.glow[i] = approach(self.glow[i], target, dt, 10.0)

    def status(self):
        m, g = self.match, self.match.game
        if g.result:
            if g.result == 'égalité':
                return 'Égalité', MUTED, False
            return f'Victoire du joueur {g.result}', (CYAN if g.result == 1 else PINK), False
        if m.paused:
            return 'Partie en pause', MUTED, False
        col = CYAN if g.turn == 1 else PINK
        if m.is_ai(g.turn):
            return 'L’ordinateur réfléchit', col, True
        if m.kinds[0] == 'human' and m.kinds[1] == 'human':
            return f'Joueur {g.turn}, à vous', col, False
        return 'À vous de jouer', col, False

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        mg = self.margin()
        self.card_rects = [QRectF(mg, 30, CARD_W, CARD_H), QRectF(w - mg - CARD_W, 30, CARD_W, CARD_H)]
        for i in range(2):
            self.paint_card(p, i, self.card_rects[i])
        text, col, thinking = self.status()
        avail = max(120.0, w - 2 * (mg + CARD_W) - 24)
        px = 21
        full = text + ('...' if thinking else '')
        while px > 12 and text_width(font(px, QFont.DemiBold), full) > avail:
            px -= 1
        f = font(px, QFont.DemiBold)
        x = w / 2 - text_width(f, full) / 2
        shown = text + ('.' * (int(self.time * 2.5) % 4) if thinking else '')
        draw_text(p, x, 68, shown, f, color(col))
        g = self.match.game
        sub = (g.reason or f'{len(g.history)} coups joués') if g.result else f'Coup {len(g.history) + 1}'
        draw_text(p, w / 2, 92, sub, font(13), color(MUTED), 'center')
        self.pause_rect = QRectF(w - mg - 140, 2, 140, 26)
        draw_keycap(p, w - mg - 120, 20, 'Échap', 'Pause')
        p.end()

    def paint_card(self, p, i, rect):
        m, g = self.match, self.match.game
        player = i + 1
        col = CYAN if i == 0 else PINK
        glow = self.glow[i]
        winner = g.result == player
        border = color(GOLD) if winner else mix(DIM, col, glow)
        p.setBrush(color('#ffffff', 8 + 10 * glow))
        p.setPen(QPen(border, 1.5))
        p.drawRoundedRect(rect, 12, 12)
        draw_symbol(p, player, rect.left() + 46, rect.center().y(), 50, col, 0.6 + 0.8 * glow)
        x = rect.left() + 92
        draw_text(p, x, rect.top() + 28, f'Joueur {player}', font(13, QFont.Normal, 1), color(MUTED))
        ai = m.kinds[i] == 'ai'
        draw_text(p, x, rect.top() + 55, 'Ordinateur' if ai else 'Humain', font(22, QFont.DemiBold), color(INK))
        if ai:
            draw_text(p, x, rect.top() + 75, f'Niveau {DIFFICULTES[m.level]["nom"]}', font(13), color(MUTED))
        if winner:
            draw_text(p, rect.right() - 16, rect.top() + 26, 'Vainqueur', font(13, QFont.DemiBold), color(GOLD), 'right')
        elif m.busy and g.turn == player and not g.result:
            for k in range(3):
                a = 90 + 165 * max(0.0, ((self.time * 3 - k * 0.6) % 3.0) < 1.0)
                p.setPen(Qt.NoPen)
                p.setBrush(color(col, a))
                p.drawEllipse(QPointF(rect.right() - 44 + k * 13, rect.top() + 22), 3.2, 3.2)
        if glow > 0.01:
            p.setPen(Qt.NoPen)
            p.setBrush(color(col, 230))
            p.drawRoundedRect(QRectF(rect.left() + 14, rect.bottom() - 6, (rect.width() - 28) * glow, 3), 1.5, 1.5)

    def mouseMoveEvent(self, event):
        point = QPointF(event.pos())
        hot = self.pause_rect.contains(point) or any(r.contains(point) for r in self.card_rects)
        self.setCursor(Qt.PointingHandCursor if hot else Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        point = QPointF(event.pos())
        if self.pause_rect.contains(point):
            self.pauseRequested.emit()
            return
        for i, rect in enumerate(self.card_rects):
            if rect.contains(point):
                self.kindToggled.emit(i)
                return


class GameScreen(QWidget):
    sfx = pyqtSignal(str)
    pauseRequested = pyqtSignal()
    restartRequested = pyqtSignal()

    def __init__(self, match, parent=None):
        super().__init__(parent)
        self.match = match
        self.setFocusPolicy(Qt.StrongFocus)
        self.hud = Hud(match)
        self.board = BoardView(interactive=True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 54)
        layout.setSpacing(8)
        layout.addWidget(self.hud)
        layout.addWidget(self.board, 1)
        self.board.moveRequested.connect(self.match.human_move)
        self.hud.kindToggled.connect(self.toggle_kind)
        self.hud.pauseRequested.connect(self.pauseRequested)
        self.match.changed.connect(self.refresh)
        self._game_ref = None

    def toggle_kind(self, index):
        self.sfx.emit('tick')
        self.match.toggle_kind(index)

    def refresh(self):
        g = self.match.game
        animate = g is self._game_ref
        self._game_ref = g
        self.board.set_game(g, self.match.allowed(), animate=animate, paused=self.match.paused)
        self.hud.update()
        self.update()

    def reset_view(self):
        self._game_ref = None
        self.refresh()

    def advance(self, dt):
        self.hud.advance(dt)
        self.board.advance(dt)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Escape, Qt.Key_P):
            self.pauseRequested.emit()
        elif key == Qt.Key_R:
            self.restartRequested.emit()
        else:
            event.ignore()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        x = self.hud.margin()
        y = self.height() - 24
        for key, label in [('Clic', 'Colorer une case ou glisser une rangée'), ('Échap', 'Pause'), ('R', 'Rejouer')]:
            x += draw_keycap(p, x, y, key, label) + 24
        p.end()
