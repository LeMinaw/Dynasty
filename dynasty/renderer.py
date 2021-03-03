import numpy as np
from itertools import islice, chain
from moderngl import LINES_ADJACENCY, BLEND

from dynasty import APP_DIR
from dynasty.geometry import translation, persp_projection
from dynasty.colors import BLACK_TO_RED
from dynasty.walkers import WalkerSystem


def adjacent_lines_indexes(indexes):
    """Given a sequence of vertices indexes, return the indexes to be used with
    GL_LINES_ADJACENCY in order to draw lines between them in a strip.\n
    Example:
    (0, 1, 2, 3) ->
    (
        0, 0, 1, 2,
        0, 1, 2, 3,
        1, 2, 3, 3
    )
    """
    assert len(indexes) >= 2

    indexes = (indexes[0], *indexes, indexes[-1])
    lines_idx = []
    for line_idx in zip(*(indexes[i:] for i in range(4))):
        lines_idx += line_idx

    return lines_idx


def chunks(iterable, n):
    """Split an `iterable` into sucessive iterators of lenght `n`."""
    iterable = iter(iterable)
    while True:
        chunk = islice(iterable, n)
        try:
            first = next(chunk)
        except StopIteration:
            return
        yield chain((first,), chunk)


class Renderer:
    """This class implements a context-agnostic ModernGL renderer for
    `WalkerSystem` instances.\n
    Its `ctx` and `screen` attributes must be setup externally to a ModernGL
    context and framebuffer respectively.
    """
    def __init__(self, system: WalkerSystem):
        self.system = system
        self.model = np.eye(4, dtype='f4')
        self.view = translation(0, 0, -100)
        self.background_color = (1, 1, 1) # White
        self.close_rings = True
        self.rings_gradient = BLACK_TO_RED

        self.ctx, self.screen = None, None

        self.needs_vbo_update = True

    def initialize_program(self):
        with (APP_DIR / 'lines.vs.glsl').open() as prog_file:
            vs_prog = prog_file.read()

        with (APP_DIR / 'lines.gs.glsl').open() as prog_file:
            gs_prog = prog_file.read()

        with (APP_DIR / 'lines.fs.glsl').open() as prog_file:
            fs_prog = prog_file.read()

        self.prog = self.ctx.program(
            vertex_shader = vs_prog,
            geometry_shader = gs_prog,
            fragment_shader = fs_prog
        )

    def initialize_vertex_buffers(self):
        # 4 bytes, 3 coordinates, 40 walkers, 1000 iterations
        self.pos_vbo = self.ctx.buffer(reserve=4 * 3 * 40 * 1000)
        # 1 byte, 4 channels, 40 walkers, 1000 iterations
        self.rings_colors_vbo = self.ctx.buffer(reserve=4 * 40 * 1000)
        # 4 bytes, 4 verts per line, 40 walkers, 1000 iterations
        self.rings_ibo = self.ctx.buffer(reserve=4 * 4 * 40 * 1000)

        #                  VAOs structure
        # +-----------------------------------+-----------+
        # |                pos                |   color   |
        # +-----------+-----------+-----------+--+--+--+--+
        # |     x     |     y     |     z     |r |g |b |a |
        # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        # |00|01|02|03|04|05|06|07|08|09|0A|0B|0C|0D|0E|0F|
        # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        rings_content = (
            (self.pos_vbo,          '3f4', 'pos'),
            (self.rings_colors_vbo, '4f1', 'color'),
        )
        self.rings_vao = self.ctx.vertex_array(
            self.prog, rings_content, self.rings_ibo
        )

    def compute_vertex_buffers(self):
        # Retrieve walkers system computed positions, in shape (iterations,
        # walkers count, 3)
        pos = self.system.positions
        iterations, walkers_count, _ = pos.shape
        vertex_count = iterations * walkers_count
        pos = pos.reshape(vertex_count, 3).astype('f4')

        # Compute vertex colors
        rings_colors = self.rings_gradient.generate(vertex_count).astype('u1')

        # Compute vertex indexes
        rings_idx = []
        for chunk in chunks(range(vertex_count), walkers_count):
            verts_idx = list(chunk)
            # If the ring needs to be closed, a line must be drawn between its
            # first and last vertices
            if self.close_rings:
                verts_idx.append(verts_idx[0])
            # Convert the list of current ring's vertices to a list with
            # adjacent segments to be used by GL_LINES_ADJACENCY
            rings_idx += adjacent_lines_indexes(verts_idx)

        self.rings_idx = np.array(rings_idx, dtype='u4') # 0-65653

        # Write data to VBOs and IBOs
        self.pos_vbo.clear()
        self.pos_vbo.write(pos)

        self.rings_colors_vbo.clear()
        self.rings_colors_vbo.write(rings_colors)

        self.rings_ibo.clear()
        self.rings_ibo.write(self.rings_idx)

        # Mark VBOs as updated
        self.needs_vbo_update = False

    def render_frame(self):
        self.ctx.clear(*self.background_color, 0)
        self.ctx.enable(BLEND)

        width, height = self.screen.width, self.screen.height

        self.projection = persp_projection(fov=40, aspect=width/height)

        self.prog['model'].write(self.model)
        self.prog['view'].write(self.view)
        self.prog['projection'].write(self.projection)
        self.prog['viewport'] = width, height
        self.prog['width'] = 3.0

        if self.needs_vbo_update:
            self.compute_vertex_buffers()

        self.rings_vao.render(LINES_ADJACENCY)
