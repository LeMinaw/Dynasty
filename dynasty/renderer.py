from collections import namedtuple
from dataclasses import dataclass, field
import numpy as np
from moderngl import LINES_ADJACENCY, BLEND

from dynasty import APP_DIR
from dynasty.colors import RGBColor, RGBAColor, Gradient, BLACK_TO_RED
from dynasty.geometry import translation, persp_projection
from dynasty.utils import chunks
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


RendererVBOs = namedtuple('VBOs', ('pos', 'rings_colors', 'edges_colors'))

RendererIBOs = namedtuple('IBOs', ('rings', 'edges'))

RendererVAOs = namedtuple('VAOs', ('rings', 'edges'))


@dataclass
class RendererParams:
    """Class intended to hold renderer settings and parameters."""
    background_color: RGBColor = (255, 255, 255)
    # Set default value through factory as Gradient is a mutable class
    rings_gradient: Gradient = field(default_factory=lambda: BLACK_TO_RED)
    edges_color: RGBAColor = (0, 0, 0, 255)
    show_rings: bool = True
    show_edges: bool = True
    close_rings: bool = True
    rings_width: float = 3
    edges_width: float = 5

    @property
    def background_color_normalized(self):
        return tuple(c/255 for c in self.background_color)


class Renderer:
    """This class implements a context-agnostic ModernGL renderer for
    `WalkerSystem` instances.\n
    Its `ctx` and `screen` attributes must be setup externally to a ModernGL
    context and framebuffer respectively.
    """
    def __init__(self, system: WalkerSystem, params=RendererParams()):
        self.system = system
        self.params = params
        self.model = np.eye(4, dtype='f4')
        self.view = translation(0, 0, -100)

        # Those need to be set externally by the subclass when the GL context
        # and framebuffer are ready
        self.ctx, self.screen = None, None

        # Those objects need the GL context to be ready to be initialized
        self.prog = None
        self.vbos, self.ibos, self.vaos = None, None, None

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
        self.vbos = RendererVBOs(
            # 4 bytes, 3 coordinates, 40 walkers, 1000 iterations
            pos = self.ctx.buffer(reserve=4 * 3 * 40 * 1000),
            # 1 byte, 4 channels, 40 walkers, 1000 iterations
            rings_colors = self.ctx.buffer(reserve=4 * 40 * 1000),
            edges_colors = self.ctx.buffer(reserve=4 * 40 * 1000)
        )
        self.ibos = RendererIBOs(
            # 4 bytes, 4 verts per line, 40 walkers, 1000 iterations
            rings = self.ctx.buffer(reserve=4 * 4 * 40 * 1000),
            edges = self.ctx.buffer(reserve=4 * 4 * 40 * 1000)
        )

        #                  VAOs structure
        # +-----------------------------------+-----------+
        # |                pos                |   color   |
        # +-----------+-----------+-----------+--+--+--+--+
        # |     x     |     y     |     z     |r |g |b |a |
        # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        # |00|01|02|03|04|05|06|07|08|09|0A|0B|0C|0D|0E|0F|
        # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        rings_content = (
            (self.vbos.pos,          '3f4', 'pos'),
            (self.vbos.rings_colors, '4f1', 'color'),
        )
        edges_content = (
            (self.vbos.pos,          '3f4', 'pos'),
            (self.vbos.edges_colors, '4f1', 'color'),
        )
        self.vaos = RendererVAOs(
            rings = self.ctx.vertex_array(
                self.prog, rings_content, self.ibos.rings
            ),
            edges = self.ctx.vertex_array(
                self.prog, edges_content, self.ibos.edges
            )
        )

    def compute_vertex_buffers(self):
        # Retrieve walkers system computed positions, in shape (iterations,
        # walkers count, 3)
        pos = self.system.positions
        iterations, walkers_count, _ = pos.shape
        vertex_count = iterations * walkers_count
        pos = pos.reshape(vertex_count, 3).astype('f4')

        # Compute vertex colors
        rings_colors = (self.params.rings_gradient
            .generate(vertex_count)
            .astype('u1')
        )
        edges_colors = np.tile(
            self.params.edges_color, (vertex_count, 1)
        ).astype('u1')

        # Compute vertex indexes
        rings_idx = []
        for chunk in chunks(range(vertex_count), walkers_count):
            verts_idx = list(chunk)
            # If the ring needs to be closed, a line must be drawn between its
            # first and last vertices
            if self.params.close_rings:
                verts_idx.append(verts_idx[0])
            # Convert the list of current ring's vertices to a list with
            # adjacent segments to be used by GL_LINES_ADJACENCY
            rings_idx += adjacent_lines_indexes(verts_idx)

        edges_idx = []
        for i in range(walkers_count):
            verts_idx = list(range(i, vertex_count, walkers_count))
            # To actually draw a line segment, at leat two points are needed
            if len(verts_idx) < 2:
                # If one edge is too short, then all others are too
                break
            # Convert the list of current edge's vertices to a list with
            # adjacent segments to be used by GL_LINES_ADJACENCY
            edges_idx += adjacent_lines_indexes(verts_idx)

        rings_idx = np.array(rings_idx, dtype='u4')
        edges_idx = np.array(edges_idx, dtype='u4')

        # Write data to VBOs and IBOs
        self.vbos.pos.clear()
        self.vbos.pos.write(pos)

        self.vbos.rings_colors.clear()
        self.vbos.rings_colors.write(rings_colors)
        self.vbos.edges_colors.clear()
        self.vbos.edges_colors.write(edges_colors)

        self.ibos.rings.clear()
        self.ibos.rings.write(rings_idx)
        self.ibos.edges.clear()
        self.ibos.edges.write(edges_idx)

        # Mark VBOs as updated
        self.needs_vbo_update = False

    def render_frame(self):
        self.ctx.clear(*self.params.background_color_normalized, 0)
        self.ctx.enable(BLEND)

        width, height = self.screen.width, self.screen.height

        self.projection = persp_projection(fov=40, aspect=width/height)

        self.prog['model'].write(self.model)
        self.prog['view'].write(self.view)
        self.prog['projection'].write(self.projection)
        self.prog['viewport'] = width, height

        if self.needs_vbo_update:
            self.compute_vertex_buffers()

        if self.params.show_rings:
            self.prog['width'] = self.params.rings_width
            self.vaos.rings.render(LINES_ADJACENCY)

        if self.params.show_edges:
            self.prog['width'] = self.params.edges_width
            self.vaos.edges.render(LINES_ADJACENCY)
