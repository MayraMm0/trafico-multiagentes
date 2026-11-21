#Agente coche decide sobre celdas, lo gráfico solo dibuja
import agentpy as ap
from graficas.ciudad.mapa import MAPA, FLECHAS
from agentes.vialidad import (DIR_A_FLECHA, LINEAS_DE_ALTO, cruce_de, sale_del_mapa,
                              transitable, maniobras, maniobras_en_cruce, ruta_en_cruce,
                              maniobra_hacia, girar, vecinos_que_entran)
from agentes.contrato import (AVANZANDO, DETENIDO, ESPERANDO_PASO, CEDIENDO, EN_CRUCE,
                              RECTO, IZQ, DER, T_PASO, DIST_SEG,
                              SOLICITAR_PASO, PASAR, INFORMAR_SALIDA)

PACIENCIA = 6  # pasos máximos cediendo (3 s); después entra igual (evita que dos se cedan siempre)

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
        self.cruce = None # id del cruce al que pidió paso (o en el que está)
        self.intencion = None # maniobra pedida en la línea de alto (RECTO / IZQ / DER)
        self.permiso = False # True al recibir PASAR de su cruce
    
    # Percepción: Solo lo que tiene enfrente (sentido d), sobre el inicio del paso
    def percibir(self, ocupadas, d=None):
        df, dc = d or self.dir
        adelante = [(self.f + df * k, self.c + dc * k) for k in range(1, DIST_SEG + 2)]
        return {
            'libre': not any(p in ocupadas for p in adelante), # destino + DIST_SEG celdas
            'linea_alto': LINEAS_DE_ALTO.get((self.f, self.c)), # id del cruce o None
            'sale': sale_del_mapa(self.f, self.c, (df, dc)), # borde abierto enfrente
        }
        
    # Percepción de maniobra en cruce: está libre su celda de salida?
    # Si no -> no entra, para no bloquear intersección
    def salida_libre(self, ocupadas):
        ruta = ruta_en_cruce(self.f, self.c, self.dir, self.intencion)
        return ruta[-1] not in ocupadas # celda de salida libre?
    
    # Percepción para ceder: hay otro coche junto a su destino que podría entrar ahí?
    # Solo cede quien gira o se incorpora (fuera de cruces con semáforo); el que va recto en
    # su carril tiene prioridad y no revisa.
    def debe_ceder(self, ocupadas, destino, d, giro):
        if self.estado == EN_CRUCE:                  # en el cruce manda el Coordinador
            return False
        ch = MAPA[destino[0]][destino[1]]
        se_incorpora = ch in FLECHAS and FLECHAS[ch] != d
        if not (giro or se_incorpora):
            return False
        vecinos = vecinos_que_entran(destino, (self.f, self.c), d)
        return any(n in ocupadas for n in vecinos)
    
    # Un step: percibir -> decidir -> actuar
    # el modelo necesita: 1. ocupadas (foto al inicio del step) 2. reservadas
    def step(self):
        self._leer_buzon()
        if (self.f, self.c) in LINEAS_DE_ALTO and self.cruce is None:
            self._pedir_paso() # p. ej. apareció justo en la línea de alto
        if self.estado == ESPERANDO_PASO and not (self.permiso and self.salida_libre(self.model.ocupadas)):
            self.t_espera += 1
            return # sigue esperando
        
        giro = self.maniobra in (IZQ, DER)
        d = girar(self.dir, self.maniobra) if giro else self.dir # segundo paso del giro
        p = self.percibir(self.model.ocupadas, d)
        
        if p['sale']:  # sale por un borde abierto
            self.salio = True    
            return
        
        destino = (self.f + d[0], self.c + d[1])
        
        if (transitable(*destino, d) and self.t_espera < PACIENCIA
                and self.debe_ceder(self.model.ocupadas, destino, d, giro)):
            self.estado = CEDIENDO # conserva maniobra
            self.t_espera += 1
            return 
        
        puede = (p['libre'] and transitable(*destino, d)
                 and destino not in self.model.reservadas)
        
        if puede:
            self.model.reservadas.add(destino) # nadie más entra a esa celda este paso
            self.f, self.c = destino
            self.dir = d
            self.t_espera = 0
            self._decidir(giro)
            self._al_entrar()
        else:
            if self.estado in (AVANZANDO, CEDIENDO):  # ESPERANDO_PASO y EN_CRUCE se conservan
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
            ops = maniobras(self.f, self.c, self.dir)
            if self.intencion in ops: # en el cruce: hace lo que pidió
                self.maniobra = self.intencion
            elif self.intencion is not None and RECTO in ops:
                self.maniobra = RECTO # sigue recto
            else:
                self.maniobra = self.model.random.choice(ops)
        
    # después de moverse: transiciones de la máquina de estados
    def _al_entrar(self):
        if self.estado == ESPERANDO_PASO:
            self.estado = EN_CRUCE # cruzó la línea de alto
        elif self.estado == EN_CRUCE:
            if cruce_de(self.f, self.c) != self.cruce:
                self._salir_del_cruce()
        else:
            self.estado = AVANZANDO
        if (self.f, self.c) in LINEAS_DE_ALTO and self.estado == AVANZANDO:
            self._pedir_paso()
            
    # En la línea de alto: sortea su maniobra y pide paso (SOLICITAR_PASO)
    def _pedir_paso(self):
        self.cruce = LINEAS_DE_ALTO[(self.f, self.c)]
        self.intencion = self.model.random.choice(maniobras_en_cruce(self.f, self.c, self.dir))
        self.estado = ESPERANDO_PASO
        self.coordinador = getattr(self.model, 'coordinador', None)
        if self.coordinador is None:
            self.permiso = True # sin Coordinador: verde permanente
            return
        self.permiso = False
        self.enviar(self.coordinador, SOLICITAR_PASO, cruce=self.cruce,
                    acceso=(self.f, self.c), maniobra=self.intencion)
        
    # Sale del rectángulo del cruce: avisa (INFORMAR_SALIDA) y vuelve a AVANZANDO
    def _salir_del_cruce(self):
        if self.coordinador is not None:
            self.enviar(self.coordinador, INFORMAR_SALIDA, cruce=self.cruce)
        self.cruce, self.intencion, self.permiso = None, None, False 
        self.estado = AVANZANDO
        
    # Lee mensajes, solo le importa PASAR de su cruce
    def _leer_buzon(self):
        for msg in self.buzon:
            if msg['tipo'] == PASAR and msg.get('cruce') == self.cruce:
                self.permiso = True
        self.buzon.clear()
           
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