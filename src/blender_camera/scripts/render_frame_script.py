import os
import shutil
import tempfile

import Imath
import numpy as np
import OpenEXR

from blender_camera.blender import Blender
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

    def _convert_exr_to_ply(
        self, color_path: str, depth_path: str, normal_path: str = None
    ) -> bytes:
        """Convert EXR files (color, depth, optionally normals) to PLY point cloud format."""
        # Read color EXR
        color_file = OpenEXR.InputFile(color_path)
        color_header = color_file.header()
        dw = color_header["dataWindow"]
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1

        (R, G, B) = color_file.channels("RGB", FLOAT)

        # Convert color to numpy arrays
        r = np.frombuffer(R, dtype=np.float32).reshape((height, width))
        g = np.frombuffer(G, dtype=np.float32).reshape((height, width))
        b = np.frombuffer(B, dtype=np.float32).reshape((height, width))

        # Read normals if provided
        normals = None
        if normal_path and os.path.exists(normal_path):
            

        # Create 3D points from depth
        # Assuming standard camera intrinsics - you may need to adjust these
        fx = fy = width * 0.7  # Rough focal length estimate
        cx, cy = width / 2, height / 2

        # Create coordinate grids
        u, v = np.meshgrid(np.arange(width), np.arange(height))

        # Convert to 3D coordinates
        # Filter out infinite/invalid depth values
        valid_mask = (depth > 0) & (depth < 1000) & np.isfinite(depth)

        x = (u - cx) * depth / fx
        y = (v - cy) * depth / fy
        z = depth

        # Flatten and filter valid points
        points_3d = np.stack([x.flatten(), y.flatten(), z.flatten()], axis=1)
        colors_rgb = np.stack([r.flatten(), g.flatten(), b.flatten()], axis=1)
        valid_indices = valid_mask.flatten()

        points_3d = points_3d[valid_indices]
        colors_rgb = colors_rgb[valid_indices]

        # Convert colors to 0-255 range
        colors_rgb = np.clip(colors_rgb * 255, 0, 255).astype(np.uint8)

        if normals is not None:
            normals_flat = normals.reshape(-1, 3)[valid_indices]

            # Create vertex data array for PLY
        vertex_data = []
        for i in range(len(points_3d)):
            vertex = [
                points_3d[i, 0],
                points_3d[i, 1],
                points_3d[i, 2],
                colors_rgb[i, 0],
                colors_rgb[i, 1],
                colors_rgb[i, 2],
            ]
            if normals is not None:
                vertex.extend(
                    [normals_flat[i, 0], normals_flat[i, 1], normals_flat[i, 2]]
                )
            vertex_data.append(tuple(vertex))

        # Define PLY data types
        if normals is not None:
            vertex_dtype = [
                ("x", "f4"),
                ("y", "f4"),
                ("z", "f4"),
                ("red", "u1"),
                ("green", "u1"),
                ("blue", "u1"),
                ("nx", "f4"),
                ("ny", "f4"),
                ("nz", "f4"),
            ]
        else:
            vertex_dtype = [
                ("x", "f4"),
                ("y", "f4"),
                ("z", "f4"),
                ("red", "u1"),
                ("green", "u1"),
                ("blue", "u1"),
            ]

        # Create PLY element
        vertex_array = np.array(vertex_data, dtype=vertex_dtype)
        vertex_element = PlyElement.describe(vertex_array, "vertex")

        # Create PLY data
        ply_data = PlyData([vertex_element])

        # Write to bytes
        ply_bytes = BytesIO()
        ply_data.write(ply_bytes)

        return ply_bytes.getvalue()
