# correr con python -m graficas.ciudad.mapa    

CELL = 2.0 # metros por celda

EDIFICIO, ARBOL = '#', '*'
CRUCE, GIRO_DER, GIRO_IZQ = '+', 'R', 'L'
FLECHAS = {'>': (0, 1), '<': (0, -1), '^': (-1, 0), 'v': (1, 0)}   # (dfila, dcol)

MAPA_TXT = """
000000000000000000000000000
1>>>>>>>>>>>>RR>>>>>>>RR>>1
1>>>>>>>>>>>>RR>>>>>>>RR>>1
1<<<<<LL<<<LL++<<<<<<<++<<1
1<<<<<LL<<<LL++<<<<<<<++<<1
0#####vv###^^^^#######vv**0
0#####vv###^^^^#######vv**0
0#####vv###^^^^#######vv**0
0#####vv###^^^^#######vv**0
1<<<<<<<<<<++++<<<<<<<RR<<1
1<<<<<<<<<<++++<<<<<<<RR<<1
1RR>>>>>>>>++++>>>>>>>RR>>1
1RR>>>>>>>>++++>>>>>>>RR>>1
0vv###^^###^^^^#######vv**0
0vv###^^###^^^^#######vv**0
0vv###^^###^^^^#######vv**0
0vv###^^###^^^^#######vv**0
1>>>>>LL>>>LL^^#######vv**0
1>>>>>LL>>>LL^^#######vv**0
0************RR<<<<<<<RR**0
0************RR<<<<<<<RR**0
000000000000000000000000000
"""

def cargar_mapa(txt):
    lines = txt.strip('\n').split('\n')
    mapa = []
    izq, der = "" , ""

    for line in lines[1:-1]:
        izq = izq + line[0]
        der = der + line[-1]
        mapa.append(line[1:-1])

    borde = {
        'arriba': lines[0][1:-1],
        'abajo': lines[-1][1:-1],
        'izq': izq,
        'der': der,
    }
    assert len(borde['arriba']) == len(borde['abajo']) == 25
    assert len(borde['izq']) == len(borde['der']) == 20

    return mapa, borde

MAPA, BORDE = cargar_mapa(MAPA_TXT)
FILAS, COLS = len(MAPA), len(MAPA[0])

def en_mapa(f, c):
    if 0 <= f < FILAS:
        if 0 <= c < COLS:
            return True
    return False


def es_calle(f, c):
    if en_mapa(f, c):
        if MAPA[f][c] not in '#*':
            return True
    return False


def borde_abierto(f, c, d):
    if d == (-1, 0) :
        return BORDE['arriba'][c] == '1'
    elif d == ( 1, 0):
        return BORDE['abajo'][c] == '1'
    elif d == ( 0,-1):
        return BORDE['izq'][f] == '1'
    elif d == ( 0, 1):
        return BORDE['der'][f] == '1'
    return None

def girar_der(d):
    df, dc = d
    return dc, -df

def girar_izq(d):
    df, dc = d
    return -dc, df

def celda_a_mundo(f, c):
    x = c*CELL + CELL/2 - COLS*CELL/2
    z = f*CELL + CELL/2 - FILAS*CELL/2
    return x, z

'''
def opciones(f, c, d, ya_giro):
    """Desde la celda (f,c) yendo en sentido d: ¿a dónde puedo ir?
       Regresa lista de (f2, c2, d2, ya_giro2); (None, None, d2, _) = sale del mapa."""
    # TODO: decidir sentidos posibles según el carácter:
    #       flecha → [su sentido]         ya_giro → [d]
    #       'R' → [d, girar_der(d)]      'L' → [d, girar_izq(d)]    '+' → [d, der, izq]
    # TODO: para cada sentido candidato calcular la celda siguiente:
    #       fuera del mapa  → válida solo si borde_abierto
    #       '#' o '*'       → descartar
    #       flecha en contra (su sentido == -d2) → descartar
    # TODO: ya_giro2 = False si la siguiente es flecha; si no, ya_giro or (d2 != d)

def calcular_entradas():
    # TODO: recorrer celdas de calle en la orilla con borde abierto de ese lado
    # TODO: si es flecha → es entrada si apunta hacia adentro
    # TODO: si es R/L/+ → avanzar hacia adentro hasta la primera flecha y usar su sentido
    # TODO: regresar lista de (f, c, sentido)

def calcular_ruta(f, c, d, destino=None):
    # TODO: BFS sobre estados (f, c, d, ya_giro) usando opciones()
    # TODO: guardar padre de cada estado para reconstruir el camino
    # TODO: termina al encontrar una salida (o el 'destino' si se pide)
    # TODO: regresar lista de celdas [(f, c), ...] o None si no hay ruta
'''
def validar_mapa():
    errores = []
    leyenda = set(FLECHAS) | {EDIFICIO, ARBOL, CRUCE, GIRO_DER, GIRO_IZQ}
    for f, fila in enumerate(MAPA):
        if len(fila) != COLS:
            errores.append(f"fila {f}: mide {len(fila)}, se esperaban {COLS}")
        for c, ch in enumerate(fila):
            if ch not in leyenda:
                errores.append(f"celda ({f},{c}): caracter desconocido {ch!r}")
    for s in SEMAFOROS:
        f, c = s['poste']
        if not en_mapa(f, c) or MAPA[f][c] not in (EDIFICIO, ARBOL):
            errores.append(f"semaforo {s['id']}: el poste {s['poste']} no está en banqueta")
    
    return errores
    # TODO: cada entrada tiene ruta a alguna salida
    # TODO: toda celda de calle aparece en al menos una ruta posible
    #       (BFS desde todas las entradas a la vez y comparar contra las celdas de calle)

# (fila_ini, fila_fin, col_ini, col_fin)
INTERSECCIONES = [
    {'id': 1, 'celdas': (0, 3, 10, 13)},
    {'id': 2, 'celdas': (0, 3, 21, 22)},
    {'id': 3, 'celdas': (8, 11, 5, 6)},
    {'id': 4, 'celdas': (8, 11, 10, 13)},
    {'id': 5, 'celdas': (8, 11, 21, 22)},
    {'id': 6, 'celdas': (16, 19, 10, 13)}
]

def centro_interseccion(id_cruce):
    for cruce in INTERSECCIONES:
        if cruce['id'] == id_cruce:
            f0, f1, c0, c1 = cruce['celdas']
            return celda_a_mundo((f0 + f1) / 2, (c0 + c1) / 2)
    raise ValueError(f"no existe el cruce {id_cruce}")

SEMAFOROS = [
    {'id': 1,  'cruce': 1, 'poste': (4, 14)},
    {'id': 2,  'cruce': 1, 'poste': (4, 9)},
    {'id': 3,  'cruce': 2, 'poste': (4, 20)},
    {'id': 4,  'cruce': 2, 'poste': (4, 23)},
    {'id': 5,  'cruce': 3, 'poste': (7, 7)},
    {'id': 6,  'cruce': 3, 'poste': (12, 4)},
    {'id': 7,  'cruce': 4, 'poste': (12, 9)},
    {'id': 8,  'cruce': 4, 'poste': (12, 14)},
    {'id': 9,  'cruce': 5, 'poste': (7, 23)},
    {'id': 10, 'cruce': 5, 'poste': (12, 20)},
    {'id': 11, 'cruce': 6, 'poste': (15, 9)},
    {'id': 12, 'cruce': 6, 'poste': (17, 14)},
]
if __name__ == "__main__":
    print(FILAS, COLS)
    print(BORDE['izq'], BORDE['der'])
    print(es_calle(0,0), es_calle(4,0), es_calle(19,24))
    print(celda_a_mundo(0,0), celda_a_mundo(19,24))
    print('errores:', validar_mapa())

    # TODO: imprimir una ruta de ejemplo desde la primera entrada