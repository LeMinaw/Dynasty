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

    @pyqtSlot()
    def reseed_start_pos(self):
        self.system.start_pos_seed = perf_counter_ns()
        self.update_start_pos()

    @pyqtSlot()
    def reseed_rel_mask(self):
        self.system.rel_mask_seed = perf_counter_ns()
        self.update_rel_mask()

    @pyqtSlot()
    def reseed_rel_matrix(self):
        self.system.rel_matrix_seed = perf_counter_ns()
        self.update_rel_matrix()

    @pyqtSlot(int)
    def set_count(self, x):
        self.system.params['count'] = x
        self.update_start_pos()

    @pyqtSlot(float)
    def set_spread(self, x):
        self.system.params['spread'] = x
        self.update_pos()

    @pyqtSlot(float)
    def set_rel_avg(self, x):
        self.system.params['rel_avg'] = x
        self.update_rel_matrix()

    @pyqtSlot(float)
    def set_rel_var(self, x):
        self.system.params['rel_var'] = x
        self.update_rel_matrix()

    @pyqtSlot(int)
    def set_iterations(self, x):
        self.system.params['iterations'] = x
        self.update_pos()

    @pyqtSlot(float)
    def set_x_rot_speed(self, x):
        self.viewport.rotation_speed[0] = x

    @pyqtSlot(float)
    def set_y_rot_speed(self, x):
        self.viewport.rotation_speed[1] = x

    @pyqtSlot(float)
    def set_z_rot_speed(self, x):
        self.viewport.rotation_speed[2] = x

    @pyqtSlot(QColor)
    def set_background_color(self, color):
        self.viewport.background_color = tuple(
            getattr(color, c)() / 255 for c in ('red', 'green', 'blue')
        )

    def update_start_pos(self):
        self.system.generate_start_pos()
        self.update_rel_mask()

    def update_rel_mask(self):
        self.system.generate_relation_mask()
        self.update_rel_matrix()

    def update_rel_matrix(self):
        self.system.generate_relation_matrix()
        self.update_pos()

    def update_pos(self):
        self.system.compute_pos()
        self.viewport.needs_vbo_update = True
