"""This module regroups classes provinding signals and slots based interfaces
for other Qt-agnostic components.\n
For consistency with Qt, this file uses camelCase for variables, instances and
functions names.
"""

from time import perf_counter_ns
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QColor

from dynasty.widgets import Viewport


class ViewportInterface(QObject):
    """This class encapsulates commands to be called by signals from the Qt GUI
    on the `Viewport` object and the `System` it is currently rendering.\n
    This is NOT final and might be removed in the future.
    """
    def __init__(self, viewport: Viewport, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.viewport = viewport

    @property
    def system(self):
        return self.viewport.system

    @property
    def ringsGradient(self):
        """Interface directly presents Gradient as it is a mutable class."""
        return self.viewport.params.rings_gradient

    @pyqtSlot()
    def reseedStartPos(self):
        self.system.start_pos_seed = perf_counter_ns()
        self.updateStartPos()

    @pyqtSlot()
    def reseedRelMask(self):
        self.system.rel_mask_seed = perf_counter_ns()
        self.updateRelMask()

    @pyqtSlot()
    def reseedRelMatrix(self):
        self.system.rel_matrix_seed = perf_counter_ns()
        self.updateRelMatrix()

    @pyqtSlot(int)
    def setCount(self, x):
        self.system.params['count'] = x
        self.updateStartPos()

    @pyqtSlot(float)
    def setSpread(self, x):
        self.system.params['spread'] = x
        self.updatePos()

    @pyqtSlot(float)
    def setRelAvg(self, x):
        self.system.params['rel_avg'] = x
        self.updateRelMatrix()

    @pyqtSlot(float)
    def setRelVar(self, x):
        self.system.params['rel_var'] = x
        self.updateRelMatrix()

    @pyqtSlot(int)
    def setIterations(self, x):
        self.system.params['iterations'] = x
        self.updatePos()

    @pyqtSlot(float)
    def setXRotSpeed(self, x):
        self.viewport.rotation_speed[0] = x

    @pyqtSlot(float)
    def setYRotSpeed(self, x):
        self.viewport.rotation_speed[1] = x

    @pyqtSlot(float)
    def setZRotSpeed(self, x):
        self.viewport.rotation_speed[2] = x

    @pyqtSlot(QColor)
    def setBackgroundColor(self, color):
        self.viewport.params.background_color = tuple(
            getattr(color, c)() for c in ('red', 'green', 'blue')
        )

    def updateStartPos(self):
        self.system.generate_start_pos()
        self.updateRelMask()

    def updateRelMask(self):
        self.system.generate_relation_mask()
        self.updateRelMatrix()

    def updateRelMatrix(self):
        self.system.generate_relation_matrix()
        self.updatePos()

    def updatePos(self):
        self.system.compute_pos()
        self.updateVBOs()

    def updateVBOs(self):
        self.viewport.needs_vbo_update = True
