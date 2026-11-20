# Fuente DEMO de snapshots: coches en línea recta, 1 celda por paso (sin Agentpy).
# Misma interfaz que tendrá MundoModelo: estado_inicial() y paso().
from graficas.ciudad.mapa import MAPA, FLECHAS, es_calle
from agentes.contrato import AVANZANDO, DETENIDO, DIST_SEG

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

class FuenteDemo:
    def __init__(self, posiciones):
        # posiciones: lista de (f, c, flecha), la misma que recibirá MundoModelo
        self.coches = [{'id': i, 'f': f, 'c': c, 'sentido': flecha,
                        'estado': DETENIDO, 'maniobra': None}
                       for i, (f, c, flecha) in enumerate(posiciones)]
        
    def estado_inicial(self):
        return [dict(x) for x in self.coches]
    
    def paso(self):
        for coche in self.coches:
            d = FLECHAS[coche['sentido']]
            f2, c2 = coche['f'] + d[0], coche['c'] + d[1]
            if not _transitable(f2, c2, d):
                f2, c2 = _inicio_de_linea(coche['f'], coche['c'], d) # reaparece (solo demo)
            if self._libre(coche, f2, c2, d):
                coche['f'], coche['c'] = f2, c2
                coche['estado'] = AVANZANDO
            else:
                coche['estado'] = DETENIDO
        return [dict(x) for x in self.coches]
    
    # Libre si ningún otro coche está en el destino ni en las celdas que le siguen.
    def _libre(self, yo, f, c, d):
        celdas = {(f + d[0] * k, c + d[1] * k) for k in range(DIST_SEG + 1)}
        return all((o['f'], o['c']) not in celdas for o in self.coches if o is not yo)

if __name__ == '__main__':
    fuente = FuenteDemo([(1, 2, '>')])
    print(f'Estado inicial: {fuente.estado_inicial()}')
    for _ in range(25):
        s = fuente.paso()[0]
        print(s['f'], s['c'], s['estado'])
        