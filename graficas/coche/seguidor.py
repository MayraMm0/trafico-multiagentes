# Une snapshot lógico con el Carro gráfico
# máquina de estados gráfica + seguimiento que llega a la celda
import math
from OpenGL.GL import *

from graficas.ciudad.mapa import FLECHAS, CELL, celda_a_mundo, girar_der, girar_izq
from graficas.coche.carro import Carro
from agentes.contrato import IZQ, DER

ESCALA = 0.46
ANGULO = {'>': 0.0, '^': 90.0, '<': 180.0, 'v': 270.0}   # Body_Ry según la flecha
MUESTRAS = 16 # puntos para medir el largo de la curva
RAMPA = 0.6 # m al inicio/fin del giro donde el volante se endereza
# Estados gráficos
PARADO, AVANZANDO, GIRANDO = 'PARADO', 'AVANZANDO', 'GIRANDO'
# pendientes: CAMBIANDO_CARRIL
MOSTRAR_RUTA = False  # tecla T: dibuja la curva del giro
RADIO = CELL  # radio del arco de giro (1 celda = 2 m)


class CocheGrafico:
    def __init__(self, snap, piezas):
        self.carro = Carro(None, 0.0, ESCALA)
        self.carro.getComponents(piezas)
        self.snap = snap
        self.estado = PARADO
        self._colocar(snap)
    
    # Pone el coche exacto en la celda del snapshot (sin interpolar).
    def _colocar(self, snap):
        x, z = celda_a_mundo(snap['f'], snap['c'])
        self.carro.set_pose(x, z, ANGULO[snap['sentido']])
        self.objetivo = (x, z)
        
    # Decide el estado gráfico comparando el snapshot nuevo con el anterior.
    def recibir(self, snap):
        ant, self.snap = self.snap, snap
        mov = (snap['f'] - ant['f'], snap['c'] - ant['c'])
        
        if self.estado == GIRANDO:
            if mov == (0, 0):
                return # detenido a media curva: misma meta
            if self.s_meta < self.largo and mov == FLECHAS[snap['sentido']]:
                self.s_meta = self.largo # 2º snapshot del giro: meta = P2
                return
            self.estado = AVANZANDO  # el giro terminó: sigue como recta
            self.carro.Ll_F_Ry = 0.0 # volante recto: que update() no lo desvíe
            
        if mov == (0, 0):
            self._colocar(snap)   # corrige residuo
            self.estado = PARADO
        elif snap['sentido'] == ant['sentido'] and mov == FLECHAS[snap['sentido']]:
            self._colocar(ant) # corrige residuo en la celda de origen
            if snap['maniobra'] in (IZQ, DER):
                self._iniciar_giro(ant, snap)
            else:
                self.objetivo = celda_a_mundo(snap['f'], snap['c'])
                self.estado = AVANZANDO
        else:
            self._colocar(snap) # salto (reaparición de la demo)
            self.estado = PARADO
       
    # Cuarto de círculo de radio RADIO: de P0 (celda anterior) a P2 (celda después del giro).
    def _iniciar_giro(self, ant, snap):
        d = FLECHAS[snap['sentido']]
        d2 = girar_der(d) if snap['maniobra'] == DER else girar_izq(d)
        self.ini = celda_a_mundo(ant['f'], ant['c']) # P0
        self.adelante = (d[1], d[0]) # sentido de llegada en (x, z)
        self.lado = (d2[1], d2[0])  # sentido de salida en (x, z)
        self.signo = 1.0 if snap['maniobra'] == IZQ else -1.0 # + = izquierda (como el volante)
        self.largo = RADIO * math.pi / 2 # longitud del arco
        self.s = 0.0
        self.s_meta = self.largo / 2  # 1er paso: llegar a la mitad
        self.estado = GIRANDO
    
    # Punto del arco a s metros del inicio: posicion(x, z) y ángulo del cuerpo
    # el centro del círculo está a RADIO de P0 hacia el lado de salida
    def arco(self, s):
        th = s / RADIO # ángulo recorrido (rad)
        a, l = self.adelante, self.lado
        x = self.ini[0] + RADIO * (a[0] * math.sin(th) + l[0] * (1 - math.cos(th)))
        z = self.ini[1] + RADIO * (a[1] * math.sin(th) + l[1] * (1 - math.cos(th)))
        tx = a[0] * math.cos(th) + l[0] * math.sin(th)    # tangente = hacia dónde mira
        tz = a[1] * math.cos(th) + l[1] * math.sin(th)
        return x, z, math.degrees(math.atan2(-tz, tx))
    
    # mueve el coche en cada frame.
    # t_restante = segundos que faltan para el siguiente snapshot
    def actualizar(self, dt, t_restante):
        if self.estado == GIRANDO:
            restante = self.s_meta - self.s
            d = restante * dt / max(t_restante, dt) if restante > 0 else 0.0
            self.s += d
            x, z, ang = self.arco(self.s)
            # volante = atan(L . K), enderezado cerca de la entrada y la salida (solo visual)
            rampa = min(1.0, self.s / RAMPA, (self.largo - self.s) / RAMPA)
            volante = self.signo * math.degrees(math.atan(self.carro.L / RADIO)) * rampa
            self.carro.colocar_en_curva(x, z, ang, volante, d)
            return
        
        if self.estado == AVANZANDO:
            x, z = self.carro.Position[0], self.carro.Position[2]
            dx, dz = self.objetivo[0] - x, self.objetivo[1] - z
            restante = dx * self.carro.Direction[0] + dz * self.carro.Direction[2]
            if restante > 0:
                #velocidad justa para llegar cuando llegue el siguiente snapshot
                self.carro.vel = restante / max(t_restante, dt)
                self.carro.setAvanza()
                
        self.carro.update(dt)
      
    # lo pinta  
    def dibujar(self, y_base):
        glPushMatrix()
        glTranslatef(0.0, y_base, 0.0)
        self.carro.draw()
        if MOSTRAR_RUTA and self.estado == GIRANDO:
            self._dibujar_ruta()
        glPopMatrix()
    
    # depuración: curva del giro, sus puntos P0/C/P2   
    def _dibujar_ruta(self):
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.4, 0.1)
        glBegin(GL_LINE_STRIP)
        for i in range(MUESTRAS + 1):
            x, z, _ = self.arco(self.largo * i / MUESTRAS)
            glVertex3f(x, 0.1, z)
        glEnd()
        glPointSize(8.0)
        glColor3f(0.1, 0.4, 1.0)
        glBegin(GL_POINTS)
        x, z, _ = self.arco(self.s_meta)
        glVertex3f(x, 0.1, z)
        glEnd()
        glEnable(GL_LIGHTING)
