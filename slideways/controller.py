"""Gestion de la partie : tours, joueurs humains ou IA, calcul de l'IA en arrière-plan."""
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal
from partie2 import Game, choisir_coup_niveau


class _Signals(QObject):
    done = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)


class Think(QRunnable):
    def __init__(self, token, game, niveau):
        super().__init__()
        self.token = token
        self.args = ([r[:] for r in game.board], game.shifts[:], game.turn, game.last, niveau)
        self.signals = _Signals()

    def run(self):
        try:
            self.signals.done.emit(self.token, choisir_coup_niveau(*self.args))
        except Exception as exc:
            self.signals.failed.emit(self.token, str(exc))


class Match(QObject):
    changed = pyqtSignal()
    moved = pyqtSignal(str, int)      # coup joué, joueur qui l'a joué
    ended = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = Game()
        self.kinds = ['human', 'ai']
        self.level = 1
        self.delay = 500
        self.active = False
        self.paused = False
        self.busy = False
        self.token = 0
        self.jobs = {}
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.start_ai)

    # --- état -----------------------------------------------------------
    def invalidate(self):
        self.token += 1
        self.timer.stop()
        self.busy = False

    def in_progress(self):
        return bool(self.game.history) and not self.game.result

    def is_ai(self, player):
        return self.kinds[player - 1] == 'ai'

    def human_turn(self):
        g = self.game
        return (self.active and not self.paused and not self.busy and not g.result
                and not self.is_ai(g.turn))

    def allowed(self):
        return set(self.game.legal()) if self.human_turn() else set()

    # --- commandes --------------------------------------------------------
    def new_game(self):
        self.invalidate()
        self.game = Game()
        self.paused = False
        self.changed.emit()
        self.schedule()

    def set_kind(self, index, kind):
        self.kinds[index] = kind
        self.invalidate()
        self.changed.emit()
        self.schedule()

    def toggle_kind(self, index):
        self.set_kind(index, 'human' if self.kinds[index] == 'ai' else 'ai')

    def set_active(self, active):
        self.active = active
        self.invalidate()
        self.changed.emit()
        self.schedule()

    def set_paused(self, paused):
        self.invalidate()
        self.paused = paused
        self.changed.emit()
        self.schedule()

    def human_move(self, move):
        if not self.human_turn():
            return False
        return self.apply(move)

    def apply(self, move):
        player = self.game.turn
        try:
            self.game.play(move)
        except ValueError:
            return False
        self.moved.emit(move, player)
        self.changed.emit()
        if self.game.result:
            self.ended.emit()
        self.schedule()
        return True

    # --- IA ---------------------------------------------------------------
    def schedule(self):
        self.timer.stop()
        g = self.game
        if self.active and not self.paused and not g.result and self.is_ai(g.turn):
            self.timer.start(self.delay)

    def start_ai(self):
        g = self.game
        if not self.active or g.result or self.paused or self.busy or not self.is_ai(g.turn):
            return
        self.busy = True
        job = Think(self.token, g, self.level)
        self.jobs[self.token] = job
        job.signals.done.connect(self.ai_done)
        job.signals.failed.connect(self.ai_failed)
        self.changed.emit()
        self.pool.start(job)

    def ai_done(self, token, move):
        self.jobs.pop(token, None)
        if token != self.token:
            return
        self.busy = False
        if move is not None:
            self.apply(move)
        else:
            self.changed.emit()

    def ai_failed(self, token, message):
        self.jobs.pop(token, None)
        if token != self.token:
            return
        self.busy = False
        self.paused = True
        self.changed.emit()
        self.failed.emit(message)

    def shutdown(self):
        self.invalidate()
        self.pool.waitForDone()
