"""Palette, polices, animations et petits outils de dessin partagés."""
import math
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (QColor, QFont, QFontMetricsF, QPainterPath, QPen, QPixmap,
                         QPainter, QIcon)

# Les deux couleurs de joueurs sont les seules couleurs vives : le reste est neutre.
INK = '#f4eeff'
MUTED = '#a69cc4'
DIM = '#645a82'
FAINT = '#2a2145'
CYAN = '#48ecff'
PINK = '#ff58c8'
GOLD = '#ffd98a'
BG_TOP = '#0d0a1f'
BG_BOTTOM = '#05040c'

FAMILIES = ['Bahnschrift', 'Segoe UI', 'Helvetica Neue', 'DejaVu Sans', 'Arial']


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(int(max(0, min(255, alpha))))
    return c


def mix(a, b, t):
    ca, cb = QColor(a), QColor(b)
    t = max(0.0, min(1.0, t))
    return QColor(int(ca.red() + (cb.red() - ca.red()) * t),
                  int(ca.green() + (cb.green() - ca.green()) * t),
                  int(ca.blue() + (cb.blue() - ca.blue()) * t))


WRAP_TOP_LEFT = int(Qt.AlignLeft) | int(Qt.AlignTop) | int(Qt.TextWordWrap)
WRAP = int(Qt.TextWordWrap)
WRAP_LEFT = int(Qt.AlignLeft) | int(Qt.TextWordWrap)


def font(px, weight=QFont.Normal, spacing=0.0):
    f = QFont()
    try:
        f.setFamilies(FAMILIES)
    except AttributeError:          # très anciennes versions de Qt
        f.setFamily(FAMILIES[1])
    f.setPixelSize(max(6, int(px)))
    f.setWeight(weight)
    if spacing:
        f.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    return f


def text_width(f, text):
    return QFontMetricsF(f).horizontalAdvance(text)


# --- animation -----------------------------------------------------------
def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def approach(current, target, dt, speed=14.0):
    """Rapprochement exponentiel, indépendant du nombre d'images par seconde."""
    value = current + (target - current) * (1 - math.exp(-speed * dt))
    return target if abs(target - value) < 0.0015 else value


# --- dessin ----------------------------------------------------------------
def draw_text(p, x, y, text, f, col, align='left'):
    """Texte posé sur la ligne de base y. col est un QColor."""
    w = text_width(f, text)
    if align == 'center':
        x -= w / 2
    elif align == 'right':
        x -= w
    p.setFont(f)
    p.setPen(col)
    p.drawText(QPointF(x, y), text)
    return w


def glow_text(p, x, y, text, f, col, glow, strength=1.0, align='left'):
    w = text_width(f, text)
    if align == 'center':
        x -= w / 2
    elif align == 'right':
        x -= w
    path = QPainterPath()
    path.addText(QPointF(x, y), f, text)
    k = f.pixelSize() / 70.0
    p.save()
    p.setBrush(Qt.NoBrush)
    for width, alpha in ((14, 16), (8, 30), (3.5, 56)):
        pen = QPen(color(glow, alpha * strength), max(1.0, width * k))
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.setBrush(col)
    p.drawPath(path)
    p.restore()
    return w


def draw_keycap(p, x, y, key, label, size=12):
    """Pastille de touche suivie de son action, comme sur une console. Renvoie la largeur."""
    kf = font(size - 1, QFont.DemiBold)
    lf = font(size)
    kw = text_width(kf, key) + 14
    box = QRectF(x, y - size - 4, kw, size + 10)
    p.setPen(QPen(color(DIM, 220), 1.2))
    p.setBrush(color('#ffffff', 10))
    p.drawRoundedRect(box, 5, 5)
    draw_text(p, x + 7, y + 1, key, kf, color(INK, 230))
    lw = draw_text(p, x + kw + 8, y + 1, label, lf, color(MUTED, 230))
    return kw + 8 + lw


def draw_tile_mark(p, cx, cy, u, t=0.0, alpha=255):
    """Le logo : deux rangées de pastilles qui glissent en sens inverse."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    slide = math.sin(t * 1.6) * 0.5
    rows = [(-0.55, slide, [CYAN, None, PINK]), (0.55, -slide, [PINK, None, CYAN])]
    for row_y, off, cols in rows:
        for i, col in enumerate(cols):
            x = cx + (i - 1 + off) * u * 1.12 - u / 2
            y = cy + row_y * u * 1.12 - u / 2
            rect = QRectF(x, y, u, u)
            p.setBrush(color('#ffffff', 8 * alpha / 255))
            p.setPen(QPen(color(col or DIM, (200 if col else 110) * alpha / 255), max(1.2, u * 0.07)))
            p.drawRoundedRect(rect, u * 0.2, u * 0.2)
    p.restore()


def app_icon():
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(color('#0d0a1f'))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(0, 0, 64, 64), 14, 14)
    draw_tile_mark(p, 32, 32, 15, 0.0)
    p.end()
    return QIcon(pix)
