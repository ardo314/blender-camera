import os
import tempfile
from io import BytesIO

import numpy as np
import open3d as o3d
from numpy.typing import NDArray
from PIL import Image

from blender_camera.models.components.has_camera_intrinsics import HasCameraIntrinsics
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

    def _depth_to_positions(self) -> NDArray[np.float32]:
        height, width = self._depth.shape

        # Get camera intrinsics if available
        fx = fy = cx = cy = None
        try:
            if (
                isinstance(self._camera, HasCameraIntrinsics)
                and self._camera.camera_intrinsics is not None
            ):
                intrinsics = self._camera.camera_intrinsics
                fx = intrinsics.fx
                fy = intrinsics.fy
                cx = intrinsics.cx
                cy = intrinsics.cy
        except (AttributeError, TypeError, ValueError):
            pass

        # Use default intrinsics if not available or invalid
        if fx is None or fy is None or cx is None or cy is None:
            fx = fy = max(width, height)  # Reasonable default focal length
            cx = width / 2.0
            cy = height / 2.0

        # Create coordinate grids
        y_coords, x_coords = np.mgrid[0:height, 0:width]

        # Convert pixel coordinates to 3D world coordinates
        z = self._depth
        x = (x_coords - cx) * z / fx
        y = (y_coords - cy) * z / fy

        # Stack into (height, width, 3) array of (x,y,z) positions
        positions = np.stack([x, y, z], axis=-1).astype(np.float32)
        return positions

    def to_depth_png_bytes(self) -> bytes:
        return _to_8bit_png(self._depth)

    def to_normal_png_bytes(self) -> bytes:
        normal = (self._normal + 1) / 2
        return _to_8bit_png(normal)

    def to_color_png_bytes(self) -> bytes:
        return _to_8bit_png(self._color)

    def to_pointcloud(self) -> o3d.geometry.PointCloud:
        """Create and return an Open3D pointcloud initialized with points, normals, and colors."""
        pointcloud = o3d.geometry.PointCloud()

        positions = self._depth_to_positions().reshape(-1, 3)
        normals = self._normal.reshape(-1, 3)
        colors = self._color.reshape(-1, 3)

        # Initialize the Open3D pointcloud with points, normals, and colors
        pointcloud.points = o3d.utility.Vector3dVector(positions)
        pointcloud.normals = o3d.utility.Vector3dVector(normals)
        pointcloud.colors = o3d.utility.Vector3dVector(colors)

        return pointcloud

    def to_ply_bytes(self) -> bytes:
        """Export the pointcloud as PLY format bytes."""
        pointcloud = self.to_pointcloud()

        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".ply", delete=False)
            o3d.io.write_point_cloud(temp_file.name, pointcloud)
            temp_file.seek(0)
            ply_bytes = temp_file.read()
            return ply_bytes
        finally:
            temp_file.close()
            os.unlink(temp_file.name)
