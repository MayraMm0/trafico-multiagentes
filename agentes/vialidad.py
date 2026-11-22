# ARCHIVO TEMPORAL después se reemplaza por lo de majo: vialidad derivada solo de mapa.py
# este archivo se reemplaza por lo de ella y se borra.
from graficas.ciudad.mapa import (MAPA, FILAS, COLS, FLECHAS, INTERSECCIONES,
                                  GIRO_DER, GIRO_IZQ, CRUCE,
                                  en_mapa, es_calle, borde_abierto, girar_der, girar_izq)
from agentes.contrato import RECTO, IZQ, DER

## TEMPORAL: todo esto ya vive en graficas/ciudad/mapa.py.
#from graficas.ciudad.mapa import (DIR_A_FLECHA, LINEAS_DE_ALTO, ESQUINAS, ENTRADAS, cruce_de,
                                 # sale_del_mapa, transitable, lleva_a_carril, girar, maniobra_hacia,
                                #  maniobras, maniobras_en_cruce, ruta_en_cruce, vecinos_que_entran)

DIR_A_FLECHA = {d: ch for ch, d in FLECHAS.items()}  # (df, dc) -> '>' '<' '^' 'v'


# id del cruce (rectángulo de INTERSECCIONES) que contiene la celda, o None
def cruce_de(f, c):
    for cruce in INTERSECCIONES:
        f0, f1, c0, c1 = cruce['celdas']
        if f0 <= f <= f1 and c0 <= c <= c1:
            return cruce['id']
    return None


# Línea de alto = flecha fuera de un cruce cuya siguiente celda ya está dentro.
# {(f, c): id_cruce}
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

# Celdas R/L que no están en ningún cruce con semáforo: ahí aplica la regla de ceder.
ESQUINAS = {(f, c) for f in range(FILAS) for c in range(COLS)
            if MAPA[f][c] in (GIRO_DER, GIRO_IZQ) and cruce_de(f, c) is None}


# True si avanzar en sentido d desde (f, c) sale por un borde abierto ('1')
def sale_del_mapa(f, c, d):
    return not en_mapa(f + d[0], c + d[1]) and bool(borde_abierto(f, c, d))


# Maniobras (misma regla que fuente_demo)

# Calle y sin flecha en contra del sentido d
def transitable(f, c, d):
    if not es_calle(f, c):
        return False
    ch = MAPA[f][c]
    return not (ch in FLECHAS and FLECHAS[ch] == (-d[0], -d[1]))


# True si yendo en d desde (f, c) la primera flecha que encuentra apunta en d
def lleva_a_carril(f, c, d):
    for _ in range(max(FILAS, COLS)):
        f, c = f + d[0], c + d[1]
        if not es_calle(f, c):
            return False
        if MAPA[f][c] in FLECHAS:
            return FLECHAS[MAPA[f][c]] == d
    return False


# Sentido nuevo después de una maniobra
def girar(d, maniobra):
    if maniobra == DER:
        return girar_der(d)
    if maniobra == IZQ:
        return girar_izq(d)
    return d

# Maniobra que convierte el sentido d en d2 (para seguir la flecha de una celda)
def maniobra_hacia(d, d2):
    if girar_der(d) == d2:
        return DER
    if girar_izq(d) == d2:
        return IZQ
    return RECTO

# Maniobras posibles al estar en (f, c) con sentido d
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

# Maniobras que puede pedir un coche parado en la línea de alto (f, c) con sentido d:
# recorre en recto las celdas del cruce y junta los giros posibles; RECTO si sale derecho.
def maniobras_en_cruce(f, c, d):
    cruce = LINEAS_DE_ALTO[(f, c)]
    posibles = set()
    f, c = f + d[0], c + d[1]                    # primera celda dentro del cruce
    while cruce_de(f, c) == cruce:
        ch = MAPA[f][c]
        if ch in FLECHAS:
            if FLECHAS[ch] != d:                 # incorporación obligada: sigue la flecha
                return sorted(posibles | {maniobra_hacia(d, FLECHAS[ch])})
        else:                                    # R, L o +
            ops = maniobras(f, c, d)
            posibles |= set(ops) - {RECTO}
            if RECTO not in ops:                 # aquí tiene que girar
                return sorted(posibles)
        f, c = f + d[0], c + d[1]
    return sorted(posibles | {RECTO})            # salió del cruce en recto


# Celdas que recorrerá un coche desde la línea de alto (f, c) haciendo 'intencion',
# hasta su primera celda fuera del cruce (incluida). Misma regla que AgenteCoche._decidir.
def ruta_en_cruce(f, c, d, intencion):
    cruce = LINEAS_DE_ALTO[(f, c)]
    ruta, ya_giro, maniobra = [], False, None
    for _ in range(FILAS * COLS):
        d = girar(d, maniobra) if maniobra in (IZQ, DER) else d
        ya_giro = ya_giro or maniobra in (IZQ, DER)
        f, c = f + d[0], c + d[1]
        ruta.append((f, c))
        if cruce_de(f, c) != cruce:              # ya salió del cruce
            return ruta
        ch, maniobra = MAPA[f][c], None
        if ch in FLECHAS:
            if FLECHAS[ch] != d:
                maniobra = maniobra_hacia(d, FLECHAS[ch])
        elif not ya_giro:
            ops = maniobras(f, c, d)
            maniobra = intencion if intencion in ops else (RECTO if RECTO in ops else ops[0])
    return ruta

# Celdas vecinas de T desde las que OTRO coche podría entrar a T (para ceder el paso).
# Ignora la celda de donde viene el coche (desde) y la que está enfrente de T.
# Si la vecina es R/L/+ no se sabe su sentido: se considera posible (conservador).
def vecinos_que_entran(T, desde, d):
    vecinos = []
    for e in FLECHAS.values():                   # e = sentido con el que el otro entraría
        n = (T[0] - e[0], T[1] - e[1])
        if n == desde or e == (-d[0], -d[1]):
            continue
        if not es_calle(*n) or not transitable(*T, e):
            continue
        ch = MAPA[n[0]][n[1]]
        if ch in FLECHAS and FLECHAS[ch] != e:   # esa flecha no apunta hacia T
            continue
        vecinos.append(n)
    return vecinos

# Entradas: dónde reaparece un coche (n constante)
# Celda de orilla con borde abierto cuyo sentido apunta hacia adentro.
# Si es R/L/+, toma el sentido de la primera flecha hacia adentro.
def _entradas():
    lados = [  # (celdas de esa orilla, sentido hacia adentro)
        ([(0, c) for c in range(COLS)],        (1, 0)),
        ([(FILAS - 1, c) for c in range(COLS)], (-1, 0)),
        ([(f, 0) for f in range(FILAS)],        (0, 1)),
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


if __name__ == '__main__':
    for k in sorted(set(LINEAS_DE_ALTO.values())):
        print(f'cruce {k}:', [p for p, v in LINEAS_DE_ALTO.items() if v == k])
    print('esquinas sin semáforo:', len(ESQUINAS), 'celdas')
    print('entradas:', len(ENTRADAS), ENTRADAS)
    print('maniobras en (3, 6) yendo <:', maniobras(3, 6, FLECHAS['<']))