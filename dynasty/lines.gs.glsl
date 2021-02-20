#version 330

/* \brief This shader program is adapted from `shader-3dcurve` by Victoria
 * Rudakova (https://github.com/vicrucann/shader-3dcurve)
 *
 * \author Victoria Rudakova
 * \date January 2017
 * \copyright MIT license
*/

uniform vec2 viewport;
uniform float width;

layout(lines_adjacency) in;
layout(triangle_strip, max_vertices=7) out;

in VertexData {
    vec4 color;
} vertex_in[4];

out VertexData {
    vec4 color;
} vertex_out;


vec2 to_screen_space(vec4 pos) {
    return vec2(pos.xy / pos.w) * viewport;
}

float to_z_depth(vec4 pos) {
    return pos.z / pos.w;
}

void draw_segment(vec2 positions[4], vec4 colors[4], float z_dephts[4]) {
    vec2 p0 = positions[0];
    vec2 p1 = positions[1];
    vec2 p2 = positions[2];
    vec2 p3 = positions[3];

    /* perform naive culling */
    vec2 area = viewport * 4;
    if (p1.x < -area.x || p1.x > area.x) return;
    if (p1.y < -area.y || p1.y > area.y) return;
    if (p2.x < -area.x || p2.x > area.x) return;
    if (p2.y < -area.y || p2.y > area.y) return;

    /* determine the direction of each of the 3 segments (previous, current, next) */
    vec2 v0 = normalize(p1 - p0);
    vec2 v1 = normalize(p2 - p1);
    vec2 v2 = normalize(p3 - p2);

    /* determine the normal of each of the 3 segments (previous, current, next) */
    vec2 n0 = vec2(-v0.y, v0.x);
    vec2 n1 = vec2(-v1.y, v1.x);
    vec2 n2 = vec2(-v2.y, v2.x);

    /* determine miter lines by averaging the normals of the 2 segments */
    vec2 miter_a = normalize(n0 + n1);	// miter at start of current segment
    vec2 miter_b = normalize(n1 + n2); // miter at end of current segment

    /* determine the length of the miter by projecting it onto normal and then inverse it */
    float an1 = dot(miter_a, n1);
    float bn1 = dot(miter_b, n2);
    if (an1 == 0) an1 = 1;
    if (bn1 == 0) bn1 = 1;
    float length_a = width / an1;
    float length_b = width / bn1;

    /* prevent excessively long miters at sharp corners */
    if (dot(v0, v1) < 0) {
        miter_a = n1;
        length_a = width;

        /* close the gap */
        if (dot(v0, n1) > 0) {
            vertex_out.color = colors[1];
            gl_Position = vec4((p1 + width*n0) / viewport, z_dephts[1], 1.0);
            EmitVertex();

            vertex_out.color = colors[1];
            gl_Position = vec4((p1 + width*n1) / viewport, z_dephts[1], 1.0);
            EmitVertex();
        }
        else {
            vertex_out.color = colors[1];
            gl_Position = vec4((p1 - width*n1) / viewport, z_dephts[1], 1.0);
            EmitVertex();

            vertex_out.color = colors[1];
            gl_Position = vec4((p1 - width*n0) / viewport, z_dephts[1], 1.0);
            EmitVertex();
        }

        vertex_out.color = colors[1];
        gl_Position = vec4(p1 / viewport, z_dephts[1], 1.0);
        EmitVertex();

        EndPrimitive();
    }

    if (dot(v1, v2) < 0) {
        miter_b = n1;
        length_b = width;
    }
    // generate the triangle strip
    vertex_out.color = colors[1];
    gl_Position = vec4((p1 + length_a*miter_a) / viewport, z_dephts[1], 1.0);
    EmitVertex();

    vertex_out.color = colors[1];
    gl_Position = vec4((p1 - length_a*miter_a) / viewport, z_dephts[1], 1.0);
    EmitVertex();

    vertex_out.color = colors[2];
    gl_Position = vec4((p2 + length_b*miter_b) / viewport, z_dephts[2], 1.0);
    EmitVertex();

    vertex_out.color = colors[2];
    gl_Position = vec4((p2 - length_b*miter_b) / viewport, z_dephts[2], 1.0);
    EmitVertex();

    EndPrimitive();
}


void main(void) {
    // receive 4 verticies as input layout is GL_LINES_ADJACENCY
    vec2 screen_pos[4];
    float z_depths[4];
    vec4 colors[4];
    
    for (int i = 0; i < 4; i++) {
        vec4 pos = gl_in[i].gl_Position;

        screen_pos[i] = to_screen_space(pos);
        z_depths[i] = to_z_depth(pos);
        colors[i] = vertex_in[i].color;
    }

    draw_segment(screen_pos, colors, z_depths);
}
