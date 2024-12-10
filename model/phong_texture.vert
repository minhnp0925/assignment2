#version 330 core

// input attribute variable, given per vertex
layout(location = 0) in vec3 position; //vx vy vz
layout(location = 1) in vec2 texcoord; //tx ty
layout(location = 2) in vec3 normal; //nx ny nz

uniform mat4 projection, modelview;
out vec3 normal_interp;
out vec3 vert_pos;
out vec2 texcoord_interp;

void main(){
  vec4 vert_pos4 = modelview * vec4(position, 1.0);
  vert_pos = vec3(vert_pos4) / vert_pos4.w;

  mat4 normal_matrix = transpose(inverse(modelview));
  normal_interp = vec3(normal_matrix * vec4(normal, 0.0));

  texcoord_interp = texcoord;
  gl_Position = projection * vert_pos4;
}
