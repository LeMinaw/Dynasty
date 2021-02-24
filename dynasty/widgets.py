import moderngl
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat, QPalette
from PyQt5.QtWidgets import (QGridLayout, QWidget, QOpenGLWidget, QLabel,
    QSlider)
from typing import Callable
from time import perf_counter

from dynasty.renderer import Renderer
from dynasty.geometry import rotation


class ModernGLWidget(QOpenGLWidget):
    """This subclass of QOpenGLWidget provides `ctx` and `screen` attributes to
    be used by ModernGL.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.screen = None
        self.ctx = None

    def initializeGL(self):
        """This function will be internaly called by Qt during OpenGL context
        setup.\n
        When subclassing, either this function has to be called or another
        way to provide the `ctx` context attribute must be implemented.
        """
        # The screen attribute can't be defined here because the framebuffer is
        # not yet available at this stage
        self.ctx = moderngl.create_context()

    def paintGL(self):
        """This function will be internally called by Qt when a redraw is
        needed.\n
        When subclassing, either this function has to be called before the
        subclass `paintGL` override or another way to setup the `screen`
        framebuffer attribute must be implemented.
        """
        # According to Qt docs, context and framebuffer are bound and viewport
        # is set up before this function is called
        # The screen attribute is setup here because the framebuffer is not
        # avalaible when initializeGL is called
        if not self.screen:
            self.screen = self.ctx.detect_framebuffer(
                self.defaultFramebufferObject()
            )
        # Explicitely instruct ModernGL to use this framebuffer before
        # performing OpenGL calls
        # This is useful in many cases, eg. to fix framebuffer clearing
        self.screen.use()
    
    def resizeGL(self, w: int, h: int):
        """This function will be internally called by Qt when the widget is
        resized.
        """
        # According to Qt docs, gets called after makeCurrent() and the
        # framebuffer is bound
        self.screen = self.ctx.detect_framebuffer(
            self.defaultFramebufferObject()
        )
        # TODO: self.ctx.fbo.width / self.ctx.fbo.height are not correct ATM


class Viewport(ModernGLWidget, Renderer):
    """3D viewport QT widget for Dynasty, subclassing its custom OpenGL
    context-agnostic renderer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        # fmt.setDepthBufferSize(24)
        fmt.setSamples(8) # MSAA
        self.setFormat(fmt)

        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/60) # 60 FPS

        self.last_update = None

    def initializeGL(self):
        """This function will be internaly called by Qt during OpenGL context
        setup.
        """
        super().initializeGL()
        # Load GLSL programs from renderer
        self.initialize_program()
        self.initialize_vertex_buffers()

    def paintGL(self):
        """This function will be internally called by Qt when a redraw is
        needed. To schedule a redraw, call `update` instead.
        """
        super().paintGL()
        # Call the renderer's rendering fuction
        self.render_frame()

    def update(self):
        """This function is to be called when a redraw is needed. It will
        schedule a `paintGL` call automatically.
        """
        # Compute deltatime since last frame
        self.last_update = self.last_update or 0
        dt = perf_counter() - self.last_update

        self.model = self.model @ rotation(10*dt, 20*dt, 30*dt)
        
        # Call Qt's update machinery
        super().update()
        self.last_update = perf_counter()


class LabelSlider(QWidget):
    """Qt compound widget composed of a slider, a name label and an
    automaticall updating value label.
    """
    def __init__(self,
            name: str='',
            start: int=0, end: int=10, default: int=0,
            hint: str='',
            *args, **kwargs
        ):
        super().__init__(*args, **kwargs)
        
        self.slider = QSlider(Qt.Horizontal, self)
        self.name_label = QLabel(name, self)
        self.value_label = QLabel('', self)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self.name_label, 0, 0, Qt.AlignLeft)
        grid.addWidget(self.value_label, 0, 1, Qt.AlignRight)
        grid.addWidget(self.slider, 1, 0, 1, 2, Qt.AlignVCenter)
        self.setLayout(grid)
        self.setMaximumHeight(60)

        self.slider.setRange(start, end)
        self.slider.valueChanged[int].connect(self.on_value_change)
        
        if hint:
            self.setStatusTip(hint)
        
        # Trigger dummy value change to initialize with default value
        self.slider.setValue(default)
    
    def on_value_change(self, value: int):
        self.value = value
        self.value_label.setText(str(round(value, 4)))
    

class ParamSlider(LabelSlider):
    """Qt widget to provide numeric parameters input.\n
    The `callback` argument must be a callable taking one argument. It will be
    called each time the value of the slider is updated, with the new slider
    value as argument.\n
    As Qt sliders can only deal with integer values, a `factor` argument is
    provided. For exemple, a slider width `start=-2`, `end=4` and `factor=0.1`
    will output values in the range `[-0.2, 0.4]` with `0.1` step.
    """
    def __init__(self,
            callback: Callable[[float], None] = lambda _: None,
            factor: float=1,
            *args, **kwargs
        ):
        self.factor = factor
        self.callback = callback

        super().__init__(*args, **kwargs)

    def on_value_change(self, value: int):
        value *= self.factor

        super().on_value_change(value)
        self.callback(value)
