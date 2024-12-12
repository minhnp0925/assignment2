import pyrr
from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.objLoader import ObjLoader

import ctypes
import cv2
import glfw


class CarModel(object):
    def __init__(self, vert_shader = "./model/phong_texture.vert", frag_shader = "./model/phong_texture.frag"):
        """
        self.vertex_attrib:
        each row: v.x, v.y, v.z, t.x, t.y, n.x, n.y, n.z
        =>  (a) stride = nbytes(v0.x -> v1.x) = 9*4 = 36
            (b) offset(vertex) = ctypes.c_void_p(0); can use "None"
                offset(texture) = ctypes.c_void_p(3*4)
                offset(normal) = ctypes.c_void_p(5*4)
        """
        
        self.obj_path = "./model/car1.obj"
        self.texture_path = "./model/car1.png"
        
        self.indices, self.vertex_attrib = ObjLoader.load_model(self.obj_path, sorted=True)
        print("Debug: ") 
        ObjLoader.show_buffer_data(self.vertex_attrib)
        print(self.vertex_attrib)
        self.vao = VAO()

        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)


    def setup(self):
        stride = 8*4
        offset_v = ctypes.c_void_p(0) 
        offset_t = ctypes.c_void_p(3*4)
        offset_n = ctypes.c_void_p(5*4)
        self.vao.add_vbo(0, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_v)
        self.vao.add_vbo(1, self.vertex_attrib, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_t)
        self.vao.add_vbo(2, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_n)

        self.uma.setup_texture("car_texture", self.texture_path)

        # Light
        I_light = np.array([
            [0.9, 0.4, 0.6],  # diffuse
            [0.9, 0.4, 0.6],  # specular
            [0.9, 0.4, 0.6]  # ambient
        ], dtype=np.float32)
        light_pos = np.array([0, 0.5, 0.9], dtype=np.float32)

        # Materials
        K_materials = np.array([
            [0.5, 0.0, 0.7],  # diffuse
            [0.5, 0.0, 0.7],  # specular
            [0.5, 0.0, 0.7]  # ambient
        ], dtype=np.float32)

        shininess = 100.0
        phong_factor = 0.0

        self.uma.upload_uniform_matrix3fv(I_light, 'I_light', False)
        self.uma.upload_uniform_vector3fv(light_pos, 'light_pos')

        self.uma.upload_uniform_matrix3fv(K_materials, 'K_materials', False)
        self.uma.upload_uniform_scalar1f(shininess, 'shininess')
        self.uma.upload_uniform_scalar1f(phong_factor, 'phong_factor')

        return self

    def draw(self, 
             projection = T.ortho(-1, 1, -1, 1, -1, 1), 
             view = np.identity(4, 'f'), 
             model = np.identity(4, 'f')
            ):
        
        self.vao.activate()
        GL.glUseProgram(self.shader.render_idx)

        # Rotate the model over time
        time = glfw.get_time()
        rotation = pyrr.Matrix44.from_y_rotation(time * 0.5)
        model = pyrr.matrix44.multiply(model, rotation)

        # Upload the rotation matrix to the shader
        modelview = pyrr.matrix44.multiply(view, model)
        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)
        
        # Draw da cube
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.indices))

        # Deactivate VAO
        self.vao.deactivate()

class ChibiModel(object):
    def __init__(self, vert_shader = "./model/phong_texture.vert", frag_shader = "./model/phong_texture.frag"):
        """
        self.vertex_attrib:
        each row: v.x, v.y, v.z, t.x, t.y, n.x, n.y, n.z
        =>  (a) stride = nbytes(v0.x -> v1.x) = 9*4 = 36
            (b) offset(vertex) = ctypes.c_void_p(0); can use "None"
                offset(texture) = ctypes.c_void_p(3*4)
                offset(normal) = ctypes.c_void_p(5*4)
        """
        
        self.obj_path = "./model/car1.obj"
        self.texture_path = "./model/car1.png"
        
        self.chibi_indices, self.chibi_buffer = ObjLoader.load_model(self.obj_path, sorted=True)

        self.VAO = GL.glGenVertexArrays(1)
        self.VBO = GL.glGenBuffers(1)

        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)


    def setup(self):
        # Chibi VAO
        GL.glBindVertexArray(VAO[0])
        # Chibi Vertex Buffer Object
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBO[0])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.chibi_buffer.nbytes, self.chibi_buffer, GL.GL_STATIC_DRAW)

        # glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        # glBufferData(GL_ELEMENT_ARRAY_BUFFER, chibi_indices.nbytes, chibi_indices, GL_STATIC_DRAW)

        # chibi vertices
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, self.chibi_buffer.itemsize * 8, ctypes.c_void_p(0))
        # chibi textures
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, self.chibi_buffer.itemsize * 8, ctypes.c_void_p(12))
        # chibi normals
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, self.chibi_buffer.itemsize * 8, ctypes.c_void_p(20))
        GL.glEnableVertexAttribArray(2)

        self.uma.setup_texture("car_texture", self.texture_path)

        # Light
        I_light = np.array([
            [0.9, 0.4, 0.6],  # diffuse
            [0.9, 0.4, 0.6],  # specular
            [0.9, 0.4, 0.6]  # ambient
        ], dtype=np.float32)
        light_pos = np.array([0, 0.5, 0.9], dtype=np.float32)

        # Materials
        K_materials = np.array([
            [0.5, 0.0, 0.7],  # diffuse
            [0.5, 0.0, 0.7],  # specular
            [0.5, 0.0, 0.7]  # ambient
        ], dtype=np.float32)

        shininess = 100.0
        phong_factor = 0.0

        self.uma.upload_uniform_matrix3fv(I_light, 'I_light', False)
        self.uma.upload_uniform_vector3fv(light_pos, 'light_pos')

        self.uma.upload_uniform_matrix3fv(K_materials, 'K_materials', False)
        self.uma.upload_uniform_scalar1f(shininess, 'shininess')
        self.uma.upload_uniform_scalar1f(phong_factor, 'phong_factor')

        return self

    def draw(self, 
             projection = T.ortho(-1, 1, -1, 1, -1, 1), 
             view = np.identity(4, 'f'), 
             model = np.identity(4, 'f')
            ):
        
        self.vao.activate()
        GL.glUseProgram(self.shader.render_idx)

        # Rotate the model over time
        time = glfw.get_time()
        rotation = pyrr.Matrix44.from_y_rotation(time * 0.5)
        model = pyrr.matrix44.multiply(model, rotation)

        # Upload the rotation matrix to the shader
        modelview = pyrr.matrix44.multiply(view, model)
        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)
        
        # Draw da cube
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.indices))

        # Deactivate VAO
        self.vao.deactivate()

