# Flota: de pos lógicas (fila, col, flecha) a coches 3D en ciudad
import random
from OpenGL.GL import *

from graficas.ciudad.mapa import MAPA, FILAS, COLS, FLECHAS, es_calle, celda_a_mundo
from graficas.coche.carro import Carro

ESCALA = 0.46 # 4.5 m de largo x 1.8 m de ancho
VEL = 0.1     # metros por frame
LARGO, ANCHO = 4.6, 1.9
ANGULO = {'>': 0.0, '^': 90.0, '<': 180.0, 'v': 270.0} # Body_Ry según la flecha

# Auxiliares: para que no hayan coches encimados ni fuera de calle
def huella(f, c, flecha):
    # Rectángulo (x0, x1, z0, z1) que ocupa un coche parado en la celda (f, c)
    x, z = celda_a_mundo(f, c)
    df, dc = FLECHAS[flecha]
    mx, mz = (LARGO / 2, ANCHO / 2) if dc != 0 else (ANCHO / 2, LARGO / 2)
    return x - mx, x + mx, z - mz, z + mz

def se_enciman(a, b):
    # si se traslapan en x y en y
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]

def cabe_en_calle(f, c, flecha):
    # La celda de atrás y la de adelante también deben ser calle
    df, dc = FLECHAS[flecha]
    return es_calle(f - df, c - dc) and es_calle(f + df, c + dc)


# sortea n lugares válido en mapa (de mientras para prueba)
def posiciones_de_prueba(n, semilla=7):
    # Regresa una lista de (fila, col, flecha)
    rng = random.Random(semilla)     # generador propio: no altera el random de decoracion
    candidatas = [(f, c, MAPA[f][c]) for f in range(FILAS) for c in range(COLS)
                  if MAPA[f][c] in FLECHAS and cabe_en_calle(f, c, MAPA[f][c])]
    rng.shuffle(candidatas)

    elegidas, huellas = [], []
    for f, c, flecha in candidatas:
        h = huella(f, c, flecha)
        if any(se_enciman(h, otra) for otra in huellas):
            continue
        elegidas.append((f, c, flecha))
        huellas.append(h)
        if len(elegidas) == n:
            break
    if len(elegidas) < n:
        print(f"[flota] solo cupieron {len(elegidas)} de {n} coches")
    return elegidas


# convierte cada lugar en un Carro con su pose
def crear_flota(posiciones, piezas):
    carros = []
    for f, c, flecha in posiciones:
        carro = Carro(None, VEL, ESCALA)
        carro.getComponents(piezas)
        x, z = celda_a_mundo(f, c)
        carro.set_pose(x, z, ANGULO[flecha])
        carros.append(carro)
    return carros


# dibuja todos los coches
def dibujar_flota(carros, y_base):
    glPushMatrix()
    glTranslatef(0.0, y_base, 0.0)
    for carro in carros:
        carro.draw()
    glPopMatrix()
    
if __name__ == "__main__":
    pos = posiciones_de_prueba(10)
    print(len(pos), "coches:", pos)
    print("máximo que caben:", len(posiciones_de_prueba(999)))
