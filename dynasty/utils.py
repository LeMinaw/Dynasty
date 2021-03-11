"""General purpose utility classes and functions, too generic to be part of a
specific module of Dynasty.
"""

from enum import Enum
from itertools import islice, chain
from typing import Iterable, Generator, Tuple


Range = Tuple[float, float]


class LinearMapper:
    """Simple class to build a callable mapping values from one range to
    another linearily.\n
    Input and output ranges are set at instanciation. The resulting object can
    then be used as a callable to map values.
    """
    def __init__(self, in_range: Range=(0, 1), out_range: Range=(0, 1)):
        self.in_range = in_range
        self.out_range = out_range

    @property
    def coef(self) -> float:
        return (
            (self.out_range[1] - self.out_range[0])
            / (self.in_range[1] - self.in_range[0])
        )

    def __call__(self, x: float) -> float:
        return (x - self.in_range[0]) * self.coef + self.out_range[0]


class LabeledEnum(Enum):
    """This subclass of Enum allows specifing a label alltogether with the
    value of each enum entry.

    Example:
        MyEnum(LabeledEnum):
            THING = 0, "A thing"
            OTHER_THING = 1, "Some other thing"
    """
    def __new__(cls, value, label):
        # Build a new entry and use the first argument as enumerated _value_
        entry = object.__new__(cls)
        entry._value_ = value
        # Set the label attribute to the second argument
        entry.label = label
        return entry

    def __str__(self):
        return str(self.label)


def clamp(value: float, min_: float=0, max_: float=1) -> float:
    """Clamp `value` in the range [min_, max_]."""
    return min(max_, max(min_, value))


def all_equals(iterable: Iterable) -> bool:
    """Return True if all elements of a given `iterable` are equals, otherwise
    return False.
    """
    return len(set(iterable)) <= 1


def chunks(iterable: Iterable, n: int) -> Generator:
    """Split an `iterable` into sucessive iterators of lenght `n`."""
    iterable = iter(iterable)
    while True:
        chunk = islice(iterable, n)
        try:
            first = next(chunk)
        except StopIteration:
            return
        yield chain((first,), chunk)
