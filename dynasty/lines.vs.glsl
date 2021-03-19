#version 330

uniform mat4 projection, view, model;
uniform float opacity;

layout(location=0) in vec3 pos;
layout(location=1) in vec4 color;

out VertexData {
    vec4 color;
} vertex_out;


void main(void) {
    vertex_out.color = vec4(color.rgb, color.a * opacity);
    gl_Position = projection * view * model * vec4(pos, 1.0);
}
