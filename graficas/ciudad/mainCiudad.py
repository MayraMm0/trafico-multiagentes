import pygame, math
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from mapa import MAPA, FILAS, COLS, CELL, es_calle, celda_a_mundo, SEMAFOROS
from decoracion import cargar_modelos, generar_edificios, dibujar_banquetas, dibujar_edificios
from modelosCiudad import configurar_luz, posicionar_luz
from objloader import *

# ---------- CONFIG ----------
SCREEN_W, SCREEN_H = 1400, 800
FOVY, ZNEAR, ZFAR = 60.0, 1.0, 300.0
DIM_X = COLS * CELL / 2          # 25
DIM_Z = FILAS * CELL / 2         # 20

Y_SUELO, Y_CALLE, Y_LINEA = 0.0, 0.05, 0.1     # capas para evitar parpadeo

# Colores en 0-255 (se dibujan con glColor3ub)
pasto = (149, 249, 39)
asfalto = (89, 89, 89)
cielo = (103, 166, 224)

# Ejes (solo para depurar)
X_MIN, X_MAX = -30, 30
Y_MIN, Y_MAX = -30, 30
Z_MIN, Z_MAX = -30, 30
MOSTRAR_EJES = True

# ---------- CÁMARA ----------
theta   = 45.0      # ángulo de la órbita     (← →)
radius  = 40.0      # distancia al centro     (W S)
EYE_Y   = 35.0      # altura de la cámara     (↑ ↓)
cenital = False     # vista desde arriba      (C)

EYE_X, EYE_Z = 0.0, 0.0
CENTER_X, CENTER_Y, CENTER_Z = 0, 0, 0
UP_X, UP_Y, UP_Z = 0, 1, 0

ALTURA_CENITAL = 60.0

# Límites y velocidades de la cámara
ALTURA_MIN, ALTURA_MAX = 5.0, 120.0
RADIO_MIN, RADIO_MAX = 10.0, 120.0
VEL_GIRO, VEL_ALTURA, VEL_ZOOM = 1.0, 0.5, 0.5


def aplicar_camara():
    global EYE_X, EYE_Z, UP_X, UP_Y, UP_Z
    if cenital:
        EYE_X, EYE_Z = 0, 0
        ojo_y = ALTURA_CENITAL
        UP_X, UP_Y, UP_Z = 0, 0, -1
    else:
        t = math.radians(theta)
        EYE_X = radius * math.sin(t)
        EYE_Z = radius * math.cos(t)
        ojo_y = EYE_Y
        UP_X, UP_Y, UP_Z = 0, 1, 0
    glLoadIdentity()
    gluLookAt(EYE_X, ojo_y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)


def teclas_continuas(keys):
    """Teclas que se mantienen presionadas."""
    global theta, EYE_Y, radius
    # Girar alrededor de la ciudad
    if keys[pygame.K_RIGHT]:
        theta = (theta + VEL_GIRO) % 360
    if keys[pygame.K_LEFT]:
        theta = (theta - VEL_GIRO) % 360
    # Subir / bajar la cámara
    if keys[pygame.K_UP]:
        EYE_Y = min(EYE_Y + VEL_ALTURA, ALTURA_MAX)
    if keys[pygame.K_DOWN]:
        EYE_Y = max(EYE_Y - VEL_ALTURA, ALTURA_MIN)
    # Zoom: acercar / alejar
    if keys[pygame.K_w]:
        radius = max(radius - VEL_ZOOM, RADIO_MIN)
    if keys[pygame.K_s]:
        radius = min(radius + VEL_ZOOM, RADIO_MAX)


def tecla_evento(key):
    """Teclas de una sola pulsación. Regresa False si hay que salir."""
    global cenital, MOSTRAR_EJES
    if key == pygame.K_c:
        cenital = not cenital
    elif key == pygame.K_e:
        MOSTRAR_EJES = not MOSTRAR_EJES
    # (después) elif key == pygame.K_SPACE: cambiar color de semáforos
    elif key == pygame.K_ESCAPE:
        return False
    return True


def Axis():
    glLineWidth(3.0)
    # X axis in red
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN, 0.0, 0.0)
    glVertex3f(X_MAX, 0.0, 0.0)
    glEnd()
    # Y axis in green
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, Y_MIN, 0.0)
    glVertex3f(0.0, Y_MAX, 0.0)
    glEnd()
    # Z axis in blue
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, Z_MIN)
    glVertex3f(0.0, 0.0, Z_MAX)
    glEnd()
    glLineWidth(1.0)


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
    # (después, al cargar .obj) luces + GL_COLOR_MATERIAL + GL_SMOOTH
    configurar_luz()
    cargar_modelos()             # .obj de assets/ciudad (antes de generar_edificios)
    generar_edificios()          # UNA sola vez (usa random con semilla fija)
    aplicar_camara()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    aplicar_camara()
    posicionar_luz()
    if MOSTRAR_EJES:
        Axis()
    dibujar_suelo()
    dibujar_calles()
    dibujar_banquetas()
    dibujar_edificios()
    # (después) árboles, semáforos


pygame.init()
Init()
done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.KEYDOWN:
            if not tecla_evento(event.key):
                done = True

    teclas_continuas(pygame.key.get_pressed())

    display()

    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()