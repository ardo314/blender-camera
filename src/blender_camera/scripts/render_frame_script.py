import os
import shutil
import tempfile

import Imath
import numpy as np
import OpenEXR

from blender_camera.blender import Blender
from blender_camera.models.entities.camera import CameraLike
from blender_camera.models.frame import Frame

FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)


def _write_tmp_state(camera: CameraLike) -> str:
    """Saves camera data to a temporary JSON file and returns the file path."""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(tmp_file.name, "w") as f:
        f.write(camera.model_dump_json())
    return tmp_file.name


def _convert_depth_exr_to_np(path: str) -> np.ndarray:  # Read depth EXR
    depth_file = OpenEXR.InputFile(path)
    depth_header = depth_file.header()

    # Get the data window (the actual image bounds)
    dw = depth_header["dataWindow"]
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1

    # Get available channels in depth file
    available_channels = depth_header["channels"].keys()

    # Try common depth channel names
    depth_channel = None
    for channel_name in ["Z", "Depth", "R", "G", "B", "A"]:
        if channel_name in available_channels:
            depth_channel = channel_name
            break

    if depth_channel is None:
        # If no depth channel found, use the first available channel
        depth_channel = list(available_channels)[0] if available_channels else "R"

    depth_data = depth_file.channel(depth_channel, FLOAT)
    return np.frombuffer(depth_data, dtype=np.float32).reshape((height, width))


def _convert_normal_exr_to_np(path: str) -> np.ndarray:
    normal_file = OpenEXR.InputFile(path)
    normal_header = normal_file.header()

    # Get the data window (the actual image bounds)
    dw = normal_header["dataWindow"]
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1

    NX = normal_file.channel("X", FLOAT)
    NY = normal_file.channel("Y", FLOAT)
    NZ = normal_file.channel("Z", FLOAT)
    nx = np.frombuffer(NX, dtype=np.float32).reshape((height, width))
    ny = np.frombuffer(NY, dtype=np.float32).reshape((height, width))
    nz = np.frombuffer(NZ, dtype=np.float32).reshape((height, width))
    normals = np.stack([nx, ny, nz], axis=-1)

    return normals


def _convert_color_exr_to_np(path: str) -> np.ndarray:
    """Convert EXR file to PNG format and return as bytes."""
    # Open the EXR file
    exr_file = OpenEXR.InputFile(path)
    header = exr_file.header()

    # Get the data window (the actual image bounds)
    dw = header["dataWindow"]
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1

    # Read the RGB channels
    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    (R, G, B) = exr_file.channels("RGB", FLOAT)

    # Convert to numpy arrays
    r = np.frombuffer(R, dtype=np.float32).reshape((height, width))
    g = np.frombuffer(G, dtype=np.float32).reshape((height, width))
    b = np.frombuffer(B, dtype=np.float32).reshape((height, width))

    # Stack the channels and convert to 8-bit
    return np.stack([r, g, b], axis=-1)


def _convert_world_to_camera_normals(
    normals: np.ndarray, camera: CameraLike
) -> np.ndarray:
    """Convert world-space normals to camera-space normals.

    Args:
        normals: World-space normal vectors as (height, width, 3) array
        camera: Camera with pose containing [x, y, z, rx, ry, rz] where
                rx, ry, rz are angle-axis rotation components

    Returns:
        Camera-space normal vectors as (height, width, 3) array
    """
    rx, ry, rz = camera.pose[3], camera.pose[4], camera.pose[5]

    # Calculate rotation angle from angle-axis representation
    angle = np.sqrt(rx * rx + ry * ry + rz * rz)

    # If no rotation, return normals unchanged
    if angle < 1e-8:
        return normals

    # Normalize axis
    axis = np.array([rx, ry, rz]) / angle

    # Create rotation matrix using Rodrigues' formula
    # R = I + sin(θ)K + (1-cos(θ))K²
    # where K is the skew-symmetric matrix of the axis
    K = np.array(
        [[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]]
    )

    identity = np.eye(3)
    R = identity + np.sin(angle) * K + (1 - np.cos(angle)) * np.dot(K, K)

    # For transforming normals from world to camera space, we need the inverse rotation
    # Since rotation matrices are orthogonal, R^-1 = R^T
    R_inv = R.T

    # Reshape normals to (N, 3) for matrix multiplication
    original_shape = normals.shape
    normals_flat = normals.reshape(-1, 3)

    # Apply rotation to each normal vector
    # normals_camera = R_inv @ normals_world
    normals_transformed = np.dot(normals_flat, R_inv.T)

    # Reshape back to original shape
    return normals_transformed.reshape(original_shape)


class RenderFrameScript:
    def __init__(self, blender: Blender):
        self._blender = blender

    async def execute(self, camera: CameraLike) -> Frame:
        input_path = _write_tmp_state(camera)
        output_path = tempfile.TemporaryDirectory(delete=False).name

        try:
            await self._blender.run(
                "--python",
                "src/scripts/render_frame.py",
                "--",
                "--input_path",
                input_path,
                "--output_path",
                output_path,
            )

            color_path = os.path.join(output_path, "frame_color_0001.exr")
            depth_path = os.path.join(output_path, "frame_depth_0001.exr")
            normal_path = os.path.join(output_path, "frame_normal_0001.exr")

            return Frame(
                camera,
                _convert_depth_exr_to_np(depth_path),
                _convert_world_to_camera_normals(
                    _convert_normal_exr_to_np(normal_path), camera
                ),
                _convert_color_exr_to_np(color_path),
            )
        finally:
            os.remove(input_path)
            shutil.rmtree(output_path)
