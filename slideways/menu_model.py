"""Modèle de menu sans dépendance graphique : sélection, choix, curseurs, interrupteurs.

L'interface (screens.py) ne fait que dessiner ce modèle et lui transmettre
clavier et souris, ce qui permet de tester la navigation sans écran.
"""


class Item:
    """Une ligne de menu : action, choix dans une liste, curseur ou interrupteur."""

    def __init__(self, kind, label, *, action=None, options=None, index=0,
                 value=0, step=5, on_change=None, hint='', visible=None,
                 enabled=None, wrap=True):
        assert kind in ('action', 'choice', 'slider', 'toggle')
        self.kind = kind
        self.label = label
        self.action = action
        self.options = list(options or [])
        self.index = index
        self.value = value
        self.step = step
        self.on_change = on_change
        self.hint = hint
        self.wrap = wrap
        self._visible = visible
        self._enabled = enabled

    # --- état -----------------------------------------------------------
    def is_visible(self):
        return True if self._visible is None else bool(self._visible())

    def is_enabled(self):
        return True if self._enabled is None else bool(self._enabled())

    def display_value(self):
        if self.kind == 'choice':
            return str(self.options[self.index])
        if self.kind == 'toggle':
            return 'OUI' if self.value else 'NON'
        if self.kind == 'slider':
            return str(int(self.value))
        return ''

    # --- interactions ---------------------------------------------------
    def _changed(self):
        if self.on_change:
            self.on_change(self.current_value())
        return True

    def current_value(self):
        if self.kind == 'choice':
            return self.index
        return self.value

    def adjust(self, delta):
        """Gauche / droite (delta = -1 ou +1). Renvoie True si la valeur change."""
        if self.kind == 'choice' and self.options:
            new = self.index + delta
            if self.wrap:
                new %= len(self.options)
            else:
                new = max(0, min(len(self.options) - 1, new))
            if new == self.index:
                return False
            self.index = new
            return self._changed()
        if self.kind == 'slider':
            new = max(0, min(100, self.value + delta * self.step))
            if new == self.value:
                return False
            self.value = new
            return self._changed()
        if self.kind == 'toggle':
            self.value = not self.value
            return self._changed()
        return False

    def set_value(self, value):
        """Affecte directement (clic sur un curseur, ou choix par index)."""
        if self.kind == 'choice':
            value = max(0, min(len(self.options) - 1, int(value)))
        elif self.kind == 'slider':
            value = max(0, min(100, int(value)))
        else:
            value = bool(value)
        same = (value == (self.index if self.kind == 'choice' else self.value))
        if self.kind == 'choice':
            self.index = value
        else:
            self.value = value
        return False if same else self._changed()

    def activate(self):
        """Entrée / clic. Renvoie True si quelque chose s'est produit."""
        if not self.is_enabled():
            return False
        if self.kind == 'action':
            if self.action:
                self.action()
            return True
        if self.kind in ('toggle', 'choice'):
            return self.adjust(1)
        return False


class ListModel:
    def __init__(self, items):
        self.items = list(items)
        self.selected = 0
        self.snap()

    def visible(self):
        return [i for i in self.items if i.is_visible()]

    def selectable(self):
        return [i for i in self.visible() if i.is_enabled()]

    def current(self):
        shown = self.visible()
        if not shown:
            return None
        self.selected = max(0, min(len(shown) - 1, self.selected))
        return shown[self.selected]

    def snap(self):
        """Replace la sélection sur une ligne visible et active."""
        shown = self.visible()
        if not shown:
            self.selected = 0
            return
        self.selected = max(0, min(len(shown) - 1, self.selected))
        if not shown[self.selected].is_enabled():
            self.move(1)

    def move(self, delta):
        shown = self.visible()
        if not shown:
            return False
        start = self.selected
        pos = start
        for _ in range(len(shown)):
            pos = (pos + delta) % len(shown)
            if shown[pos].is_enabled():
                break
        else:
            return False
        self.selected = pos
        return pos != start

    def select_item(self, item):
        shown = self.visible()
        if item in shown and item.is_enabled():
            changed = shown.index(item) != self.selected
            self.selected = shown.index(item)
            return changed
        return False

    def index_of(self, item):
        shown = self.visible()
        return shown.index(item) if item in shown else -1

    def adjust(self, delta):
        item = self.current()
        return bool(item and item.is_enabled() and item.adjust(delta))

    def activate(self):
        item = self.current()
        return bool(item and item.activate())
