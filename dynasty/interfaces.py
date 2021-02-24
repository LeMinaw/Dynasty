from PyQt5.QtCore import QObject, pyqtSlot
from time import perf_counter_ns

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
        self.system.generate_start_pos()
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True

    @pyqtSlot()
    def reseed_rel_mask(self):
        self.system.rel_mask_seed = perf_counter_ns()
        self.system.generate_relation_mask()
        self.system.generate_relation_matrix()
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True

    @pyqtSlot()
    def reseed_rel_matrix(self):
        self.system.rel_matrix_seed = perf_counter_ns()
        self.system.generate_relation_matrix()
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True

    @pyqtSlot()
    def set_count(self, x):
        self.system.params['count'] = x
        self.system.generate_start_pos()
        self.system.generate_relation_mask()
        self.system.generate_relation_matrix()
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True

    @pyqtSlot()
    def set_spread(self, x):
        self.system.params['spread'] = x
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True
    
    @pyqtSlot()
    def set_rel_avg(self, x):
        self.system.params['rel_avg'] = x
        self.system.generate_relation_matrix()
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True
    
    @pyqtSlot()
    def set_rel_var(self, x):
        self.system.params['rel_var'] = x
        self.system.generate_relation_matrix()
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True

    @pyqtSlot()
    def set_iterations(self, x):
        self.system.params['iterations'] = x
        self.system.compute_pos()

        self.viewport.needs_vbo_update = True
        