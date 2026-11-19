# ciudad + coches estáticos
# ejecutar desde raíz: python -m graficas.main

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from graficas import camara
from graficas.ciudad.mainCiudad import preparar_ciudad, dibujar_ciudad, Y_CALLE
from graficas.ciudad.modelosCiudad import configurar_luz, posicionar_luz
from graficas.coche.carro import cargar_piezas
from graficas.coche.flota import posiciones_de_prueba, crear_flota, dibujar_flota

SCREEN_W, SCREEN_H = 1400, 800
FOVY, ZNEAR, ZFAR = 60.0, 1.0, 300.0
CIELO = (103 / 255, 166 / 255, 224 / 255)
N_COCHES = 15
FPS_OBJETIVO = 0     # 0 = sin límite (para medir). Ya optimizado: 60

carros = []

def init():
    pygame.display.set_mode((SCREEN_W, SCREEN_H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simulación de tráfico")
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, SCREEN_W / SCREEN_H, ZNEAR, ZFAR)
    glMatrixMode(GL_MODELVIEW)
    
    glClearColor(*CIELO, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    # Luz
    configurar_luz()
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)   # el color de cada material del .obj alimenta la luz
    glEnable(GL_NORMALIZE)        # la escala 0.46 encoge las normales; esto las corrige
    
    # Recursos: todo después de crear la ventana
    preparar_ciudad()
    piezas = cargar_piezas()
    carros.extend(crear_flota(posiciones_de_prueba(N_COCHES), piezas))
    
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    camara.aplicar_camara()
    posicionar_luz()   # DESPUÉS de la cámara: luz fija al mundo
    camara.dibujar_ejes()

    # Ciudad: sin luz, colores planos (como la diseñó Majo)
    glShadeModel(GL_FLAT)
    dibujar_ciudad()

    # Coches: con luz y sombreado suave
    glEnable(GL_LIGHTING)
    glShadeModel(GL_SMOOTH)
    dibujar_flota(carros, Y_CALLE)
    glDisable(GL_LIGHTING)

def main():
    pygame.init()
    init()
    reloj = pygame.time.Clock()
    frames = 0
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
        reloj.tick(FPS_OBJETIVO)        # reemplaza pygame.time.wait(10)
        frames += 1
        if frames % 30 == 0:
            pygame.display.set_caption(f"Simulación de tráfico — {reloj.get_fps():.0f} FPS")


    pygame.quit()
    
if __name__ == "__main__":
    main()