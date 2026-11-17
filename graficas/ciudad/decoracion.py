# Ciudad estática: banquetas y edificios (después: árboles, farolas, display list)
import random
from OpenGL.GL import *
from mapa import MAPA, FILAS, COLS, CELL, en_mapa, celda_a_mundo

SEMILLA = 42                     # misma semilla -> misma ciudad cada vez
Y_BANQUETA = 0.15                # más alta que la calle (0.05)
COLOR_BANQUETA = (190, 190, 185)
MARGEN_LOTE = 0.4                # metros que se encoge cada edificio dentro de su lote
ALTURA_MIN, ALTURA_MAX = 4.0, 16.0
PALETA = [
    (222, 205, 170),   # beige
    (184, 98, 72),     # ladrillo
    (160, 165, 170),   # gris concreto
    (150, 190, 215),   # azul claro (vidrio)
    (235, 225, 200),   # crema
    (120, 130, 140),   # gris oscuro
    (205, 160, 120),   # terracota claro
]

edificios = []                   # se llena UNA vez en generar_edificios()
manzanas = []


def encontrar_manzanas():
    """Agrupa las celdas '#' conectadas y regresa sus rectángulos (f0, f1, c0, c1)."""
    visitado = set()
    resultado = []
    for f in range(FILAS):
        for c in range(COLS):
            if MAPA[f][c] != '#' or (f, c) in visitado:
                continue
            pila = [(f, c)]
            visitado.add((f, c))
            celdas = []
            while pila:
                a, b = pila.pop()
                celdas.append((a, b))
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (a + da, b + db)
                    if en_mapa(*n) and MAPA[n[0]][n[1]] == '#' and n not in visitado:
                        visitado.add(n)
                        pila.append(n)
            filas = [p[0] for p in celdas]
            cols = [p[1] for p in celdas]
            resultado.append((min(filas), max(filas), min(cols), max(cols)))
    return resultado


def partir(n):
    pedazos = []
    while n > 3:
        pedazos.append(2)
        n -= 2
    pedazos.append(n)
    return pedazos


def rect_a_mundo(f0, f1, c0, c1):
    m = CELL / 2
    x0, z0 = celda_a_mundo(f0, c0)
    x1, z1 = celda_a_mundo(f1, c1)
    return x0 - m, x1 + m, z0 - m, z1 + m


def generar_edificios():
    global manzanas
    random.seed(SEMILLA)
    manzanas = encontrar_manzanas()
    edificios.clear()
    for (f0, f1, c0, c1) in manzanas:
        f = f0
        for alto in partir(f1 - f0 + 1):
            c = c0
            for ancho in partir(c1 - c0 + 1):
                x0, x1, z0, z1 = rect_a_mundo(f, f + alto - 1, c, c + ancho - 1)
                edificios.append({
                    'x0': x0 + MARGEN_LOTE, 'x1': x1 - MARGEN_LOTE,
                    'z0': z0 + MARGEN_LOTE, 'z1': z1 - MARGEN_LOTE,
                    'altura': random.uniform(ALTURA_MIN, ALTURA_MAX),
                    'color': random.choice(PALETA),
                })
                c += ancho
            f += alto


def _tono(color, factor):
    return tuple(int(v * factor) for v in color)


def caja(x0, x1, y0, y1, z0, z1, color):
    glBegin(GL_QUADS)
    # Techo
    glColor3ub(*color)
    glNormal3f(0, 1, 0)
    glVertex3f(x0, y1, z0); glVertex3f(x0, y1, z1); glVertex3f(x1, y1, z1); glVertex3f(x1, y1, z0)
    # Lados que miran a +Z y -Z
    glColor3ub(*_tono(color, 0.85))
    glNormal3f(0, 0, 1)
    glVertex3f(x0, y0, z1); glVertex3f(x1, y0, z1); glVertex3f(x1, y1, z1); glVertex3f(x0, y1, z1)
    glNormal3f(0, 0, -1)
    glVertex3f(x1, y0, z0); glVertex3f(x0, y0, z0); glVertex3f(x0, y1, z0); glVertex3f(x1, y1, z0)
    # Lados que miran a +X y -X
    glColor3ub(*_tono(color, 0.70))
    glNormal3f(1, 0, 0)
    glVertex3f(x1, y0, z1); glVertex3f(x1, y0, z0); glVertex3f(x1, y1, z0); glVertex3f(x1, y1, z1)
    glNormal3f(-1, 0, 0)
    glVertex3f(x0, y0, z0); glVertex3f(x0, y0, z1); glVertex3f(x0, y1, z1); glVertex3f(x0, y1, z0)
    glEnd()


def dibujar_banquetas():
    for (f0, f1, c0, c1) in manzanas:
        x0, x1, z0, z1 = rect_a_mundo(f0, f1, c0, c1)
        caja(x0, x1, 0.0, Y_BANQUETA, z0, z1, COLOR_BANQUETA)


def dibujar_edificios():
    for e in edificios:
        caja(e['x0'], e['x1'], Y_BANQUETA, Y_BANQUETA + e['altura'],
             e['z0'], e['z1'], e['color'])