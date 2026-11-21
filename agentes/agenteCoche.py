#Agente coche decide sobre celdas, lo gráfico solo dibuja
import agentpy as ap
from graficas.ciudad.mapa import MAPA, FLECHAS
from agentes.vialidad import (DIR_A_FLECHA, LINEAS_DE_ALTO, sale_del_mapa,
                              transitable, maniobras, maniobra_hacia, girar)
from agentes.contrato import (AVANZANDO, DETENIDO, ESPERANDO_PASO, CEDIENDO, EN_CRUCE,
                              RECTO, IZQ, DER, T_PASO, DIST_SEG)

class AgenteCoche(ap.Agent):
    def setup(self, f, c, flecha):
        self.coordinador = None
        self.buzon = [] # mensajes recibidos; se leen al inicio del paso
        self.reaparecer(f, c, flecha)
    
    # Coloca el coche en (f, c)
    def reaparecer(self, f, c, flecha):
        self.f, self.c = f, c
        self.dir = FLECHAS[flecha]  # (dfila, dcol)
        self.estado = AVANZANDO
        self.maniobra = None  # maniobra que hará al SALIR de la celda actual
        self.ya_giro = False # no girar 2 veces en la misma zona
        self.t_espera = 0 # pasos seguidos sin avanzar
        self.salio = False # True = salió por un borde, el modelo lo reaparece
    
    # Percepción: Solo lo que tiene enfrente (sentido d), sobre el inicio del paso
    def percibir(self, ocupadas, d=None):
        df, dc = d or self.dir
        adelante = [(self.f + df * k, self.c + dc * k) for k in range(1, DIST_SEG + 2)]
        return {
            'libre': not any(p in ocupadas for p in adelante), # destino + DIST_SEG celdas
            'linea_alto': LINEAS_DE_ALTO.get((self.f, self.c)), # id del cruce o None
            'sale': sale_del_mapa(self.f, self.c, (df, dc)), # borde abierto enfrente
        }
    
    # Un step: percibir -> decidir -> actuar
    # el modelo necesita: 1. ocupadas (foto al inicio del step) 2. reservadas
    def step(self):
        giro = self.maniobra in (IZQ, DER)
        d = girar(self.dir, self.maniobra) if giro else self.dir # segundo paso del giro
        p = self.percibir(self.model.ocupadas, d)
        
        if p['sale']:  # sale por un borde abierto
            self.salio = True    
            return
        
        destino = (self.f + d[0], self.c + d[1])
        puede = (p['libre'] and transitable(*destino, d)
                 and destino not in self.model.reservadas)
        
        if puede:
            self.model.reservadas.add(destino) # nadie más entra a esa celda este paso
            self.f, self.c = destino
            self.dir = d
            self.estado = AVANZANDO
            self.t_espera = 0
            self._decidir(giro)
        else:
            self.estado = DETENIDO # conserva su maniobra
            self.t_espera += 1
            
    # Al entrar a una celda decide qué hará al salir de ella
    def _decidir(self, acaba_de_girar):
        self.maniobra = None
        ch = MAPA[self.f][self.c]
        if ch in FLECHAS: # carril normal
            self.ya_giro = False
            if FLECHAS[ch] != self.dir: # se incorpora a otra calle: sigue la flecha
                self.maniobra = maniobra_hacia(self.dir, FLECHAS[ch])
        elif acaba_de_girar:
            self.ya_giro = True
        elif not self.ya_giro:
            self.maniobra = self.model.random.choice(maniobras(self.f, self.c, self.dir))
            
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