# ciudad + coches estáticos
# ejecutar desde raíz: python -m graficas.main

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from graficas import camara
from graficas.ciudad.mainCiudad import (preparar_ciudad, dibujar_ciudad, actualizar_ciudad,
                                        alternar_pausa, Y_CALLE)
from graficas.ciudad.modelosCiudad import configurar_luz, posicionar_luz
from graficas.coche.carro import cargar_piezas
from graficas.coche.seguidor import CocheGrafico
from agentes.fuente_demo import FuenteDemo
from agentes.contrato import T_PASO

SCREEN_W, SCREEN_H = 1400, 800
FOVY, ZNEAR, ZFAR = 60.0, 1.0, 300.0
CIELO = (103 / 255, 166 / 255, 224 / 255)
FPS_OBJETIVO = 60  # 0 = sin límite (para medir). Ya optimizado: 60
POSICIONES = [(1, 2, '>')]   # (f, c, flecha) iniciales; las mismas que recibirá MundoModelo

fuente = None # quién produce los snapshots (hoy FuenteDemo, después MundoModelo)
coches = {}  # id -> CocheGrafico



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
    glEnable(GL_COLOR_MATERIAL)  # el color de cada material del .obj alimenta la luz
    glEnable(GL_NORMALIZE)  # la escala 0.46 encoge las normales; esto las corrige

    # Recursos: todo después de crear la ventana
    preparar_ciudad()  # modelos, edificios, decoración, semáforos y display list (UNA vez)
    piezas = cargar_piezas()
    global fuente
    fuente = FuenteDemo(POSICIONES)
    for snap in fuente.estado_inicial():
        coches[snap['id']] = CocheGrafico(snap, piezas)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    camara.aplicar_camara()
    posicionar_luz()  # DESPUÉS de la cámara: luz fija al mundo
    camara.dibujar_ejes()

    # Ciudad: sin luz, colores planos (como la diseñó Majo)
    glShadeModel(GL_FLAT)
    dibujar_ciudad()  # cada frame: reproduce la display list + semáforos

    # Coches: con luz y sombreado suave
    glEnable(GL_LIGHTING)
    glShadeModel(GL_SMOOTH)
    for coche in coches.values():
        coche.dibujar(Y_CALLE)
    glDisable(GL_LIGHTING)


def main():
    pygame.init()
    init()
    reloj = pygame.time.Clock()
    frames = 0
    done = False
    acumulado = 0.0 # segundos desde el último paso lógico
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    alternar_pausa()  # congela / reanuda los semáforos
                elif not camara.tecla_evento(event.key):
                    done = True

        camara.teclas_continuas(pygame.key.get_pressed())
        dt = reloj.tick(FPS_OBJETIVO) / 1000  # segundos desde el frame anterior
        actualizar_ciudad(dt)  # semáforos (demo por tiempo)
        # Lógica: un paso cada T_PASO segundos (como máximo uno por frame)
        acumulado += dt   # 1. suma lo que duró este frame
        if acumulado >= T_PASO: # 2. ¿ya pasaron 0.5 s?
            # 3. sí → un paso lógico
            for snap in fuente.paso():  
                coches[snap['id']].recibir(snap)
            # 4. resta, no reinicia
            acumulado = min(acumulado - T_PASO, T_PASO)

        # Gráfico: cada coche avanza hacia su celda objetivo
        for coche in coches.values():
            coche.actualizar(dt, T_PASO - acumulado) # 5. cuánto falta
            
        display()
        pygame.display.flip()
        frames += 1
        if frames % 30 == 0:
            pygame.display.set_caption(f"Simulación de tráfico — {reloj.get_fps():.0f} FPS")

    pygame.quit()


if __name__ == "__main__":
    main()