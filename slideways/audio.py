"""Musiques OGG locales et effets sonores synthétisés : aucune connexion requise."""
import os
import math
import random
import struct
from pathlib import Path
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

RATE = 44100


def _render(parts, gain=0.5):
    """parts : liste de (durée, fonction(t) -> échantillon). Renvoie du PCM 16 bits stéréo."""
    samples = []
    for duration, fn in parts:
        for i in range(int(duration * RATE)):
            samples.append(fn(i / RATE))
    out = bytearray()
    for s in samples:
        v = int(max(-1.0, min(1.0, s * gain)) * 32767)
        out += struct.pack('<hh', v, v)
    return bytes(out)


def _beep(freq, decay, amp=1.0):
    return lambda t: amp * math.sin(2 * math.pi * freq * t) * math.exp(-t * decay)


def _build_effects():
    rng = random.Random(7)
    noise = [rng.uniform(-1, 1) for _ in range(RATE)]
    state = {'lp': 0.0}

    def whoosh(t):
        i = int(t * RATE) % len(noise)
        state['lp'] += (noise[i] - state['lp']) * (0.10 + 0.5 * t)
        return state['lp'] * math.sin(math.pi * min(1.0, t / 0.16)) * 1.6

    def thump(t):
        freq = 90 + 130 * math.exp(-t * 30)
        return math.sin(2 * math.pi * freq * t) * math.exp(-t * 26)

    return {
        'tick': _render([(0.04, _beep(1500, 70))], 0.28),
        'select': _render([(0.07, _beep(660, 30)), (0.12, _beep(990, 22))], 0.35),
        'back': _render([(0.07, _beep(740, 30)), (0.10, _beep(494, 26))], 0.32),
        'place': _render([(0.14, thump)], 0.7),
        'slide': _render([(0.16, whoosh)], 0.45),
        'win': _render([(0.12, _beep(f, 12)) for f in (523, 659, 784, 1047)], 0.35),
        'draw': _render([(0.14, _beep(392, 14)), (0.22, _beep(311, 12))], 0.35),
    }


class Audio:
    def __init__(self):
        self.ready = False
        self.track = None
        self.volume = 0.30
        self.muted = False
        self.sfx_on = True
        self.error = ''
        self.sounds = {}
        try:
            import pygame.mixer as mixer
            mixer.init(frequency=RATE, size=-16, channels=2, buffer=1024)
            self.mixer = mixer
            self.ready = True
        except Exception as exc:
            self.error = str(exc)
        if self.ready:
            try:
                for name, data in _build_effects().items():
                    self.sounds[name] = self.mixer.Sound(buffer=data)
            except Exception:
                self.sounds = {}

    def play(self, mode):
        if not self.ready or mode == self.track:
            return
        name = 'empacotatron_menu.ogg' if mode == 'menu' else 'empacotatron_loop.ogg'
        try:
            self.mixer.music.load(str(Path(__file__).parent / 'assets' / 'music' / name))
            self.mixer.music.set_volume(0 if self.muted else self.volume)
            self.mixer.music.play(-1, fade_ms=500)
            self.track = mode
        except Exception as exc:
            self.error = str(exc)
            self.ready = False

    def sfx(self, name):
        sound = self.sounds.get(name)
        if not sound or self.muted or not self.sfx_on:
            return
        try:
            sound.set_volume(min(1.0, 0.35 + self.volume * 1.4))
            sound.play()
        except Exception:
            pass

    def set_volume(self, value):
        self.volume = value / 100
        if self.ready:
            self.mixer.music.set_volume(0 if self.muted else self.volume)

    def toggle(self):
        self.muted = not self.muted
        if self.ready:
            self.mixer.music.set_volume(0 if self.muted else self.volume)

    def close(self):
        if self.ready:
            self.mixer.quit()
