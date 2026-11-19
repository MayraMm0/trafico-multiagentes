# Correrlo con python -m graficas.coche.prueba_carro
import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math

from graficas.coche.carro import Carro, cargar_piezas

screen_width = 1400
screen_height = 800
#vc para el obser.
FOVY=60.0
ZNEAR=1.0
ZFAR=900.0
#Variables para definir la posicion del observador
#gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
EYE_X = 18.0
EYE_Y = 12.0
EYE_Z = 18.0
CENTER_X = 0
CENTER_Y = 0
CENTER_Z = 0
UP_X=0
UP_Y=1
UP_Z=0
#Variables para dibujar los ejes del sistema
X_MIN=-500
X_MAX=500
Y_MIN=-500
Y_MAX=500
Z_MIN=-500
Z_MAX=500
#Dimension del plano
DimBoard = 30

# Array para los objetos tipo carro
objetos = []
carros = []
ncarros = 1

#Variables para el control del observador
theta = 0.0
radius = 18

pygame.init()

# Dibuja los ejes de referencia
def Axis():
    glLineWidth(3.0)
    #X axis in red
    glColor3f(1.0,0.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN,0.0,0.0)
    glVertex3f(X_MAX,0.0,0.0)
    glEnd()
    #Y axis in green
    glColor3f(0.0,1.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,Y_MIN,0.0)
    glVertex3f(0.0,Y_MAX,0.0)
    glEnd()
    #Z axis in blue
    glColor3f(0.0,0.0,1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,0.0,Z_MIN)
    glVertex3f(0.0,0.0,Z_MAX)
    glEnd()
    glLineWidth(1.0)


def Init():
    screen = pygame.display.set_mode(
        (screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: cubos")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width/screen_height, ZNEAR, ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # coloca la cámara
    gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
    glClearColor(0,0,0,0)
    glEnable(GL_DEPTH_TEST) # que lo cercano tape a lo lejano
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glShadeModel(GL_SMOOTH)
        
    #glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
    glLightfv(GL_LIGHT0, GL_POSITION,  (0, 200, 0, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)
    
    # las piezas se cargan una sola vez y los n coches comparten
    objetos.extend(cargar_piezas())
    
    # se genera un carro
    for i in range(ncarros):
        carros.append(Carro(DimBoard, 0.1, 0.46))
        carros[-1].getComponents(objetos)
        carros[-1].set_pose(10.0, 5.0, 90.0)
        

#Se mueve al observador circularmente al rededor del plano XZ a una altura fija (EYE_Y)
def lookat():
    global EYE_X
    global EYE_Z
    global radius
    EYE_X = radius * (math.cos(math.radians(theta)) + math.sin(math.radians(theta)))
    EYE_Z = radius * (-math.sin(math.radians(theta)) + math.cos(math.radians(theta)))
    glLoadIdentity()
    gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    Axis()
    #Se dibuja el plano gris
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3d(-DimBoard, 0, -DimBoard)
    glVertex3d(-DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, -DimBoard)
    glEnd()
        
    #Se dibuja el carro
    for car in carros:
        car.update() # lógica: nueva posición y ángulos
        car.draw()   # se pinta con esos valores
    
done = False
Init()
while not done:
    keys = pygame.key.get_pressed()
    #avanzar observador
    if keys[pygame.K_RIGHT]:
        if theta > 359.0:
            theta = 0
        else:
            theta += 1.0
        lookat()        
    if keys[pygame.K_LEFT]:
        if theta < 1.0:
            theta = 360.0
        else:
            theta += -1.0
        lookat()
    # solo se controla el ultimo carrito en el array
    # setAvanza()/setRota() son peticiones, el movimiento real ocurre en update()
    if keys[pygame.K_w]:
        carros[-1].setAvanza()
    if keys[pygame.K_a]:
        carros[-1].setRota('L')
    if keys[pygame.K_d]:
        carros[-1].setRota('R')
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done = True

    display()

    pygame.display.flip() # intercambia el buffer donde se dibujó con el que se muestra (doble buffer) 
    pygame.time.wait(10)

pygame.quit()