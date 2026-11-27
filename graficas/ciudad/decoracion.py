import random
from OpenGL.GL import *
from OpenGL.raw.GLU import gluBuild2DMipmaps
from . import modelosCiudad as modelos
import os
import pygame
from OpenGL.GLU import gluNewQuadric, gluQuadricNormals, gluCylinder, gluSphere, GLU_SMOOTH
import math
from .mapa import MAPA, FILAS, COLS, CELL, FLECHAS, BORDE, en_mapa, es_calle, celda_a_mundo

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
    'arbol': 'decoracion/arbol.obj',
    'hotdogs': 'decoracion/sausagesaloon/sausagesaloon.obj',
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

FACHADAS = {
    0: 'building6',
    1: 'building4',
    2: 'building3',
    3: 'building1',
    4: 'building5',
    5: 'building2',
}

edificios = []                   # se llena UNA vez en generar_edificios()
especiales = []                  # modelos colocados en manzanas
manzanas = []

# lineas de la calle
Y_LINEA = 0.10                                # entre calle (0.05) y banqueta (0.15)
COLOR_AMARILLO = (240, 200, 40)
COLOR_BLANCO = (240, 240, 240)
ANCHO_LINEA = 0.12                            # cada línea de la doble amarilla
SEPARACION_DOBLE = 0.15                       # hueco entre las dos amarillas
FRANJA_ANCHO, FRANJA_HUECO, FRANJA_LARGO = 0.30, 0.30, 1.4   # cebra
N_FRANJAS = 3                                 # por celda (6 por carril de 2 celdas)

# arboles y farolasr

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

TEXTURAS = {
    'pasto':    ('texturas/pasto.png', 1.4),
    'asfalto':  ('texturas/pavimento.png', 3.0),
    'banqueta': ('texturas/banqueta.png', 1.9),
    # Fachadas de los edificios de cubos (una repetición = cuadrado de N metros)
    'building1': ('texturas/edificios/building1.png', 3.0),    # muro rojo con ladrillo expuesto
    'building2': ('texturas/edificios/building2.png', 3.0),    # aplanado deteriorado
    'building3': ('texturas/edificios/building3.png', 2.0),    # ladrillo
    'building4': ('texturas/edificios/building4.png', 18.0),   # Facade018A: 6 pisos x 6 ventanas
    'building5': ('texturas/edificios/building5.png', 18.0),   # Facade020A: 6 pisos x 6 ventanas
    'building6': ('texturas/edificios/building6.png', 24.0),   # Facade006: 8 pisos x 14 ventanas
}

FACHADAS_ALTOS = ['building4', 'building5', 'building6']   # con ventanas
FACHADAS_BAJOS = ['building1', 'building2', 'building3']   # muros
ALTURA_ALTO = 8.0                                          # metros: más alto que esto = "alto"
COLOR_TECHO = (120, 120, 125)
_tex = {}      # nombre -> id de OpenGL (o None si no se pudo cargar)



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

    if usar_textura('banqueta'):
        glBegin(GL_QUADS)
        for (f0, f1, c0, c1) in manzanas:
            x0, x1, z0, z1 = rect_a_mundo(f0, f1, c0, c1)
            quad_texturizado(x0, x1, z0, z1, Y_BANQUETA + 0.005, 'banqueta')
        glEnd()
        dejar_textura()

def asignar_fachadas():
    rnd = random.Random(SEMILLA + 2)
    mazos = {}
    for nombre_grupo, grupo in (('altos', FACHADAS_ALTOS), ('bajos', FACHADAS_BAJOS)):
        disponibles = [n for n in grupo if _tex.get(n) is not None]
        rnd.shuffle(disponibles)
        mazos[nombre_grupo] = disponibles
    usados = {'altos': 0, 'bajos': 0}
    for i, e in enumerate(edificios):
        if i in FACHADAS and _tex.get(FACHADAS[i]) is not None:
            e['fachada'] = FACHADAS[i]



def caja_con_fachada(x0, x1, y0, y1, z0, z1, fachada, color_techo):
    """Como caja(), pero los 4 lados llevan la textura de fachada.
    La textura arranca en la base (y0): así la planta baja queda abajo y los pisos van subiendo."""
    t = TEXTURAS[fachada][1]                 # metros que mide una repetición

    # Techo: color liso (gris), sin textura
    glColor3ub(*color_techo)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(x0, y1, z0); glVertex3f(x0, y1, z1); glVertex3f(x1, y1, z1); glVertex3f(x1, y1, z0)
    glEnd()

    usar_textura(fachada)
    glBegin(GL_QUADS)
    # Lados que miran a +Z y -Z: la textura avanza en X.  Sombra falsa al 85 %.
    glColor3f(0.85, 0.85, 0.85)              # gris en lugar de blanco = sombra (la textura se multiplica)
    glNormal3f(0, 0, 1)
    glTexCoord2f(x0 / t, 0);             glVertex3f(x0, y0, z1)
    glTexCoord2f(x1 / t, 0);             glVertex3f(x1, y0, z1)
    glTexCoord2f(x1 / t, (y1 - y0) / t); glVertex3f(x1, y1, z1)
    glTexCoord2f(x0 / t, (y1 - y0) / t); glVertex3f(x0, y1, z1)
    glNormal3f(0, 0, -1)
    glTexCoord2f(-x1 / t, 0);             glVertex3f(x1, y0, z0)
    glTexCoord2f(-x0 / t, 0);             glVertex3f(x0, y0, z0)
    glTexCoord2f(-x0 / t, (y1 - y0) / t); glVertex3f(x0, y1, z0)
    glTexCoord2f(-x1 / t, (y1 - y0) / t); glVertex3f(x1, y1, z0)
    # Lados que miran a +X y -X: la textura avanza en Z.  Sombra falsa al 70 %.
    glColor3f(0.70, 0.70, 0.70)
    glNormal3f(1, 0, 0)
    glTexCoord2f(-z1 / t, 0);             glVertex3f(x1, y0, z1)
    glTexCoord2f(-z0 / t, 0);             glVertex3f(x1, y0, z0)
    glTexCoord2f(-z0 / t, (y1 - y0) / t); glVertex3f(x1, y1, z0)
    glTexCoord2f(-z1 / t, (y1 - y0) / t); glVertex3f(x1, y1, z1)
    glNormal3f(-1, 0, 0)
    glTexCoord2f(z0 / t, 0);             glVertex3f(x0, y0, z0)
    glTexCoord2f(z1 / t, 0);             glVertex3f(x0, y0, z1)
    glTexCoord2f(z1 / t, (y1 - y0) / t); glVertex3f(x0, y1, z1)
    glTexCoord2f(z0 / t, (y1 - y0) / t); glVertex3f(x0, y1, z0)
    glEnd()
    dejar_textura()



def dibujar_edificios():
    for e in edificios:
        y0, y1 = Y_BANQUETA, Y_BANQUETA + e['altura']
        if e.get('fachada'):
            caja_con_fachada(e['x0'], e['x1'], y0, y1, e['z0'], e['z1'], e['fachada'], COLOR_TECHO)
        else:                                # respaldo: sin textura, el color de siempre
            caja(e['x0'], e['x1'], y0, y1, e['z0'], e['z1'], e['color'])
    for e in especiales:
        modelos.dibujar_ajustado(e['modelo'], e['x0'], e['x1'], e['z0'], e['z1'],
                                 Y_BANQUETA, e['rot'])




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



#arboles y farolas

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


#texturas

def cargar_texturas():
    """Llamar UNA vez después de crear la ventana (antes de compilar la display list)."""
    for nombre, (ruta, _) in TEXTURAS.items():
        archivo = os.path.join(modelos.ASSETS, ruta)
        try:
            img = pygame.image.load(archivo)
            datos = pygame.image.tostring(img, 'RGBA', 1)
            ancho, alto = img.get_size()
            tid = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            # mipmaps: versiones más chicas para lo lejano (evita el "hormigueo" a lo lejos)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, ancho, alto, GL_RGBA, GL_UNSIGNED_BYTE, datos)
            glBindTexture(GL_TEXTURE_2D, 0)
            _tex[nombre] = tid
        except Exception as e:
            print(f"[decoracion] textura '{nombre}' no disponible ({archivo}): {e}. Uso color liso.")
            _tex[nombre] = None


def usar_textura(nombre):
    """Activa la textura. Regresa False si no existe (entonces se dibuja con color)."""
    tid = _tex.get(nombre)
    if tid is None:
        return False
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tid)
    glColor3f(1.0, 1.0, 1.0)          # blanco: si no, el color actual tiñe la textura
    return True


def dejar_textura():
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)


def quad_texturizado(x0, x1, z0, z1, y, nombre):
    """Quad plano. Coordenadas de textura = coordenadas del MUNDO / tamaño de la repetición:
    así la textura continúa de una celda a otra sin que se noten las uniones.
    Va DENTRO de un glBegin(GL_QUADS)."""
    t = TEXTURAS[nombre][1]
    glNormal3f(0, 1, 0)
    glTexCoord2f(x0 / t, z0 / t); glVertex3f(x0, y, z0)
    glTexCoord2f(x0 / t, z1 / t); glVertex3f(x0, y, z1)
    glTexCoord2f(x1 / t, z1 / t); glVertex3f(x1, y, z1)
    glTexCoord2f(x1 / t, z0 / t); glVertex3f(x1, y, z0)


#afuera de la ciudad
# --- Círculo de jacarandas ---
ANILLO_MODELO = 'arbol'
ANILLO_N = 40                    # cuántos árboles (algunos se saltan por las salidas de los coches)
ANILLO_RADIO = 55.0              # metros del centro de la ciudad
ANILLO_VARIACION = 4.0           # ± metros: que no quede un círculo perfecto
ANILLO_ALTO = (6.0, 9.0)         # altura de cada árbol, en metros (al azar entre estos dos)

# --- Objetos sueltos ---
# 'pos': (x, z) en metros.  'rot': grados.  'mirar_centro': True = se gira solo hacia la ciudad
# (y 'rot' se suma por si el frente del modelo no apunta hacia donde esperamos).
OBJETOS_AFUERA = [
    {'modelo': 'hotdogs', 'pos': (-31.0, 27.0), 'alto': 4.4, 'mirar_centro': True, 'rot': 0},
    {'modelo': 'hotdogs', 'pos': (12.0, -28.0), 'alto': 4.4, 'mirar_centro': True, 'rot': 0},
    {'modelo': 'hotdogs', 'pos': (-10.0, 30.0), 'alto': 4.4, 'mirar_centro': True, 'rot': 0},
    {'modelo': 'hotdogs', 'pos': (-33.0, -8.0), 'alto': 2.5, 'mirar_centro': True, 'rot': 15},
    {'modelo': 'hotdogs', 'pos': (33.0, 12.0), 'alto': 2.3, 'mirar_centro': True, 'rot': -15},
]

# Pasillos libres frente a las salidas de los coches (no se pone nada ahí)
ANCHO_PASILLO = 4.0              # metros extra a cada lado del carril
LARGO_PASILLO = 90.0             # metros hacia afuera desde la orilla de la ciudad

alrededores = []                 # se llena UNA vez en generar_alrededores()


def _pasillos_libres():
    """Rectángulos (x0, x1, z0, z1) frente a cada borde abierto ('1') del mapa."""
    m = CELL / 2
    lim_x, lim_z = COLS * CELL / 2, FILAS * CELL / 2
    zonas = []
    for f in range(FILAS):
        _, z = celda_a_mundo(f, 0)
        if BORDE['izq'][f] == '1':
            zonas.append((-lim_x - LARGO_PASILLO, -lim_x, z - m - ANCHO_PASILLO, z + m + ANCHO_PASILLO))
        if BORDE['der'][f] == '1':
            zonas.append((lim_x, lim_x + LARGO_PASILLO, z - m - ANCHO_PASILLO, z + m + ANCHO_PASILLO))
    for c in range(COLS):
        x, _ = celda_a_mundo(0, c)
        if BORDE['arriba'][c] == '1':
            zonas.append((x - m - ANCHO_PASILLO, x + m + ANCHO_PASILLO, -lim_z - LARGO_PASILLO, -lim_z))
        if BORDE['abajo'][c] == '1':
            zonas.append((x - m - ANCHO_PASILLO, x + m + ANCHO_PASILLO, lim_z, lim_z + LARGO_PASILLO))
    return zonas


def _libre(x, z, zonas):
    return not any(x0 <= x <= x1 and z0 <= z <= z1 for x0, x1, z0, z1 in zonas)


def _angulo_hacia_centro(x, z):
    """Grados para que el frente del modelo (+Z local) mire al centro de la ciudad."""
    return math.degrees(math.atan2(-x, -z))


def generar_alrededores():
    """UNA vez, después de cargar_modelos(). Usa su propio random (SEMILLA + 3)."""
    rnd = random.Random(SEMILLA + 3)
    zonas = _pasillos_libres()
    alrededores.clear()

    # Círculo de árboles
    if modelos.existe(ANILLO_MODELO):
        for i in range(ANILLO_N):
            ang = 2 * math.pi * i / ANILLO_N + rnd.uniform(-0.05, 0.05)
            r = ANILLO_RADIO + rnd.uniform(-ANILLO_VARIACION, ANILLO_VARIACION)
            x, z = r * math.cos(ang), r * math.sin(ang)
            alrededores.append({'modelo': ANILLO_MODELO, 'x': x, 'z': z,
                                'rot': rnd.uniform(0, 360), 'alto': rnd.uniform(*ANILLO_ALTO)})

    # Objetos sueltos
    for o in OBJETOS_AFUERA:
        if not modelos.existe(o['modelo']):
            continue
        x, z = o['pos']
        rot = o.get('rot', 0) + (_angulo_hacia_centro(x, z) if o.get('mirar_centro') else 0)
        if not _libre(x, z, zonas):
            print(f"[decoracion] aviso: '{o['modelo']}' en {o['pos']} queda frente a una salida de coches")
        alrededores.append({'modelo': o['modelo'], 'x': x, 'z': z, 'rot': rot, 'alto': o['alto']})

    total = sum(modelos.vertices(a['modelo']) for a in alrededores)
    print(f"[decoracion] alrededores: {len(alrededores)} objetos, ~{total} vértices")
    if total > 400_000:
        print("[decoracion] aviso: son muchos vértices; baja ANILLO_N o simplifica el modelo en Blender")


def dibujar_alrededores():
    for a in alrededores:
        modelos.dibujar_escalado(a['modelo'], a['x'], a['z'], 0.0, a['rot'], a['alto'])