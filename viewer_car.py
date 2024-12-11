import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean windows system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
from patch import *
from itertools import cycle   # cyclic iterator to easily toggle polygon rendering modes
from patch.textured.TexturedPatch import *
from model.model import CarModel
from libs.transform import Trackball
from libs.camera import *

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
            # display depth image
            projection_matrix = self.cameraArray.get_current_projection((480, 360))
            view_matrix = self.cameraArray.get_current_view()
            for drawable in self.drawables:
                drawable.uma.upload_uniform_scalar1i(0, "depth_shader")
                drawable.draw(projection=projection_matrix, view=view_matrix)

            GL.glViewport(480, 0, 480, 360)
            # display depth image
            projection_matrix = self.cameraArray.get_current_projection((480, 360))
            view_matrix = self.cameraArray.get_current_view()
            for drawable in self.drawables:
                drawable.uma.upload_uniform_scalar1i(1, "depth_shader")
                drawable.draw(projection=projection_matrix, view=view_matrix)
            
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

        self.povCamera.process_mouse_movement(xoffset, yoffset)


# -------------- main program and scene setup --------------------------------
def main():
    """ create windows, add shaders & scene objects, then run rendering loop """
    viewer = Viewer()

    #model = Patch("./gouraud.vert", "./gouraud.frag",
    #              "./phong.vert", "./phong.frag").setup()

    #model = PatchEx("./phongex.vert", "./phongex.frag").setup()

    # model = TexturedPatch("./textured/phong_texture.vert", "./textured/phong_texture.frag", vertices, indices).setup()
    model = CarModel().setup()
    viewer.add(model)

    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    glfw.init()                # initialize windows system glfw
    main()                     # main function keeps variables locally scoped
    glfw.terminate()           # destroy all glfw windows and GL contexts
