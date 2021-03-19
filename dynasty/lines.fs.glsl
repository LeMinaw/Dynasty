#version 330

const float falloff = 1.0;

uniform float width;
uniform vec2 viewport;

in VertexData {
    vec4 color;
    vec2 center;
} vertex_in;

layout(location=0) out vec4 color;


vec2 ndc_to_screen(vec2 pos) {
    return (pos + vec2(1, 1)) * viewport/2;
}


void main(void) {
    color = vertex_in.color;

    float d = distance(ndc_to_screen(vertex_in.center), gl_FragCoord.xy); 
    float w = width / 2;
    
    if (d > w) {
        discard;
    } else if (d > w-falloff) {
        color.a *= (d - w) / -falloff;
    }
}
