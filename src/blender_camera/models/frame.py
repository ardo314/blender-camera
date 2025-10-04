from io import BytesIO

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from plyfile import PlyData, PlyElement

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

        # Convert to numpy arrays for plyfile
        num_points = len(points)
        if num_points == 0:
            # Handle case with no valid points
            vertex_data = np.array(
                [],
                dtype=[
                    ("x", "f4"),
                    ("y", "f4"),
                    ("z", "f4"),
                    ("nx", "f4"),
                    ("ny", "f4"),
                    ("nz", "f4"),
                    ("red", "u1"),
                    ("green", "u1"),
                    ("blue", "u1"),
                ],
            )
        else:
            points_array = np.array(points, dtype=np.float32)
            normals_array = np.array(normals, dtype=np.float32)
            colors_array = np.array(colors, dtype=np.uint8)

            # Create structured array for plyfile
            vertex_data = np.empty(
                num_points,
                dtype=[
                    ("x", "f4"),
                    ("y", "f4"),
                    ("z", "f4"),
                    ("nx", "f4"),
                    ("ny", "f4"),
                    ("nz", "f4"),
                    ("red", "u1"),
                    ("green", "u1"),
                    ("blue", "u1"),
                ],
            )

            vertex_data["x"] = points_array[:, 0]
            vertex_data["y"] = points_array[:, 1]
            vertex_data["z"] = points_array[:, 2]
            vertex_data["nx"] = normals_array[:, 0]
            vertex_data["ny"] = normals_array[:, 1]
            vertex_data["nz"] = normals_array[:, 2]
            vertex_data["red"] = colors_array[:, 0]
            vertex_data["green"] = colors_array[:, 1]
            vertex_data["blue"] = colors_array[:, 2]

        # Create PLY element and data
        vertex_element = PlyElement.describe(vertex_data, "vertex")
        ply_data = PlyData([vertex_element], text=True)

        # Write to bytes
        buffer = BytesIO()
        ply_data.write(buffer)
        return buffer.getvalue()
