#version 330

uniform mat4 projection, view, model;

layout(location=0) in vec3 pos;
layout(location=1) in vec4 color;

out VertexData {
    vec4 color;
} vertex_out;


void main(void) {
    vertex_out.color = color;
    gl_Position = projection * view * model * vec4(pos, 1.0);
}
