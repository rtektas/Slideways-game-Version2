"""Slideways — Neon Arcade. Projet de Resul Tektas."""
import sys
import math
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QSettings
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QRadialGradient, QFont
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QComboBox,
 QVBoxLayout, QHBoxLayout, QGridLayout, QSpinBox, QStackedWidget, QFrame, QSlider,
 QGraphicsDropShadowEffect, QMessageBox)
from controller import Controller, Think, QThreadPool
from partie2 import Game
from audio import Audio

CYAN = '#48ecff'
PINK = '#ff58c8'


def label(text, size=14, color='#a5a0c9', bold=False):
    w = QLabel(text)
    w.setStyleSheet(f'color:{color};font-size:{size}px;font-weight:{"bold" if bold else "normal"};background:transparent;')
    return w


def button(text, action, primary=False):
    b = QPushButton(text); b.setCursor(Qt.PointingHandCursor)
    if primary: b.setObjectName('primary')
    b.clicked.connect(action)
    return b


def glow(widget, color, blur=24):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur); effect.setOffset(0, 0); effect.setColor(QColor(color))
    widget.setGraphicsEffect(effect)


class Backdrop(QWidget):
    def __init__(self):
        super().__init__(); self.phase = 0
        self.anim = QTimer(self); self.anim.timeout.connect(self.tick); self.anim.start(50)
    def tick(self):
        self.phase = (self.phase + 0.012) % 1; self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(),self.height()
        bg = QLinearGradient(0,0,w,h);bg.setColorAt(0,QColor('#100b29'));bg.setColorAt(1,QColor('#060815'))
        p.fillRect(self.rect(),bg)
        for x,y,col,radius in [(w*.8,h*.18,'#622162',w*.5),(w*.1,h*.6,'#073c57',w*.5)]:
            rad = QRadialGradient(QPointF(x,y),radius)
            c=QColor(col);c.setAlpha(120);rad.setColorAt(0,c);rad.setColorAt(1,QColor(0,0,0,0))
            p.fillRect(self.rect(),rad)
        horizon=h*.72
        p.setPen(QPen(QColor(116,61,164,65),1))
        for i in range(-10,11):
            p.drawLine(QPointF(w/2+i*20,horizon),QPointF(w/2+i*w*.13,h))
        for i in range(12):
            t=(i+self.phase)/12; y=horizon+(h-horizon)*t*t
            p.drawLine(QPointF(0,y),QPointF(w,y))
        for i in range(45):
            x=(i*137+37)%max(w,1); y=(i*73+19)%max(int(h*.7),1)
            p.setPen(QColor(170,169,224,55+(i%4)*15));p.drawPoint(x,y)


class Tile(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent); self.value=0; self.recent=False
        self.setFixedSize(60,60); self.setCursor(Qt.PointingHandCursor)
    def paintEvent(self, event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        rect=QRectF(3,3,self.width()-6,self.height()-6)
        col=QColor(CYAN if self.value==1 else PINK if self.value==2 else '#66518d')
        hover=self.underMouse() and self.isEnabled()
        fill=QColor('#13283a' if self.value==1 else '#31152e' if self.value==2 else '#171329')
        if hover: fill=fill.lighter(150)
        p.setBrush(fill);p.setPen(QPen(col if self.value or hover else QColor('#413459'),1.5));p.drawRoundedRect(rect,9,9)
        if self.recent:
            p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor('#ffe398'),2));p.drawRoundedRect(rect.adjusted(-2,-2,2,2),10,10)
        if self.value:
            for thick,alpha in [(10,18),(6,45),(3,255)]:
                c=QColor(col);c.setAlpha(alpha);p.setPen(QPen(c,thick,Qt.SolidLine,Qt.RoundCap));p.setBrush(Qt.NoBrush)
                if self.value==1:
                    p.drawLine(QPointF(20,20),QPointF(40,40));p.drawLine(QPointF(40,20),QPointF(20,40))
                else: p.drawEllipse(QRectF(18,18,24,24))
        else:
            p.setPen(Qt.NoPen);p.setBrush(QColor('#6e5b8b' if hover else '#3e3453'));p.drawEllipse(QPointF(30,30),2,2)
        if not self.isEnabled() and not self.value:
            p.setBrush(QColor(5,4,12,65));p.setPen(Qt.NoPen);p.drawRoundedRect(rect,9,9)


class GamePanel(Controller):
    def __init__(self, shell):
        QWidget.__init__(self)
        self.shell=shell; self.active=False; self.token=0;self.busy=False;self.paused=False;self.jobs={}
        self.pool=QThreadPool(self);self.pool.setMaxThreadCount(1)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.start_ai)
        layout=QVBoxLayout(self);layout.setContentsMargins(16,8,16,8);layout.setSpacing(14)
        top=QHBoxLayout();top.addWidget(label('SLIDEWAYS',25,'#f0e6ff',True));top.addStretch()
        top.addWidget(button('← MENU',self.shell.menu));layout.addLayout(top)
        controls=QHBoxLayout();self.modes=[]
        for i in range(2):
            controls.addWidget(label(f'{"✕" if i==0 else "○"}  JOUEUR {i+1}',13,CYAN if i==0 else PINK,True))
            combo=QComboBox();combo.addItems(['Humain','IA']);combo.setCurrentIndex(i)
            combo.currentIndexChanged.connect(self.mode_changed);self.modes.append(combo);controls.addWidget(combo)
            if i==0: controls.addStretch()
        controls.addSpacing(16);controls.addWidget(label('RYTHME IA',11))
        self.delay=QSpinBox();self.delay.setRange(100,3000);self.delay.setValue(500);self.delay.setSuffix(' ms');self.delay.setSingleStep(100)
        controls.addWidget(self.delay);layout.addLayout(controls)
        self.status=label('',19,'#ffffff',True);self.status.setAlignment(Qt.AlignCenter);self.status.setMinimumHeight(44)
        layout.addWidget(self.status)
        arena=QFrame();arena.setObjectName('arena');arena.setFixedSize(862,310)
        self.grid=QGridLayout(arena);self.grid.setContentsMargins(16,16,16,16);self.grid.setSpacing(6)
        for c in range(1,11): self.grid.setColumnMinimumWidth(c,60)
        self.buttons={};self.arrows={}
        for r in range(4):
            for direction,col,text in [('-',0,'‹'),('+',11,'›')]:
                move=f'{r+1}{direction}';b=button(text,lambda checked=False,m=move:self.human_move(m))
                b.setFixedSize(40,60);b.setStyleSheet('font-size:28px;padding:0px;');b.setAccessibleName('Glisser à gauche' if direction=='-' else 'Glisser à droite')
                self.grid.addWidget(b,3-r,col);self.arrows[move]=b
            for c in range(4):
                move=f'{"ABCD"[c]}{r+1}';b=Tile();b.clicked.connect(lambda checked=False,m=move:self.human_move(m));self.buttons[move]=b
        center=QHBoxLayout();center.addStretch();center.addWidget(arena);center.addStretch();layout.addLayout(center)
        self.last_label=label('',12);self.last_label.setAlignment(Qt.AlignCenter);layout.addWidget(self.last_label)
        hint=label('COLOREZ  •  GLISSEZ  •  ALIGNEZ QUATRE',12,'#80759d',True);hint.setAlignment(Qt.AlignCenter);layout.addWidget(hint)
        row=QHBoxLayout();row.addStretch()
        row.addWidget(button('↻  REJOUER',self.new_game))
        self.pause=button('Ⅱ  PAUSE',self.toggle_pause);row.addWidget(self.pause)
        row.addWidget(button('RÈGLES',self.shell.rules));row.addStretch();layout.addLayout(row)
        layout.addStretch();self.game=Game();self.render()

    def new_game(self):
        self.invalidate();self.game=Game();self.paused=False;self.pause.setText('Ⅱ  PAUSE');self.render();self.schedule()
    def render(self):
        g=self.game;allowed=set(g.legal())
        human=self.active and not self.paused and not self.busy and self.modes[g.turn-1].currentText()=='Humain'
        for b in self.buttons.values(): self.grid.removeWidget(b)
        for r in range(4):
            for c in range(4):
                move=f'{"ABCD"[c]}{r+1}';b=self.buttons[move];b.value=g.board[r][c];b.recent=move==g.last
                b.setAccessibleName(f'Rangée {r+1}, case {c+1}, '+['vide','croix','cercle'][b.value])
                b.setEnabled(human and move in allowed);b.update();self.grid.addWidget(b,3-r,c+g.shifts[r]+4)
        for m,b in self.arrows.items(): b.setEnabled(human and m in allowed)
        if g.result: msg='ÉGALITÉ  —  '+g.reason if g.result=='égalité' else f'VICTOIRE DU JOUEUR {g.result} !'
        elif self.paused: msg='PARTIE EN PAUSE'
        else: msg=f'JOUEUR {g.turn}  •  '+('L’IA RÉFLÉCHIT…' if self.modes[g.turn-1].currentText()=='IA' else 'À VOUS DE JOUER')
        self.status.setText(msg)
        self.last_label.setText(f'{len(g.history):02d} COUPS JOUÉS   /   '+('PARTIE TERMINÉE' if g.result else 'LE CONTOUR DORÉ INDIQUE LA DERNIÈRE CASE JOUÉE'))
    def schedule(self):
        if self.active: super().schedule()
        else: self.timer.stop()
    def start_ai(self):
        if self.active: super().start_ai()
    def human_move(self,move):
        if self.active: super().human_move(move)


class Window(Backdrop):
    def __init__(self):
        super().__init__();self.setWindowTitle('Slideways • Neon Arcade');self.resize(1120,780);self.setMinimumSize(980,740)
        self.settings=QSettings('ResulTektas','SlidewaysArcade')
        self.audio=Audio();self.audio.volume=int(self.settings.value('volume',30))/100
        self.audio.muted=str(self.settings.value('muted','false')).lower()=='true'
        self.setStyleSheet('''QWidget{color:#eee7ff;font-family:Consolas,"DejaVu Sans Mono",monospace;font-size:13px;}
          QLabel{background:transparent;} QPushButton{background:#211734;border:1px solid #5d407d;border-radius:7px;padding:11px 20px;font-weight:bold;}
          QPushButton:hover{background:#392049;border:1px solid #ff58c8;} QPushButton:pressed{background:#54275d;}
          QPushButton:disabled{color:#5e536f;border-color:#332744;background:#191222;}
          QPushButton#primary{background:#e653bd;color:#160e24;border:1px solid #ff9bdd;font-size:19px;padding:16px;}
          QPushButton#primary:hover{background:#ff83d7;} QComboBox,QSpinBox{background:#20162f;border:1px solid #594074;border-radius:5px;padding:8px;}
          QComboBox QAbstractItemView{background:#211734;color:white;selection-background-color:#713363;}
          QFrame#arena{background:rgba(12,9,27,210);border:1px solid #624275;border-radius:18px;}
          QSlider::groove:horizontal{height:4px;background:#49365c;border-radius:2px;}
          QSlider::handle:horizontal{background:#48ecff;width:12px;margin:-5px 0;border-radius:5px;}
          QMessageBox{background:#171026;}
        ''')
        outer=QVBoxLayout(self);outer.setContentsMargins(28,18,28,14)
        host=QWidget();host.setMaximumWidth(1040);middle=QHBoxLayout();middle.addStretch();middle.addWidget(host);middle.addStretch();outer.addLayout(middle,1)
        inner=QVBoxLayout(host);inner.setContentsMargins(0,0,0,0)
        self.stack=QStackedWidget();inner.addWidget(self.stack)
        self.menu_page=self.build_menu();self.stack.addWidget(self.menu_page)
        self.panel=GamePanel(self);self.stack.addWidget(self.panel)
        footer=QHBoxLayout();footer.addWidget(label('RESUL TEKTAS  /  NEON ARCADE',10,'#8b7aa4'));footer.addStretch()
        self.sound_button=button('',self.toggle_sound);footer.addWidget(self.sound_button)
        self.volume=QSlider(Qt.Horizontal);self.volume.setRange(0,100);self.volume.setValue(int(self.audio.volume*100));self.volume.setFixedWidth(100)
        self.volume.valueChanged.connect(self.change_volume);footer.addWidget(self.volume)
        footer.addWidget(button('CRÉDITS',self.credits));inner.addLayout(footer)
        self.refresh_sound();self.menu()

    def build_menu(self):
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(40,10,40,25);v.setSpacing(12);v.addStretch()
        tag=label('✦  STRATEGY MEETS ARCADE  ✦',12,CYAN,True);tag.setAlignment(Qt.AlignCenter);v.addWidget(tag)
        title=label('SLIDEWAYS',70,'#f9eaff',True);title.setAlignment(Qt.AlignCenter);glow(title,PINK,32);v.addWidget(title)
        sub=label('DÉPLACEZ LES LIGNES. CHANGEZ LA PARTIE.',13,'#c2acd8');sub.setAlignment(Qt.AlignCenter);v.addWidget(sub)
        art=QHBoxLayout();art.addStretch()
        for value in [1,0,2,1]:
            t=Tile();t.value=value;t.setEnabled(False);art.addWidget(t)
        art.addStretch();v.addLayout(art);v.addSpacing(15)
        modes=QHBoxLayout();modes.addStretch();modes.addWidget(label('MODE DE JEU',12))
        self.mode=QComboBox();self.mode.addItems(['SOLO  /  CONTRE L’IA','DUEL  /  DEUX JOUEURS','DÉMO  /  IA CONTRE IA']);self.mode.setMinimumWidth(280)
        modes.addWidget(self.mode);modes.addStretch();v.addLayout(modes)
        start=button('▶   JOUER',self.start,True);start.setFixedWidth(380);glow(start,'#a62e83',20);v.addWidget(start,0,Qt.AlignCenter)
        self.resume_button=button('REPRENDRE LA PARTIE',self.resume);self.resume_button.setFixedWidth(380);v.addWidget(self.resume_button,0,Qt.AlignCenter)
        extras=QHBoxLayout();extras.addStretch();extras.addWidget(button('COMMENT JOUER',self.rules));extras.addWidget(button('QUITTER',self.close));extras.addStretch();v.addLayout(extras)
        v.addSpacing(8);note=label('4 SYMBOLES ALIGNÉS. UNE SEULE VICTOIRE.',11,'#88769f');note.setAlignment(Qt.AlignCenter);v.addWidget(note);v.addStretch()
        return page

    def refresh_sound(self):
        self.sound_button.setText('SON INDISPONIBLE' if not self.audio.ready else 'SON : OFF' if self.audio.muted else 'SON : ON')
        self.sound_button.setToolTip(self.audio.error if not self.audio.ready else 'Couper ou rétablir la musique')
    def toggle_sound(self):
        self.audio.toggle();self.settings.setValue('muted',self.audio.muted);self.refresh_sound()
    def change_volume(self,value):
        self.audio.set_volume(value);self.settings.setValue('volume',value)
    def start(self):
        p=self.panel;p.active=False;p.invalidate()
        index=self.mode.currentIndex()
        p.modes[0].setCurrentIndex(1 if index==2 else 0);p.modes[1].setCurrentIndex(0 if index==1 else 1)
        p.active=True;p.new_game();self.stack.setCurrentWidget(p);self.audio.play('game');self.refresh_sound()
    def menu(self):
        p=self.panel;p.active=False;p.invalidate();p.render()
        self.resume_button.setVisible(bool(p.game.history) and not p.game.result)
        self.stack.setCurrentWidget(self.menu_page);self.audio.play('menu');self.refresh_sound()
    def resume(self):
        p=self.panel;p.active=True;p.render();p.schedule();self.stack.setCurrentWidget(p);self.audio.play('game');self.refresh_sound()
    def rules(self):
        QMessageBox.information(self,'Comment jouer',
            'BUT : aligner quatre symboles de votre couleur, en ligne, colonne ou diagonale.\n\n'
            'À VOTRE TOUR : cliquez sur une case vide ou adverse pour la colorer, OU sur une flèche pour déplacer une rangée.\n\n'
            'Vous ne pouvez pas rejouer immédiatement la dernière case ni annuler le dernier glissement. Chaque rangée peut glisser de trois cases dans chaque sens.\n\n'
            'Les cases restent solidaires de leur rangée. Deux couleurs gagnantes en même temps donnent une égalité. Trois répétitions ou 300 coups terminent aussi la partie à égalité.')
    def credits(self):
        QMessageBox.information(self,'Crédits',
            'SLIDEWAYS — Projet de Resul Tektas\nNeon Arcade edition\n\n'
            'Musique : Empacotatron, par Fupi\nVersions menu et loop — CC0 1.0\n'
            'https://opengameart.org/content/empacotatron\n\n'
            'Décor, grille et symboles : graphismes vectoriels dessinés par le jeu.\n'
            'Sources et licence : CREDITS.md. Musiques incluses, aucun streaming.')
    def closeEvent(self,event):
        self.panel.invalidate();self.panel.pool.waitForDone();self.audio.close();self.settings.sync();event.accept()


if __name__=='__main__':
    app=QApplication(sys.argv);window=Window();window.show();sys.exit(app.exec_())
