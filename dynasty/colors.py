from __future__ import annotations
import numpy as np
from typing import Tuple, Union
from sortedcontainers import SortedDict

from dynasty.utils import all_equals


RGBColor = Tuple[int, int, int]

RGBAColor = Tuple[int, int, int, int]

Color = Union[RGBColor, RGBAColor]

ColorStop = Tuple[float, Color]


class Gradient(SortedDict):
    """Basic gradient.\n
    This is a sorted by key dict depicting the color stops of the gradient. Its
    keys are float values in the range [0, 1], specifing the position of the
    color stop in the overall gradient. Its values are colors. It is required
    each color stop has the same number of channels.\n
    For exemple, the following:
        Gradient({
            0.0: (255, 0, 0),
            0.5: (0, 255, 0),
            1.0: (0, 0, 255)
        })
    Denotes a gradient starting with red, having a green point at the middle,
    and ending with blue.
    """
    @property
    def channels(self) -> int | None:
        """Number of color channels the gradient stops have.\n
        Return `None` if the gradient if empty."""
        # Check all colors have the same number of channels
        assert all_equals(len(c) for c in self.values())

        if not self:
            return None
        return len(self.peekitem()[1]) # Length of last color stop value

    @property
    def endpoints(self) -> Gradient:
        """Return a new `Gradient` containing only the first and last color
        stops of the current gradient.\n
        Return an empty `Gradient` if current gradient is empty.
        """
        if not self:
            return type(self)()
        return type(self)((self.peekitem(0), self.peekitem()))

    def previous_stop(self, pos: float) -> ColorStop | None:
        """Return the nearest color stop before `pos`, or `None` if it does not
        exist.
        """
        index = self.bisect(pos)
        try:
            return self.peekitem(index-1)
        except IndexError:
            return None

    def next_stop(self, pos: float) -> ColorStop | None:
        """Return the nearest color stop after `pos`, or `None` if it does not
        exist.
        """
        index = self.bisect(pos)
        try:
            return self.peekitem(index)
        except IndexError:
            return None

    def nearest_stop(self, pos: float) -> ColorStop | None:
        """Return the nearest color stop around `pos`, or `None` id the
        `Gradient` is empty.
        """
        # Return None if the gradient does not have any color stop
        if not self:
            return None

        prev_stop = self.previous_stop(pos)
        next_stop = self.next_stop(pos)
        prev_pos = prev_stop[0] if prev_stop else float('-inf')
        next_pos = next_stop[0] if next_stop else float('+inf')

        if abs(prev_pos - pos) <= abs(next_pos - pos):
            return prev_stop
        return next_stop

    def generate(self, steps: int=10) -> np.ndarray:
        """Generates a an array of `steps` colors from the gradient.\n
        First array axis correponds to colors steps, second to color channels.
        """
        # Check all stop indexes are in [0, 1]
        assert all(0 <= i <= 1 for i in self.keys())

        # Map positions from [0, 1] to [0, steps]
        positions = np.array(tuple(self.keys())) * steps

        # Generate the array with f-order so it will be C-contiguous when
        # transposed
        return np.array(tuple(
            np.interp(
                range(steps), # Final array indexes
                positions, # Color stop positions
                tuple(c[i] for c in self.values()) # Color channel values
            ) for i in range(self.channels)
        ), order='f').T


WHITE_TO_BLACK = Gradient({
    0: (255, 255, 255, 255),
    1: (0,   0,   0,   255)
})

BLACK_TO_RED = Gradient({
    0: (0,   0, 0, 255),
    1: (255, 0, 0, 255)
})
