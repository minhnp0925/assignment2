
import glfw
import numpy as np
from OpenGL.GL import *
import pyrr
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GLUT import *
from OpenGL.GLU import *
from math import sin, cos, radians
from PIL import Image
import sys

jump = -1

x=38
y=60

car_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([-4, 0, -5]))
floor_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
floor_pos2 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
floor_pos3 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
sky_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
#obstacle_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([-10, 2.5, 30]))
#engrenagem_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([-15, 0, 30]))
predio_pos = []
wall_pos = []
car1_pos = []
car2_pos = []
obstacle_pos = []

for j in range(12):
    for i in range(8):
        car1_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([0+(i*70), 0, -220+(j*y)])))
        car2_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([-36+(i*70), 0, -220+(j*y)])))
        wall_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([5+(i*45), 0, -200+(j*y)])))
        obstacle_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([(i*45), 2.5, -200+(j*y)])))
        predio_pos.append(pyrr.matrix44.create_from_translation(pyrr.Vector3([-86+(i*x), 0, -250+(j*y)])))

print(car1_pos)