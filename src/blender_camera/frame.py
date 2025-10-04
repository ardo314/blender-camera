import numpy as np


class BlenderFrame:
    def __init__(self, depth: np.ndarray, normal: np.ndarray, color: np.ndarray):
        self._depth = depth
        self._normal = normal
        self._color = color

    def to_depth_png_bytes(self) -> bytes:
        return self._convert_exr_to_png(self._depth)

    def to_normal_png_bytes(self) -> bytes:
        return self._convert_exr_to_png(self._normal)

    def to_color_png_bytes(self) -> bytes:
        return self._convert_exr_to_png(self._color)

    def to_ply_bytes(self) -> bytes:
        return self._convert_exr_to_ply(
            self._color,
            self._depth,
            self._normal if self._normal is not None else None,
        )
