#!/usr/bin/python
# -*- coding: utf-8 -*-
# Python 3

import sys

from PyQt5.Qt import *

class fenetre(QWidget):

    def __init__(self):
        super().__init__()

        # taille de la fenetre
        self.setFixedSize(805, 455)
        self.form = QFormLayout()
        # image d'origine
        self.image = QImage('slideways.jpg')
        self.setWindowTitle("arcade : Slideways")

        image = self.image
        # affiche l'image de fond
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(image))
        self.setPalette(palette)

        # bouton 1
        button = QPushButton('JOUER', self)
        button.setToolTip('Clickez ici')
        button.setStyleSheet('background-color: #ff6699')
        button.setGeometry(200, 200, 200, 50)
        button.setFont(QFont("arial", 20, QFont.Bold))
        button.clicked.connect(self.test)

        # bouton 2
        button2 = QPushButton('QUITTER', self)
        button2.setToolTip('Clickez ici')
        button2.setStyleSheet('background-color: blue')
        button2.setGeometry(200, 270, 200, 50)
        button2.setFont(QFont("arial", 20, QFont.Bold))
        button2.clicked.connect(QApplication.instance().quit)

    def test(self):
        self.a = fenetreJeu()
        self.close()


class fenetreJeu(QWidget):
    def __init__(self):
        super().__init__()
        self.flag = 0
        # taille de la fenetre
        self.setFixedSize(1000, 750)
        self.form = QFormLayout()
        self.move(200, 50)
        self.matrice1 = []
        self.m = []
        self.matrice = []
        self.position = []

        # image d'origine
        self.image = QImage('jeu.jpg')
        self.setWindowTitle("arcade : Slideways")

        image = self.image
        # affiche l'image de fond
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(image))
        self.setPalette(palette)
        self.dernierCoup=()
        self.joueur=1

        self.debut()
        self.show()

    def debut(self):
        self.bouton()
        self.slider()

    def bouton(self):
        x, y = 300, 200
        for i in range(4):
            y += 70
            x = 385
            self.matrice = []
            for j in range(4):
                self.position.append([x, y])
                button3 = QPushButton(self)
                button3.setGeometry(x, y, 50, 50)
                button3.setStyleSheet('background-color: #FFCCFF')
                self.matrice.append(button3)
                x += 60
            self.m.append(self.matrice)
        print(self.m)
        x, y, x1, y1 = 50, 270, 900, 270
        for j in range(4):
            button4 = QPushButton('⬅', self)
            button4.setGeometry(x, y, 50, 50)
            button4.setStyleSheet('background-color: Blue')
            self.matrice1.append(button4)
            y += 70
            button5 = QPushButton('➡︎', self)
            button5.setGeometry(x1, y1, 50, 50)
            button5.setStyleSheet('background-color: #ff6699')
            self.matrice1.append(button5)
            y1 += 70

        self.matrice1[0].clicked.connect(self.affiche1)
        self.matrice1[1].clicked.connect(self.affiche1_1)
        self.matrice1[2].clicked.connect(self.affiche2)
        self.matrice1[3].clicked.connect(self.affiche2_2)
        self.matrice1[4].clicked.connect(self.affiche3)
        self.matrice1[5].clicked.connect(self.affiche3_3)
        self.matrice1[6].clicked.connect(self.affiche4)
        self.matrice1[7].clicked.connect(self.affiche4_4)

        for j in range(4):
            for j in range(16):
                self.couleur(i, j)

    def couleur(self, i, j):
        self.m[i][j].clicked.connect(lambda: self.click(i, j))

    def click(self, i, j):
        self.flag += 1
        self.choix = (i, j)
        if self.joueur == 1 and self.choix != self.dernierCoup:
            self.m[i][j].setStyleSheet("background-color : blue ")
            self.joueur = (self.joueur % 2) +1
            self.dernierCoup = self.choix
        elif self.joueur == 2 and self.choix != self.dernierCoup:
            self.m[i][j].setStyleSheet("background-color : #ff6699")
            self.joueur = (self.joueur % 2) + 1
            self.dernierCoup = self.choix


    def affiche1(self):
        r = 0
        for i in range(4):
            self.position[r][0] = self.position[r][0] - 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche1_1(self):
        r = 0
        for i in range(4):
            self.position[r][0] = self.position[r][0] + 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche2(self):
        r = 4
        for i in range(4):
            self.position[r][0] = self.position[r][0] - 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche2_2(self):
        r = 4
        for i in range(4):
            self.position[r][0] = self.position[r][0] + 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche3(self):
        r = 8
        for i in range(4):
            self.position[r][0] = self.position[r][0] - 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche3_3(self):
        r = 8
        for i in range(4):
            self.position[r][0] = self.position[r][0] + 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche4(self):
        r = 12
        for i in range(4):
            self.position[r][0] = self.position[r][0] - 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def affiche4_4(self):
        r = 12
        for i in range(4):
            self.position[r][0] = self.position[r][0] + 60
            self.m[0][r].move(self.position[r][0], self.position[r][1])
            r += 1

    def slider(self):
        self.s1 = QSlider(Qt.Horizontal, self)
        self.s1.setTickPosition(QSlider.TicksAbove)
        SLIDER = """QSlider::groove:horizontal {border: 3px solid #A0A5B2;
                        border-radius: 3px;
                        height: 10px;
                        background: #E8E8E8;}
                    QSlider::handle:horizontal {background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #FFFFFF, stop: 0.7 #9500ff,
                        stop: 1.0 #C0C0FF);
                        width: 20px;
                        border-top: 1px solid #ff0004;
                        border-left: 1px solid #ff0004;
                        border-right: 1px solid #ff0004;
                        border-bottom: 2px solid #ff0004;
                        border-radius: 2px;
                        margin: -3px 0;}"""

        self.bb = QComboBox(self)
        self.bb.setGeometry(QRect(10, 20, 200, 100))
        self.bb.addItem("Humain")
        self.bb.addItem("IA")

        self.bb2 = QComboBox(self)
        self.bb2.setGeometry(QRect(790, 20, 200, 100))
        self.bb2.addItem("Humain")
        self.bb2.addItem("IA")

        self.s1.setGeometry(300, 30, 400, 200)
        self.s1.setStyleSheet(SLIDER)
        v_box = QVBoxLayout()
        self.setLayout(v_box)

        self.label = QLabel("intervalle de temps :", self)
        self.label.setFont(QFont("arial", 15, QFont.Bold))
        self.label.setGeometry(QRect(450, 90, 200, 40))

        self.label1 = QLabel("JOUEUR 1 :", self)
        self.label1.setFont(QFont("arial", 20, QFont.Bold))
        self.label1.setGeometry(QRect(20, 30, 100, 20))
        self.label1.setStyleSheet('background-color: white')

        self.label2 = QLabel("JOUEUR 2 :", self)
        self.label2.setFont(QFont("arial", 20, QFont.Bold))
        self.label2.setGeometry(QRect(880, 30, 100, 20))
        self.label2.setStyleSheet('background-color: white')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = fenetre()
    fenetre.show()

    sys.exit(app.exec_())