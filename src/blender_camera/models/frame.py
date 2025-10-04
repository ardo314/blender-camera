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
        """Convert frame data to PLY point cloud format."""
        height, width = self._depth.shape

        # Get camera intrinsics if available
        fx = fy = cx = cy = None
        try:
            if (
                hasattr(self._camera, "camera_intrinsics")
                and self._camera.camera_intrinsics is not None
            ):
                intrinsics = self._camera.camera_intrinsics
                if (
                    hasattr(intrinsics, "fx")
                    and hasattr(intrinsics, "fy")
                    and hasattr(intrinsics, "cx")
                    and hasattr(intrinsics, "cy")
                ):
                    fx = float(intrinsics.fx)
                    fy = float(intrinsics.fy)
                    cx = float(intrinsics.cx)
                    cy = float(intrinsics.cy)
        except (AttributeError, TypeError, ValueError):
            pass

        # Use default intrinsics if not available or invalid
        if fx is None or fy is None or cx is None or cy is None:
            fx = fy = max(width, height)  # Reasonable default focal length
            cx = width / 2.0
            cy = height / 2.0

        # Create arrays for 3D coordinates
        points = []
        colors = []
        normals = []

        for y in range(height):
            for x in range(width):
                depth_val = self._depth[y, x]

                # Skip invalid depth values
                if depth_val <= 0 or not np.isfinite(depth_val):
                    continue

                # Convert pixel coordinates to 3D world coordinates
                # Using pinhole camera model
                world_x = (x - cx) * depth_val / fx
                world_y = (y - cy) * depth_val / fy
                world_z = depth_val

                points.append([world_x, world_y, world_z])

                # Get color (convert from [0,1] to [0,255])
                color_rgb = (self._color[y, x] * 255).astype(np.uint8)
                colors.append(color_rgb)

                # Get normal
                normal_vec = self._normal[y, x]
                normals.append(normal_vec)

        # Create PLY header
        num_points = len(points)
        header = f"""ply
format ascii 1.0
element vertex {num_points}
property float x
property float y
property float z
property float nx
property float ny
property float nz
property uchar red
property uchar green
property uchar blue
end_header
"""

        # Create PLY data
        ply_data = header
        for i in range(num_points):
            point = points[i]
            normal = normals[i]
            color = colors[i]
            ply_data += f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f} "
            ply_data += f"{normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f} "
            ply_data += f"{color[0]} {color[1]} {color[2]}\n"

        return ply_data.encode("utf-8")
