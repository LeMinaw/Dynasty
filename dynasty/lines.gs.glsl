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
    vec2 center;
} vertex_out;


vec2 to_screen_space(vec4 pos) {
    /* Convert a 3D position to its (x, y) positions in a "simili-screen"
     * space.
     * This is not exactly OpenGL screen coordinates, but is it enough to
     * compute screen-dependant operations before converting back to OpenGL
     * NDCs (by divinding the resulting position by `viewport`). */
    return vec2(pos.xy / pos.w) * viewport;
}

float to_z_depth(vec4 pos) {
    /* Extract the z-depth value of a 3D position. */
    return pos.z / pos.w;
}

vec2 normal(vec2 v) {
    /* Return the "left hand" orthogonal vector of the input.
     * Output vector has the same norm as the inpout. */
    return vec2(-v.y, v.x);
}

vec2 unit_proj(vec2 v1, vec2 v2) {
    /* Return the orthogonal projection of the `v1` vector on `v2`.
     * This assumes `v2` is a unit vector (its norm equals one). */
    return v2 * dot(v2, v1);
}

void emit_vertex(vec2 pos, vec2 center, float z_depht, vec4 color) {
    /* Utility function to emit a vertex according to its given properties.
     * `pos` is the vertex position in "simili-screen" space, `center` is the
     * position of the projection of the vertex on the current line segment. */
    vertex_out.color = color;
    // Convert positions back to NDC coords
    vertex_out.center = center / viewport;
    gl_Position = vec4(pos / viewport, z_depht, 1.0);
    EmitVertex();
}

void draw_segment(vec2 positions[4], float z_dephts[4], vec4 colors[4]) {
    // Vertex positions
    vec2 p0 = positions[0];
    vec2 p1 = positions[1];
    vec2 p2 = positions[2];
    vec2 p3 = positions[3];

    // Culling
    vec2 area = viewport * 4;
    if (p1.x < -area.x || p1.x > area.x) return;
    if (p1.y < -area.y || p1.y > area.y) return;
    if (p2.x < -area.x || p2.x > area.x) return;
    if (p2.y < -area.y || p2.y > area.y) return;

    // Unit vectors along the 3 segments (previous, current, next one)
    vec2 v0 = normalize(p1 - p0);
    vec2 v1 = normalize(p2 - p1);
    vec2 v2 = normalize(p3 - p2);

    // Unit vectors normals to each segment
    vec2 n0 = normal(v0);
    vec2 n1 = normal(v1);
    vec2 n2 = normal(v2);

    // Average the two adjacent normals to get miter direction
    vec2 miter_a = normalize(n0 + n1);
    vec2 miter_b = normalize(n1 + n2);

    // Miters lenghts are obtained by projecting miters directions onto
    // next segment normals, inverting them and multiplying by target width
    float an1 = dot(miter_a, n1);
    float bn1 = dot(miter_b, n2);
    float length_a = width / an1;
    float length_b = width / bn1;

    // Offset between input and output vertices positions
    vec2 offset;
    // Offset between projection of output vertex onto current segment and
    // input vertex positions
    vec2 offset_proj;

    // Prevent excessively long miters at sharp corners (inner angle < 90°)
    if (dot(v0, v1) < 0) {
        miter_a = n1;
        length_a = width;

        // Close the gap between line segments
        if (dot(v0, n1) > 0) {
            offset = width * n0;
            offset_proj = unit_proj(offset, v1);
            emit_vertex(p1+offset, p1+offset_proj, z_dephts[1], colors[1]);
            
            offset = width * n1;
            offset_proj = unit_proj(offset, v1);
            emit_vertex(p1+offset, p1+offset_proj, z_dephts[1], colors[1]);
        }
        else {
            offset = -width * n1;
            offset_proj = unit_proj(offset, v1);
            emit_vertex(p1+offset, p1+offset_proj, z_dephts[1], colors[1]);

            offset = -width * n0;
            offset_proj = unit_proj(offset, v1);
            emit_vertex(p1+offset, p1+offset_proj, z_dephts[1], colors[1]);
        }

        emit_vertex(p1, p1, z_dephts[1], colors[1]);
    }

    // Prevent excessively long miters at sharp corners (inner angle < 90°)
    if (dot(v1, v2) < 0) {
        miter_b = n1;
        length_b = width;
    }

    // Line triangles strip
    offset = length_a * miter_a;
    offset_proj = unit_proj(offset, v1);
    emit_vertex(p1+offset, p1+offset_proj, z_dephts[1], colors[1]);

    offset = -length_a * miter_a;
    offset_proj = unit_proj(offset, v1);
    emit_vertex(p1+offset, p1+offset_proj, z_dephts[1], colors[1]);

    offset = length_b * miter_b;
    offset_proj = unit_proj(offset, v1);
    emit_vertex(p2+offset, p2+offset_proj, z_dephts[2], colors[2]);

    offset = -length_b * miter_b;
    offset_proj = unit_proj(offset, v1);
    emit_vertex(p2+offset, p2+offset_proj, z_dephts[2], colors[2]);

    EndPrimitive();
}


void main(void) {
    // Receive 4 vertices as input layout is GL_LINES_ADJACENCY
    vec2 screen_pos[4];
    float z_dephts[4];
    vec4 colors[4];
    
    for (int i = 0; i < 4; i++) {
        vec4 pos = gl_in[i].gl_Position;

        screen_pos[i] = to_screen_space(pos);
        z_dephts[i] = to_z_depth(pos);
        colors[i] = vertex_in[i].color;
    }

    draw_segment(screen_pos, z_dephts, colors);
}
