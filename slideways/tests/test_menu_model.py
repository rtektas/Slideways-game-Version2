import unittest
from menu_model import Item, ListModel


class MenuModel(unittest.TestCase):
    def make(self):
        self.calls = []
        self.show_resume = False
        items = [
            Item('action', 'CONTINUER', action=lambda: self.calls.append('resume'),
                 visible=lambda: self.show_resume),
            Item('action', 'JOUER', action=lambda: self.calls.append('play')),
            Item('choice', 'Difficulté', options=['Facile', 'Normal', 'Difficile', 'Expert'], index=1,
                 on_change=lambda v: self.calls.append(('level', v))),
            Item('slider', 'Volume', value=30, step=10, on_change=lambda v: self.calls.append(('vol', v))),
            Item('toggle', 'Effets', value=True, on_change=lambda v: self.calls.append(('fx', v))),
            Item('action', 'GRISÉ', enabled=lambda: False),
            Item('action', 'QUITTER', action=lambda: self.calls.append('quit')),
        ]
        return ListModel(items)

    def test_hidden_item_is_skipped(self):
        m = self.make()
        self.assertEqual(m.current().label, 'JOUER')
        self.show_resume = True
        m.snap()
        self.assertEqual([i.label for i in m.visible()][0], 'CONTINUER')

    def test_move_wraps_and_skips_disabled(self):
        m = self.make()
        labels = []
        for _ in range(7):
            labels.append(m.current().label)
            m.move(1)
        self.assertEqual(labels, ['JOUER', 'Difficulté', 'Volume', 'Effets', 'QUITTER', 'JOUER', 'Difficulté'])
        m.selected = 0
        m.move(-1)
        self.assertEqual(m.current().label, 'QUITTER')

    def test_choice_wraps_and_notifies(self):
        m = self.make()
        m.move(1)
        self.assertEqual(m.current().display_value(), 'Normal')
        m.adjust(1); m.adjust(1); m.adjust(1)
        self.assertEqual(m.current().display_value(), 'Facile')
        self.assertEqual(self.calls[-1], ('level', 0))
        m.adjust(-1)
        self.assertEqual(m.current().display_value(), 'Expert')

    def test_slider_clamps(self):
        m = self.make()
        m.move(1); m.move(1)
        item = m.current()
        for _ in range(20):
            item.adjust(1)
        self.assertEqual(item.value, 100)
        self.assertFalse(item.adjust(1))
        item.set_value(-5)
        self.assertEqual(item.value, 0)

    def test_toggle_and_activate(self):
        m = self.make()
        m.selected = 0
        self.assertTrue(m.activate())
        self.assertEqual(self.calls, ['play'])
        m.move(1); m.move(1); m.move(1)
        self.assertEqual(m.current().label, 'Effets')
        m.activate()
        self.assertFalse(m.current().value)
        self.assertEqual(self.calls[-1], ('fx', False))

    def test_select_item_ignores_disabled(self):
        m = self.make()
        disabled = [i for i in m.items if i.label == 'GRISÉ'][0]
        self.assertFalse(m.select_item(disabled))
        self.assertFalse(disabled.activate())

if __name__ == '__main__':
    unittest.main()
