# Carga cada .obj UNA vez y lo dibuja ajustado a un rectángulo del mapa.
import os
from OpenGL.GL import *
from ..objloader import OBJ

# graficas/ciudad/modelosCiudad.py  ->  graficas/assets/ciudad/
AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(AQUI, '..', 'assets', 'ciudad'))

_modelos = {}


def cargar(nombre, ruta_relativa, swapyz=True):
    """Carga un .obj de assets/ciudad y guarda su caja (para autoajustar)."""
    obj = OBJ(os.path.join(ASSETS, ruta_relativa), swapyz=swapyz)
    xs = [v[0] for v in obj.vertices]
    ys = [v[1] for v in obj.vertices]
    zs = [v[2] for v in obj.vertices]
    _modelos[nombre] = {
        'obj': obj,
        'swapyz': swapyz,
        'centro_x': (min(xs) + max(xs)) / 2,
        'centro_z': (min(zs) + max(zs)) / 2,
        'base_y': min(ys),
        'ancho': max(xs) - min(xs),     # en X
        'fondo': max(zs) - min(zs),     # en Z
        'alto': max(ys) - min(ys),
    }
    m = _modelos[nombre]
    print(f"[modelos] {nombre}: {m['ancho']:.1f} x {m['fondo']:.1f} m, alto {m['alto']:.1f} m, "
          f"{len(obj.vertices)} vértices")


def existe(nombre):
    return nombre in _modelos


def dibujar_ajustado(nombre, x0, x1, z0, z1, y, rot=0, escala_extra=1.0):
    """Dibuja el modelo centrado en el rectángulo [x0,x1] x [z0,z1], parado en altura y.
    rot: grados en Y (0, 90, 180, 270). Se escala para que quepa sin deformarse."""
    m = _modelos[nombre]
    ancho, fondo = m['ancho'], m['fondo']
    if rot % 180 == 90:                 # girado 90°: se intercambian ancho y fondo
        ancho, fondo = fondo, ancho
    s = min((x1 - x0) / ancho, (z1 - z0) / fondo) * escala_extra

    glPushMatrix()
    glTranslatef((x0 + x1) / 2, y, (z0 + z1) / 2)
    glRotatef(rot, 0, 1, 0)
    glScalef(s, s, s)
    if m['swapyz']:
        glScalef(1, 1, -1)              # swapyz del loader deja el modelo en espejo; esto lo corrige
    glTranslatef(-m['centro_x'], -m['base_y'], -m['centro_z'])

    # Luz solo para los modelos (los cubos usan sombreado falso)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)             # al escalar, las normales se deforman; esto las corrige
    glShadeModel(GL_SMOOTH)
    m['obj'].render()
    glShadeModel(GL_FLAT)
    glDisable(GL_LIGHTING)
    glPopMatrix()


def posicionar_luz():
    """Llamar en cada frame, justo después de aplicar_camara()
    (si no, la luz se mueve con la cámara)."""
    glLightfv(GL_LIGHT0, GL_POSITION, (0.4, 1.0, 0.3, 0.0))     # luz direccional (sol)


def configurar_luz():
    """Llamar una vez en Init()."""
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.45, 0.45, 0.45, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.75, 0.75, 0.75, 1.0))
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)