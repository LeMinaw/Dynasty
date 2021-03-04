from __future__ import annotations
import numpy as np
from typing import Tuple, Union, Iterable
from sortedcontainers import SortedDict


RGBColor = Tuple[int, int, int]

RGBAColor = Tuple[int, int, int, int]

Color = Union[RGBColor, RGBAColor]


def all_equals(iterable: Iterable) -> bool:
    """Return True if all elements of a given `iterable` are equals, otherwise
    return False.
    """
    return len(set(iterable)) <= 1


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
    def channels(self) -> Union[int, None]:
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

    def generate(self, steps:int =10) -> np.ndarray:
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
