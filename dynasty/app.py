from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDockWidget,
        QVBoxLayout, QAction)

from dynasty import APP_DIR, __version__
from dynasty.widgets import Viewport, ParamSlider
from dynasty.interfaces import ViewportInterface
from dynasty.walkers import WalkerSystem, InterLaw, RelModel


class Application(QApplication):
    pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"Dynasty {__version__}")
        self.setWindowIcon(QIcon(str(APP_DIR / 'res' / 'dynasty.png')))
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

        params_dock = ParamsDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, params_dock)

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
        exit_act.triggered.connect(exit)

        view_params_act = params_dock.toggleViewAction()
        view_params_act.setStatusTip("Show/hide parameters palette")

        export_act = QAction("Export raster...", self)
        export_act.setStatusTip("Export viewport as raster file")
        export_act.setShortcut('Ctrl+E')
        export_act.triggered.connect(self.not_implemented)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        view_menu = menubar.addMenu("View")
        file_menu.addAction(reset_act)
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)
        file_menu.addAction(exit_act)
        view_menu.addAction(view_params_act)
        edit_menu.addAction(export_act)


    def not_implemented(self):
        self.statusBar().showMessage("Not implemented!")
    

class ParamsDock(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Simulation parameters")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        widget = QWidget(self)
        layout = QVBoxLayout()
        
        self.setWidget(widget)
        widget.setLayout(layout)
        widget.setMinimumWidth(210)

        layout.addWidget(ParamSlider(
            name = "Demo slider",
            hint = "Wonderful demo slider",
            start = -10,
            end = 10,
            default = 2,
            callback = lambda x: print(x),
            factor = .5,
        ))
        