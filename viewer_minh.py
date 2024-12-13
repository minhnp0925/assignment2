import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean windows system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
from patch import *
from itertools import cycle   # cyclic iterator to easily toggle polygon rendering modes
from patch.textured.TexturedPatch import *
from model.model import *
from libs.transform import Trackball
from libs.camera import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from PIL import Image
from PIL import ImageOps

def save_image(start_points = [0,0], width_heigth = [480, 360], save_name = 'rgb', path_folder = 'save_images'):
    data = glReadPixels(start_points[0], start_points[1], width_heigth[0], width_heigth[1], GL_RGBA, GL_UNSIGNED_BYTE)
    image = Image.frombytes("RGBA", (width_heigth[0], width_heigth[1]), data)
    image = ImageOps.flip(image) # in my case image is flipped top-bottom for some reason
    save_path = os.path.join(path_folder, f'{save_name}.png')
    image.save(save_path, 'PNG')

# ------------  Viewer class & windows management ------------------------------
class Viewer:
    """ GLFW viewer windows, with classic initialization & graphics loop """
    def __init__(self, width=960, height=1080):
        self.fill_modes = cycle([GL.GL_LINE, GL.GL_POINT, GL.GL_FILL])

        # version hints: create GL windows with >= OpenGL 3.3 and core profile
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)
        glfw.window_hint(glfw.DEPTH_BITS, 16)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        self.win = glfw.create_window(width, height, 'Viewer', None, None)

        # make win's OpenGL context current; no OpenGL calls can happen before
        glfw.make_context_current(self.win)

        # register event handlers
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse)
        # glfw.set_scroll_callback(self.win, self.on_scroll)

        # useful message to check OpenGL renderer characteristics
        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        # initialize GL by setting viewport and default render characteristics
        GL.glClearColor(240 / 255.0, 234 / 255.0, 218 / 255.0, 1.0)

        GL.glEnable(GL.GL_DEPTH_TEST)  # enable depth test (Exercise 1)
        GL.glDepthFunc(GL.GL_LESS)  # GL_LESS: default

        self.first_mouse = True
        self.lastX = width/2
        self.lastY = height/2

        # initially empty list of object to draw
        self.drawables = []

        # cameras
        self.povCamera = PovCamera()
        self.cameraArray = CameraArray()

        # shaders
        initialize_model_shader()
        initialize_marker_shader()

    def run(self):
        """ Main render loop for this OpenGL windows """
        while not glfw.window_should_close(self.win):
            # clear draw buffer
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            win_size = glfw.get_window_size(self.win)

            projection_matrix = self.povCamera.get_projection_matrix(winsize=win_size)
            view_matrix = self.povCamera.get_view_matrix()
            
            GL.glViewport(0, 360, 960, 720)
            # draw objects in master window

            for drawable in self.drawables:
                drawable.uma.upload_uniform_scalar1i(0, "depth_shader")
                drawable.draw(projection=projection_matrix, view=view_matrix)
            
            # draw camera markers
            markers = self.cameraArray.get_all_drawables()
            for marker in markers:
                marker.draw(projection=projection_matrix, view=view_matrix)

            GL.glViewport(0, 0, 480, 360)
            # display rgb image
            projection_matrix = self.cameraArray.get_current_projection((480, 360))
            view_matrix = self.cameraArray.get_current_view()
            for drawable in self.drawables:
                drawable.draw(projection=projection_matrix, view=view_matrix)
            x_cam,y_cam,z_cam = np.round(self.cameraArray.get_current_pos(),1)
            save_image(start_points=[0,0], width_heigth=[480,360], save_name=f'rgb_({x_cam},{y_cam},{z_cam})')
            GL.glViewport(480, 0, 480, 360)
            # display depth image
            projection_matrix = self.cameraArray.get_current_projection((480, 360))
            view_matrix = self.cameraArray.get_current_view()
            for drawable in self.drawables:
                drawable.uma.upload_uniform_scalar1i(1, "depth_shader")
                drawable.draw(projection=projection_matrix, view=view_matrix)
            
            save_image(start_points=[480,0], width_heigth=[480,360], save_name=f'depth_({x_cam},{y_cam},{z_cam})')
            # flush render commands, and swap draw buffers
            glfw.swap_buffers(self.win)

            # Poll for and process events
            glfw.poll_events()

    def add(self, *drawables):
        """ add objects to draw in this windows """
        self.drawables.extend(drawables)

    def on_key(self, _win, key, _scancode, action, _mods):
        if action == glfw.PRESS or action == glfw.REPEAT:
            """'Escape' quits"""
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(self.win, True)
            """'Q' changes mode"""
            if key == glfw.KEY_Q:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))

            if key in [glfw.KEY_W, glfw.KEY_A, glfw.KEY_S, glfw.KEY_D, glfw.KEY_LEFT_SHIFT, glfw.KEY_SPACE]:
                self.povCamera.process_keyboard(key)

            if key in [glfw.KEY_LEFT, glfw.KEY_RIGHT]:
                self.cameraArray.process_keyboard(key)    
            if key in [glfw.KEY_M]:
                self.cameraArray.process_keyboard(key)

            for drawable in self.drawables:
                if hasattr(drawable, 'key_handler'):
                    drawable.key_handler(key)
    
    def on_mouse(self, _win, xpos, ypos):
        if self.first_mouse:
            self.lastX = xpos
            self.lastY = ypos
            self.first_mouse = False

        xoffset = xpos - self.lastX
        yoffset = self.lastY - ypos

        self.lastX = xpos
        self.lastY = ypos

        # self.povCamera.process_mouse_movement(xoffset, yoffset)

def position_matrix():
    predio_pos = []

    car1_pos = []
    car2_pos = []

    x=38
    y=60
    for j in range(2):
        for i in range(2):
            car1_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([0+(i*70), 0, -220+(j*y)])))
            car2_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([-36+(i*70), 0, -220+(j*y)])))
            predio_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([-86+(i*x), 0, -250+(j*y)])))
    return car1_pos,car2_pos, predio_pos
# -------------- main program and scene setup --------------------------------
def main():
    """ create windows, add shaders & scene objects, then run rendering loop """
    viewer = Viewer()

    #model = Patch("./gouraud.vert", "./gouraud.frag",
    #              "./phong.vert", "./phong.frag").setup()

    #model = PatchEx("./phongex.vert", "./phongex.frag").setup()

    # model = TexturedPatch("./textured/phong_texture.vert", "./textured/phong_texture.frag", vertices, indices).setup()
    car1_pos,car2_pos, predio_pos = position_matrix()
    floor_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    floor_pos2 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    # floor_pos3 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    floor_model1 = Model(obj_path  = "./objects/grass.obj", texture_path = "./textures/grass.jpg", model_name="floor1",tranformatrix=floor_pos).setup()
    floor_model2 = Model(obj_path  = "./objects/asfalto.obj", texture_path = "./textures/asfalto.jpg", model_name="floor2",tranformatrix=floor_pos2).setup()
    # floor_model3 = Model(obj_path  = "./objects/amarelo.obj", texture_path = "./textures/amarelo.jpg", model_name="floor3",tranformatrix=floor_pos3).setup()
    viewer.add(floor_model1)
    viewer.add(floor_model2)
    # viewer.add(floor_model3)
    floor_model = Model(obj_path  = "./objects/skybox.obj", texture_path = "./textures/skybox_texture.jpg", model_name="skybox").setup()
    viewer.add(floor_model)

    for i in range(len(car1_pos)):
        car1 = Model(obj_path  = "./objects/car1.obj", texture_path = "./textures/car1.png", model_name="car1", tranformatrix=car1_pos[i], translation = [0,0, 180]).setup()
        viewer.add(car1)
        car2 = Model(obj_path  = "./objects/car2.obj", texture_path = "./textures/car2.png", model_name="car2", tranformatrix=car2_pos[i], translation = [0,0, 180]).setup()
        viewer.add(car2)
        predio = Model(obj_path  = "./objects/predio2.obj", texture_path = "./textures/predio.png", model_name="predio",  tranformatrix=predio_pos[i], translation = [30,0, 180]).setup()
        viewer.add(predio)
    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    glfw.init()                # initialize windows system glfw
    main()                     # main function keeps variables locally scoped
    glfw.terminate()           # destroy all glfw windows and GL contexts
