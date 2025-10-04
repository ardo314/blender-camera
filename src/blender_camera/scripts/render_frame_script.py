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


def convert_normal_exr_to_np(path: str) -> np.ndarray:
    normal_file = OpenEXR.InputFile(path)
    normal_header = normal_file.header()

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
                convert_depth_exr_to_np(depth_path),
                convert_normal_exr_to_np(normal_path),
                convert_color_exr_to_np(color_path),
            )
        finally:
            os.remove(input_path)
            shutil.rmtree(output_path)
