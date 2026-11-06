"""Head orientation from MediaPipe's facial transformation matrix.

The Face Landmarker can output a 4x4 matrix mapping MediaPipe's canonical face
model into camera space (OpenGL convention: x right, y up, z toward the camera).
We decompose its rotation as R = Rx(pitch) · Ry(yaw) · Rz(roll):

    R[0,2] =  sin(yaw)
    R[1,2] = -sin(pitch)·cos(yaw)       R[2,2] = cos(pitch)·cos(yaw)
    R[0,1] = -cos(yaw)·sin(roll)        R[0,0] = cos(yaw)·cos(roll)

Sign check against sample images: a face pointing toward image-right gives
yaw > 0, a face pointing downward gives pitch > 0. Because Gestura processes the
*mirrored* frame by default, image-right is the user's right. For an unmirrored
frame we flip yaw and roll so the semantics stay "user's right".
"""

from __future__ import annotations

import math

import numpy as np

from ..core.types import HeadPose


def euler_from_matrix(matrix: np.ndarray) -> tuple[float, float, float]:
    """Return (yaw, pitch, roll) in degrees from a 3x3 or 4x4 matrix."""
    r = np.asarray(matrix, dtype=float)[:3, :3]
    # Remove any scale the transform may carry.
    norms = np.linalg.norm(r, axis=0)
    norms[norms == 0] = 1.0
    r = r / norms
    yaw = math.asin(max(-1.0, min(1.0, r[0, 2])))
    pitch = math.atan2(-r[1, 2], r[2, 2])
    roll = math.atan2(-r[0, 1], r[0, 0])
    return math.degrees(yaw), math.degrees(pitch), math.degrees(roll)


def head_pose_from_matrix(matrix: np.ndarray, mirrored: bool = True) -> HeadPose:
    yaw, pitch, roll = euler_from_matrix(matrix)
    if not mirrored:
        yaw, roll = -yaw, -roll
    # Image roll (counter-clockwise positive in a y-up frame) tilts the head
    # toward image-left; convert so positive roll = toward the user's right
    # shoulder in the mirrored view.
    return HeadPose(yaw=yaw, pitch=pitch, roll=-roll)


def rotation_matrix(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """Inverse of `euler_from_matrix` (degrees in, 3x3 out). Used by tests."""
    y, p, r = (math.radians(a) for a in (yaw, pitch, roll))
    rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return rx @ ry @ rz
