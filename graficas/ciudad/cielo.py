# ===================== cielo.py =====================
# Cielo con paisaje: una esfera enorme con una foto panorámica pegada por dentro.
# La esfera siempre está centrada en la cámara, así que nunca te acercas al horizonte.
#
# Dos opciones (se usa la primera que exista):
#   1. SKYBOX de 6 imágenes en graficas/assets/ciudad/texturas/skybox/:
#        frente.png  derecha.png  atras.png  izquierda.png  arriba.png  abajo.png
#   2. Panorámica "equirectangular" (el doble de ancha que de alta, p. ej. 2048 x 1024)
#      en graficas/assets/ciudad/texturas/cielo.png
# Si no hay ninguna, se usa el color liso de siempre.
import os
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from . import modelosCiudad as modelos

RADIO_CIELO = 280.0      # metros; tiene que ser MENOR que ZFAR (300) o la esfera no se ve
LADO_SKYBOX = 160.0      # mitad del lado del cubo; la esquina queda a 160·√3 ≈ 277 m < ZFAR
CARAS = ['frente', 'derecha', 'atras', 'izquierda', 'arriba', 'abajo']
ALTURA_HORIZONTE = 0.48  # fila de la imagen (0 = arriba, 1 = abajo) que se usa para el color de la niebla

_tex = None
_q = None
_caras = None            # {nombre_cara: id_textura} si se usa el skybox de 6 imágenes


def _cargar_imagen(archivo, repetir_s):
    """Sube una imagen a OpenGL y regresa (id, superficie de pygame)."""
    img = pygame.image.load(archivo)
    datos = pygame.image.tostring(img, 'RGBA', 1)
    ancho, alto = img.get_size()
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT if repetir_s else GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)   # CLAMP: sin costuras en las orillas
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ancho, alto, 0, GL_RGBA, GL_UNSIGNED_BYTE, datos)
    glBindTexture(GL_TEXTURE_2D, 0)
    return tid, img


def _color_promedio(img, y):
    fila = [img.get_at((x, y))[:3] for x in range(0, img.get_width(), 8)]
    return [sum(p[i] for p in fila) / len(fila) / 255 for i in range(3)]


def _usar_color_horizonte(color):
    """La niebla y el fondo toman el color del horizonte: el pasto lejano se funde con el paisaje."""
    glFogfv(GL_FOG_COLOR, (*color, 1.0))
    glClearColor(*color, 1.0)


def cargar_cielo(ruta='texturas/cielo.png', carpeta_skybox='texturas/skybox'):
    """Llamar UNA vez después de crear la ventana (y después de configurar_niebla)."""
    global _tex, _q, _caras
    # 1) Skybox de 6 imágenes
    carpeta = os.path.join(modelos.ASSETS, carpeta_skybox)
    if all(os.path.isfile(os.path.join(carpeta, c + '.png')) for c in CARAS):
        try:
            _caras, imgs = {}, {}
            for c in CARAS:
                _caras[c], imgs[c] = _cargar_imagen(os.path.join(carpeta, c + '.png'), repetir_s=False)
            img = imgs['frente']
            _usar_color_horizonte(_color_promedio(img, int(img.get_height() * 0.52)))
            return
        except Exception as e:
            print(f"[cielo] skybox no disponible ({carpeta}): {e}. Pruebo la panorámica.")
            _caras = None

    # 2) Panorámica
    archivo = os.path.join(modelos.ASSETS, ruta)
    try:
        _tex, img = _cargar_imagen(archivo, repetir_s=True)
        _usar_color_horizonte(_color_promedio(img, int(img.get_height() * ALTURA_HORIZONTE)))
    except Exception as e:
        print(f"[cielo] no disponible ({archivo}): {e}. Uso el color liso.")
        _tex = None
    _q = gluNewQuadric()
    gluQuadricTexture(_q, GL_TRUE)        # que gluSphere genere coordenadas de textura


# Esquinas de cada cara del cubo, en orden: abajo-izq, abajo-der, arriba-der, arriba-izq
# TAL COMO SE VEN DESDE ADENTRO (parado en el centro, mirando esa cara).
_ESQUINAS = {
    'frente':    [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)],    # mira hacia -Z
    'derecha':   [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)],        # mira hacia +X
    'atras':     [(1, -1, 1), (-1, -1, 1), (-1, 1, 1), (1, 1, 1)],        # mira hacia +Z
    'izquierda': [(-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, 1)],    # mira hacia -X
    'arriba':    [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)],        # el borde de abajo toca 'frente'
    'abajo':     [(-1, -1, 1), (1, -1, 1), (1, -1, -1), (-1, -1, -1)],    # el borde de arriba toca 'frente'
}
_COORDS = [(0, 0), (1, 0), (1, 1), (0, 1)]


def _dibujar_skybox():
    L = LADO_SKYBOX
    for cara in CARAS:
        glBindTexture(GL_TEXTURE_2D, _caras[cara])
        glBegin(GL_QUADS)
        for (x, y, z), (s, t) in zip(_ESQUINAS[cara], _COORDS):
            glTexCoord2f(s, t)
            glVertex3f(x * L, y * L, z * L)
        glEnd()


def dibujar_cielo():
    """Llamar en CADA frame, después de la cámara y ANTES que todo lo demás."""
    if _tex is None and _caras is None:
        return

    # Quitar la traslación de la cámara (solo dejar su rotación):
    # así la esfera siempre queda centrada en la cámara.
    m = [list(fila) for fila in glGetFloatv(GL_MODELVIEW_MATRIX)]
    m[3][0] = m[3][1] = m[3][2] = 0.0

    glPushMatrix()
    glLoadMatrixf(m)
    glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)                     # el cielo no lleva niebla
    glDepthMask(GL_FALSE)                 # no escribe profundidad: todo lo demás se dibuja encima
    glEnable(GL_TEXTURE_2D)
    glColor3f(1.0, 1.0, 1.0)
    if _caras is not None:
        _dibujar_skybox()
    else:
        glBindTexture(GL_TEXTURE_2D, _tex)
        glRotatef(-90, 1, 0, 0)           # gluSphere tiene sus polos en Z; así quedan arriba/abajo
        gluSphere(_q, RADIO_CIELO, 48, 24)
    glBindTexture(GL_TEXTURE_2D, 0)
    glPopAttrib()                         # regresa luz, niebla, texturas y profundidad como estaban
    glPopMatrix()