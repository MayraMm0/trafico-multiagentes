import os
import pygame
from OpenGL.GL import *


class OBJ:
    generate_on_init = True
    _texturas = {}               # cache: la misma imagen se sube a la GPU una sola vez

    @classmethod
    def loadTexture(cls, imagefile):
        if imagefile in cls._texturas:
            return cls._texturas[imagefile]
        if not os.path.isfile(imagefile):
            # Sin la imagen no truena: el material usa su color Kd
            print("[objloader] textura no encontrada, uso color Kd:", imagefile)
            cls._texturas[imagefile] = None
            return None
        try:
            surf = pygame.image.load(imagefile)
            image = pygame.image.tostring(surf, 'RGBA', 1)
        except Exception as e:
            # Imagen dañada o en un formato que pygame no lee: usar color Kd
            print("[objloader] no se pudo leer la textura, uso color Kd:", imagefile, "->", e)
            cls._texturas[imagefile] = None
            return None
        ix, iy = surf.get_rect().size
        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        glBindTexture(GL_TEXTURE_2D, 0)
        cls._texturas[imagefile] = texid
        return texid

    @classmethod
    def loadMaterial(cls, filename):
        contents = {}
        mtl = None
        dirname = os.path.dirname(filename)

        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'newmtl':
                mtl = contents[values[1]] = {'Kd': (0.8, 0.8, 0.8)}
            elif mtl is None:
                raise ValueError("mtl file doesn't start with newmtl stmt")
            elif values[0] == 'map_Kd':
                # load the texture referred to by this declaration
                mtl['map_Kd'] = values[1]
                texid = cls.loadTexture(os.path.join(dirname, mtl['map_Kd']))
                if texid is not None:
                    mtl['texture_Kd'] = texid
            else:
                mtl[values[0]] = list(map(float, values[1:]))
        return contents

    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = {}
        dirname = os.path.dirname(filename)

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = self.loadMaterial(os.path.join(dirname, values[1]))
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
        if self.generate_on_init:
            self.generate()

    def generate(self):
        """Compila el modelo en una display list agrupando caras por material:
        un cambio de color/textura y un solo glBegin(GL_TRIANGLES) por material."""
        por_material = {}
        for vertices, normals, texture_coords, material in self.faces:
            por_material.setdefault(material, []).append((vertices, normals, texture_coords))

        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glFrontFace(GL_CCW)
        for material, caras in por_material.items():
            mtl = self.mtl.get(material, {'Kd': (0.8, 0.8, 0.8)})
            if 'texture_Kd' in mtl:
                # textura: color blanco para no teñirla
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
                glColor3f(1.0, 1.0, 1.0)
            else:
                # sin textura: apagar texturas para que no se "pegue" la anterior
                glDisable(GL_TEXTURE_2D)
                glColor3f(*mtl['Kd'][:3])

            glBegin(GL_TRIANGLES)
            for vertices, normals, texture_coords in caras:
                # abanico: el polígono (0,1,2,3,...) se parte en (0,1,2), (0,2,3), ...
                for i in range(1, len(vertices) - 1):
                    for k in (0, i, i + 1):
                        if normals[k] > 0:
                            glNormal3fv(self.normals[normals[k] - 1])
                        if texture_coords[k] > 0:
                            glTexCoord2fv(self.texcoords[texture_coords[k] - 1])
                        glVertex3fv(self.vertices[vertices[k] - 1])
            glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        glCallList(self.gl_list)

    def free(self):
        glDeleteLists([self.gl_list])