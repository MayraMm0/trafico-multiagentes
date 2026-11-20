# Une snapshot lógico con el Carro gráfico
# máquina de estados gráfica + seguimiento que llega a la celda
from OpenGL.GL import *

from graficas.ciudad.mapa import FLECHAS, celda_a_mundo
from graficas.coche.carro import Carro

ESCALA = 0.46
ANGULO = {'>': 0.0, '^': 90.0, '<': 180.0, 'v': 270.0}   # Body_Ry según la flecha

# Estados gráficos
PARADO, AVANZANDO = 'PARADO', 'AVANZANDO'
# pendientes: GIRANDO, CAMBIANDO_CARRIL

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
        ant = self.snap
        mov = (snap['f'] - ant['f'], snap['c'] - ant['c'])
        if mov == (0, 0):
            self._colocar(snap)
            self.estado = PARADO
        elif snap['sentido'] == ant['sentido'] and mov == FLECHAS[snap['sentido']]:
            self._colocar(ant)
            self.objetivo = celda_a_mundo(snap['f'], snap['c'])
            self.estado = AVANZANDO
        else:
            self._colocar(snap)
            self.estado = PARADO
        self.snap = snap  # actualiza snapshot para el próximo paso

    # mueve el coche en cada frame.
    def actualizar(self, dt, t_restante):
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
        glPopMatrix()
