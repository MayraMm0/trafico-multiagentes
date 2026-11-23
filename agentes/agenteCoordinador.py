"""Coordinador central de tráfico.

Un único agente administra los seis cruces. Cada cruce conserva su propio
estado interno; los coches y los semáforos siguen comunicándose por mensajes.
"""
import agentpy as ap
from itertools import combinations
from math import factorial

from graficas.ciudad.mapa import (
    INTERSECCIONES, SEMAFOROS, MAPA, FLECHAS, LINEAS_DE_ALTO,
    SEMAFORO_DE_ALTO, celdas_cola,
)
from agentes.vialidad import maniobras_en_cruce, ruta_en_cruce
from agentes.contrato import (
    SOLICITAR_PASO, PASAR, INFORMAR_SALIDA, CAMBIAR_FASE,
    REQUEST, AGREE, INFORM,
)


VERDE = 'VERDE'
AMARILLO = 'AMARILLO'
TODO_ROJO = 'TODO_ROJO'


class EstadoCruce:
    """Estado lógico independiente de una intersección."""

    def __init__(self, id_cruce, semaforos, accesos, movimientos):
        self.id = id_cruce
        self.semaforos = tuple(semaforos)  # (fase 0, fase 1): sid de mapa
        self.accesos = dict(accesos)       # (f,c) -> sid
        self.movimientos = list(movimientos)  # (acceso, maniobra)
        self.fase = 0
        self.fase_objetivo = 0
        self.luz = TODO_ROJO
        self.t_luz = 0
        self.pendientes = []
        self.autorizados = {}  # id_coche -> agente coche
        self.rutas_autorizadas = {}  # id_coche -> celdas reservadas del recorrido


class AgenteCoordinador(ap.Agent):
    """Agente central que decide qué fase puede avanzar en cada cruce."""

    def setup(self, semaforos):
        self.buzon = []
        self.semaforos = {s.sid: s for s in semaforos}

        # Tiempos expresados en pasos de 0.5 segundos.
        self.T_VERDE_MIN = 6
        self.T_VERDE_MAX = 24
        self.T_AMARILLO = 3
        self.T_COLA_MAX = 12

        # Pesos de la decisión: Shapley, cola y espera.
        self.pesos = {'alpha': 0.50, 'beta': 0.30, 'gamma': 0.20}

        self.cruces = {}
        for datos in INTERSECCIONES:
            cid = datos['id']
            sems = sorted(
                [s['id'] for s in SEMAFOROS if s['cruce'] == cid]
            )
            if len(sems) != 2:
                raise ValueError(
                    f"El cruce {cid} debe tener exactamente dos fases; "
                    f"se encontraron los semáforos {sems}."
                )

            accesos = {
                acceso: sid
                for acceso, cruce in LINEAS_DE_ALTO.items()
                if cruce == cid
                for sid in [SEMAFORO_DE_ALTO[acceso]]
            }
            movimientos = []
            for acceso in sorted(accesos):
                f, c = acceso
                maniobras = maniobras_en_cruce(f, c, FLECHAS[MAPA[f][c]])
                movimientos.extend((acceso, maniobra) for maniobra in maniobras)

            self.cruces[cid] = EstadoCruce(
                cid, sems, accesos, movimientos
            )

            # Se conserva el estado inicial original: todos los semáforos en rojo.
            # En el primer step el coordinador habilita la fase inicial (fase 0).
            for sid in sems:
                self.semaforos[sid].luz = 'ROJO'

        self.contadores = {
            SOLICITAR_PASO: 0,
            PASAR: 0,
            INFORMAR_SALIDA: 0,
            CAMBIAR_FASE: 0,
            'cambios_fase': 0,
        }

    # Comunicación 

    def recibir(self, msg):
        self.buzon.append(msg)

    def enviar(self, destino, tipo, **campos):
        performativa = {
            SOLICITAR_PASO: REQUEST,
            PASAR: AGREE,
            INFORMAR_SALIDA: INFORM,
            CAMBIAR_FASE: REQUEST,
        }.get(tipo, INFORM)
        mensaje = {
            'tipo': tipo,
            'performativa': performativa,
            'emisor': self,
            'destino': destino,
            't': self.model.t,
            **campos,
        }
        destino.recibir(mensaje)
        if tipo in self.contadores:
            self.contadores[tipo] += 1

    def procesar_buzon(self):
        mensajes, self.buzon = self.buzon, []
        for msg in mensajes:
            tipo = msg.get('tipo')
            if tipo == SOLICITAR_PASO:
                self.contadores[SOLICITAR_PASO] += 1
                cid = msg.get('cruce')
                estado = self.cruces.get(cid)
                acceso = tuple(msg.get('acceso', ()))
                coche = msg.get('emisor')
                if estado is None or acceso not in estado.accesos or coche is None:
                    continue
                sid = estado.accesos[acceso]
                maniobra = msg.get('maniobra')
                if (acceso, maniobra) not in estado.movimientos:
                    continue
                if coche.id in estado.autorizados:
                    continue
                if any(p['coche'].id == coche.id for p in estado.pendientes):
                    continue
                estado.pendientes.append({
                    'coche': coche,
                    'id_coche': coche.id,
                    'acceso': acceso,
                    'maniobra': maniobra,
                    'sid': sid,
                    't': msg.get('t', self.model.t),
                })

            elif tipo == INFORMAR_SALIDA:
                self.contadores[INFORMAR_SALIDA] += 1
                cid = msg.get('cruce')
                estado = self.cruces.get(cid)
                coche = msg.get('emisor')
                if estado is not None and coche is not None:
                    estado.autorizados.pop(coche.id, None)
                    estado.rutas_autorizadas.pop(coche.id, None)

    # Sensores

    def medir_colas(self, cruce):
        """Cuenta coches en la línea de alto y detrás de ella por cada acceso."""
        estado = self.cruces[cruce]
        ocupadas = getattr(self.model, 'ocupadas', set())
        colas = {}
        for acceso in estado.accesos:
            celdas = [acceso] + celdas_cola(*acceso, self.T_COLA_MAX)
            colas[acceso] = sum(1 for celda in celdas if celda in ocupadas)
        return colas

    def _demanda_fase(self, estado, fase, colas=None):
        if colas is None:
            colas = self.medir_colas(estado.id)
        sid = estado.semaforos[fase]
        return sum(
            cantidad for acceso, cantidad in colas.items()
            if estado.accesos[acceso] == sid
        )

    def _espera_fase(self, estado, fase):
        sid = estado.semaforos[fase]
        solicitudes = [p for p in estado.pendientes if p['sid'] == sid]
        if not solicitudes:
            return 0
        return max(self.model.t - p['t'] for p in solicitudes)

    # Teoría de juegos

    @staticmethod
    def funcion_caracteristica(jugadores, coalicion):
        """v(C) = máximo flujo simultáneo de una de las dos fases."""
        if not coalicion:
            return 0.0
        por_fase = {}
        for indice in coalicion:
            jugador = jugadores[indice]
            por_fase[jugador['sid']] = (
                por_fase.get(jugador['sid'], 0.0) + jugador['peso']
            )
        return max(por_fase.values(), default=0.0)

    def shapley(self, jugadores):
        """Calcula Shapley exacto por enumeración de coaliciones."""
        n = len(jugadores)
        if n == 0:
            return []
        resultado = [0.0] * n
        denominador = factorial(n)
        indices = set(range(n))
        for i in range(n):
            otros = sorted(indices - {i})
            for tam in range(n):
                coeficiente = (
                    factorial(tam) * factorial(n - tam - 1)
                    / denominador
                )
                for subconjunto in combinations(otros, tam):
                    coalicion = set(subconjunto)
                    marginal = (
                        self.funcion_caracteristica(jugadores, coalicion | {i})
                        - self.funcion_caracteristica(jugadores, coalicion)
                    )
                    resultado[i] += coeficiente * marginal
        return resultado

    def _jugadores_con_demanda(self, estado, colas):
        # Solo hay un coche en la línea de alto por acceso; por ello el
        # número de jugadores no supera el número de accesos del cruce.
        jugadores = []
        for solicitud in estado.pendientes:
            acceso = solicitud['acceso']
            jugadores.append({
                'acceso': acceso,
                'maniobra': solicitud['maniobra'],
                'sid': solicitud['sid'],
                'peso': float(max(1, colas.get(acceso, 0))),
            })
        return jugadores

    def elegir_fase(self, cruce):
        """Combina Shapley, cola y espera; devuelve índice 0 o 1."""
        estado = self.cruces[cruce]
        colas = self.medir_colas(cruce)
        jugadores = self._jugadores_con_demanda(estado, colas)
        valores_shapley = self.shapley(jugadores)

        shapley_fase = [0.0, 0.0]
        for jugador, valor in zip(jugadores, valores_shapley):
            indice_fase = estado.semaforos.index(jugador['sid'])
            shapley_fase[indice_fase] += valor

        cola_fase = [
            self._demanda_fase(estado, fase, colas) for fase in (0, 1)
        ]
        espera_fase = [
            self._espera_fase(estado, fase) for fase in (0, 1)
        ]

        def normalizar(valores):
            maximo = max(valores, default=0)
            return [v / maximo if maximo > 0 else 0.0 for v in valores]

        s_norm = normalizar(shapley_fase)
        c_norm = normalizar(cola_fase)
        e_norm = normalizar(espera_fase)

        alpha = self.pesos['alpha']
        beta = self.pesos['beta']
        gamma = self.pesos['gamma']
        puntajes = [
            alpha * s_norm[i] + beta * c_norm[i] + gamma * e_norm[i]
            for i in (0, 1)
        ]

        if puntajes[0] > puntajes[1]:
            return 0
        if puntajes[1] > puntajes[0]:
            return 1

        # Desempate por espera, luego por cola, y finalmente alternancia.
        if espera_fase[0] != espera_fase[1]:
            return 0 if espera_fase[0] > espera_fase[1] else 1
        if cola_fase[0] != cola_fase[1]:
            return 0 if cola_fase[0] > cola_fase[1] else 1
        return 1 - estado.fase

    # Control de fases

    def cambiar_luz(self, estado, luz, nueva_fase=None):
        if nueva_fase is not None:
            estado.fase_objetivo = nueva_fase
        estado.luz = luz
        estado.t_luz = 0
        sid_activo = estado.semaforos[estado.fase]
        for sid in estado.semaforos:
            if luz == VERDE:
                color = VERDE if sid == sid_activo else 'ROJO'
            elif luz == AMARILLO:
                color = AMARILLO if sid == sid_activo else 'ROJO'
            else:
                color = 'ROJO'
            self.enviar(
                self.semaforos[sid], CAMBIAR_FASE,
                cruce=estado.id, luz=color, fase=estado.fase
            )
        self.contadores['cambios_fase'] += 1

    def actualizar_luz(self, estado):
        estado.t_luz += 1

        if estado.luz == VERDE:
            if estado.t_luz < self.T_VERDE_MIN:
                return
            otra_fase = 1 - estado.fase
            demanda_otra = self._demanda_fase(estado, otra_fase) > 0
            fase_elegida = self.elegir_fase(estado.id)

            if demanda_otra and (
                fase_elegida == otra_fase or estado.t_luz >= self.T_VERDE_MAX
            ):
                self.cambiar_luz(estado, AMARILLO, nueva_fase=otra_fase)

        elif estado.luz == AMARILLO:
            if estado.t_luz >= self.T_AMARILLO:
                self.cambiar_luz(estado, TODO_ROJO)

        elif estado.luz == TODO_ROJO:
            # Nunca se habilita la fase opuesta mientras haya coches dentro.
            if not estado.autorizados:
                estado.fase = estado.fase_objetivo
                self.cambiar_luz(estado, VERDE)

    def autorizar(self, estado):
        """Autoriza solo solicitudes de la fase que actualmente está en verde."""
        if estado.luz != VERDE:
            return
        sid_verde = estado.semaforos[estado.fase]
        conservar = []
        ocupadas = getattr(self.model, 'ocupadas', set())
        rutas_reservadas = set().union(*estado.rutas_autorizadas.values()) if estado.rutas_autorizadas else set()
        for solicitud in estado.pendientes:
            if solicitud['sid'] != sid_verde:
                conservar.append(solicitud)
                continue
            coche = solicitud['coche']
            if coche.id in estado.autorizados:
                continue

            # Primera capa: el coordinador usa la foto común de ocupación para
            # no autorizar una trayectoria que ya está bloqueada. El coche
            # vuelve a comprobar la ruta al recibir PASAR (segunda capa).
            acceso = solicitud['acceso']
            direccion = FLECHAS[MAPA[acceso[0]][acceso[1]]]
            ruta = set(ruta_en_cruce(
                acceso[0], acceso[1], direccion, solicitud['maniobra']
            ))
            if not ruta or ruta.intersection(ocupadas) or ruta.intersection(rutas_reservadas):
                conservar.append(solicitud)
                continue

            self.enviar(coche, PASAR, cruce=estado.id)
            estado.autorizados[coche.id] = coche
            estado.rutas_autorizadas[coche.id] = ruta
            rutas_reservadas.update(ruta)
        estado.pendientes = conservar

    def step(self):
        self.procesar_buzon()
        for estado in self.cruces.values():
            self.actualizar_luz(estado)
            self.autorizar(estado)
