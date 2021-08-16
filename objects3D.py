import OpenGL
import OpenGL_accelerate
import pywavefront  
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


class __Object:

    def __init__(self, position) -> None:
        self.position = position
        #eventually add rotation
        pass


    def draw(self) -> None:
        glBegin(self._RENDER_MODE)

        for i_face,face in enumerate(self.faces):
            glNormal3fv(self.normals[i_face]) # set the normal vector the vertices of the surface
            for vertex in face:
                glVertex3fv([
                    self.vertices[vertex][0] + self.position[0],
                    self.vertices[vertex][1] + self.position[1],
                    self.vertices[vertex][2] + self.position[2]])
        
        glEnd()
        glFlush()


    def _calculate_normals(self) -> list:
        """
        Newell's Normal calculation method
        """
        normals = []
        for face in self.faces:
            new_normal = [0,0,0]
            for x in range(len(face)):
                current = self.vertices[x]
                next = self.vertices[(x+1) % len(face)] #the modulo stuff is to make the last object do stuff with the first 10230 -> 0
                new_normal[0] += (current[1] - next[1]) * (current[2] - next[2]) 
                new_normal[1] += (current[2] - next[2]) * (current[0] - next[0]) 
                new_normal[2] += (current[0] - next[0]) * (current[1] - next[1]) 
            normals.append(new_normal)
        return normals
    

    def rotate(self, angle, x, y, z) -> None:
        
        pass


    def translate(self, x, y, z) -> None:
        self.position = (
            self.position[0] + x, 
            self.position[1] + y, 
            self.position[2] + z
            )
        pass


class Open(__Object):

    def __init__(self, model, position = (0,0,0)) -> None:
        if model != None:
            self.vertices = model.vertices
            # self.edges = model.edges
            self.faces = model.mesh_list[0].faces
        else:
            error('Missing Model')
        self.normals = super()._calculate_normals()
        self._RENDER_MODE = GL_TRIANGLES
        super().__init__(position)

    