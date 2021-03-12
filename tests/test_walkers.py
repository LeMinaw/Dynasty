"""Unit tests for walkers module."""
# pylint: disable = redefined-outer-name

import numpy as np
from pytest import fixture

from dynasty.walkers import diff_array


@fixture()
def scalar_array():
    """NumPy array with shape (4,) containing scalars."""
    return np.array((1, -3, 6, 4))

@fixture()
def points_array():
    """NumPy array with shape (4, 3) containing scalars, representing four
    points in 3D space.
    """
    return np.array((
        ( 1,  0, -2),
        (-3,  5,  4),
        ( 6, -2,  5),
        ( 4, -1, -4)
    ))


def test_diff_array_scalars(scalar_array):
    res = np.array((
        ( 0, -4,  5,  3),
        ( 4,  0,  9,  7),
        (-5, -9,  0, -2),
        (-3, -7,  2,  0)
    ))
    assert np.all(diff_array(scalar_array) == res)

def test_diff_array_points(points_array):
    res = np.array((
        (
            ( 0,  0,  0),
            (-4,  5,  6),
            ( 5, -2,  7),
            ( 3, -1, -2)
        ), (
            ( 4, -5, -6),
            ( 0,  0,  0),
            ( 9, -7,  1),
            ( 7, -6, -8)
        ), (
            (-5,  2, -7),
            (-9,  7, -1),
            ( 0,  0,  0),
            (-2,  1, -9)
        ), (
            (-3,  1,  2),
            (-7,  6,  8),
            ( 2, -1,  9),
            ( 0,  0,  0)
        )
    ))
    assert np.all(diff_array(points_array) == res)
