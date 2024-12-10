#version 330 core

precision mediump float;
in vec3 normal_interp;  // Surface normal
in vec3 vert_pos;       // Vertex position
in vec2 texcoord_interp;

uniform mat3 K_materials;
uniform mat3 I_light;

uniform float phong_factor; //Phong factor
uniform float shininess; // Shininess
uniform vec3 light_pos; // Light position
out vec4 fragColor;

uniform sampler2D car_texture;

void main() {
  vec3 N = normalize(normal_interp);
  vec3 L = normalize(light_pos - vert_pos);
  vec3 R = reflect(-L, N);      // Reflected light vector
  vec3 V = normalize(-vert_pos); // Vector to viewer

  vec3 lv = light_pos - vert_pos;
  float lvd = 1.0/(dot(lv, lv));
  float specAngle = max(dot(R, V), 0.0);
  float specular = pow(specAngle, shininess);
  vec3 g = vec3(lvd*max(dot(L, N), 0.0), specular, 1.0);
  vec3 rgb = matrixCompMult(K_materials, I_light) * g; // +  colorInterp;

  fragColor = vec4(rgb, 1.0);
  float texture_factor = 1.0 - phong_factor;

  vec4 texture_color;
  texture_color = texture(car_texture, texcoord_interp);

  fragColor = phong_factor*fragColor + texture_factor*texture_color;
}
