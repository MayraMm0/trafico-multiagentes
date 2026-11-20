#Agente coche decide sobre celdas, lo gráfico solo dibuja
import agentpy as ap
from graficas.ciudad.mapa import FLECHAS
from agentes.contrato import (AVANZANDO, DETENIDO, ESPERANDO_PASO, CEDIENDO, EN_CRUCE,
                              RECTO, IZQ, DER, T_PASO, DIST_SEG)

# para decidir giro según flecha de la celda
DIR_A_FLECHA = {d: ch for ch, d in FLECHAS.items()}  # (dfila, dcol) -> '>' '<' '^' 'v' 

class AgenteCoche(ap.Agent):
    def setup(self, f, c, flecha):
        self.f, self.c = f, c
        self.dir = FLECHAS[flecha]  # (dfila, dcol)
        self.estado = AVANZANDO
        self.maniobra = None # se sortea al llegar a R / L / +
        self.coordinador = None # Coordinador del cruce al que pidió paso
        self.buzon = [] # mensajes recibidos; se leen al inicio del paso
        
    # Comunicación
    def recibir(self, msg):
        self.buzon.append(msg)
        
    def enviar(self, destino, tipo, **campos):
        mensaje = {
            'tipo': tipo,
            'emisor': self,
            'destino': destino,
            't': self.model.t,
            **campos
        }
        destino.recibir(mensaje)
        
    # Contrato/Unión con lo gráfico
    def snapshot(self):
        return {
            'id': self.id,
            'f': self.f,
            'c': self.c,
            'sentido': DIR_A_FLECHA[self.dir],
            'estado': self.estado,
            'maniobra': self.maniobra
        }