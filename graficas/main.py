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
from graficas.coche import seguidor
from agentes.fuente_demo import FuenteDemo
from agentes.contrato import T_PASO


from graficas import camara
from graficas.ciudad.mainCiudad import (preparar_ciudad, dibujar_ciudad, actualizar_ciudad,
                                        aplicar_luces, alternar_pausa, Y_CALLE)
from graficas.ciudad.modelosCiudad import configurar_luz, posicionar_luz
from graficas.coche.carro import cargar_piezas
from graficas.coche.flota import posiciones_de_prueba, crear_flota, dibujar_flota

SCREEN_W, SCREEN_H = 1400, 800
FOVY, ZNEAR, ZFAR = 60.0, 1.0, 300.0
CIELO = (103 / 255, 166 / 255, 224 / 255)
FPS_OBJETIVO = 60  # 0 = sin límite (para medir). Ya optimizado: 60
POSICIONES = [(1, 2, '>')]   # (f, c, flecha) iniciales; las mismas que recibirá MundoModelo
N_COCHES = 15

fuente = None # quién produce los snapshots (hoy FuenteDemo, después MundoModelo)
coches = {}  # id -> CocheGrafico

USAR_MODELO = False
T_PASO = 0.5         # segundos por paso del modelo (igual que agentes/contrato.py)

carros = []
modelo = None
snapshot = None


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
    # modelos, edificios, decoración, semáforos y display list (UNA vez)
    preparar_ciudad(modo='simulacion' if USAR_MODELO else 'demo')
    piezas = cargar_piezas()
    carros.extend(crear_flota(posiciones_de_prueba(N_COCHES), piezas))

    if USAR_MODELO:
        iniciar_modelo()


def iniciar_modelo():
    """Crea el MundoModelo y aplica su primer snapshot."""
    global modelo, snapshot
    from agentes.mundoModelo import MundoModelo  # aquí adentro: con USAR_MODELO=False no se necesita
    modelo = MundoModelo({'n_coches': N_COCHES, 'steps': 10 ** 9, 'seed': 1})
    snapshot = modelo.estado_inicial()
    aplicar_snapshot(snapshot)


def aplicar_snapshot(s):
    """Puente lógica -> gráficos: lo que diga el modelo en este paso."""
    aplicar_luces(s['semaforos'])  # semáforos: {sid: luz}
    # TODO (Mayra): actualizar la flota con s['coches'] (id, f, c, sentido, estado, maniobra)


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
    dibujar_flota(carros, Y_CALLE)
    glDisable(GL_LIGHTING)


def main():
    pygame.init()
    init()
    reloj = pygame.time.Clock()
    frames = 0
    acumulado = 0.0  # tiempo desde el último paso del modelo
    done = False
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
        if USAR_MODELO:
            # un paso del modelo cada T_PASO segundos reales (el dibujo sigue a 60 FPS)
            acumulado += dt
            while acumulado >= T_PASO:
                acumulado -= T_PASO
                aplicar_snapshot(modelo.paso())
        else:
            actualizar_ciudad(dt)  # semáforos con temporizador (demo)
        display()
        pygame.display.flip()
        frames += 1
        if frames % 30 == 0:
            pygame.display.set_caption(f"Simulación de tráfico — {reloj.get_fps():.0f} FPS")

    pygame.quit()


if __name__ == "__main__":
    main()