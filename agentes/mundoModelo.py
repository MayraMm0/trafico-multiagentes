# El mundo: crea los agentes, ordena el paso y entrega un snapshot para la parte gráfica.
# Parámetros (self.p): 'n_coches', 'steps', 'seed'.   Después: 'politica', pesos del coordinador...
import agentpy as ap
from graficas.ciudad.mapa import MAPA, FLECHAS, FILAS, COLS, SEMAFOROS, ENTRADAS, cruce_de       # luego: desde graficas.ciudad.mapa
from agentes.contrato import DIST_SEG
from agentes.agenteCoche import AgenteCoche
from agentes.agenteSemaforo import AgenteSemaforo
from agentes.agenteCoordinador import AgenteCoordinador


class MundoModelo(ap.Model):

    def setup(self):
        self.ocupadas = set()
        self.reservadas = set()
        self.semaforos = ap.AgentList(self, [AgenteSemaforo(self, datos=s) for s in SEMAFOROS])
        # Un solo coordinador central administra los seis estados de cruce.
        self.coordinador = AgenteCoordinador(self, semaforos=self.semaforos)
        self.coches = ap.AgentList(self, [AgenteCoche(self, f=f, c=c, flecha=fl) for f, c, fl in self.posiciones_iniciales(self.p['n_coches'])])
        self.reapariciones = 0

    def posiciones_iniciales(self, n):
        # 1. Todas las celdas con flecha que no estén dentro de un cruce
        candidatas = [(f, c, MAPA[f][c])
                      for f in range(FILAS)
                      for c in range(COLS)
                      if MAPA[f][c] in FLECHAS and cruce_de(f, c) is None]

        # 2. Revolverlas con el random del modelo
        self.random.shuffle(candidatas)

        # 3. Elegir las que estén a más de DIST_SEG celdas de todas las ya elegidas
        elegidas = []
        for f, c, fl in candidatas:
            lejos = all(abs(f - f2) + abs(c - c2) > DIST_SEG for f2, c2, _ in elegidas)
            if lejos:
                elegidas.append((f, c, fl))
                if len(elegidas) == n:
                    break

        if len(elegidas) < n:
            print(f"[MundoModelo] solo cupieron {len(elegidas)} de {n} coches")
        return elegidas

    def step(self):
        self.reservadas.clear()
        self.ocupadas = {(c.f, c.c) for c in self.coches}
        self.coordinador.step()
        self.semaforos.step()
        self.coches.shuffle().step()
        self.reaparecer()

    def reaparecer(self):
        # Posiciones DESPUÉS de moverse (no la foto del inicio del paso)
        ocupadas_ahora = {(coche.f, coche.c) for coche in self.coches if not coche.salio}

        for coche in self.coches:
            if not coche.salio:
                continue
            # la entrada y las DIST_SEG celdas de enfrente deben estar libres
            libres = [(f, c, fl) for (f, c, fl) in ENTRADAS
                      if all((f + FLECHAS[fl][0] * k, c + FLECHAS[fl][1] * k) not in ocupadas_ahora
                             for k in range(DIST_SEG + 1))]
            if libres:
                f, c, fl = self.random.choice(libres)
                coche.reaparecer(f, c, fl)  # vuelve con salio = False
                ocupadas_ahora.add((f, c))  # para que otro no caiga en la misma
                self.reapariciones += 1
            # si no hay entrada libre: sigue con salio = True y lo intenta el siguiente paso

# parte grafica

    def snapshot(self):
        return {
            't': self.t,
            'coches': [c.snapshot() for c in self.coches],
            'semaforos': {s.sid: s.luz for s in self.semaforos},
            'cruces': {
                cid: {
                    'fase': estado.fase,
                    'fase_objetivo': estado.fase_objetivo,
                    'luz': estado.luz,
                    'pendientes': len(estado.pendientes),
                    'autorizados': len(estado.autorizados),
                }
                for cid, estado in self.coordinador.cruces.items()
            },
            'mensajes': dict(self.coordinador.contadores),
        }

    def estado_inicial(self):
        self.sim_setup()
        return self.snapshot()

    def paso(self):
        self.sim_step()
        return self.snapshot()
