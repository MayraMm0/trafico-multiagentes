import random
from OpenGL.GL import *
from .mapa import MAPA, FILAS, COLS, CELL, FLECHAS, en_mapa, es_calle, celda_a_mundo
from . import modelosCiudad as modelos

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

# nombre -> archivo dentro de graficas/assets/ciudad/
MODELOS = {
    'oxxo': 'oxxo/oxxo_listo.obj',
    'farmacia': 'farmacia/FarmaciaG_lista.obj',
    'vips': 'vips/vips_listo.obj',
}

# Manzanas que usan un modelo en vez de cubos.
# El número es el índice de la manzana (ver tabla en el chat / print al iniciar):
#   0:(4-7,0-4)  1:(4-7,7-9)  2:(4-7,14-20)  3:(12-15,2-4)  4:(12-15,7-9)  5:(12-17,14-20)
# rot = hacia dónde se gira el modelo (0, 90, 180, 270) para que el frente mire a la calle
MANZANAS_ESPECIALES = {
    0: {'modelo': 'farmacia', 'rot': 270},   # letreros hacia la avenida superior y la calle de cols 5-6
    2: {'modelo': 'oxxo', 'rot': 0},         # entrada hacia la avenida superior
    5: {'modelo': 'vips', 'rot': 0},         # entrada hacia la avenida media
}

edificios = []                   # se llena UNA vez en generar_edificios()
especiales = []                  # modelos colocados en manzanas
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
    """Divide n celdas en pedazos de 2 o 3.  5 -> [2, 3], 7 -> [2, 2, 3]."""
    pedazos = []
    while n > 3:
        pedazos.append(2)
        n -= 2
    pedazos.append(n)
    return pedazos


def rect_a_mundo(f0, f1, c0, c1):
    """Esquinas en metros de un rectángulo de celdas (incluye las celdas f1 y c1)."""
    m = CELL / 2
    x0, z0 = celda_a_mundo(f0, c0)
    x1, z1 = celda_a_mundo(f1, c1)
    return x0 - m, x1 + m, z0 - m, z1 + m


# generacion
def cargar_modelos():
    """Carga los .obj (necesita la ventana OpenGL ya creada)."""
    for nombre, ruta in MODELOS.items():
        try:
            modelos.cargar(nombre, ruta, swapyz=True)
        except Exception as e:
            print(f"[decoracion] no se pudo cargar {nombre} ({ruta}): {e}")


def generar_edificios():
    global manzanas
    random.seed(SEMILLA)
    manzanas = encontrar_manzanas()
    edificios.clear()
    especiales.clear()
    for i, (f0, f1, c0, c1) in enumerate(manzanas):
        esp = MANZANAS_ESPECIALES.get(i)
        if esp and modelos.existe(esp['modelo']):
            x0, x1, z0, z1 = rect_a_mundo(f0, f1, c0, c1)
            especiales.append({'modelo': esp['modelo'], 'rot': esp.get('rot', 0),
                               'x0': x0 + MARGEN_LOTE, 'x1': x1 - MARGEN_LOTE,
                               'z0': z0 + MARGEN_LOTE, 'z1': z1 - MARGEN_LOTE})
            continue                    # esta manzana no lleva cubos
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


# dibujo
def _tono(color, factor):
    return tuple(int(v * factor) for v in color)


def caja(x0, x1, y0, y1, z0, z1, color):
    """Prisma: 4 lados + techo, con sombreado falso (no necesita luces)."""
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
    for e in especiales:
        modelos.dibujar_ajustado(e['modelo'], e['x0'], e['x1'], e['z0'], e['z1'],
                                 Y_BANQUETA, e['rot'])


# lineas de la calle
Y_LINEA = 0.10                                # entre calle (0.05) y banqueta (0.15)
COLOR_AMARILLO = (240, 200, 40)
COLOR_BLANCO = (240, 240, 240)
ANCHO_LINEA = 0.12                            # cada línea de la doble amarilla
SEPARACION_DOBLE = 0.15                       # hueco entre las dos amarillas
FRANJA_ANCHO, FRANJA_HUECO, FRANJA_LARGO = 0.30, 0.30, 1.4   # cebra
N_FRANJAS = 3                                 # por celda (6 por carril de 2 celdas)


def quad_plano(x0, x1, z0, z1, color):
    """Un rectángulo plano en y = Y_LINEA.
    Va DENTRO de un glBegin(GL_QUADS) que abre quien llama (más rápido)."""
    glColor3ub(*color)
    glVertex3f(x0, Y_LINEA, z0)
    glVertex3f(x0, Y_LINEA, z1)
    glVertex3f(x1, Y_LINEA, z1)
    glVertex3f(x1, Y_LINEA, z0)


def opuestas(a, b):
    """True si a y b son flechas que apuntan en sentidos contrarios ('>' y '<', '^' y 'v')."""
    if a not in FLECHAS or b not in FLECHAS:
        return False
    da, db = FLECHAS[a], FLECHAS[b]
    return da == (-db[0], -db[1])


def dibujar_lineas_centrales():
    m = CELL / 2
    s = SEPARACION_DOBLE / 2
    glNormal3f(0, 1, 0)
    glBegin(GL_QUADS)
    # Horizontales: frontera entre la fila f y la f+1
    for f in range(FILAS - 1):
        for c in range(COLS):
            a, b = MAPA[f][c], MAPA[f + 1][c]
            if opuestas(a, b) and FLECHAS[a][0] == 0:
                x, z = celda_a_mundo(f, c)
                z_borde = z + m
                quad_plano(x - m, x + m, z_borde - s - ANCHO_LINEA, z_borde - s, COLOR_AMARILLO)
                quad_plano(x - m, x + m, z_borde + s, z_borde + s + ANCHO_LINEA, COLOR_AMARILLO)
    # Verticales: frontera entre la columna c y la c+1
    for f in range(FILAS):
        for c in range(COLS - 1):
            a, b = MAPA[f][c], MAPA[f][c + 1]
            if opuestas(a, b) and FLECHAS[a][1] == 0:
                x, z = celda_a_mundo(f, c)
                x_borde = x + m
                quad_plano(x_borde - s - ANCHO_LINEA, x_borde - s, z - m, z + m, COLOR_AMARILLO)
                quad_plano(x_borde + s, x_borde + s + ANCHO_LINEA, z - m, z + m, COLOR_AMARILLO)
    glEnd()


def dibujar_pasos_peatonales():
    m = CELL / 2
    total = N_FRANJAS * FRANJA_ANCHO + (N_FRANJAS - 1) * FRANJA_HUECO
    inicio = -total / 2                       # grupo de franjas centrado en la celda
    glNormal3f(0, 1, 0)
    glBegin(GL_QUADS)
    for f in range(FILAS):
        for c in range(COLS):
            ch = MAPA[f][c]
            if ch not in FLECHAS:
                continue
            d = FLECHAS[ch]
            n = (f + d[0], c + d[1])
            if not es_calle(*n) or MAPA[n[0]][n[1]] == ch:
                continue                      # la siguiente es igual: no llega a un cruce
            x, z = celda_a_mundo(f, c)
            for i in range(N_FRANJAS):
                a0 = inicio + i * (FRANJA_ANCHO + FRANJA_HUECO)
                a1 = a0 + FRANJA_ANCHO
                if d[0] == 0:   # tráfico horizontal: franjas largas en X, repartidas en Z
                    quad_plano(x - FRANJA_LARGO / 2, x + FRANJA_LARGO / 2, z + a0, z + a1, COLOR_BLANCO)
                else:           # tráfico vertical: franjas largas en Z, repartidas en X
                    quad_plano(x + a0, x + a1, z - FRANJA_LARGO / 2, z + FRANJA_LARGO / 2, COLOR_BLANCO)
    glEnd()


def dibujar_lineas():
    dibujar_lineas_centrales()
    dibujar_pasos_peatonales()


# arboles y farolas
from OpenGL.GLU import gluNewQuadric, gluQuadricNormals, gluCylinder, gluSphere, GLU_SMOOTH

PROB_ARBOL = 0.85                         # en cada celda '*' hay árbol con esta probabilidad
COLOR_TRONCO = (0.42, 0.28, 0.16)
COLORES_COPA = [(0.20, 0.55, 0.20), (0.25, 0.62, 0.25), (0.15, 0.45, 0.18), (0.32, 0.60, 0.22)]

ESPACIO_FAROLA = 5.0                      # metros entre farolas a lo largo de la banqueta
MARGEN_FAROLA = 0.25                      # distancia al borde de la banqueta
LIBRE_ESQUINA = 2.0                       # no poner farolas cerca de las esquinas (ahí van semáforos)
ALTO_FAROLA, BRAZO_FAROLA = 4.0, 0.8
COLOR_FAROLA = (0.30, 0.32, 0.35)
COLOR_LAMPARA = (255, 240, 190)

arboles = []
farolas = []
_q = None


def _quadric():
    global _q
    if _q is None:
        _q = gluNewQuadric()
        gluQuadricNormals(_q, GLU_SMOOTH)
    return _q


def generar_decoracion():
    """Llamar UNA vez después de generar_edificios() (usa las manzanas)."""
    rnd = random.Random(SEMILLA + 1)      # generador aparte: no cambia los edificios
    m = CELL / 2

    # Árboles en las celdas '*'
    arboles.clear()
    for f in range(FILAS):
        for c in range(COLS):
            if MAPA[f][c] != '*' or rnd.random() > PROB_ARBOL:
                continue
            x, z = celda_a_mundo(f, c)
            arboles.append({
                'x': x + rnd.uniform(-0.4, 0.4), 'z': z + rnd.uniform(-0.4, 0.4),
                'tronco': rnd.uniform(1.0, 1.6), 'copa': rnd.uniform(0.6, 0.9),
                'tipo': rnd.choice(['redondo', 'redondo', 'pino']),
                'color': rnd.choice(COLORES_COPA),
            })

    # Farolas en las orillas de cada manzana, mirando hacia la calle
    farolas.clear()
    lim_x, lim_z = COLS * CELL / 2, FILAS * CELL / 2
    for (f0, f1, c0, c1) in manzanas:
        x0, x1, z0, z1 = rect_a_mundo(f0, f1, c0, c1)
        lados = [  # (punto inicial, punto final, hacia dónde está la calle)
            ((x0, z0), (x1, z0), (0, -1)),   # norte
            ((x0, z1), (x1, z1), (0, 1)),    # sur
            ((x0, z0), (x0, z1), (-1, 0)),   # oeste
            ((x1, z0), (x1, z1), (1, 0)),    # este
        ]
        for (ax, az), (bx, bz), (nx, nz) in lados:
            # lado pegado a la orilla del mapa: ahí no hay calle
            if abs(ax + nx * 0.01) >= lim_x or abs(az + nz * 0.01) >= lim_z:
                continue
            largo = abs(bx - ax) + abs(bz - az)
            libre = largo - 2 * LIBRE_ESQUINA
            if libre <= 0:
                continue
            n = int(libre // ESPACIO_FAROLA) + 1
            paso = libre / n
            for i in range(n):
                t = (LIBRE_ESQUINA + paso * (i + 0.5)) / largo
                px, pz = ax + (bx - ax) * t, az + (bz - az) * t
                farolas.append({'x': px - nx * MARGEN_FAROLA, 'z': pz - nz * MARGEN_FAROLA,
                                'nx': nx, 'nz': nz})


def dibujar_arboles():
    q = _quadric()
    glEnable(GL_LIGHTING)
    for a in arboles:
        glPushMatrix()
        glTranslatef(a['x'], 0.0, a['z'])
        # Tronco
        glColor3f(*COLOR_TRONCO)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 0.12, 0.10, a['tronco'], 8, 1)
        glPopMatrix()
        # Copa
        glColor3f(*a['color'])
        if a['tipo'] == 'redondo':
            glTranslatef(0, a['tronco'] + a['copa'] * 0.7, 0)
            gluSphere(q, a['copa'], 10, 8)
        else:   # pino: cono
            glTranslatef(0, a['tronco'] * 0.6, 0)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(q, a['copa'], 0.0, a['copa'] * 3.0, 10, 1)
        glPopMatrix()
    glDisable(GL_LIGHTING)


def dibujar_farolas():
    q = _quadric()
    for fa in farolas:
        glPushMatrix()
        glTranslatef(fa['x'], Y_BANQUETA, fa['z'])
        # Poste
        glEnable(GL_LIGHTING)
        glColor3f(*COLOR_FAROLA)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 0.06, 0.05, ALTO_FAROLA, 8, 1)
        glPopMatrix()
        glDisable(GL_LIGHTING)
        # Brazo hacia la calle
        bx, bz = fa['nx'] * BRAZO_FAROLA, fa['nz'] * BRAZO_FAROLA
        g = 0.04
        caja(min(0, bx) - g, max(0, bx) + g, ALTO_FAROLA - 0.08, ALTO_FAROLA,
             min(0, bz) - g, max(0, bz) + g, (75, 80, 88))
        # Lámpara (sin luz -> se ve encendida)
        glColor3ub(*COLOR_LAMPARA)
        glPushMatrix()
        glTranslatef(bx, ALTO_FAROLA - 0.12, bz)
        gluSphere(q, 0.14, 8, 6)
        glPopMatrix()
        glPopMatrix()