#version 330

uniform float opacity;

in VertexData {
    vec4 color;
} vertex_in;

layout(location=0) out vec4 color;


void main(void) {
    color = vertex_in.color;

}
