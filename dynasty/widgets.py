import moderngl
import numpy as np
from typing import Union
from time import perf_counter, strftime
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, pyqtSlot, pyqtSignal
from PyQt5.QtGui import (QSurfaceFormat, QImage, QPainter, QLinearGradient,
        QColor, QPen)
from PyQt5.QtWidgets import (QGridLayout, QHBoxLayout, QVBoxLayout, QWidget, QOpenGLWidget,
        QLabel, QSlider, QColorDialog, QSpinBox, qDrawShadePanel)

from dynasty.colors import Color, Gradient, WHITE_TO_BLACK
from dynasty.geometry import rotation, translation
from dynasty.renderer import Renderer
from dynasty.utils import LinearMapper, clamp


def toRGBA(color: QColor) -> Color:
    """Simple utility function to convert from a QColor to a tuple of integers
    depicting RGBA values in the range [0, 255].
    """
    return tuple(
        getattr(color, c)() for c in ('red', 'green', 'blue', 'alpha')
    )


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
        # pylint: disable = unused-argument
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

        self.rotation_speed = np.zeros(3)

        self.last_update = None
        self.last_pos = None

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
        dt = (perf_counter() - self.last_update)

        self.model = self.model @ rotation(*(dt * self.rotation_speed))

        # Call Qt's update machinery
        super().update()
        self.last_update = perf_counter()

    def mouseMoveEvent(self, event):
        """Perform a rotation and/or translation on the viewport model matrix
        when mouse is dragged.
        """
        last_pos = self.last_pos or event.pos()
        dx = event.x() - last_pos.x()
        dy = event.y() - last_pos.y()

        # Simple check to avoid "jumping" of the viewport when the mouse is
        # released, dragged somewhere else then pressed again
        if abs(dx) < 100 and abs(dy) < 100:
            if event.buttons() & Qt.LeftButton:
                self.model = self.model @ rotation(-.5*dy, -.5*dx, 0)

            if event.buttons() & Qt.RightButton:
                self.model = self.model @ translation(.1*dx, -.1*dy, 0)

        self.last_pos = event.pos()

    def wheelEvent(self, event):
        """Perform a translation on the viewport view matrix when mouse wheel
        is scrolled.
        """
        dy = event.angleDelta().y()
        self.view = self.view @ translation(0, 0, .1*dy)

    @pyqtSlot()
    def saveFramebuffer(self):
        """Save the current viewport framebuffer to a raster image file, in
        both PNG and JPEG formats. Exported files resolution is twice the
        current viewport resolution (aspect ratio is therefore preserved).
        """
        size = self.size()
        self.resize(size * 2)

        image = self.grabFramebuffer()
        # This reinterpret is needed in orther to fix a strange Qt bug when
        # exporting in any other format than JPEG, where the colors channels
        # seem mixed up weirdly
        image.reinterpretAsFormat(QImage.Format_ARGB32)
        filename = strftime('%Y-%m-%d_%H-%M-%S')
        image.save(filename + '.jpg', 'jpg', 100)
        image.save(filename + '.png', 'png')

        self.parent().statusBar().showMessage("Raster saved as " + filename)
        self.resize(size)


class Slider(QSlider):
    """Slight variation of Qt's `QSlider` accepting range values in its
    constructor.
    """
    def __init__(self, *args, start: int=0, end: int=0, **kwargs):
        super().__init__(*args, **kwargs)

        self.setRange(start, end)


class FloatSlider(Slider):
    """Variation of Qt's `QSlider` allowing to deal with non-integer values.\n
    The `factor` argument is used to map from integer to float values. For
    example, a slider width `start=-2`, `end=4` and `factor=0.1` will output
    values in the range `[-0.2, 0.4]` with `0.1` step.
    """
    # Redefine this signal to handle float values
    valueChanged = pyqtSignal(float)

    def __init__(self, *args, factor: float=1, **kwargs):
        super().__init__(*args, **kwargs)

        assert factor != 0
        self.factor = factor
        # Connect the valueChanged signal from the superclass to the float
        # conversion method
        super().valueChanged.connect(self.emitFloatValue)

    @pyqtSlot(int)
    def emitFloatValue(self, value: int):
        """Given an integer (generaly from the slider position), emit the
        corresponding float value.
        """
        self.valueChanged.emit(value * self.factor)

    @pyqtSlot(float)
    def setValue(self, value: float):
        """Set the value of the slider.\n
        It has to be a float value, and will be converted to an integer to set
        the slider internal state.
        """
        super().setValue(round(value / self.factor))


class AbstractLabeledSlider(QWidget):
    """Compound Qt widget composed of a slider, a name label and an
    automatically updating value label.\n
    This abstract base class needs a slider instance as argument and will
    support both integer (`Slider`) and float (`FloatSlider`) slider classes.
    """
    valueChanged = pyqtSignal([int], [float])

    def __init__(self, *args, name: str, slider: Slider, **kwargs):
        super().__init__(*args, **kwargs)

        self.slider = slider
        self.nameLabel = QLabel(name, self)
        self.valueLabel = QLabel('', self)
        # Set initial value label using decicated method
        self.setValueLabel(self.slider.value())

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self.nameLabel, 0, 0, Qt.AlignLeft)
        grid.addWidget(self.valueLabel, 0, 1, Qt.AlignRight)
        grid.addWidget(self.slider, 1, 0, 1, 2, Qt.AlignVCenter)
        self.setLayout(grid)
        self.setMaximumHeight(60)

        # Connect child slider signals
        self.slider.valueChanged.connect(self.valueChanged.emit)
        self.slider.valueChanged.connect(self.setValueLabel)

    @pyqtSlot(int)
    @pyqtSlot(float)
    def setValue(self, value: float):
        """Set the child slider to a given value."""
        self.slider.setValue(value)

    @pyqtSlot(int)
    @pyqtSlot(float)
    def setValueLabel(self, value: float):
        """Set the value label to display a given value."""
        self.valueLabel.setText(str(round(value, 4)))


class LabeledSlider(AbstractLabeledSlider):
    """Labeled slider embedding an horizontal `Slider` and outputing integer
    values.\n
    See docs for `Slider` and `AbstractLabeledSlider`.
    """
    # Enforce signal typing because sometimes Qt casts types weirdly
    valueChanged = pyqtSignal(int)

    def __init__(self, *args,
            name: str='',
            start: int=0, end: int=10,
            **kwargs
        ):
        sld = Slider(Qt.Horizontal, start=start, end=end)

        super().__init__(*args, name=name, slider=sld, **kwargs)


class LabeledFloatSlider(AbstractLabeledSlider):
    """Labeled slider embedding an horizontal `FloatSlider` and outputing float
    values.\n
    See docs for `FloatSlider` and `AbstractLabeledSlider`.
    """
    # Enforce signal typing because sometimes Qt casts types weirdly
    valueChanged = pyqtSignal(float)

    def __init__(self, *args,
            name: str='',
            start: int=0, end: int=10,
            factor: float=1,
            **kwargs
        ):
        sld = FloatSlider(Qt.Horizontal, start=start, end=end, factor=factor)

        super().__init__(*args, name=name, slider=sld, **kwargs)


class ColorAlphaPicker(QWidget):
    """This widget is inspired by Qt's `QColorLuminancePicker` and is intended
    to be inserted in `QColorDialog`, in order to provide a more user-friendly
    way to change the alpha value.
    """
    valueChanged = pyqtSignal(int)

    def __init__(self, *args, color=QColor('black'), **kwargs):
        super().__init__(*args, **kwargs)

        self.cursorSize = 5
        self.color = color
        self._value = 255

        self.setMinimumWidth(20)

    @property
    def value(self) -> int:
        """Current value of the alpha picker."""
        return self._value

    @value.setter
    def value(self, value: int):
        value = clamp(value, 0, 255)
        # Only trigger update machinery if value has actually changed
        if value != self._value:
            self._value = value
            self.valueChanged.emit(value)
            self.update()

    @property
    def posToVal(self) -> LinearMapper:
        """A `LinearMapper` instance mapping cursor positions in widget space
        to the corresponding values in the range [0, 255].
        """
        return LinearMapper(
            (self.gradientRect.bottom(), self.gradientRect.top()), (0, 255)
        )

    @property
    def valToPos(self) -> LinearMapper:
        """A `LinearMapper` instance mapping integer values in the range
        [0, 255] to the corresponding cursor positions in widget space.
        """
        return LinearMapper(
            (0, 255), (self.gradientRect.bottom(), self.gradientRect.top())
        )

    @property
    def gradientRect(self) -> QRect:
        """Boundaries of the displayed gradient color bar."""
        w, h = self.width(), self.height()
        # Those somewhat weird coordinates are designed to match the
        # original QColorLuminancePicker behavior
        return QRect(
            0,                       1 + self.cursorSize/2,
            w - self.cursorSize, h - 1 - self.cursorSize
        )

    # Qt events

    def paintEvent(self, event):
        # pylint: disable = unused-argument
        painter = QPainter(self)
        palette = self.palette()
        painter.setPen(palette.windowText().color())
        painter.setBrush(palette.windowText())

        # Draw gradient color bar
        transparent_color = QColor(self.color)
        transparent_color.setAlpha(0)

        gradient = QLinearGradient(0, 0, 0, self.gradientRect.height())
        gradient.setColorAt(0, self.color)
        gradient.setColorAt(1, transparent_color)
        painter.fillRect(self.gradientRect, gradient)
        qDrawShadePanel(painter, self.gradientRect, palette, True)

        # Draw cursor
        y = self.valToPos(self.value)
        painter.drawPolygon(
            QPoint(self.gradientRect.width(), y),
            QPoint(self.width(),              y - self.cursorSize),
            QPoint(self.width(),              y + self.cursorSize)
        )

    def mouseMoveEvent(self, event):
        self.value = self.posToVal(event.y())

    def mousePressEvent(self, event):
        self.value = self.posToVal(event.y())

    # End Qt events

    @pyqtSlot(QColor)
    def setColor(self, color: QColor):
        # RGB channels are used for widget color bar display
        self.color = QColor(color.rgb())
        # Alpha channel will be used as the new widget value
        self.value = color.alpha()
        self.update()


class ColorDialog(QColorDialog):
    """Slight variation of Qt's default color dialog."""
    def __init__(self, *args, alpha=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.setOption(QColorDialog.NoButtons, True)
        self.setOption(QColorDialog.ShowAlphaChannel, alpha)

        # Add a ColorAlphaPicker to the QColorDialog if needed
        if alpha:
            # This is the QSpinBox usually used to set the alpha value
            alphaSpinBox = self.findChildren(QSpinBox)[-1]

            alphaPicker = ColorAlphaPicker()
            alphaPicker.valueChanged.connect(alphaSpinBox.setValue)
            self.currentColorChanged.connect(alphaPicker.setColor)
            # Add the ColorAlphaPicker at the end of the correct layout
            self.findChildren(QHBoxLayout)[1].addWidget(alphaPicker)


class GradientEditor(QWidget):
    """This custom Qt widget allows editing and preview of a `Gradient` with an
    arbitrary and variable number of color stops.
    """
    #: This signal will be emitted when the bound Gradient has changed
    gradientChanged = pyqtSignal()

    def __init__(self, gradient: Gradient=WHITE_TO_BLACK, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.gradient = gradient
        self.selectedPos = None

        self.colorDialog = ColorDialog(self, alpha=True)
        self.colorDialog.currentColorChanged.connect(self._callback)

        self.setMinimumHeight(30)

    # Qt events

    def paintEvent(self, event):
        # pylint: disable = unused-argument
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = painter.device().width()
        height = painter.device().height()

        # Gradient draw pass
        gradient = QLinearGradient(0, 0, width, 0)
        for stop, color in self.gradient.items():
            gradient.setColorAt(stop, QColor(*color))
        painter.fillRect(0, 0, width, height, gradient)

        # Handles draw pass
        pen = QPen()
        pen.setWidth(3)
        pen.setColor(QColor(255, 255, 255, 191))
        painter.setPen(pen)

        y = height / 2
        for pos in self.gradient.keys():
            x = pos * width
            painter.drawLine(
                QPoint(x, y - 12),
                QPoint(x, y + 12)
            )
            painter.drawEllipse(QPoint(x, y), 6, 6)

        painter.end()

    def mousePressEvent(self, event):
        pos = self.getHandlePosFromEvent(event)
        # Select the color stop under the cursor and update the color picker
        # dialog accordingly
        if pos:
            self.selectedPos = pos
            color = self.gradient[pos]
            self.colorDialog.setCurrentColor(QColor(*color))

            # Show the color picker if the right mouse button is pressed above
            # a color stop
            if event.button() == Qt.RightButton:
                self.colorDialog.show()

    def mouseDoubleClickEvent(self, event):
        pos = self.getHandlePosFromEvent(event)
        # If one color stop was found, remove it
        if pos:
            self.removeColorStop(pos)
        # If no color stop was found, add one and select it
        else:
            pos = self.normalizePos(event.x())
            self.setColorStop(pos)
            self.selectedPos = pos

    def mouseMoveEvent(self, event):
        # Move the last selected color stop if it exists and the left mouse
        # left button is pressed
        if event.buttons() | Qt.LeftButton and self.selectedPos is not None:
            pos = self.normalizePos(event.x())
            self.moveColorStop(self.selectedPos, pos)
            self.selectedPos = pos

    # End of Qt events

    def getHandlePosFromEvent(self, event) -> Union[float, None]:
        """If a handle is found near where the event occured, return its
        position (in the range [0, 1]), otherwise return None.
        """
        pos = self.normalizePos(event.x())
        nearestPos = self.gradient.nearest_stop(pos)[0]

        # Only return color stop position if it is nearly enough to the event
        if abs(nearestPos - pos) * self.width() < 6:
            return nearestPos

    def normalizePos(self, pos: float) -> float:
        """Converts a color stop position from screen space to "gradient"
        space, i.e. from [0, widget width] to [0, 1].\n
        Additionnaly, output value is clamped.
        """
        return clamp(pos / self.width())

    def setColorStop(self, pos: float, color: Union[Color, None]=None):
        """Set the color of the gradient at a given position.\n
        If no color stop exists at this position, one will be created. If no
        color is specified, the nearest color of the gradient will be used.
        """
        self.gradient[pos] = color or self.gradient.nearest_stop(pos)[1]
        self.gradientChanged.emit()
        self.update()

    def removeColorStop(self, pos: float):
        """Remove the color stop at position `pos` from the gradient.\n
        Removing the first or last color stop is not allowed and will be no-op.
        """
        if pos not in self.gradient.endpoints.keys():
            del self.gradient[pos]

            # If the currently selected pos was deleted, select the nearest one
            if self.selectedPos == pos:
                self.selectedPos = self.gradient.nearest_stop(pos)[0]

            self.gradientChanged.emit()
            self.update()

    def moveColorStop(self, pos: float, newPos: float):
        """Move the color stop at `pos` to `newPos`."""
        color = self.gradient.pop(pos)
        self.gradient[newPos] = color
        self.gradientChanged.emit()
        self.update()

    def _callback(self, color: QColor):
        """Color picker dialog callback function. It will be called by the
        color picker widget each time a stop color is modified.
        """
        self.setColorStop(self.selectedPos, toRGBA(color))
    