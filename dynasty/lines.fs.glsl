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
    /* Convert a given position from OpenGL NDCs to OpenGL sceen space
     * (fragment) coordinates. */
    return (pos + vec2(1, 1)) * viewport/2;
}


void main(void) {
    /* This fragment shader provides distance-based antialiasing by dimming
     * alpha values at the edge of the segment.
     * 
     * ----+------+------- <-- End of alpha gradient (a = 0)
     *   . |.  .  |  .  .
     * .  .| .  falloff  .
     *  .  |  .  .| .  .
     * ----|------+------- <-- Start of alpha gradient (a = 1)
     * .  .| .  .  .  .  .
     *  .  |  .  .  .X .   <-- Arbitrary fragment position
     *  width/2.  .  |  .
     * .  .| .  .  . d.  .
     *  .  |  .  .  .| .
     * ====+=========+==== <-- Segment center axis
     * .  .  .  .  .  .  .
     *  SAME ON THIS SIDE
     *   .  .  .  .  .  .
    */
    color = vertex_in.color;

    // Distance between current fragment and interpolated line center
    float d = distance(ndc_to_screen(vertex_in.center), gl_FragCoord.xy); 
    float w = width / 2;

    // Dim the alpha value of the fragment if it is in the "falloff zone"
    if (d > w-falloff) {
        // Linear falloff between w-falloff and w
        color.a *= (d - w) / -falloff;
    }
}
