"""This module contains various shortcuts method aimed at making common Qt
widgets instanciation less verbose and error-prone.
"""

from __future__ import annotations
from typing import Sequence, Callable
from PyQt5.QtWidgets import QPushButton, QAction, QCheckBox
from PyQt5.QtCore import QObject

from dynasty.widgets import LabeledSlider, LabeledFloatSlider


def make_action(
        name: str = '',
        parent: QObject|None = None,
        shortcut: str = '',
        slots: Sequence[Callable, ...] = (),
        hint: str = ''
    ):
    """Make a simple, default Qt action.\n
    Slots will be connected to the `triggered` signal.
    """
    if parent is not None:
        act = QAction(text=name, parent=parent)
    else:
        act = QAction(text=name)

    for slot in slots:
        act.triggered.connect(slot)

    if hint:
        act.setStatusTip(hint)
    if shortcut:
        act.setShortcut(shortcut)

    return act


def make_button(
        name: str = '',
        parent: QObject|None = None,
        slots: Sequence[Callable, ...] = (),
        hint: str = ''
    ):
    """Make a simple, default Qt push button.\n
    Slots will be connected to the `clicked` signal.
    """
    if parent is not None:
        btn = QPushButton(text=name, parent=parent)
    else:
        btn = QPushButton(text=name)

    for slot in slots:
        btn.clicked.connect(slot)

    if hint:
        btn.setStatusTip(hint)

    return btn


def make_checkbox(
        name: str = '',
        parent: QObject|None = None,
        default: bool = False,
        slots: Sequence[Callable, ...] = (),
        hint: str = ''
    ):
    """Make a simple, default Qt labeled checkbox button.\n
    Slots will be connected to the `stateChanged` signal.
    """
    if parent is not None:
        cbx = QCheckBox(text=name, parent=parent)
    else:
        cbx = QCheckBox(text=name)

    for slot in slots:
        cbx.stateChanged.connect(slot)

    cbx.setChecked(default)
    if hint:
        cbx.setStatusTip(hint)

    return cbx


def make_slider(
        name: str = '',
        parent: QObject|None = None,
        start: int = 0,
        end: int = 10,
        factor: float|None = None,
        default: float = 0,
        slots: Sequence[Callable, ...] = (),
        hint: str = ''
    ):
    """Make a `LabeledSlider`. If a `factor` is given, a `LabeledFloatSlider`
    will be created.\n
    Slots will be connected to the `valueChanged` signal.
    """
    kwargs = {
        'name': name,
        'start': start,
        'end': end,
    }
    if parent is not None:
        kwargs['parent'] = parent

    if factor is not None:
        kwargs['factor'] = factor
        sld = LabeledFloatSlider(**kwargs)
    else:
        sld = LabeledSlider(**kwargs)

    for slot in slots:
        sld.valueChanged.connect(slot)

    sld.setValue(default)
    if hint:
        sld.setStatusTip(hint)

    return sld
