"""This module contains Qt models to interface Qt views with Qt-agnostic data
types.\n
For consistency with Qt, this file uses camelCase for variables, instances and
functions names.
"""

from enum import Enum
from PyQt5.QtCore import Qt, QAbstractListModel

from dynasty.walkers import RelModel, InterLaw


class EnumModel(QAbstractListModel):
    """Qt list model around a Python enumeration."""
    def __init__(self, enum: Enum, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.enum = enum

    def data(self, index, role):
        entry = self.enum(index.row())

        if role == Qt.DisplayRole:
            return str(entry)
        return None

    def rowCount(self, index):
        # pylint: disable = unused-argument
        return len(self.enum)


REL_MODELS_MODEL = EnumModel(RelModel)

INTER_LAWS_MODEL = EnumModel(InterLaw)
