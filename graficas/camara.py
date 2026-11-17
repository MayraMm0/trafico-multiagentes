# Cámara orbital/cenital, controles de teclado y ejes de referencia.

import math
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

# Ejes
X_MIN, X_MAX = -30, 30
Y_MIN, Y_MAX = -30, 30
Z_MIN, Z_MAX = -30, 30
MOSTRAR_EJES = True

theta   = 45.0      # ángulo de la órbita
radius  = 40.0      # distancia al centro
EYE_Y   = 35.0      # altura de la cámara
cenital = False     # vista desde arriba

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


def dibujar_ejes():
    if not MOSTRAR_EJES:
        return
    
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