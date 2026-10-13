"""Écrans du jeu : menus, intro, tutoriel, crédits. Tout est dessiné, aucune fenêtre externe."""
import math
import random
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFont, QFontMetricsF, QLinearGradient, QBrush
from PyQt5.QtWidgets import QWidget
from board_view import BoardView
from partie2 import Game, choisir_coup
from rules_data import RULES_SLIDES
from theme import (INK, MUTED, DIM, CYAN, PINK, color, font, text_width, draw_text,
                   glow_text, draw_keycap, draw_tile_mark, approach, ease_out_cubic, clamp,
                   WRAP_TOP_LEFT, WRAP, WRAP_LEFT)


class Fade(QWidget):
    """Fondu au noir entre deux écrans."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.alpha = 0.0
        self.phase = 'idle'
        self.callback = None
        self.hide()

    def start(self, callback):
        self.callback = callback
        self.phase = 'out'
        self.show()
        self.raise_()

    def advance(self, dt):
        if self.phase == 'out':
            self.alpha = min(1.0, self.alpha + dt / 0.13)
            if self.alpha >= 1.0:
                callback, self.callback = self.callback, None
                self.phase = 'in'
                if callback:
                    callback()
        elif self.phase == 'in':
            self.alpha = max(0.0, self.alpha - dt / 0.22)
            if self.alpha <= 0.0:
                self.phase = 'idle'
                self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), color('#05040c', 255 * self.alpha))
        p.end()


class ListScreen(QWidget):
    """Liste verticale pilotée au clavier et à la souris : menus, réglages, fenêtres internes."""
    sfx = pyqtSignal(str)
    backRequested = pyqtSignal()

    def __init__(self, model, title='', subtitle='', big=False, overlay=False, parent=None):
        super().__init__(parent)
        self.model = model
        self.title = title
        self.subtitle = subtitle
        self.big = big
        self.overlay = overlay
        self.title_color = INK
        self.hints = [('↑ ↓', 'Naviguer'), ('Entrée', 'Valider'), ('Échap', 'Retour')]
        self.footer_right = ''
        self.right_painter = None
        self.advance_hook = None
        self.time = 0.0
        self.bar_y = None
        self.shift = {}
        self.slider_rects = {}
        self.dragging = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    # --- géométrie --------------------------------------------------------
    def margin(self):
        return max(56.0, self.width() * 0.075)

    def rows_top(self):
        return self.height() * 0.46

    def metrics(self):
        w, h = self.width(), self.height()
        if self.overlay:
            n = len(self.model.visible())
            panel_h = 124 + n * 54 + 24
            panel = QRectF((w - 460) / 2, (h - panel_h) / 2, 460, panel_h)
            return {'px': 22, 'row_h': 54, 'x': panel.left() + 30, 'w': 400,
                    'y': panel.top() + 110, 'panel': panel}
        if self.big:
            return {'px': min(36, h * 0.05), 'row_h': min(60, h * 0.078), 'x': self.margin(),
                    'w': 400, 'y': self.rows_top(), 'panel': None}
        return {'px': 21, 'row_h': 56, 'x': self.margin(), 'w': 520, 'y': h * 0.30, 'panel': None}

    def compute_rows(self, m=None):
        m = m or self.metrics()
        rows = []
        for i, item in enumerate(self.model.visible()):
            rows.append((item, QRectF(m['x'], m['y'] + i * m['row_h'], m['w'], m['row_h'])))
        return rows

    def row_at(self, pos):
        point = QPointF(pos)
        for item, rect in self.compute_rows():
            if rect.contains(point):
                return item, rect
        return None, None

    def reset_selection(self):
        self.model.selected = 0
        self.model.snap()
        self.bar_y = None

    # --- animation -----------------------------------------------------------
    def advance(self, dt):
        self.time += dt
        current = self.model.current()
        for item, rect in self.compute_rows():
            target = (14.0 if self.big else 8.0) if item is current else 0.0
            self.shift[id(item)] = approach(self.shift.get(id(item), 0.0), target, dt, 16.0)
            if item is current:
                cy = rect.center().y()
                self.bar_y = cy if self.bar_y is None else approach(self.bar_y, cy, dt, 18.0)
        if self.advance_hook:
            self.advance_hook(dt)

    def showEvent(self, event):
        super().showEvent(event)
        self.bar_y = None
        self.setFocus()

    # --- dessin ----------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = self.metrics()
        if self.overlay:
            panel = m['panel']
            p.fillRect(self.rect(), color('#05040c', 175))
            p.setBrush(color('#110d24', 248))
            p.setPen(QPen(color('#3a2d5e'), 1.2))
            p.drawRoundedRect(panel, 14, 14)
            draw_text(p, panel.center().x(), panel.top() + 58, self.title,
                      font(30, QFont.DemiBold, 1.0), color(self.title_color), 'center')
            if self.subtitle:
                draw_text(p, panel.center().x(), panel.top() + 86, self.subtitle,
                          font(14), color(MUTED), 'center')
        else:
            self.paint_header(p, m)
            if self.right_painter:
                self.right_painter(p, self)
        self.paint_rows(p, m, self.compute_rows(m))
        if not self.overlay:
            self.paint_footer(p)
        p.end()

    def paint_header(self, p, m):
        x = self.margin()
        draw_text(p, x, self.height() * 0.17 + 30, self.title, font(42, QFont.DemiBold, 1.0), color(INK))
        if self.subtitle:
            draw_text(p, x + 2, self.height() * 0.17 + 62, self.subtitle, font(16), color(MUTED))

    def paint_rows(self, p, m, rows):
        current = self.model.current()
        px = m['px']
        if not self.overlay and current is not None and rows:
            for item, rect in rows:
                if item is current:
                    cy = self.bar_y if self.bar_y is not None else rect.center().y()
                    band = QRectF(rect.left() - 14, cy - rect.height() / 2, rect.width() + 28, rect.height())
                    grad = QLinearGradient(band.left(), 0, band.right(), 0)
                    grad.setColorAt(0.0, color(CYAN, 44))
                    grad.setColorAt(1.0, color(PINK, 0))
                    p.fillRect(band, QBrush(grad))
                    bar = QRectF(rect.left() - 12, cy - rect.height() * 0.3, 4, rect.height() * 0.6)
                    g2 = QLinearGradient(0, bar.top(), 0, bar.bottom())
                    g2.setColorAt(0.0, color(CYAN))
                    g2.setColorAt(1.0, color(PINK))
                    p.setPen(Qt.NoPen)
                    p.setBrush(QBrush(g2))
                    p.drawRoundedRect(bar, 2, 2)
        for item, rect in rows:
            sel = item is current
            enabled = item.is_enabled()
            col = INK if sel else (MUTED if enabled else DIM)
            if not enabled:
                col = DIM
            elif getattr(item, 'accent', False) and not sel:
                col = CYAN
            weight = QFont.DemiBold if (sel or self.big) else QFont.Normal
            f = font(px, weight, px * 0.04 if self.big else 0.4)
            base = rect.center().y() + px * 0.34
            if self.overlay:
                if sel:
                    p.setBrush(color('#ffffff', 16))
                    p.setPen(Qt.NoPen)
                    p.drawRoundedRect(rect.adjusted(-10, 4, 10, -4), 8, 8)
                draw_text(p, rect.center().x(), base, item.label, f, color(col), 'center')
                continue
            draw_text(p, rect.left() + 22 + self.shift.get(id(item), 0.0), base, item.label, f, color(col))
            if item.kind != 'action':
                self.paint_value(p, item, rect, sel, px)
        if current is not None and current.hint and not self.overlay and rows:
            last = rows[-1][1]
            hint_rect = QRectF(m['x'] + 22, last.bottom() + 18, m['w'] - 20, 80)
            p.setFont(font(15))
            p.setPen(color(MUTED, 220))
            p.drawText(hint_rect, WRAP_TOP_LEFT, current.hint)

    def paint_value(self, p, item, rect, sel, px):
        right = rect.right() - 20
        small = font(px * 0.88, QFont.DemiBold)
        col = color(INK if sel else MUTED)
        base = rect.center().y() + px * 0.30
        if item.kind == 'slider':
            width = 170.0
            track = QRectF(right - width - 42, rect.center().y() - 2, width, 4)
            self.slider_rects[id(item)] = track
            frac = item.value / 100.0
            p.setPen(Qt.NoPen)
            p.setBrush(color('#3a2f58'))
            p.drawRoundedRect(track, 2, 2)
            p.setBrush(color(CYAN if sel else MUTED))
            p.drawRoundedRect(QRectF(track.left(), track.top(), width * frac, 4), 2, 2)
            p.setBrush(color(INK))
            r = 7 if sel else 5
            p.drawEllipse(QPointF(track.left() + width * frac, track.center().y()), r, r)
            draw_text(p, right, base, str(int(item.value)), small, col, 'right')
        elif item.kind == 'toggle':
            on = bool(item.value)
            pill = QRectF(right - 46, rect.center().y() - 11, 46, 22)
            p.setPen(QPen(color(CYAN if on else DIM, 230), 1.5))
            p.setBrush(color(CYAN, 55) if on else color('#ffffff', 8))
            p.drawRoundedRect(pill, 11, 11)
            p.setPen(Qt.NoPen)
            p.setBrush(color(CYAN if on else MUTED))
            p.drawEllipse(QPointF(pill.right() - 11 if on else pill.left() + 11, pill.center().y()), 7, 7)
        else:
            text = item.display_value()
            tw = text_width(small, text)
            draw_text(p, right - 20, base, text, small, col, 'right')
            if sel:
                arrows = font(px * 1.1)
                draw_text(p, right - 20 - tw - 22, base, '‹', arrows, color(CYAN))
                draw_text(p, right, base, '›', arrows, color(CYAN), 'right')

    def paint_footer(self, p):
        x = self.margin()
        y = self.height() - 30
        for key, label in self.hints:
            x += draw_keycap(p, x, y, key, label) + 24
        if self.footer_right:
            draw_text(p, self.width() - self.margin(), y, self.footer_right, font(12), color(DIM), 'right')

    # --- entrées -----------------------------------------------------------------
    def drag_to(self, x):
        item = self.dragging
        track = self.slider_rects.get(id(item)) if item is not None else None
        if track is None or track.width() <= 0:
            return
        item.set_value(round((x - track.left()) / track.width() * 100))
        self.update()

    def mouseMoveEvent(self, event):
        if self.dragging is not None:
            self.drag_to(event.pos().x())
            return
        item, rect = self.row_at(event.pos())
        if item is not None and item.is_enabled():
            if self.model.select_item(item):
                self.sfx.emit('tick')
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()
        self.update()

    def mousePressEvent(self, event):
        if event.button() not in (Qt.LeftButton, Qt.RightButton):
            return
        item, rect = self.row_at(event.pos())
        if item is None or not item.is_enabled():
            return
        self.model.select_item(item)
        step = -1 if event.button() == Qt.RightButton else 1
        if item.kind == 'slider':
            self.dragging = item
            self.drag_to(event.pos().x())
            self.sfx.emit('tick')
        elif item.kind == 'action':
            if event.button() == Qt.LeftButton:
                self.sfx.emit('select')
                item.activate()
        elif item.kind == 'choice':
            item.adjust(step)
            self.sfx.emit('tick')
        else:
            item.activate()
            self.sfx.emit('tick')
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = None

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Up, Qt.Key_W):
            if self.model.move(-1):
                self.sfx.emit('tick')
        elif key in (Qt.Key_Down, Qt.Key_S):
            if self.model.move(1):
                self.sfx.emit('tick')
        elif key in (Qt.Key_Left, Qt.Key_A):
            if self.model.adjust(-1):
                self.sfx.emit('tick')
        elif key in (Qt.Key_Right, Qt.Key_D):
            if self.model.adjust(1):
                self.sfx.emit('tick')
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            item = self.model.current()
            if item is not None and item.is_enabled():
                self.sfx.emit('select' if item.kind == 'action' else 'tick')
                item.activate()
        elif key in (Qt.Key_Escape, Qt.Key_Backspace):
            self.sfx.emit('back')
            self.backRequested.emit()
        else:
            event.ignore()
            return
        self.update()


class MainMenu(ListScreen):
    """Menu principal : titre découpé en bandes qui glissent, démonstration jouée en direct."""

    def __init__(self, model, parent=None):
        super().__init__(model, big=True, parent=parent)
        self.hints = [('↑ ↓', 'Naviguer'), ('Entrée', 'Choisir'), ('Échap', 'Quitter')]
        self.footer_right = 'Slideways  v1.0'
        self.intro = 0.0
        self.long_intro = True
        self.glitch = (0, 9.0)
        self.glitch_wait = 5.0
        self.hero = BoardView(interactive=False, parent=self)
        self.hero.setMinimumSize(10, 10)
        self.demo = Game()
        self.demo_wait = 1.2
        self.demo_hold = False

    # --- géométrie ---------------------------------------------------------------
    def title_px(self):
        return min(self.width() * 0.105, self.height() * 0.16)

    def title_base(self):
        return self.height() * 0.13 + self.title_px() * 0.9

    def rows_top(self):
        return self.title_base() + self.title_px() * 0.42 + 66

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        width = int(w * 0.50)
        if hasattr(self, 'hero'):
            self.hero.setGeometry(int(w * 0.47), int(h * 0.36), width, int(width * 0.37))
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.intro = 0.0 if self.long_intro else 0.55
        self.long_intro = False
        self.demo = Game()
        self.demo_hold = False
        self.demo_wait = 1.0
        self.hero.set_game(self.demo, animate=False)

    # --- animation -----------------------------------------------------------------
    def advance(self, dt):
        super().advance(dt)
        self.intro += dt
        self.glitch_wait -= dt
        if self.glitch_wait <= 0 and self.intro > 1.8:
            self.glitch = (random.randrange(3), 0.0)
            self.glitch_wait = random.uniform(5.0, 9.0)
        self.glitch = (self.glitch[0], self.glitch[1] + dt)
        self.demo_wait -= dt
        if self.demo_wait <= 0:
            self.demo_step()
        self.hero.advance(dt)

    def demo_step(self):
        g = self.demo
        if g.result or len(g.history) >= 80:
            if not self.demo_hold:
                self.demo_hold = True
                self.demo_wait = 2.8
                return
            self.demo = Game()
            self.demo_hold = False
            self.demo_wait = 1.0
            self.hero.set_game(self.demo, animate=False)
            return
        move = choisir_coup(g.board, g.shifts, g.turn, g.last, profondeur=1, hasard=0.2)
        if move is None:
            self.demo_hold = True
            self.demo_wait = 0.1
            g.result = 'égalité'
            return
        g.play(move)
        self.hero.set_game(g)
        self.demo_wait = 0.9

    # --- dessin ----------------------------------------------------------------------
    def paint_header(self, p, m):
        px = self.title_px()
        x = self.margin()
        base = self.title_base()
        f = font(px, QFont.Bold, px * 0.03)
        cap = px * 0.72
        top = base - cap
        band = cap / 3.0
        glows = [CYAN, None, PINK]
        for i in range(3):
            delay = i * 0.14
            prog = ease_out_cubic((self.intro - delay) / 0.85)
            direction = -1 if i % 2 == 0 else 1
            off = (1 - prog) * direction * px * 3.2
            if self.glitch[0] == i and self.glitch[1] < 0.4:
                off += math.sin(self.glitch[1] / 0.4 * math.pi) * px * 0.09 * direction
            p.save()
            gap = 1.5
            p.setClipRect(QRectF(0, top + i * band + gap / 2 - (px * 0.04 if i == 0 else 0),
                                 self.width(), band - gap + (px * 0.04 if i == 0 else 0) + (px * 0.3 if i == 2 else 0)))
            glow_text(p, x + off, base, 'SLIDEWAYS', f, color(INK, 255 * prog),
                      glows[i] or PINK, strength=(0.0 if glows[i] is None else prog))
            p.restore()
        tag = clamp((self.intro - 0.9) / 0.6)
        draw_text(p, x + 4, base + px * 0.42, 'Glissez les rangées. Alignez quatre.',
                  font(max(15, px * 0.15), QFont.Normal, 1.2), color(MUTED, 255 * tag))


class Splash(QWidget):
    """Écran de lancement, passable d'une touche ou d'un clic."""
    finished = pyqtSignal()
    LENGTH = 2.7

    def __init__(self, parent=None):
        super().__init__(parent)
        self.time = 0.0
        self.done = False
        self.setFocusPolicy(Qt.StrongFocus)

    def showEvent(self, event):
        super().showEvent(event)
        self.time = 0.0
        self.done = False
        self.setFocus()

    def finish(self):
        if not self.done:
            self.done = True
            self.finished.emit()

    def advance(self, dt):
        self.time += dt
        if self.time >= self.LENGTH:
            self.finish()

    def keyPressEvent(self, event):
        self.finish()

    def mousePressEvent(self, event):
        self.finish()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.time
        a = clamp(t / 0.7) * clamp((self.LENGTH - t) / 0.5)
        cx, cy = self.width() / 2, self.height() / 2
        draw_tile_mark(p, cx, cy - 70, 30, t, 255 * a)
        draw_text(p, cx, cy + 18, 'RESUL TEKTAS', font(30, QFont.DemiBold, 10), color(INK, 255 * a), 'center')
        draw_text(p, cx, cy + 50, 'présente', font(16, QFont.Normal, 3), color(MUTED, 255 * a), 'center')
        p.end()


class RulesScreen(QWidget):
    """Comment jouer : diapositives avec démonstration jouée sur un vrai plateau."""
    sfx = pyqtSignal(str)
    backRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.board = BoardView(interactive=False, parent=self)
        self.board.setMinimumSize(10, 10)
        self.index = 0
        self.fade = 1.0
        self.prev_rect = QRectF()
        self.next_rect = QRectF()
        self.dot_rects = []
        self.load_slide(0)

    def margin(self):
        return max(56.0, self.width() * 0.075)

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        width = int(w * 0.50)
        if hasattr(self, 'board'):
            self.board.setGeometry(int(w * 0.46), int(h * 0.30), width, int(width * 0.37))
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_slide(0)
        self.setFocus()

    def load_slide(self, index, keep_fade=False):
        self.index = max(0, min(len(RULES_SLIDES) - 1, index))
        if not keep_fade:
            self.fade = 0.0
        self.game = Game()
        self.step = 0
        self.wait = 0.9
        self.hold = False
        self.board.set_game(self.game, animate=False)

    def go(self, delta):
        new = self.index + delta
        if 0 <= new < len(RULES_SLIDES):
            self.sfx.emit('tick')
            self.load_slide(new)
        elif new >= len(RULES_SLIDES):
            self.sfx.emit('back')
            self.backRequested.emit()

    def advance(self, dt):
        self.fade = min(1.0, self.fade + dt / 0.35)
        self.board.advance(dt)
        self.wait -= dt
        if self.wait > 0:
            return
        script = RULES_SLIDES[self.index]['script']
        if self.step < len(script):
            self.game.play(script[self.step])
            self.step += 1
            self.board.set_game(self.game)
            self.wait = 0.85
        elif not self.hold:
            self.hold = True
            self.wait = 2.6
        else:
            self.load_slide(self.index, keep_fade=True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        x = self.margin()
        slide = RULES_SLIDES[self.index]
        ease = ease_out_cubic(self.fade)
        off = (1 - ease) * 26
        col_w = min(w * 0.36, 460)
        draw_text(p, x, h * 0.17 + 30, 'Comment jouer', font(16, QFont.Normal, 2), color(MUTED))
        draw_text(p, x + off, h * 0.17 + 84, slide['title'], font(38, QFont.DemiBold, 0.5), color(INK, 255 * ease))
        y = h * 0.17 + 118
        f = font(18)
        fm = QFontMetricsF(f)
        p.setFont(f)
        for paragraph in slide['text']:
            height = fm.boundingRect(QRectF(0, 0, col_w, 1000), WRAP, paragraph).height()
            p.setPen(color(MUTED, 255 * ease))
            p.drawText(QRectF(x + off, y, col_w, height + 4), WRAP_LEFT, paragraph)
            y += height + 20
        self.paint_pager(p, x, h)
        keys_y = h - 30
        kx = x
        for key, label in [('← →', 'Diapositives'), ('Entrée', 'Suivant'), ('Échap', 'Retour')]:
            kx += draw_keycap(p, kx, keys_y, key, label) + 24
        p.end()

    def paint_pager(self, p, x, h):
        y = h * 0.78
        self.dot_rects = []
        dx = x
        for i in range(len(RULES_SLIDES)):
            active = i == self.index
            width = 30 if active else 10
            rect = QRectF(dx, y, width, 10)
            self.dot_rects.append(rect)
            p.setPen(Qt.NoPen)
            if active:
                grad = QLinearGradient(rect.left(), 0, rect.right(), 0)
                grad.setColorAt(0.0, color(CYAN))
                grad.setColorAt(1.0, color(PINK))
                p.setBrush(QBrush(grad))
            else:
                p.setBrush(color('#4a3f6b'))
            p.drawRoundedRect(rect, 5, 5)
            dx += width + 10
        f = font(16, QFont.DemiBold)
        last = self.index == len(RULES_SLIDES) - 1
        prev_col = color(INK if self.index > 0 else DIM)
        draw_text(p, x, y + 58, '‹  Précédent', f, prev_col)
        self.prev_rect = QRectF(x, y + 36, 150, 30)
        label = 'Terminer' if last else 'Suivant  ›'
        nx = x + 190
        draw_text(p, nx, y + 58, label, f, color(CYAN))
        self.next_rect = QRectF(nx, y + 36, 140, 30)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        point = QPointF(event.pos())
        if self.prev_rect.contains(point):
            self.go(-1)
        elif self.next_rect.contains(point):
            self.go(1)
        else:
            for i, rect in enumerate(self.dot_rects):
                if rect.adjusted(-4, -8, 4, 8).contains(point) and i != self.index:
                    self.sfx.emit('tick')
                    self.load_slide(i)

    def mouseMoveEvent(self, event):
        point = QPointF(event.pos())
        hot = self.prev_rect.contains(point) or self.next_rect.contains(point)
        self.setCursor(Qt.PointingHandCursor if hot else Qt.ArrowCursor)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Left, Qt.Key_A):
            self.go(-1)
        elif key in (Qt.Key_Right, Qt.Key_D, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.go(1)
        elif key in (Qt.Key_Escape, Qt.Key_Backspace):
            self.sfx.emit('back')
            self.backRequested.emit()
        else:
            event.ignore()


CREDITS = [
    ('title', 'SLIDEWAYS'),
    ('sub', 'Un jeu de stratégie à deux joueurs'),
    ('gap', 2),
    ('head', 'Conception du jeu'),
    ('line', 'Resul Tektas'),
    ('gap', 1),
    ('head', 'Musique'),
    ('line', '« Empacotatron » par Fupi'),
    ('small', 'Versions menu et partie, licence CC0 1.0'),
    ('small', 'opengameart.org/content/empacotatron'),
    ('gap', 1),
    ('head', 'Effets sonores et graphismes'),
    ('line', 'Générés et dessinés par le jeu'),
    ('small', 'Aucune image ni sonorité tierce'),
    ('gap', 1),
    ('head', 'Technologies'),
    ('line', 'Python 3, PyQt5, pygame-ce'),
    ('gap', 3),
    ('title2', 'Merci d\u2019avoir joué'),
]


class CreditsScreen(QWidget):
    sfx = pyqtSignal(str)
    backRequested = pyqtSignal()
    SPEED = 44.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.scroll = 0.0

    def showEvent(self, event):
        super().showEvent(event)
        self.scroll = float(self.height()) * 0.85
        self.setFocus()

    def line_height(self, kind, value):
        return {'title': 92, 'title2': 80, 'sub': 52, 'head': 50, 'line': 40, 'small': 30}.get(kind, 0) or value * 44

    def total_height(self):
        return sum(self.line_height(k, v) for k, v in CREDITS)

    def advance(self, dt):
        self.scroll -= self.SPEED * dt
        if self.scroll + self.total_height() < -40:
            self.scroll = float(self.height())

    def wheelEvent(self, event):
        self.scroll += event.angleDelta().y() * 0.3

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w / 2
        y = self.scroll
        for kind, value in CREDITS:
            lh = self.line_height(kind, value)
            mid = y + lh / 2
            a = clamp(min(mid / 110.0, (h - 60 - mid) / 110.0))
            if a > 0:
                base = y + lh * 0.7
                if kind == 'title':
                    glow_text(p, cx, base, value, font(64, QFont.Bold, 2), color(INK, 255 * a), PINK, a, 'center')
                elif kind == 'title2':
                    glow_text(p, cx, base, value, font(40, QFont.DemiBold, 1), color(INK, 255 * a), CYAN, a, 'center')
                elif kind == 'sub':
                    draw_text(p, cx, base, value, font(17, QFont.Normal, 1.5), color(MUTED, 255 * a), 'center')
                elif kind == 'head':
                    draw_text(p, cx, base, value, font(15, QFont.DemiBold, 3), color(CYAN, 220 * a), 'center')
                elif kind == 'line':
                    draw_text(p, cx, base, value, font(24, QFont.DemiBold), color(INK, 255 * a), 'center')
                elif kind == 'small':
                    draw_text(p, cx, base, value, font(14), color(MUTED, 230 * a), 'center')
            y += lh
        draw_keycap(p, max(56.0, w * 0.075), h - 30, 'Échap', 'Retour')
        p.end()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Backspace, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.sfx.emit('back')
            self.backRequested.emit()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        self.sfx.emit('back')
        self.backRequested.emit()
