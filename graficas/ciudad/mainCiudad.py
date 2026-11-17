# correrlo con python -m graficas.ciudad.mainCiudad 
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from graficas import camara
from graficas.ciudad.mapa import MAPA, FILAS, COLS, CELL, es_calle, celda_a_mundo, SEMAFOROS
from graficas.ciudad.decoracion import generar_edificios, dibujar_banquetas, dibujar_edificios
from graficas.objloader import OBJ


SCREEN_W, SCREEN_H = 1400, 800
FOVY, ZNEAR, ZFAR = 60.0, 1.0, 300.0
DIM_X = COLS * CELL / 2          # 25
DIM_Z = FILAS * CELL / 2         # 20

Y_SUELO, Y_CALLE, Y_LINEA = 0.0, 0.05, 0.1     # capas para evitar parpadeo

pasto = (149, 249, 39)
asfalto = (89, 89, 89)
cielo = (103, 166, 224)


def dibujar_suelo():
    glColor3ub(*pasto)
    glBegin(GL_QUADS)
    glVertex3f(-DIM_X, Y_SUELO, -DIM_Z)
    glVertex3f(-DIM_X, Y_SUELO,  DIM_Z)
    glVertex3f( DIM_X, Y_SUELO,  DIM_Z)
    glVertex3f( DIM_X, Y_SUELO, -DIM_Z)
    glEnd()


def dibujar_calles():
    m = CELL / 2
    glColor3ub(*asfalto)
    glBegin(GL_QUADS)              # un solo glBegin para todas las celdas (más rápido)
    for f in range(FILAS):
        for c in range(COLS):
            if es_calle(f, c):
                x, z = celda_a_mundo(f, c)
                glVertex3f(x - m, Y_CALLE, z - m)
                glVertex3f(x - m, Y_CALLE, z + m)
                glVertex3f(x + m, Y_CALLE, z + m)
                glVertex3f(x + m, Y_CALLE, z - m)
    glEnd()
    # (en el inciso 9 esto pasa a una display list)


def Init():
    pygame.display.set_mode((SCREEN_W, SCREEN_H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Ciudad")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, SCREEN_W / SCREEN_H, ZNEAR, ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glClearColor(cielo[0] / 255, cielo[1] / 255, cielo[2] / 255, 1.0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glShadeModel(GL_FLAT)
    preparar_ciudad()          # UNA sola vez (usa random con semilla fija)
    camara.aplicar_camara()

def preparar_ciudad():
    # Se hace una vez, después de crear la ventana
    generar_edificios()

def dibujar_ciudad():
    # Todo lo estático de la ciudad, se llama una ves por frame
    dibujar_suelo()
    dibujar_calles()
    dibujar_banquetas()
    dibujar_edificios()
    #después añadir árboles, semáforos
    
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    camara.aplicar_camara()
    camara.dibujar_ejes()
    dibujar_ciudad()


def main():
    pygame.init()
    Init()
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if not camara.tecla_evento(event.key):
                    done = True

        camara.teclas_continuas(pygame.key.get_pressed())

        display()

        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()