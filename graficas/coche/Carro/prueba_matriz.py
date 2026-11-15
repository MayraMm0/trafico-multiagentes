import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
import numpy as np

pygame.init()
pygame.display.set_mode((200, 200), DOUBLEBUF | OPENGL)

M = np.identity(4, dtype=np.float32).T   # igual que en Carro.py
M[0, 3] = 5.0                            # traslación de 5 en X (fila 0, columna 3)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
glMultMatrixf(M.T)
print(glGetFloatv(GL_MODELVIEW_MATRIX))
pygame.quit()