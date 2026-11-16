#Autor: Ivan Olmos Pineda

import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Import obj loader
from objloader import *

import numpy as np
import random
import math

class Carro:
    
    def __init__(self, dim, vel, Scale):
        self.DimBoard = dim
        #Se inicializa una posicion en el tablero
        self.Position = np.array([0.0, 0.0, 0.0])
        #Se inicializa un vector de direccion
        self.Direction = np.array([1.0, 0.0, 0.0])
        #Se normaliza el vector de direccion
        m = math.sqrt(self.Direction[0]*self.Direction[0] + self.Direction[2]*self.Direction[2])
        self.Direction[0] /= m
        self.Direction[2] /= m
        #Se almacena la magnitud de velocidad
        self.vel = vel
        #arreglo de cubos
        self.component = []
        #Variables de control globales del carro
        self.Avanza = False
        self.Rota = False
        self.Scale = Scale
        self.Body_Ry = 0.0
        #rotacion de llantas frontales
        self.Ll_F_Ry = 0.0
        self.Ll_F_max = 35.0 #giro max en grados
        self.Ll_F_paso = 2.0 # cuánto cambia ang de dirección por frame
        
        self.cos_ang = 0.0
        self.sin_ang = 0.0
        self.cos_angF = 0.0
        self.sin_angF = 0.0
        #Matrices para optimizacion de operadores
        # La siguiente declaracion asume que en tiempo de ejecucion se transpone la matriz
        # para usarla como la requiere OpenGL
        # self.M_Carroceria = np.identity(4, dtype=np.float32)
        # Para optimizar, se declaran las matrices identidad traspuestas
        self.M_Carroceria = np.identity(4, dtype=np.float32).T
        self.M_Carroceria[1, 1] = self.Scale
        # Matriz para las llantas traseras
        self.M_Llantas_traseras = np.identity(4, dtype=np.float32).T
        # Matriz para la llanta frontal izquierda
        self.M_Llanta_F = np.identity(4, dtype=np.float32).T
        # Matriz para la llanta frontal derecha
        #self.M_Llanta_FR = np.identity(4, dtype=np.float32).T

        # Se define el radio base del objeto llanta (depende del tamaño del objeto grafico)
        # (se debe modificar manualmente dependiendo de dicho tamaño)
        self.Llanta_radio_base = 0.707
        # Radio de la llanta considerando la escala del carro
        self.Llanta_radio = self.Llanta_radio_base * self.Scale
        # Traslacion base del origen a la posicon del eje trasero del carro
        # Este vector depende de la escala del carro
        self.LlantaT_dist = np.array([-2.3,-0.5,0.0]) # eje trasero
        self.LlantaT_pos = np.copy(self.LlantaT_dist)
        self.M_Llantas_traseras[0:3, 3] = self.LlantaT_pos # la posición del eje en el coche nunca cambia, así que se fija una vez
        # Para que las llantas tengan el efecto de girar hacia adelante
        # se debe calcular el angulo de rotacion de las mismas a partir de la formula
        # theta = (360 * d) / (2*pi*r), donde d es la distancia a recorrer y r el 
        # radio de la llanta
        # La distancia a recorrer depende de la velocidad (el vector de direccion es unitario)
        # como se desea que el carrito avance, la rotación es en contra de las manecillas del reloj
        # con respecto al eje Z, por lo tanto es una rotación negativa
        self.LlantaT_angZ_delta = math.radians((-1.0 * 360.0 * self.vel) / (2.0 * np.pi * self.Llanta_radio))
        # angulo de rotacion inicial para las llantas frontales y traseras
        self.LlantaT_angZ = 0.0
        # variables para llantas frontales
        self.LlantaFL_pos = np.array([3.4, -0.5, -1.6])
        self.LlantaFR_pos = np.array([3.4, -0.5, 1.6])
        # Distancia entre ejes
        self.L = abs(self.LlantaFL_pos[0] - self.LlantaT_pos[0]) * self.Scale
        #Distancia del origen del coche al eje trasero
        self.d_eje = abs(self.LlantaT_pos[0]) * self.Scale
        #Estado real del modelo de bicicleta: posición del eje trasero
        self.P_trasero = self.Position - self.Direction * self.d_eje
        # Intervalo de tiempo por frame
        self.dt = 100
    

    def _mult(self, M):
        glMultMatrixf(M.T)
        
    def getComponents(self, comp):
        self.component = comp
        
    def setAvanza(self):
        self.Avanza = True
    
    # variar ang con límite, dir de las llantas
    def setRota(self, dir):
        self.Rota = dir  # 'L' o 'R'
        # solo guarda petición porque update ejecuta

    # Avanzar según dirección y vel, y que se consuma(condición de no avanzar)
    def update(self):
        # 0. Dir de las llantas F (volante)
        if self.Rota == 'L':
            self.Ll_F_Ry += self.Ll_F_paso # izq es -Z, pero ang positivo
        elif self.Rota == 'R':
            self.Ll_F_Ry -= self.Ll_F_paso
        elif abs(self.Ll_F_Ry) <= self.Ll_F_paso:
            self.Ll_F_Ry = 0.0
        else:
            self.Ll_F_Ry -= math.copysign(self.Ll_F_paso, self.Ll_F_Ry) # regresa al centro
        
        # limites
        self.Ll_F_Ry = max(-self.Ll_F_max, min(self.Ll_F_max, self.Ll_F_Ry))
        
        # 1. Giro del cuerpo (solo si avanza) Δθ = (v/L)·tan(δ)
        if self.Avanza:
            dtheta = (self.vel / self.L) * math.tan(math.radians(self.Ll_F_Ry))
            self.Body_Ry = (self.Body_Ry + math.degrees(dtheta)) % 360.0
            
        # 2. Dirección sale del nuevo ángulo del cuerpo/carrocería
        rad = math.radians(self.Body_Ry)
        self.Direction[0] = math.cos(rad)
        self.Direction[2] = -math.sin(rad)
        
        # 3. Si hubo petición en frame:
        # avance del eje trasero y position derivada
        if self.Avanza:
            self.P_trasero += self.Direction * self.vel # direction unitario, recorre vel por frame
            self.LlantaT_angZ += self.LlantaT_angZ_delta
        self.Position = self.P_trasero + self.Direction * self.d_eje
        
        # 4. consumir peticiones para que se verifique cada frame
        self.Avanza = False    
        self.Rota = False
        
    
    # T_llanta: vector para ubicar la llanta en su posicion
    # id_llanta: para identificar si es llanta izquierda(1) o derecha(2)
    def llantaFrontal(self, T_llanta, id_llanta):
        glPushMatrix() # global e2 -> eje delantero
        cF = self.cos_angF # cos dirección
        sF = self.sin_angF # sin dirección
        c = math.cos(self.LlantaT_angZ) # cos rodado
        s = math.sin(self.LlantaT_angZ) # sin rodado
        M = self.M_Llanta_F
        
        M[0, 0] = cF * c
        M[0, 1] = -cF * s
        M[0, 2] = sF
        M[1, 0] = s
        M[1, 1] = c
        M[2, 0] = -sF * c
        M[2, 1] = sF * s
        M[2, 2] = cF
        M[0:3, 3] = T_llanta
        self._mult(M)
        self.component[id_llanta].render()
        glPopMatrix()
        
    
    # llenar las tres matrices y llamar a render
    def draw(self):
        # Se define la maquina de estados
        glPushMatrix() # e0 -> guarda estado de mundo 
        # Se actualizan los componentes de la matriz optimizada
        self.cos_ang = math.cos(math.radians(self.Body_Ry))
        self.sin_ang = math.sin(math.radians(self.Body_Ry))
        # se calculan ángulos de dirección una vez por frame
        self.cos_angF = math.cos(math.radians(self.Ll_F_Ry))
        self.sin_angF = math.sin(math.radians(self.Ll_F_Ry))
        
        # e1 -> marco del coche
        M = self.M_Carroceria # modifica matriz guardada en obj, sin crear nueva
        S = self.Scale
        M[0, 0] = self.cos_ang * S
        M[0, 2] = self.sin_ang * S
        M[2, 0] = -self.sin_ang * S
        M[2,2] = self.cos_ang * S
        M[0, 3] = self.Position[0]
        M[1, 3] = self.Position[1]
        M[2, 3] = self.Position[2]
        self._mult(M)
        self.component[0].render() # carrocería
        
        # e2 -> Llantas traseras 
        glPushMatrix()
        c = math.cos(self.LlantaT_angZ)
        s = math.sin(self.LlantaT_angZ)
        Mt = self.M_Llantas_traseras
        Mt[0, 0] = c
        Mt[0, 1] = -s
        Mt[1, 0] = s
        Mt[1, 1] = c
        self._mult(Mt)
        self.component[3].render() # dibuja llantas traseras
        glPopMatrix() # regresa a e1 carrocería
        
        # e2 -> llantas frontales
        self.llantaFrontal(self.LlantaFL_pos, 1)
        self.llantaFrontal(self.LlantaFR_pos, 2)

        glPopMatrix() # e0 -> volvemos a estado de mundo
        
        
