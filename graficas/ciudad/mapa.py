
# correr con python -m graficas.ciudad.mapa

CELL = 2.0  # metros por celda

EDIFICIO, ARBOL = '#', '*'
CRUCE, GIRO_DER, GIRO_IZQ = '+', 'R', 'L'
FLECHAS = {'>': (0, 1), '<': (0, -1), '^': (-1, 0), 'v': (1, 0)}

RECTO, IZQ, DER = 'RECTO', 'IZQ', 'DER'

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

# (fila_ini, fila_fin, col_ini, col_fin)
INTERSECCIONES = [
    {'id': 1, 'celdas': (0, 3, 10, 13)},
    {'id': 2, 'celdas': (0, 3, 21, 22)},
    {'id': 3, 'celdas': (8, 11, 5, 6)},
    {'id': 4, 'celdas': (8, 11, 10, 13)},
    {'id': 5, 'celdas': (8, 11, 21, 22)},
    {'id': 6, 'celdas': (16, 19, 10, 13)}
]

SEMAFOROS = [
    {'id': 1, 'cruce': 1, 'poste': (4, 14), 'accesos': ['^']},
    {'id': 2, 'cruce': 1, 'poste': (4, 9), 'accesos': ['>', '<']},
    {'id': 3, 'cruce': 2, 'poste': (4, 20), 'accesos': ['>']},
    {'id': 4, 'cruce': 2, 'poste': (4, 23), 'accesos': ['<']},
    {'id': 5, 'cruce': 3, 'poste': (7, 7), 'accesos': ['v', '^']},
    {'id': 6, 'cruce': 3, 'poste': (12, 4), 'accesos': ['<', '>']},
    {'id': 7, 'cruce': 4, 'poste': (12, 9), 'accesos': ['<', '>']},
    {'id': 8, 'cruce': 4, 'poste': (12, 14), 'accesos': ['^']},
    {'id': 9, 'cruce': 5, 'poste': (7, 23), 'accesos': ['v']},
    {'id': 10, 'cruce': 5, 'poste': (12, 20), 'accesos': ['<', '>']},
    {'id': 11, 'cruce': 6, 'poste': (15, 9), 'accesos': ['>']},
    {'id': 12, 'cruce': 6, 'poste': (17, 14), 'accesos': ['<']},
]


def cargar_mapa(txt):
    lines = txt.strip('\n').split('\n')
    mapa = []
    izq, der = "", ""

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
    if d == (-1, 0):
        return BORDE['arriba'][c] == '1'
    elif d == (1, 0):
        return BORDE['abajo'][c] == '1'
    elif d == (0, -1):
        return BORDE['izq'][f] == '1'
    elif d == (0, 1):
        return BORDE['der'][f] == '1'
    return None


def girar_der(d):
    df, dc = d
    return dc, -df


def girar_izq(d):
    df, dc = d
    return -dc, df


def celda_a_mundo(f, c):
    x = c * CELL + CELL / 2 - COLS * CELL / 2
    z = f * CELL + CELL / 2 - FILAS * CELL / 2
    return x, z


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
            errores.append(
                f"semaforo {s['id']}: el poste {s['poste']} no está en banqueta"
            )

    return errores
    # TODO: cada entrada tiene ruta a alguna salida
    # TODO: toda celda de calle aparece en al menos una ruta posible
    # (BFS desde todas las entradas a la vez y comparar contra las celdas de calle)


def centro_interseccion(id_cruce):
    for cruce in INTERSECCIONES:
        if cruce['id'] == id_cruce:
            f0, f1, c0, c1 = cruce['celdas']
            return celda_a_mundo((f0 + f1) / 2, (c0 + c1) / 2)

    raise ValueError(f"no existe el cruce {id_cruce}")


DIR_A_FLECHA = {d: ch for ch, d in FLECHAS.items()}


# id del cruce que contiene la celda, o None
def cruce_de(f, c):
    for cruce in INTERSECCIONES:
        f0, f1, c0, c1 = cruce['celdas']
        if f0 <= f <= f1 and c0 <= c <= c1:
            return cruce['id']
    return None


# Línea de alto = flecha fuera de un cruce cuya siguiente celda ya está dentro.
def _lineas_de_alto():
    lineas = {}

    for f in range(FILAS):
        for c in range(COLS):
            ch = MAPA[f][c]

            if ch in FLECHAS and cruce_de(f, c) is None:
                df, dc = FLECHAS[ch]
                cruce = cruce_de(f + df, c + dc)

                if cruce is not None:
                    lineas[(f, c)] = cruce

    return lineas


LINEAS_DE_ALTO = _lineas_de_alto()


# Celdas R/L que no están en ningún cruce con semáforo.
ESQUINAS = {
    (f, c)
    for f in range(FILAS)
    for c in range(COLS)
    if MAPA[f][c] in (GIRO_DER, GIRO_IZQ) and cruce_de(f, c) is None
}


# True si avanzar en sentido d desde (f, c) sale por un borde abierto.
def sale_del_mapa(f, c, d):
    return not en_mapa(f + d[0], c + d[1]) and bool(borde_abierto(f, c, d))


# Maniobras

def transitable(f, c, d):
    if not es_calle(f, c):
        return False

    ch = MAPA[f][c]
    return not (ch in FLECHAS and FLECHAS[ch] == (-d[0], -d[1]))


def lleva_a_carril(f, c, d):
    for _ in range(max(FILAS, COLS)):
        f, c = f + d[0], c + d[1]

        if not es_calle(f, c):
            return False

        if MAPA[f][c] in FLECHAS:
            return FLECHAS[MAPA[f][c]] == d

    return False


def girar(d, maniobra):
    if maniobra == DER:
        return girar_der(d)

    if maniobra == IZQ:
        return girar_izq(d)

    return d


def maniobra_hacia(d, d2):
    if girar_der(d) == d2:
        return DER

    if girar_izq(d) == d2:
        return IZQ

    return RECTO


def maniobras(f, c, d):
    ch = MAPA[f][c]
    ops = []

    if transitable(f + d[0], c + d[1], d) or sale_del_mapa(f, c, d):
        ops.append(RECTO)

    if ch in (GIRO_DER, CRUCE) and lleva_a_carril(f, c, girar_der(d)):
        ops.append(DER)

    if ch in (GIRO_IZQ, CRUCE) and lleva_a_carril(f, c, girar_izq(d)):
        ops.append(IZQ)

    return ops or [RECTO]


def maniobras_en_cruce(f, c, d):
    cruce = LINEAS_DE_ALTO[(f, c)]
    posibles = set()

    f, c = f + d[0], c + d[1]

    while cruce_de(f, c) == cruce:
        ch = MAPA[f][c]

        if ch in FLECHAS:
            if FLECHAS[ch] != d:
                return sorted(posibles | {maniobra_hacia(d, FLECHAS[ch])})

        else:
            ops = maniobras(f, c, d)
            posibles |= set(ops) - {RECTO}

            if RECTO not in ops:
                return sorted(posibles)

        f, c = f + d[0], c + d[1]

    return sorted(posibles | {RECTO})


def ruta_en_cruce(f, c, d, intencion):
    cruce = LINEAS_DE_ALTO[(f, c)]
    ruta, ya_giro, maniobra = [], False, None

    for _ in range(FILAS * COLS):
        d = girar(d, maniobra) if maniobra in (IZQ, DER) else d
        ya_giro = ya_giro or maniobra in (IZQ, DER)

        f, c = f + d[0], c + d[1]
        ruta.append((f, c))

        if cruce_de(f, c) != cruce:
            return ruta

        ch, maniobra = MAPA[f][c], None

        if ch in FLECHAS:
            if FLECHAS[ch] != d:
                maniobra = maniobra_hacia(d, FLECHAS[ch])

        elif not ya_giro:
            ops = maniobras(f, c, d)
            maniobra = intencion if intencion in ops else (
                RECTO if RECTO in ops else ops[0]
            )

    return ruta


# Celdas vecinas de T desde las que OTRO coche podría entrar a T.
def vecinos_que_entran(T, desde, d):
    vecinos = []

    for e in FLECHAS.values():
        n = (T[0] - e[0], T[1] - e[1])

        if n == desde or e == (-d[0], -d[1]):
            continue

        if not es_calle(*n) or not transitable(*T, e):
            continue

        ch = MAPA[n[0]][n[1]]

        if ch in FLECHAS and FLECHAS[ch] != e:
            continue

        vecinos.append(n)

    return vecinos


# Entradas: dónde reaparece un coche.
def _entradas():
    lados = [
        ([(0, c) for c in range(COLS)], (1, 0)),
        ([(FILAS - 1, c) for c in range(COLS)], (-1, 0)),
        ([(f, 0) for f in range(FILAS)], (0, 1)),
        ([(f, COLS - 1) for f in range(FILAS)], (0, -1)),
    ]

    entradas = []

    for celdas, adentro in lados:
        for f, c in celdas:
            afuera = (-adentro[0], -adentro[1])

            if not es_calle(f, c) or not borde_abierto(f, c, afuera):
                continue

            ch = MAPA[f][c]

            if ch in FLECHAS:
                ok = FLECHAS[ch] == adentro
            else:
                ok = lleva_a_carril(f, c, adentro)

            if ok:
                entradas.append((f, c, DIR_A_FLECHA[adentro]))

    return sorted(set(entradas))


ENTRADAS = _entradas()


# Funciones para el coordinador

def _semaforo_de_alto():
    """Regresa {(f, c): id_semaforo} para cada línea de alto."""
    resultado = {}

    for (f, c), id_cruce in LINEAS_DE_ALTO.items():
        direccion = MAPA[f][c]

        candidatos = [
            sem for sem in SEMAFOROS
            if sem['cruce'] == id_cruce
            and direccion in sem.get('accesos', [])
        ]

        if len(candidatos) != 1:
            raise ValueError(
                f"La línea de alto {(f, c)} del cruce {id_cruce} "
                f"({direccion}) corresponde a {len(candidatos)} semáforos."
            )

        resultado[(f, c)] = candidatos[0]['id']

    return resultado


SEMAFORO_DE_ALTO = _semaforo_de_alto()


def celdas_cola(f, c, n=12):
    """Regresa hasta n celdas detrás de la línea de alto, en el mismo carril."""
    direccion = MAPA[f][c]

    if direccion not in FLECHAS:
        return []

    df, dc = FLECHAS[direccion]
    resultado = []

    for k in range(1, n + 1):
        g, h = f - df * k, c - dc * k

        if not en_mapa(g, h) or MAPA[g][h] != direccion:
            break

        resultado.append((g, h))

    return resultado


if __name__ == "__main__":
    print(FILAS, COLS)
    print(BORDE['izq'], BORDE['der'])
    print(es_calle(0, 0), es_calle(4, 0), es_calle(19, 24))
    print(celda_a_mundo(0, 0), celda_a_mundo(19, 24))
    print('errores:', validar_mapa())

    # TODO: imprimir una ruta de ejemplo desde la primera entrada
