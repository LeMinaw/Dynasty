import moderngl
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat, QPalette
from PyQt5.QtWidgets import QOpenGLWidget
from time import time

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


class DynastyViewport(ModernGLWidget, Renderer):
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
        dt = time() - self.last_update

        self.model = self.model @ rotation(10*dt, 20*dt, 30*dt)
        
        # Call Qt's update machinery
        super().update()
        self.last_update = time()
