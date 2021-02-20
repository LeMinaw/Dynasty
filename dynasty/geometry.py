import numpy as np


def x_rotation(angle):
    """Rotation matrix around X axis. Angle is in degrees."""
    angle *= np.pi / 180
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array((
        ( 1,  0,  0,  0),
        ( 0,  c, -s,  0),
        ( 0,  s,  c,  0),
        ( 0,  0,  0,  1)
    ), dtype='f4')


def y_rotation(angle):
    """Rotation matrix around Y axis. Angle is in degrees."""
    angle *= np.pi / 180
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array((
        ( c,  0,  s,  0),
        ( 0,  1,  0,  0),
        (-s,  0,  c,  0),
        ( 0,  0,  0,  1)
    ), dtype='f4')


def z_rotation(angle):
    """Rotation matrix around Z axis. Angle is in degrees."""
    angle *= np.pi / 180
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array((
        ( c, -s,  0,  0),
        ( s,  c,  0,  0),
        ( 0,  0,  1,  0),
        ( 0,  0,  0,  1)
    ), dtype='f4')


def rotation(x=0, y=0, z=0):
    """Rotation matrix around X, Y and Z axis. Angles are in degrees."""
    return x_rotation(x) @ y_rotation(y) @ z_rotation(z)


def translation(x=0, y=0, z=0):
    """Translation matrix in X, Y and Z directions."""
    trans = np.eye(4, dtype='f4')
    trans[3, 0:3] = x, y, z
    return trans


def ortho_projection(left=-1, right=1, bottom=-1, top=1, near=.1, far=1000):
    """Orthographic projection matrix."""
    return np.array((
        (2 / (right-left), 0,                0,              -(right+left) / (right-left)),
        (0,                2 / (top-bottom), 0,              -(top+bottom) / (top-bottom)),
        (0,                0,                2 / (near-far), (far+near) / (far-near)),
        (0,                0,                0,              1)
    ), dtype='f4')


def persp_projection(fov=30, aspect=1, near=.1, far=1000):
    """Perspective projection matrix."""
    # Distance of left/right boundaries from origin
    y = near * np.tan(fov * np.pi/360) 
    # Same for bottom/top boundaries
    x = y * aspect

    return np.array((
        (near / x, 0,        0,                       0),
        (0,        near / y, 0,                       0),
        (0,        0,        (near+far) / (near-far), -1),
        (0,        0,        2*near*far / (near-far), 0)
    ), dtype='f4')
