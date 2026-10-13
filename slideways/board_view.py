"""Plateau dessiné et animé : rangées qui glissent, cases qui apparaissent, victoire qui pulse."""
import math
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFont
from PyQt5.QtWidgets import QWidget
from partie2 import cases_gagnantes
from theme import (CYAN, PINK, GOLD, DIM, INK, color, font, draw_text, approach,
                   ease_out_back)

ARROW = 0.72        # largeur d'une zone de flèche, en cases
COLUMNS = 10        # 4 cases + 3 de chaque côté pour les glissements
POP_TIME = 0.32


def draw_symbol(p, value, cx, cy, u, col, boost=1.0):
    """Dessine un X (value 1) ou un O (value 2) lumineux au centre (cx, cy)."""
    reach = u * 0.19
    p.setBrush(Qt.NoBrush)
    for width, alpha in ((u * 0.17, 20), (u * 0.1, 48), (u * 0.052, 255)):
        pen = QPen(color(col, min(255, alpha * boost)), width)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        if value == 1:
            p.drawLine(QPointF(cx - reach, cy - reach), QPointF(cx + reach, cy + reach))
            p.drawLine(QPointF(cx + reach, cy - reach), QPointF(cx - reach, cy + reach))
        else:
            p.drawEllipse(QPointF(cx, cy), reach * 1.05, reach * 1.05)


class BoardView(QWidget):
    moveRequested = pyqtSignal(str)

    def __init__(self, interactive=True, parent=None):
        super().__init__(parent)
        self.interactive = interactive
        self.setMouseTracking(True)
        self.values = [[0] * 4 for _ in range(4)]
        self.shown = [0.0] * 4
        self.target = [0] * 4
        self.pop = {}
        self.winners = set()
        self.last = ''
        self.allowed = set()
        self.finished = False
        self.veil = 0.0
        self.veil_target = 0.0
        self.hover = None
        self.time = 0.0
        self.setMinimumSize(420, 190)
        if not interactive:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    # --- données ----------------------------------------------------------
    def set_game(self, game, allowed=(), animate=True, paused=False):
        if animate:
            for r in range(4):
                for c in range(4):
                    new = game.board[r][c]
                    if new and new != self.values[r][c]:
                        self.pop[(r, c)] = 0.0
        else:
            self.pop.clear()
            self.shown = [float(s) for s in game.shifts]
        self.values = [row[:] for row in game.board]
        self.target = list(game.shifts)
        self.last = game.last
        self.allowed = set(allowed)
        self.finished = bool(game.result)
        self.winners = cases_gagnantes(game.board, game.shifts) if game.result else set()
        self.veil_target = 1.0 if paused else 0.0
        if not self.allowed:
            self.hover = None
            self.unsetCursor()
        self.update()

    def advance(self, dt):
        self.time += dt
        for r in range(4):
            self.shown[r] = approach(self.shown[r], float(self.target[r]), dt, 15.0)
        for key in list(self.pop):
            self.pop[key] += dt
            if self.pop[key] > POP_TIME:
                del self.pop[key]
        self.veil = approach(self.veil, self.veil_target, dt, 10.0)

    # --- géométrie ----------------------------------------------------------
    def geometry_info(self):
        w, h = self.width(), self.height()
        u = min(86.0, w / (COLUMNS + 2 * ARROW + 0.4), h / 4.3)
        total_w = (COLUMNS + 2 * ARROW) * u
        x0 = (w - total_w) / 2
        y0 = (h - 4 * u) / 2
        return u, x0, y0

    def tile_rect(self, r, c, u, x0, y0, shift=None):
        shift = self.shown[r] if shift is None else shift
        x = x0 + ARROW * u + (c + shift + 3) * u
        y = y0 + (3 - r) * u
        return QRectF(x, y, u, u)

    def arrow_rect(self, r, side, u, x0, y0):
        x = x0 if side < 0 else x0 + (ARROW + COLUMNS) * u
        return QRectF(x, y0 + (3 - r) * u, ARROW * u, u)

    def hit(self, pos):
        u, x0, y0 = self.geometry_info()
        point = QPointF(pos)
        for r in range(4):
            for side, sign in ((-1, '-'), (1, '+')):
                if self.arrow_rect(r, side, u, x0, y0).contains(point):
                    return f'{r + 1}{sign}'
            for c in range(4):
                if self.tile_rect(r, c, u, x0, y0).contains(point):
                    return f'{"ABCD"[c]}{r + 1}'
        return None

    # --- souris -------------------------------------------------------------
    def mouseMoveEvent(self, event):
        if not self.interactive:
            return
        move = self.hit(event.pos())
        move = move if move in self.allowed else None
        if move != self.hover:
            self.hover = move
            self.setCursor(Qt.PointingHandCursor if move else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.unsetCursor()
        self.update()

    def mousePressEvent(self, event):
        if not self.interactive or event.button() != Qt.LeftButton:
            return
        move = self.hit(event.pos())
        if move in self.allowed:
            self.moveRequested.emit(move)

    # --- dessin ---------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        u, x0, y0 = self.geometry_info()
        for r in range(4):
            self.paint_row(p, r, u, x0, y0)
        if self.veil > 0.01:
            p.setOpacity(1.0)
            p.setBrush(color('#05040c', 190 * self.veil))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(x0, y0, (COLUMNS + 2 * ARROW) * u, 4 * u), u * 0.2, u * 0.2)
            draw_text(p, x0 + (COLUMNS + 2 * ARROW) * u / 2, y0 + 2 * u + u * 0.12, 'EN PAUSE',
                      font(u * 0.42, QFont.DemiBold, u * 0.08), color(INK, 255 * self.veil), 'center')
        p.end()

    def paint_row(self, p, r, u, x0, y0):
        y = y0 + (3 - r) * u
        track = QRectF(x0 + ARROW * u, y + u * 0.06, COLUMNS * u, u * 0.88)
        p.setPen(Qt.NoPen)
        p.setBrush(color('#ffffff', 7))
        p.drawRoundedRect(track, u * 0.16, u * 0.16)
        # emplacements de départ de la rangée
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color(DIM, 70), 1.0))
        for c in range(4):
            slot = QRectF(x0 + ARROW * u + (c + 3) * u, y, u, u).adjusted(u * 0.1, u * 0.1, -u * 0.1, -u * 0.1)
            p.drawRoundedRect(slot, u * 0.14, u * 0.14)
        for side in (-1, 1):
            self.paint_arrow(p, r, side, u, x0, y0)
        for c in range(4):
            self.paint_tile(p, r, c, u, x0, y0)

    def paint_arrow(self, p, r, side, u, x0, y0):
        move = f'{r + 1}{"-" if side < 0 else "+"}'
        rect = self.arrow_rect(r, side, u, x0, y0)
        usable = move in self.allowed
        hot = usable and move == self.hover
        if self.interactive:
            alpha = 255 if hot else 150 if usable else 45
        else:
            alpha = 55
        cx, cy = rect.center().x(), rect.center().y()
        d = u * 0.17
        p.setBrush(Qt.NoBrush)
        pen = QPen(color(INK if hot else '#cdbfff', alpha), max(1.6, u * 0.05))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(cx + side * d * 0.5, cy - d * 1.4), QPointF(cx - side * d * 0.5, cy))
        p.drawLine(QPointF(cx - side * d * 0.5, cy), QPointF(cx + side * d * 0.5, cy + d * 1.4))

    def paint_tile(self, p, r, c, u, x0, y0):
        value = self.values[r][c]
        rect = self.tile_rect(r, c, u, x0, y0).adjusted(u * 0.06, u * 0.06, -u * 0.06, -u * 0.06)
        move = f'{"ABCD"[c]}{r + 1}'
        hot = self.interactive and move == self.hover
        col = CYAN if value == 1 else PINK if value == 2 else DIM
        in_win = (r, c) in self.winners
        p.save()
        if self.finished and self.winners and not in_win:
            p.setOpacity(0.38)
        age = self.pop.get((r, c))
        if age is not None:
            s = 0.45 + 0.55 * ease_out_back(age / POP_TIME)
            center = rect.center()
            p.translate(center)
            p.scale(s, s)
            p.translate(-center.x(), -center.y())
        fill = color('#10303f') if value == 1 else color('#35153a') if value == 2 else color('#171329')
        if hot:
            fill = fill.lighter(165)
        pulse = 0.5 + 0.5 * math.sin(self.time * 6.0) if in_win else 0.0
        if in_win:
            fill = fill.lighter(int(130 + 40 * pulse))
        p.setBrush(fill)
        edge = 2.0 if (value or hot) else 1.2
        p.setPen(QPen(color(col, 255 if (value or hot) else 90), edge))
        p.drawRoundedRect(rect, u * 0.16, u * 0.16)
        if move == self.last and not self.finished:
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(color(GOLD), max(1.5, u * 0.04)))
            p.drawRoundedRect(rect.adjusted(-u * 0.035, -u * 0.035, u * 0.035, u * 0.035), u * 0.18, u * 0.18)
        cx, cy = rect.center().x(), rect.center().y()
        if value:
            self.paint_symbol(p, value, cx, cy, u, col, 1.0 + 0.35 * pulse)
        elif hot:
            p.setPen(Qt.NoPen)
            p.setBrush(color(DIM, 200))
            p.drawEllipse(QPointF(cx, cy), u * 0.045, u * 0.045)
        p.restore()

    def paint_symbol(self, p, value, cx, cy, u, col, boost):
        draw_symbol(p, value, cx, cy, u, col, boost)
