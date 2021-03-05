import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDockWidget,
        QVBoxLayout, QGroupBox, QAction, QPushButton)

from dynasty import APP_DIR, __version__
from dynasty.widgets import Viewport, ParamSlider, ColorDialog
from dynasty.interfaces import ViewportInterface
from dynasty.walkers import WalkerSystem, InterLaw, RelModel


class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowIcon(QIcon(str(APP_DIR / 'res' / 'icon.png')))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"Dynasty {__version__}")
        self.resize(900, 600)
        self.statusBar().showMessage("Welcome to Dynasty!")

        system = WalkerSystem({
            'count': 6,
            'spread': 10,
            'inter_law': InterLaw.POSITION,
            'rel_model': RelModel.ONE_TO_ONE,
            'rel_avg': .02,
            'rel_var': .03,
            'iterations': 100
        })

        viewport = Viewport(system=system, parent=self)
        self.setCentralWidget(viewport)

        self.viewport_interface = ViewportInterface(
            viewport=viewport, parent=self
        )

        sim_params_dock = SimParamsDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, sim_params_dock)

        view_params_dock = ViewParamsDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, view_params_dock)

        reset_act = QAction("Reset simulation", self)
        reset_act.setStatusTip("Load default simulation parameters")
        reset_act.setShortcut('Ctrl+N')
        reset_act.triggered.connect(self.not_implemented)

        open_act = QAction("Recall parameters...", self)
        open_act.setStatusTip("Load simulation parameters")
        open_act.setShortcut('Ctrl+O')
        open_act.triggered.connect(self.not_implemented)

        save_act = QAction("Save parameters...", self)
        save_act.setStatusTip("Save simulation parameters")
        save_act.setShortcut('Ctrl+S')
        save_act.triggered.connect(self.not_implemented)

        exit_act = QAction("Quit", self)
        exit_act.setStatusTip("Exit application")
        exit_act.setShortcut('Ctrl+Q')
        exit_act.triggered.connect(sys.exit)

        toggle_sim_params_act = sim_params_dock.toggleViewAction()
        toggle_sim_params_act.setStatusTip("Show/hide simulation parameters "
            "palette")

        toggle_view_params_act = view_params_dock.toggleViewAction()
        toggle_view_params_act.setStatusTip("Show/hide viewport settings "
            "palette")

        export_act = QAction("Export raster...", self)
        export_act.setStatusTip("Export viewport as raster file")
        export_act.setShortcut('Ctrl+E')
        export_act.triggered.connect(viewport.saveFramebuffer)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        view_menu = menubar.addMenu("View")
        file_menu.addAction(reset_act)
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)
        file_menu.addAction(exit_act)
        view_menu.addAction(toggle_sim_params_act)
        view_menu.addAction(toggle_view_params_act)
        edit_menu.addAction(export_act)


    def not_implemented(self):
        self.statusBar().showMessage("Not implemented!")


class ParamsDock(QDockWidget):
    def __init__(self, *args, name='', **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle(name)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        widget = QWidget(self)
        self.layout = QVBoxLayout()

        self.setWidget(widget)
        widget.setLayout(self.layout)
        widget.setMinimumWidth(210)

        self.interface = self.parent().viewport_interface


class SimParamsDock(ParamsDock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="Simulation parameters", **kwargs)

        random_box = QGroupBox("Randomize", self)
        random_lay = QVBoxLayout(random_box)
        random_box.setMaximumHeight(200)
        random_box.setLayout(random_lay)
        self.layout.addWidget(random_box)

        btn = QPushButton(text="Start positions", parent=random_box)
        btn.clicked.connect(self.interface.reseed_start_pos)
        btn.setStatusTip("Randomize walkers start positions")
        random_lay.addWidget(btn)

        btn = QPushButton(text="Relation matrix mask", parent=random_box)
        btn.clicked.connect(self.interface.reseed_rel_mask)
        btn.setStatusTip("Randomize walkers relation matrix mask. Only "
            "effective when using a mask type involving random")
        random_lay.addWidget(btn)

        btn = QPushButton(text="Relation matrix values", parent=random_box)
        btn.clicked.connect(self.interface.reseed_rel_matrix)
        btn.setStatusTip("Randomize walkers relation matrix values. Only "
            "effective when using a relation matrix involving random")
        random_lay.addWidget(btn)

        self.layout.addWidget(ParamSlider(
            name = "Walkers count",
            start = 2,
            end = 40,
            default = 4,
            callback = self.interface.set_count,
            hint = "Number of interacting walkers"
        ))
        self.layout.addWidget(ParamSlider(
            name = "Walkers spread",
            start = 1,
            end = 100,
            default = 50,
            callback = self.interface.set_spread,
            hint = "Average distance from origin walkers have at start"
        ))
        self.layout.addWidget(ParamSlider(
            name = "Average attraction",
            start = -100,
            end = 100,
            default = 50,
            factor = .001,
            callback = self.interface.set_rel_avg,
            hint = ("Average values that binds walkers together. Negative "
                "value means repulsion, zero means no relation, positive is "
                "attraction")
        ))
        self.layout.addWidget(ParamSlider(
            name = "Attraction variance",
            end = 100,
            default = 0,
            factor = .001,
            callback = self.interface.set_rel_var,
            hint = "How random attraction values are. Zero means no random"
        ))
        self.layout.addWidget(ParamSlider(
            name = "Iterations",
            start = 1,
            end = 1000,
            default = 10,
            callback = self.interface.set_iterations,
            hint = "Number of iterations to compute"
        ))


class ViewParamsDock(ParamsDock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="Viewport settings", **kwargs)

        rot_box = QGroupBox("Rotation speed", self)
        rot_lay = QVBoxLayout(rot_box)
        rot_box.setMaximumHeight(200)
        rot_box.setLayout(rot_lay)
        self.layout.addWidget(rot_box)

        rot_lay.addWidget(ParamSlider(
            name = "X axis",
            start = -180,
            end = 180,
            callback = self.interface.set_x_rot_speed,
            hint = "Viewport rotation speed around X axis"
        ))
        rot_lay.addWidget(ParamSlider(
            name = "Y axis",
            start = -180,
            end = 180,
            default = 10,
            callback = self.interface.set_y_rot_speed,
            hint = "Viewport rotation speed around Y axis"
        ))
        rot_lay.addWidget(ParamSlider(
            name = "Z axis",
            start = -180,
            end = 180,
            callback = self.interface.set_z_rot_speed,
            hint = "Viewport rotation speed around Z axis"
        ))

        bck_dialog = BackgroundColorDialog(self)

        btn = QPushButton(text="Background color", parent=self)
        btn.clicked.connect(bck_dialog.show)
        btn.setStatusTip("Set the background color of the viewport")
        self.layout.addWidget(btn)


class BackgroundColorDialog(ColorDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Background color")

        interface = self.parent().interface
        self.currentColorChanged.connect(interface.set_background_color)
