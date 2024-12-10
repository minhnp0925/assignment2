import pyrr
from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.objLoader import ObjLoader

import ctypes
import cv2
import glfw

obj_path = "./model/car1.obj"
texture_path = "./model/car1.png"

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
        
        self.indices, self.vertex_attrib = ObjLoader.load_model(obj_path, True)
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

        self.uma.setup_texture("car_texture", texture_path)

        projection = T.ortho(-0.5, 2.5, -0.5, 1.5, -1, 1)
        modelview = np.identity(4, 'f')

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
        phong_factor = 0.3

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

    # def key_handler(self, key):
    #     if key == glfw.KEY_1:
    #         self.selected_texture = 1
    #     if key == glfw.KEY_2:
    #         self.selected_texture = 2

