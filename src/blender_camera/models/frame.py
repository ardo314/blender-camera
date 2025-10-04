from io import BytesIO

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from blender_camera.models.entities.camera import CameraLike


def _to_8bit_png(image: NDArray[np.float32]) -> bytes:
    """Convert a floating-point image to 8-bit PNG bytes."""
    image = np.clip(image, 0.0, 1.0)
    rgb_8bit = (image * 255).astype(np.uint8)

    # Convert to PIL Image and save to bytes
    pil_image = Image.fromarray(rgb_8bit)
    img_bytes = BytesIO()
    pil_image.save(img_bytes, format="PNG")

    return img_bytes.getvalue()


class Frame:
    def __init__(
        self,
        camera: CameraLike,
        depth: NDArray[np.float32],  # 2D array of floats (height, width)
        normal: NDArray[np.float32],  # 2D array of (x,y,z) vectors (height, width, 3)
        color: NDArray[np.float32],  # 2D array of (r,g,b) values (height, width, 3)
    ):
        self._camera = camera
        self._depth = depth
        self._normal = normal
        self._color = color

    def to_depth_png_bytes(self) -> bytes:
        depth = np.clip(self._depth, 0.0, 1.0)
        return _to_8bit_png(depth)

    def to_normal_png_bytes(self) -> bytes:
        normal = np.clip(self._normal, 0.0, 1.0)
        return _to_8bit_png(normal)

    def to_color_png_bytes(self) -> bytes:
        rgb = np.clip(self._color, 0.0, 1.0)
        return _to_8bit_png(rgb)

    def to_ply_bytes(self) -> bytes:
        raise NotImplementedError("PLY export not implemented yet")
