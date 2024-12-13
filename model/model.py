import pyrr
from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.objLoader import ObjLoader

import ctypes
import cv2
import glfw

model_shader = None
model_uma = None

def initialize_model_shader():  
    global model_shader, model_uma
      
    vert_shader = "./model/phong_texture.vert"
    frag_shader = "./model/phong_texture.frag"

    model_shader = Shader(vert_shader, frag_shader)
    model_uma = UManager(model_shader)

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

    model_uma.upload_uniform_matrix3fv(I_light, 'I_light', False)
    model_uma.upload_uniform_vector3fv(light_pos, 'light_pos')

    model_uma.upload_uniform_matrix3fv(K_materials, 'K_materials', False)
    model_uma.upload_uniform_scalar1f(shininess, 'shininess')
    model_uma.upload_uniform_scalar1f(phong_factor, 'phong_factor')


class Model(object):
    def __init__(self, obj_path, texture_path, model_name, translation = [0,0,0], tranformatrix = None):
        """
        self.vertex_attrib:
        each row: v.x, v.y, v.z, t.x, t.y, n.x, n.y, n.z
        =>  (a) stride = nbytes(v0.x -> v1.x) = 9*4 = 36
            (b) offset(vertex) = ctypes.c_void_p(0); can use "None"
                offset(texture) = ctypes.c_void_p(3*4)
                offset(normal) = ctypes.c_void_p(5*4)
        """
        
        self.obj_path = obj_path
        self.texture_path = texture_path
        self.model_name = model_name
        self.translation = translation
        self.is_translate = False
        self.tranformatrix = tranformatrix
        self.indices, self.vertex_attrib = ObjLoader.load_model(self.obj_path, sorted=True)

        self.vao = VAO()
        self.shader = model_shader
        self.uma = model_uma

    def setup(self):
        stride = 8*4
        offset_v = ctypes.c_void_p(0) 
        offset_t = ctypes.c_void_p(3*4)
        offset_n = ctypes.c_void_p(5*4)
        self.vao.add_vbo(0, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_v)
        self.vao.add_vbo(1, self.vertex_attrib, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_t)
        self.vao.add_vbo(2, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_n)

        self.uma.setup_texture(self.model_name, self.texture_path)
        return self

    def draw(self, 
             projection = T.ortho(-10, 10, -10, 10, -10, 10), 
             view = np.identity(4, 'f'), 
             model = np.identity(4, 'f')
            ):
        
        self.vao.activate()
        GL.glUseProgram(self.shader.render_idx)

        # Rotate the model over time
        time = glfw.get_time()
        rotation = pyrr.Matrix44.from_y_rotation(time*0)
        model = pyrr.matrix44.multiply(model, rotation)
        if self.tranformatrix is not None:
            model = self.tranformatrix.T
            if self.is_translate == False:
                model[0,3] += self.translation[0]
                model[1,3] += self.translation[1]
                model[2,3] += self.translation[2]
                self.is_translate = True
        else:
            model[0,3] = self.translation[0]
            model[1,3] = self.translation[1]
            model[2,3] = self.translation[2]
        # Upload the rotation matrix to the shader
        modelview = pyrr.matrix44.multiply(view, model)
        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)
        
        self.uma.bind_texture(self.model_name)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.indices))

        # Deactivate VAO
        self.vao.deactivate()