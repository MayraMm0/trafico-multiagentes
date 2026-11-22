# Semáforo gráfico (poste + caja + 3 focos) y un control por tiempo para la demo.
# Después, AgentPy solo tiene que llamar a set_estado() en cada semáforo.
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from ..ciudad.mapa import CELL, celda_a_mundo, centro_interseccion
from ..ciudad.decoracion import caja

VERDE, AMARILLO, ROJO = 'VERDE', 'AMARILLO', 'ROJO'
COLORES_ON  = {ROJO: (255, 40, 40), AMARILLO: (255, 200, 0), VERDE: (40, 230, 70)}
COLORES_OFF = {ROJO: (70, 20, 20),  AMARILLO: (70, 55, 10),  VERDE: (15, 60, 25)}

# Medidas en metros
ALTO_POSTE, RADIO_POSTE = 3.2, 0.08
CAJA_ANCHO, CAJA_ALTO, CAJA_FONDO = 0.40, 1.05, 0.30
RADIO_FOCO = 0.12
ALTURA_FOCO = {ROJO: 0.85, AMARILLO: 0.52, VERDE: 0.19}   # desde la base de la caja
Y_BASE = 0.15                                               # banqueta
MARGEN_ESQUINA = 0.25                                       # distancia al borde de la banqueta
COLOR_POSTE = (0.25, 0.27, 0.30)
COLOR_CAJA = (25, 25, 28)

_quadric = None


def iniciar_quadric():
    """Llamar una vez en Init() (necesita la ventana OpenGL ya creada)."""
    global _quadric
    _quadric = gluNewQuadric()
    gluQuadricNormals(_quadric, GLU_SMOOTH)


def _signo(v):
    return (v > 0) - (v < 0)


class Semaforo:
    def __init__(self, datos):
        """datos: un dict de mapa.SEMAFOROS -> {'id', 'cruce', 'poste'}"""
        self.id = datos['id']
        self.cruce = datos['cruce']
        self.estado = ROJO

        # Posición: en la esquina de la celda del poste más cercana al cruce
        x, z = celda_a_mundo(*datos['poste'])
        cx, cz = centro_interseccion(self.cruce)
        d = CELL / 2 - MARGEN_ESQUINA
        self.x = x + _signo(cx - x) * d
        self.z = z + _signo(cz - z) * d

        # Ángulo: el frente de la caja (+Z local) mira al centro del cruce
        self.angulo = math.degrees(math.atan2(cx - self.x, cz - self.z))

    def set_estado(self, estado):
        """Solo PINTA el color que le digan (el control vive en los agentes).
        Cualquier luz que no sea VERDE/AMARILLO/ROJO (p. ej. 'TODO_ROJO') se pinta en rojo."""
        self.estado = estado if estado in (VERDE, AMARILLO) else ROJO

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, Y_BASE, self.z)
        glRotatef(self.angulo, 0, 1, 0)

        # Poste (con luz, para que se vea redondo)
        glEnable(GL_LIGHTING)
        glColor3f(*COLOR_POSTE)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)                  # gluCylinder crece en +Z -> lo paramos en +Y
        gluCylinder(_quadric, RADIO_POSTE, RADIO_POSTE, ALTO_POSTE, 8, 1)
        glPopMatrix()
        glDisable(GL_LIGHTING)

        # Caja negra
        a, f = CAJA_ANCHO / 2, CAJA_FONDO / 2
        caja(-a, a, ALTO_POSTE, ALTO_POSTE + CAJA_ALTO, -f, f, COLOR_CAJA)

        # Focos (sin luz -> brillan)
        for color in (ROJO, AMARILLO, VERDE):
            glColor3ub(*(COLORES_ON[color] if color == self.estado else COLORES_OFF[color]))
            glPushMatrix()
            glTranslatef(0, ALTO_POSTE + ALTURA_FOCO[color], f + 0.01)
            gluSphere(_quadric, RADIO_FOCO, 10, 10)
            glPopMatrix()

        glPopMatrix()


# ---------- CONTROL POR TIEMPO: SOLO PARA LA DEMO DE LA CIUDAD SOLA ----------
# En la simulación NO se usa: quien decide es el Coordinador (agentes) y el color
# llega en el snapshot del MundoModelo (ver mainCiudad.aplicar_luces).
T_VERDE, T_AMARILLO = 6.0, 1.5


class ControlSemaforos:
    def __init__(self, semaforos):
        # {cruce: [semáforos]}: el primero es el grupo A, el resto el grupo B
        self.cruces = {}
        for s in semaforos:
            self.cruces.setdefault(s.cruce, []).append(s)
        # Estado por cruce; desfasado para que no cambien todos al mismo tiempo
        self.estado = {c: {'fase': 'A', 'color': VERDE, 't': (c * 1.3) % T_VERDE}
                       for c in self.cruces}
        for c in self.cruces:
            self._aplicar(c)

    def _aplicar(self, c):
        e = self.estado[c]
        grupo = self.cruces[c]
        activos = grupo[:1] if e['fase'] == 'A' else grupo[1:]
        for s in grupo:
            s.set_estado(e['color'] if s in activos else ROJO)

    def update(self, dt):
        for c, e in self.estado.items():
            e['t'] += dt
            if e['color'] == VERDE and e['t'] >= T_VERDE:
                e['color'], e['t'] = AMARILLO, 0.0
            elif e['color'] == AMARILLO and e['t'] >= T_AMARILLO:
                e['fase'] = 'B' if e['fase'] == 'A' else 'A'     # el otro grupo pasa a verde
                e['color'], e['t'] = VERDE, 0.0
            self._aplicar(c)