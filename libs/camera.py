from libs.transform import *
from typing import List
from math import radians, sin, cos
from libs.buffer import VAO, Shader, UManager
import OpenGL.GL as GL
import libs.transform as T
from pyrr import Matrix44, matrix44, Vector3, vector3, vector
import glfw



class Camera(Trackball):
    def __init__(self, yaw=0., roll=0., pitch=0., distance=3., radians=None):
        super(Camera, self).__init__(yaw=yaw, roll=roll, pitch=pitch, distance=distance, radians=radians)

    @staticmethod
    def place(eye, at, up):
        direction = eye - at
        distance = np.linalg.norm(direction)
        direction = direction / distance
        x, y, z = direction[0], direction[1], direction[2]
        pitch = math.asin(y) * (180. / math.pi)
        yaw = math.atan2(x, z) * (180. / math.pi)
        yaw = yaw - 90.0

        u = np.cross(up, direction)
        u = u / np.linalg.norm(u)
        v = np.cross(direction, u)
        v = v / np.linalg.norm(v)
        roll = math.acos(v[1]) * (180. / math.pi)
        roll = roll - 90.0
        return Camera(yaw=yaw, roll=roll, pitch=pitch, distance=distance)


class StaticCamera:
    def __init__(self, xpos, ypos, zpos):
        self.camera_eye = Vector3([xpos, ypos, zpos])
        self.camera_at = Vector3([0.0, 1.0, 0.0])
        self.camera_up = Vector3([0.0, 1.0, 0.0])

    def get_view_matrix(self):
        return np.transpose(matrix44.create_look_at(self.camera_eye, self.camera_at, self.camera_up))
    
    def get_projection_matrix(self, winsize = (640,640)):
        distance = vector.length(self.camera_eye)
        return perspective(45, winsize[0]/winsize[1], distance*0.01, distance*100)
    
    def get_drawable(self, is_active):
        drawable = Marker(self.camera_eye[0], self.camera_eye[1], self.camera_eye[2], is_active=is_active).setup()
        # print("marker pos:", self.camera_eye)
        return drawable

class CameraArray:
    def __init__(self, radius=45, num_latitude=5, num_longitude=5):
        self.cameras = []
        self.active_index = 0

        self.radius = radius
        self.num_latitude = num_latitude
        self.num_longitude = num_longitude
        self.m = False
        self.time = 0
        # Generate camera positions
        self.generate_camera_positions()

    def generate_camera_positions(self):
        """Generate cameras in a north hemisphere pattern."""
        for i in range(1, self.num_latitude+1):
            # Latitude range limited to 0 (equator) to π/2 (north pole)
            theta = (i / (self.num_latitude+1) ) * (np.pi / 2)
            for j in range(0, self.num_longitude):
                # Full longitude range: 0 to 2π
                phi = (j / self.num_longitude) * (2 * np.pi)

                # Calculate camera positions based on spherical coordinates
                x = self.radius * np.sin(theta) * np.cos(phi)
                y = self.radius * np.cos(theta)
                z = self.radius * np.sin(theta) * np.sin(phi)

                # Add the camera at the calculated position
                self.add_camera(x, y, z)


    def add_camera(self, xpos, ypos, zpos):
        # print("Add cam: ", xpos, ypos, zpos)
        self.cameras += [StaticCamera(xpos=xpos, ypos=ypos, zpos=zpos)]
    
    def get_current_view(self):
        if (self.active_index == -1 or self.active_index >= len(self.cameras)):
            print("[ERROR] CameraArray get_current_view: Invalid index!")
            return np.identity(4,'f')
        
        return self.cameras[self.active_index].get_view_matrix()
    def get_current_pos(self):
        if (self.active_index == -1 or self.active_index >= len(self.cameras)):
            print("[ERROR] CameraArray get_current_view: Invalid index!")
            return np.identity(4,'f')
        
        return self.cameras[self.active_index].camera_eye
    
    def get_current_projection(self, winsize=(640, 640)):
        if (self.active_index == -1 or self.active_index >= len(self.cameras)):
            print("[ERROR] CameraArray get_current_projection: Invalid index!")
            return T.ortho(-15, 15, -15, 15, -15, 15)

        return self.cameras[self.active_index].get_projection_matrix(winsize)

    def set_active(self, idx):
        self.active_index = idx

    def process_keyboard(self, key):
        next_idx = (self.active_index + 1) % len(self.cameras)
        prev_idx = (self.active_index + len(self.cameras) - 1) % len(self.cameras)
        if key == glfw.KEY_RIGHT:
            self.set_active(next_idx)
        if key == glfw.KEY_LEFT:
            self.set_active(prev_idx)
        if key == glfw.KEY_M:
            self.m = not(self.m)
        
    def get_drawable(self):
        return self.cameras[self.active_index].get_drawable(True) if self.active_index > -1 else None
    
    def get_all_drawables(self):
        drawables = []
        self.time  += 1
        if (self.m == True and self.time %3 == 0): 
            self.active_index = (self.active_index + 1) % len(self.cameras)
        for i in range(0, len(self.cameras)):
            if i == self.active_index:
                drawables += [self.cameras[i].get_drawable(True)]
            else:
                drawables += [self.cameras[i].get_drawable(False)]

        return drawables
    

marker_shader = None
marker_uma = None

def initialize_marker_shader():
    global marker_shader, marker_uma
    vert_shader = "./gouraud.vert"
    frag_shader = "./gouraud.frag"

    marker_shader = Shader(vert_shader, frag_shader)
    marker_uma = UManager(marker_shader)

class Marker:
    def __init__(self, xpos, ypos, zpos, scale=0.05, is_active=False):
        self.position = np.array([xpos, ypos, zpos], dtype=np.float32)
        pyramid_height = scale * np.linalg.norm(self.position)

        # Define the vertices of the pyramid (local coordinates)
        self.vertices = np.array([
            [0.0, 0.0, 0.0],  # Apex of the pyramid
            [pyramid_height / 2, -pyramid_height, pyramid_height / 2],
            [pyramid_height / 2, -pyramid_height, -pyramid_height / 2],
            [-pyramid_height / 2, -pyramid_height, -pyramid_height / 2],
            [-pyramid_height / 2, -pyramid_height, pyramid_height / 2],
        ], dtype=np.float32)
        if is_active:
            self.colors = np.array([
                [0.0, 1.0, 0.0],  # Red
                [0.5, 0.5, 0.5],  # Gray
                [0.4, 0.5, 0.6],  # Gray
                [0.6, 0.5, 0.4],  # Gray
                [0.4, 0.6, 0.5],  # Gray
            ], dtype=np.float32) 
        else: 
            self.colors = np.array([
                [1.0, 0.0, 0.0],  # Red
                [0.5, 0.5, 0.5],  # Gray
                [0.4, 0.5, 0.6],  # Gray
                [0.6, 0.5, 0.4],  # Gray
                [0.4, 0.6, 0.5],  # Gray
            ], dtype=np.float32) 

        self.indices = np.array([
            0, 1, 2,
            0, 2, 3,
            0, 3, 4,
            0, 4, 1,
            1, 2, 4,
            4, 2, 3
        ], dtype=np.uint32)

        # Create the transformation matrix
        self.rotation_matrix = self.calculate_orientation_matrix()
        self.model_matrix = self.rotation_matrix @ matrix44.create_from_translation(Vector3(self.position))
        self.model_matrix = np.transpose(self.model_matrix)

        # Setup VAO, shader, and uniform manager
        self.vao = VAO()
        self.shader = marker_shader
        self.uma = marker_uma

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_ebo(self.indices)
        return self

    def calculate_orientation_matrix(self):
        # Target direction from apex to origin (negative position vector)
        target_direction = -self.position / np.linalg.norm(self.position)

        # Default "up" vector in local coordinates
        up_vector = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        # Check if target direction is already aligned
        if np.allclose(target_direction, up_vector):
            rotation_matrix = np.eye(4, dtype=np.float32)
        else:
            # Calculate rotation axis using cross product
            rotation_axis = np.cross(up_vector, target_direction)
            rotation_axis /= np.linalg.norm(rotation_axis)

            # Calculate rotation angle using dot product and arccos
            cos_angle = np.dot(up_vector, target_direction)
            angle = math.acos(cos_angle)

            # Create rotation matrix using axis-angle method
            rotation_matrix = matrix44.create_from_axis_rotation(rotation_axis, angle)
        
        # Additional 180-degree rotation around local x-axis to flip the pyramid
        flip_matrix = matrix44.create_from_x_rotation(np.radians(180))

        # Combine the orientation and flip
        return flip_matrix @ rotation_matrix

    def draw(self, 
             projection = T.ortho(-1, 1, -1, 1, -1, 1), 
             view = np.identity(4, 'f'), 
             model = np.identity(4, 'f')
            ):
        
        self.vao.activate()
        GL.glUseProgram(self.shader.render_idx)

        # Combine rotation matrices
        modelview = matrix44.multiply(view, self.model_matrix)

        # Upload the rotation matrix to the shader
        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)

        # Draw the tetrahedron
        GL.glDrawElements(GL.GL_TRIANGLES, 18, GL.GL_UNSIGNED_INT, None)

        # Deactivate VAO
        self.vao.deactivate()


class PovCamera:
    def __init__(self):
        self.camera_pos = Vector3([0.0, 0.0, 50.0])
        self.camera_front = Vector3([0.0, 0.0, -1.0])
        self.camera_up = Vector3([0.0, 1.0, 0.0])
        self.camera_right = Vector3([1.0, 0.0, 0.0])

        self.mouse_sensitivity = 0.1
        self.yaw = 90
        self.pitch = 0
        self.roll = 0

    def get_view_matrix(self):
        return np.transpose(matrix44.create_look_at(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up))
    
    def get_projection_matrix(self, winsize = (640,640)):
        distance = vector.length(self.camera_pos)
        return perspective(45, winsize[0]/winsize[1], distance*0.01, distance*100)

    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch=True):
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.yaw += xoffset
        self.pitch += yoffset

        if constrain_pitch:
            if self.pitch > 60:
                self.pitch = 60
            if self.pitch < -60:
                self.pitch = -60

        self.update_camera_vectors()

    def tilt(self, speed):
        self.roll += speed
        self.update_camera_vectors()

    def update_camera_vectors(self):
        # Calculate the new front vector based on yaw and pitch
        front = Vector3([0.0, 0.0, 0.0])
        front.x = cos(radians(self.yaw)) * cos(radians(self.pitch))
        front.y = sin(radians(self.pitch))
        front.z = sin(radians(self.yaw)) * cos(radians(self.pitch))
        
        self.camera_front = vector.normalise(front)
        world_up = Vector3([0.0, 1.0, 0.0])
        self.camera_right = vector.normalise(vector3.cross(self.camera_front, world_up))
        self.camera_up = vector.normalise(vector3.cross(self.camera_right, self.camera_front))

        # print("Front:", self.camera_front)
        # print("Right:", self.camera_right)
        # print("Up:", self.camera_up)

    # Camera method for the WASD movement
    def process_keyboard(self, key, velocity=0.5):
        front = Vector3([self.camera_front[0], 0, self.camera_front[2]])
        right = Vector3([self.camera_right[0], 0, self.camera_right[2]])

        if key == glfw.KEY_SPACE:
            #fly up
            self.camera_pos += Vector3([0,1,0]) * velocity
        if key == glfw.KEY_LEFT_SHIFT:
            #fly down
            self.camera_pos -= Vector3([0,1,0]) * velocity
        if key == glfw.KEY_A:
            #left
            self.camera_pos -= right * velocity
        if key == glfw.KEY_D:
            #right
            self.camera_pos += right * velocity
        if key == glfw.KEY_W:
            #forward
            self.camera_pos += front * velocity
        if key == glfw.KEY_S:
            #backward
            self.camera_pos -= front * velocity

        print("Camera pos:", self.camera_pos)

    