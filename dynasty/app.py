"""This module contains top-level Qt elements such as the application root
class, the main window and its docking panels.\n
For consistency with Qt, this file uses camelCase for variables, instances and
functions names.
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDockWidget,
        QVBoxLayout, QGroupBox)

from dynasty import APP_DIR, __version__
from dynasty.factory import make_action, make_button, make_slider
from dynasty.interfaces import ViewportInterface
from dynasty.walkers import WalkerSystem, InterLaw, RelModel
from dynasty.widgets import (Viewport, LabeledColorWidget,
        LabeledGradientWidget)


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

        self.viewportInterface = ViewportInterface(
            viewport=viewport, parent=self
        )

        simParamsDock = SimParamsDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, simParamsDock)

        viewParamsDock = ViewParamsDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, viewParamsDock)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("File")
        editMenu = menubar.addMenu("Edit")
        viewMenu = menubar.addMenu("View")

        fileMenu.addAction(make_action(
            name = "Reset simulation",
            parent = self,
            shortcut = 'Ctrl+N',
            slots = [self.notImplemented],
            hint = "Load default simulation parameters"
        ))
        fileMenu.addAction(make_action(
            name = "Recall parameters...",
            parent = self,
            shortcut = 'Ctrl+O',
            slots = [self.notImplemented],
            hint = "Load simulation parameters"
        ))
        fileMenu.addAction(make_action(
            name = "Save parameters...",
            parent = self,
            shortcut = 'Ctrl+S',
            slots = [self.notImplemented],
            hint = "Save simulation parameters"
        ))
        fileMenu.addAction(make_action(
            name = "Quit",
            parent = self,
            shortcut = 'Ctrl+Q',
            slots = [sys.exit],
            hint = "Exit application"
        ))

        editMenu.addAction(make_action(
            name = "Export raster...",
            parent = self,
            shortcut = 'Ctrl+E',
            slots = [viewport.saveFramebuffer],
            hint = "Export viewport as raster file."
        ))

        act = simParamsDock.toggleViewAction()
        act.setStatusTip("Show/hide simulation parameters palette.")
        viewMenu.addAction(act)

        act = viewParamsDock.toggleViewAction()
        act.setStatusTip("Show/hide viewport settings palette.")
        viewMenu.addAction(act)

    def notImplemented(self):
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

        self.interface = self.parent().viewportInterface


class SimParamsDock(ParamsDock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="Simulation parameters", **kwargs)

        randBox = QGroupBox("Randomize", self)
        randLay = QVBoxLayout(randBox)
        randBox.setMaximumHeight(200)
        randBox.setLayout(randLay)
        self.layout.addWidget(randBox)

        randLay.addWidget(make_button(
            name = "Start positions",
            parent = randBox,
            slots = [self.interface.reseedStartPos],
            hint = "Randomize walkers start positions."
        ))
        randLay.addWidget(make_button(
            name = "Relation matrix mask",
            parent = randBox,
            slots = [self.interface.reseedRelMask],
            hint = ("Randomize walkers relation matrix mask. Only effective "
                "when using a mask type involving random.")
        ))
        randLay.addWidget(make_button(
            name = "Relation matrix values",
            parent = randBox,
            slots = [self.interface.reseedRelMatrix],
            hint = ("Randomize walkers relation matrix values. Only effective "
                "when using a relation matrix involving random.")
        ))

        self.layout.addWidget(make_slider(
            name = "Walkers count",
            parent = self,
            start = 2, end = 40,
            default = 4,
            slots = [self.interface.setCount],
            hint = "Number of interacting walkers."
        ))
        self.layout.addWidget(make_slider(
            name = "Walkers spread",
            parent = self,
            start = 1, end = 100, factor = 1,
            default = 50,
            slots = [self.interface.setSpread],
            hint = "Average distance from origin walkers have at start."
        ))
        self.layout.addWidget(make_slider(
            name = "Average attraction",
            parent = self,
            start = -100, end = 100, factor = .001,
            default = .05,
            slots = [self.interface.setRelAvg],
            hint = ("Average values that binds walkers together. Negative "
                "value means repulsion, zero means no relation, positive is "
                "attraction.")
        ))
        self.layout.addWidget(make_slider(
            name = "Attraction variance",
            parent = self,
            end = 100, factor = .001,
            slots = [self.interface.setRelVar],
            hint = "How random attraction values are. Zero means no random."
        ))
        self.layout.addWidget(make_slider(
            name = "Iterations",
            start = 1, end = 1000,
            default = 50,
            slots = [self.interface.setIterations],
            hint = "Number of iterations to compute."
        ))


class ViewParamsDock(ParamsDock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="Viewport settings", **kwargs)

        rotBox = QGroupBox("Rotation speed", self)
        rotLay = QVBoxLayout(rotBox)
        rotBox.setMaximumHeight(200)
        rotBox.setLayout(rotLay)
        self.layout.addWidget(rotBox)

        rotLay.addWidget(make_slider(
            name = "X axis",
            parent = rotBox,
            start = -180, end = 180, factor = 1,
            slots = [self.interface.setXRotSpeed],
            hint = "Viewport rotation speed around X axis."
        ))
        rotLay.addWidget(make_slider(
            name = "Y axis",
            parent = rotBox,
            start = -180, end = 180, factor = 1,
            default = 10,
            slots = [self.interface.setYRotSpeed],
            hint = "Viewport rotation speed around Y axis."
        ))
        rotLay.addWidget(make_slider(
            name = "Z axis",
            parent = rotBox,
            start = -180, end = 180, factor = 1,
            slots = [self.interface.setZRotSpeed],
            hint = "Viewport rotation speed around Z axis."
        ))

        wdg = LabeledColorWidget(self, name="Background color")
        wdg.setStatusTip("Set the background color of the viewport.")
        wdg.colorChanged.connect(self.interface.setBackgroundColor)
        self.layout.addWidget(wdg)

        wdg = LabeledGradientWidget(
            self.interface.ringsGradient, self, name="Rings gradient"
        )
        wdg.setStatusTip("Edit the gradient alongside the rings of the "
            "3D model.")
        wdg.gradientChanged.connect(self.interface.updateVBOs)
        self.layout.addWidget(wdg)
