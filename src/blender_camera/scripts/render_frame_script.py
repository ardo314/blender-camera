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


def convert_depth_exr_to_np(path: str) -> np.ndarray:  # Read depth EXR
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


def convert_normal_exr_to_np(path: str, camera: CameraLike) -> np.ndarray:
    normal_file = OpenEXR.InputFile(path)
    normal_header = normal_file.header()

    # Get the data window (the actual image bounds)
    dw = normal_header["dataWindow"]
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1

    # Get available channels in normal file
    normal_channels = normal_header["channels"].keys()

    # Try to read normal channels - they might be XYZ format or RGB format
    if all(ch in normal_channels for ch in ["X", "Y", "Z"]):
        NX = normal_file.channel("X", FLOAT)
        NY = normal_file.channel("Y", FLOAT)
        NZ = normal_file.channel("Z", FLOAT)
        nx = np.frombuffer(NX, dtype=np.float32).reshape((height, width))
        ny = np.frombuffer(NY, dtype=np.float32).reshape((height, width))
        nz = np.frombuffer(NZ, dtype=np.float32).reshape((height, width))
        normals = np.stack([nx, ny, nz], axis=-1)
    elif all(ch in normal_channels for ch in ["R", "G", "B"]):
        (NX, NY, NZ) = normal_file.channels("RGB", FLOAT)
        nx = np.frombuffer(NX, dtype=np.float32).reshape((height, width))
        ny = np.frombuffer(NY, dtype=np.float32).reshape((height, width))
        nz = np.frombuffer(NZ, dtype=np.float32).reshape((height, width))
        normals = np.stack([nx, ny, nz], axis=-1)
    else:
        # If no suitable channels found, create a default normal map
        normals = np.zeros((height, width, 3), dtype=np.float32)
        normals[:, :, 2] = 1.0  # Default to pointing towards camera (0, 0, 1)

    # Transform normals from world space to camera space
    if hasattr(camera, "pose") and camera.pose is not None:
        # Extract rotation angles from pose [x, y, z, rx, ry, rz]
        rx, ry, rz = camera.pose[3], camera.pose[4], camera.pose[5]

        # Create rotation matrices for each axis (in radians)
        cos_x, sin_x = np.cos(rx), np.sin(rx)
        cos_y, sin_y = np.cos(ry), np.sin(ry)
        cos_z, sin_z = np.cos(rz), np.sin(rz)

        # Rotation matrix around X axis
        R_x = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])

        # Rotation matrix around Y axis
        R_y = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])

        # Rotation matrix around Z axis
        R_z = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])

        # Combined rotation matrix (order: Z * Y * X for Blender's default)
        R_world_to_camera = R_z @ R_y @ R_x

        # Transform normals from world space to camera space
        # Reshape normals to (height*width, 3) for matrix multiplication
        original_shape = normals.shape
        normals_flat = normals.reshape(-1, 3)

        # Apply the inverse rotation (transpose for orthogonal matrices)
        normals_camera = (R_world_to_camera.T @ normals_flat.T).T

        # Reshape back to original shape
        normals = normals_camera.reshape(original_shape)

    return normals


def convert_color_exr_to_np(path: str) -> np.ndarray:
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


class RenderFrameScript:
    def __init__(self, blender: Blender):
        self._blender = blender

    def _write_tmp_state(self, camera: CameraLike) -> str:
        """Saves camera data to a temporary JSON file and returns the file path."""
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(tmp_file.name, "w") as f:
            f.write(camera.model_dump_json())
        return tmp_file.name

    async def execute(self, camera: CameraLike) -> Frame:
        input_path = self._write_tmp_state(camera)
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
                convert_depth_exr_to_np(depth_path),
                convert_normal_exr_to_np(normal_path, camera),
                convert_color_exr_to_np(color_path),
            )
        finally:
            os.remove(input_path)
            shutil.rmtree(output_path)
