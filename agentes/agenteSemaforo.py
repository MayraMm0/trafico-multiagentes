# Estado LÓGICO de un semáforo. No decide: guarda la luz que le ordena el Coordinador
# (mensaje CAMBIAR_FASE). La parte gráfica solo la pinta.
import agentpy as ap
from agentes.contrato import CAMBIAR_FASE


class AgenteSemaforo(ap.Agent):
    def setup(self, datos):
        self.sid = datos['id']       # ID del mapa (1-12), no el ID interno de AgentPy
        self.cruce = datos['cruce']
        self.luz = 'ROJO'
        self.buzon = []

    def recibir(self, msg):
        self.buzon.append(msg)

    def step(self):
        mensajes, self.buzon = self.buzon, []
        for msg in mensajes:
            if msg.get('tipo') == CAMBIAR_FASE:
                self.luz = msg.get('luz', 'ROJO')



