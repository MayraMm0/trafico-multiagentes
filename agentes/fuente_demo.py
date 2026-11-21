# Fuente DEMO de snapshots: 1 celda por paso y giros al azar en R, L y + (sin Agentpy).
# Misma interfaz que tendrá MundoModelo: estado_inicial() y paso().
import random
from graficas.ciudad.mapa import MAPA, FLECHAS, es_calle, en_mapa, girar_der, girar_izq
from agentes.contrato import AVANZANDO, DETENIDO, DIST_SEG, RECTO, IZQ, DER

DIR_A_FLECHA = {d: ch for ch, d in FLECHAS.items()}   # (df, dc) -> '>' '<' '^' 'v'

# True si (f, c) es una flecha que apunta en sentido contrario a d
def _contraria(f, c, d):
    ch = MAPA[f][c]
    return ch in FLECHAS and FLECHAS[ch] == (-d[0], -d[1])

def _transitable(f, c, d):
    return es_calle(f, c) and not _contraria(f, c, d)

# Camina hacia atrás mientras la celda siga siendo transitable.
def _inicio_de_linea(f, c, d):
    while _transitable(f - d[0], c - d[1], d):
        f, c = f - d[0], c - d[1]
    return f, c

# True si yendo en d desde (f, c) la primera flecha que se encuentra apunta en d
def _lleva_a_carril(f, c, d):
    for _ in range(max(len(MAPA), len(MAPA[0]))):
        f, c = f + d[0], c + d[1]
        if not es_calle(f, c):
            return False
        if MAPA[f][c] in FLECHAS:
            return FLECHAS[MAPA[f][c]] == d
    return False

# Maniobras posibles al estar en (f, c) con sentido d
def _opciones(f, c, d):
    ch = MAPA[f][c]
    sig = (f + d[0], c + d[1])
    ops = [RECTO] if (_transitable(*sig, d) or not en_mapa(*sig)) else []
    if ch in 'R+' and _lleva_a_carril(f, c, girar_der(d)):
        ops.append(DER)
    if ch in 'L+' and _lleva_a_carril(f, c, girar_izq(d)):
        ops.append(IZQ)
    return ops or [RECTO]

class FuenteDemo:
    def __init__(self, posiciones, semilla=3):
        # posiciones: lista de (f, c, flecha), la misma que recibirá MundoModelo
        self.coches = [{'id': i, 'f': f, 'c': c, 'sentido': flecha,
                        'estado': DETENIDO, 'maniobra': None}
                       for i, (f, c, flecha) in enumerate(posiciones)]
        self.ya_giro = {c['id']: False for c in self.coches}   # no girar 2 veces en un cruce
        self.rng = random.Random(semilla)

    def estado_inicial(self):
        return [dict(x) for x in self.coches]

    def paso(self):
        for coche in self.coches:
            d = FLECHAS[coche['sentido']]
            giro = coche['maniobra'] in (IZQ, DER)
            if giro:                                  # 2º paso del giro: cambia el sentido
                d = girar_der(d) if coche['maniobra'] == DER else girar_izq(d)
            f2, c2 = coche['f'] + d[0], coche['c'] + d[1]
            if not _transitable(f2, c2, d):
                f2, c2 = _inicio_de_linea(coche['f'], coche['c'], d) # reaparece (solo demo)
            if self._libre(coche, f2, c2, d):
                coche['f'], coche['c'] = f2, c2
                coche['sentido'] = DIR_A_FLECHA[d]
                coche['estado'] = AVANZANDO
                self._decidir(coche, giro)
            else:
                coche['estado'] = DETENIDO            # conserva su maniobra
        return [dict(x) for x in self.coches]

    # Al entrar a una celda: decide la maniobra que hará al salir de ella
    def _decidir(self, coche, acaba_de_girar):
        f, c, d = coche['f'], coche['c'], FLECHAS[coche['sentido']]
        coche['maniobra'] = None
        if MAPA[f][c] in FLECHAS:                    # carril normal: fuera del cruce
            self.ya_giro[coche['id']] = False
        elif acaba_de_girar:
            self.ya_giro[coche['id']] = True
        elif not self.ya_giro[coche['id']]:
            coche['maniobra'] = self.rng.choice(_opciones(f, c, d))

    # Libre si ningún otro coche está en el destino ni en las celdas que le siguen.
    def _libre(self, yo, f, c, d):
        celdas = {(f + d[0] * k, c + d[1] * k) for k in range(DIST_SEG + 1)}
        return all((o['f'], o['c']) not in celdas for o in self.coches if o is not yo)

if __name__ == '__main__':
    fuente = FuenteDemo([(1, 2, '>')])
    print(f'Estado inicial: {fuente.estado_inicial()}')
    for _ in range(40):
        s = fuente.paso()[0]
        print(s['f'], s['c'], s['sentido'], s['estado'], s['maniobra'] or '')