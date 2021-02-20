import numpy as np
import numpy.lib.recfunctions as rf
import moderngl
from time import time
from moderngl import LINES_ADJACENCY, BLEND

from dynasty import APP_DIR
from dynasty.geometry import translation, persp_projection


from dynasty.walkers import WalkerSystem, InterLaw, RelModel
sys = WalkerSystem({
    'count': 6,
    'spread': 10,
    'inter_law': InterLaw.POSITION,
    'rel_model': RelModel.ONE_TO_ONE,
    'rel_avg': .02,
    'rel_var': .03,
    'iterations': 100
})
sys.generate_start_pos()
sys.generate_relation_mask()
sys.generate_relation_matrix()
sys.compute_pos()


class Renderer:
    """This class implements a context-agnostic ModernGL renderer.\n
    Its `ctx` and `screen` attributes must be setup externally to a ModernGL
    context and framebuffer respectively.
    """
    def __init__(self):
        super().__init__()

        self.model = np.eye(4, dtype='f4')
        self.view = translation(0, 0, -30)
        self.background_color = (1, 1, 1) # White

        self.ctx, self.screen = None, None

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

        # pos = np.array((
        #     (0, .5, 1),
        #     (1, .5, 1),
        #     (1, .5, 0),
        #     (1, .5, 0),
        #     (1, .5, -1),
        #     (2, .5, -1)
        # ), dtype='f4')

        # colors = np.array((
        #     (255, 000, 000, 255),
        #     (000, 255, 000, 255),
        #     (000, 000, 255, 255),
        #     (000, 255, 255, 255),
        #     (255, 000, 255, 255),
        #     (255, 255, 000, 255)
        # ), dtype='u1')

        # index = np.array((
        #     0, 0, 1, 2,
        #     0, 1, 2, 3,
        #     1, 2, 3, 4,
        #     2, 3, 4, 5,
        #     3, 4, 5, 5
        # ), dtype='u4') # 0-65653

        # sys.positions.shape is (iterations, walkers count, 3)
        v_count = sys.positions.shape[0] * sys.positions.shape[1]
        pos = sys.positions.reshape(v_count, 3).astype('f4')

        colors = [(30, 100, 255, 130) for _ in range(v_count)]
        colors = np.array(colors, dtype='u1')

        index = []
        for i in range(v_count):
            index += [i+j for j in range(-1, 3)]
        index[0] = 0
        index[-1] = v_count
        index = np.array(index, dtype='u4')

        # Concatenate arrays on axis 1 while preserving their dtypes
        vertices = rf.merge_arrays((*pos.T, *colors.T))

        vbo = self.ctx.buffer(vertices)
        ibo = self.ctx.buffer(index)

        #                  VBO structure
        # +-----------------------------------+-----------+
        # |                pos                |   color   |
        # +-----------+-----------+-----------+--+--+--+--+
        # |     x     |     y     |     z     |r |g |b |a |
        # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        # |00|01|02|03|04|05|06|07|08|09|0A|0B|0C|0D|0E|0F|
        # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        content = (
            (vbo, '3f4 4f1', 'pos', 'color'),
        )
        vao = self.ctx.vertex_array(self.prog, content, ibo)

        vao.render(LINES_ADJACENCY)


if __name__ == '__main__':
    import moderngl_window as mglw

    from dynasty.geometry import rotation


    class TestWindow(mglw.WindowConfig, Renderer):
        gl_version = (3, 3)
        window_size = (900, 600)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.screen = self.ctx.detect_framebuffer()
            self.initialize_program()

            self.model = np.eye(4, dtype='f4')
            self.view = translation(0, 0, -30)

        def render(self, time, frametime):
            dt = frametime
            self.model = self.model @ rotation(10*dt, 20*dt, 30*dt)
            self.render_frame()


    mglw.run_window_config(TestWindow)
