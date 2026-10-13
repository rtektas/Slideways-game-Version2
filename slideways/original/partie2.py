import os,copy,random
"""
projet Slideways: partie2:
La deuxième partie de ce projet permettra d’introduire la possibilité de bouger une rangée d’un cran
vers la gauche ou vers la droite comme mouvement, ainsi qu’une AI basique comme adversaire.
matricule:000495364
Auteur: Tektas Resul
Date: 14-12-19
"""

def afficher(plateau,decalage):
    """
    Affiche le plateau de jeu avec les coups joués par les joueurs et les numéros et lettre pour les lignes et colonnes
    :param plateau: liste de liste, 0 pour vide, 1 ou 2 pour joueur
    :param decalage: list d'entiers, représentent le décalage des lignes du plateau
    """
    os.system("clear")  # permet de supprimer le terminal
    matrice1 = copy.deepcopy(plateau)  # copie le plateau
    matrice1, r = matrice1[::-1], 0  # inverse les indices de la copie
    for a in range(4):
        b = 0
        for i in range(4):
            if matrice1[r][b] == 1:
                matrice1[r][b] = str(1)
                matrice1[r][b] = "X" #transforme les "1" en "X" dans une copie du plateau
            elif matrice1[r][b] == 2:
                matrice1[r][b] = str(2)
                matrice1[r][b] = "O" #transforme les "2" en "O" dans une copie du plateau
            elif matrice1[r][b] == 0:
                matrice1[r][b] = str(0)
                matrice1[r][b] = "-" #transforme les "0" en "-" dans une copie du plateau
            b += 1
        r += 1
    indice = 4
    for elem in matrice1:  # affiche le plateau
        i = 10 +decalage[indice-1]*3 #l'espace pour l'affichage du décalage
        if decalage[indice-1]!=0:
            print(indice," "*i, *elem, sep="  ") #affiche une ligne du plateau dans les règles
        else:
            print(indice," "*i, *elem, sep="  ")
        indice -= 1
    print(" "*10,'    A  B  C  D')
def indice_plateau(coup):
    """
    cette fonction transforme le coup rentré par le joueur en coordonnées du plateau
    :param: coup: le coup rentré par le joueur
    :return:list: une liste du coup transformé
    """
    i,list=5,[]
    if coup[0] == 'A':
        i=0
    elif coup[0] == 'B':
        i=1
    elif coup[0] == 'C':
        i=2
    elif coup[0] == 'D':
        i = 3
    l, b = 0, 1
    for a in range(4):
        if coup[1] == str(b): #si le deuxième caractère est 1,2,3 ou 4
            list.append(l) #ajoute la deuxième valeur du coup transformé dans la liste(list)
            list.append(i) #ajoute la première valeur du coup transformé dans la liste(list)
        b += 1
        l += 1
    return list
def coup_possible(plateau,decalage,joueur,dernier_coup):
    """
        cette fonction teste tous les coups possibles et renvoie une liste de celui-ci
        :param plateau: liste de liste, 0 pour vide, 1 ou 2 pour joueur
        :param decalage: list d'entiers, représentent le décalage des lignes du plateau
        :param joueur: entier, 1 ou 2
        :param dernier_coup: string de deux caractères, dernier coup joué
        :return:list1: une liste de tous les coups possibles
    """
    lettres,nb,list1,list2=['A','B','C','D'],['1', '2', '3', '4'],[],[]
    for i in nb:
        for j in lettres:
            list1.append(str(j+i)) #Ajoute tout les coups possibles dans une liste(list1)
            list2.append((str(j+i),indice_plateau(str(j+i)))) #ajoute un tuple du coup et du coup transformé dans une liste(list2)
        list1.append(str(i+"+")) #Ajoute tous les décalages positifs possibles dans une liste(list1)
        list1.append(str(i+"-")) #Ajoute tous les décalages negatifs possibles dans une liste(list1)
    for a in list2:
        if plateau[a[1][0]][a[1][1]]==joueur: #si la case est de la couleur du joueur
            list1.remove(str(a[0])) #enlève ce coup des coups possibles
    if dernier_coup[0] in lettres and dernier_coup[1] in nb:
        if dernier_coup in list1:
            list1.remove(dernier_coup)
    elif dernier_coup[0] in nb:
        if dernier_coup[1]=="-":
            list1.remove(str(dernier_coup[0]+"+"))
        elif dernier_coup[1]=="+":
            list1.remove(str(dernier_coup[0]+"-"))
    nombre = 1
    for i in decalage:
        if i ==-3:
            list1.remove(str(nombre)+"-")
        if i ==+3:
            list1.remove(str(nombre) + "+")
        nombre+=1
    return list1
def coup_AI(plateau, decalage, joueur, coup):
    """
    Cette fonction va modifier le plateau et le vecteur de décalage en fonction du coup et du joueur reçus en paramètres.
    :param plateau: liste de liste, 0 pour vide, 1 ou 2 pour joueur
    :param decalage: list d'entiers, représentent le décalage des lignes du plateau
    :param joueur: entier, 1 ou 2
    :param coup: string de deux caractères, coup joué
    """
    if coup[0] in ['1','2','3','4']: #si le coup est un décalage
        if coup[1] == '-':
            decalage[int(coup[0]) - 1] += -1  #mettre le nombre de decalage dans la liste ''decalage''
        elif coup[1] == '+' :
            decalage[int(coup[0]) - 1] += 1
    elif coup[0] in ["A","B","C","D"]: #si le coup est une cordonnée du plateau
        indice=indice_plateau(coup)
        plateau[indice[0]][indice[1]]=joueur #mettre "joueur" à l'emplacement du coup donné

def minimax(plateau, decalage, dernier_coup, profondeur=2,maxi=True):
    """
    cette fonction suit le principe de l’algorithme Minimax, un algorithme récursif.
    :param plateau: liste de liste, 0 pour vide, 1 ou 2 pour joueur
    :param decalage: list d'entiers, représentent le décalage des lignes du plateau
    :param dernier_coup: string de deux caractères, dernier coup joué
    :param profondeur: variable int, égale à 2 de base
    :param maxi: variable booléenne, égale à True de base
    :return:
    """
    gagnant,score = fin(plateau,decalage),0
    if maxi:
        joueur=2
    else:
        joueur=1
    if profondeur==0 or gagnant==2 or gagnant==1:
        if gagnant==1:
            score=-1
        elif gagnant==2:
            score = 1
        return (None,score)
    if maxi: #si maxi est true
        meilleurscore,meilleurcoup = -1000,[]
        for coup in coup_possible(plateau,decalage,joueur,dernier_coup):
            nouveauplateau,nouveaudecalage=copy.deepcopy(plateau),copy.deepcopy(decalage) #copie du plateau,copie du plateau
            coup_AI(nouveauplateau, nouveaudecalage, joueur, coup) #appelle la fonction coup_AI
            score = minimax(nouveauplateau,nouveaudecalage,coup,profondeur - 1, False)[1]
            if meilleurscore < score:
                meilleurscore,meilleurcoup = score,[(coup, score)]
            elif meilleurscore == score:
                meilleurcoup.append((coup,score))
    else:
        meilleurscore,meilleurcoup=1000,[]
        for coup in coup_possible(plateau,decalage,joueur,dernier_coup):
            nouveauplateau,nouveaudecalage = copy.deepcopy(plateau),copy.deepcopy(decalage)
            coup_AI(nouveauplateau, nouveaudecalage, joueur, coup)
            score = minimax(nouveauplateau,nouveaudecalage,coup,profondeur-1, True)[1]
            if meilleurscore > score:
                meilleurscore,meilleurcoup=score,[(coup,score)]
            elif meilleurscore ==score:
                meilleurcoup.append((coup,score))
    return random.choice(meilleurcoup)
def nouveau_plateau():
    """
    Crée le plateau de jeu
    :return: liste de liste de dimension 4x4 contenant des 0
    """
    plateau = []
    for i in range(4):
        plateau.append([0]*4)
    return plateau
def coup(plateau, joueur, dernier_coup,decalage):
    """
        Demande un coup au joueur jusqu'à ce qu'il soit valide et le joue en modifiant le plateau
        :param plateau: liste de liste, 0 pour vide, 1 ou 2 pour joueur
        :param joueur: entier, 1 ou 2
        :param dernier_coup: string de deux caractères, dernier coup joué
        :param decalage: list d'entiers, représentent le décalage des lignes du plateau
        :return: coup joué lors du tour
        """
    fini = False
    # demande au joueur d'entrer son coup, vérifie que le coup est correct, et l'effectue
    while not fini:
        if joueur==1:
            c = input('joueur ' + str(joueur) + ' > ')
        elif joueur==2:
            c = minimax(plateau, decalage, dernier_coup, profondeur=2, maxi=True)[0]
            print('joueur ' + str(joueur) + ' > ',c)
        if len(c) ==2 and c[0] in ['1', '2', '3','4'] and c[1] in ['+','-']:
            if dernier_coup[0] == c[0] and dernier_coup[1] != c[1]:
                print('commande invalide')
            else :
                if  -3<= decalage[int(c[0]) - 1] <= 3 :
                    if c[1] =='-':
                        decalage[int(c[0]) - 1] += -1  # mettre le nombre de decalage dans la liste ''decalage''
                        fini = True
                    elif c[1] =='+' and decalage[int(c[0]) - 1]<3 :
                        decalage[int(c[0])-1] += 1
                        fini = True
                    else:
                        print('commande invalide')
                else:
                    print('commande invalide')
        elif len(c) == 2 and c[0] in ['A', 'B', 'C', 'D'] and c[1] in ['1', '2', '3', '4']:

            # si pas dernier coup, déchiffre le coup pour le plateau
            if c[0:2]==dernier_coup:
                print("ce coup vient d'être joué")
            else:
                i = int(c[1]) - 1
                j = ['A', 'B', 'C', 'D'].index(c[0])
                if plateau[i][j] != joueur:
                    plateau[i][j] = joueur
                    fini = True
                else:
                    print('cette case est déjà de votre couleur')
        else:
            print('commande invalide')
    return c[0:2]
def fin(plateau,decalage):
    """
    Détermine si quelqu'un a gagné
    :param plateau: liste de liste, 0 pour vide, 1 ou 2 pour joueur
    :return: int, 0 si pas de gagnant, sinon le numéro du joueur gagnant
    """
    l = []
    #création tableau 4*6:
    matrice1 = []
    for a in range(4):
        matrice1.append([0] * 6)
    for i in range(4):
        for j in range(4):
            matrice1[i].insert(3 - decalage[i], plateau[i][j])
    #lignes et colonnes
    for b in range(4):
        l.append(set(plateau[b]))
    for n in range(10):
        l.append(set( [matrice1[r][n] for r in range(4)]))
    for t in range(7):
        # diagonales
        l.append(set( [matrice1[i][i+t] for i in range(4)] ))
        l.append(set( [matrice1[3-i][i+t] for i in range(4)] ))
    # vérifie si gagnant
    g = []
    for s in l:
        if len(s)==1 and s != {0}:
            g.append(list(s))
    if len(g) == 2 and g != {0}:
        return "égalité"
    elif len(g) == 1 and g != {0}:
        return g[0][0]
    return 0

def boucle_jeu():
    """
    Lance une partie entre joueur et les laisse chacun jouer un coup jusqu'à ce qu'il y ait un gagnant
    :return: None
    """
    decalage = [0, 0, 0, 0]
    print(decalage)
    plateau = nouveau_plateau()
    joueur = 1  # 1 ou 2
    gagnant = 0
    dernier_coup = "éé"
    # continue jusqu'à ce qu'on ait un gagnant
    while gagnant==0:
        afficher(plateau,decalage)
        dernier_coup = coup(plateau, joueur, dernier_coup,decalage)
        gagnant = fin(plateau,decalage)
        joueur = (joueur%2) + 1
    afficher(plateau,decalage)
    if gagnant ==1 or gagnant==2:
        print('joueur', gagnant, 'gagnant')
    elif gagnant=="égalité":
        print('il y a une égalité')
if __name__ == "__main__":
    boucle_jeu()