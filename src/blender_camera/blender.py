import asyncio
import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Union

import Imath
import numpy as np
import OpenEXR
from PIL import Image

from blender_camera.models.components.has_id import HasId
from blender_camera.models.components.has_pose import HasPose

CameraLike = Union[HasId, HasPose]


class Blender:
    def __init__(self, scene: str):
        self._scene = scene

    def _write_tmp_state(self, camera: CameraLike) -> str:
        """Saves camera data to a temporary JSON file and returns the file path."""
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(tmp_file.name, "w") as f:
            f.write(camera.model_dump_json())
        return tmp_file.name

    @asynccontextmanager
    async def _render_frame(self, camera: CameraLike):
        input_path = self._write_tmp_state(camera)
        output_path = tempfile.TemporaryDirectory(delete=False).name

        try:
            proc = await asyncio.create_subprocess_exec(
                "blender",
                self._scene,
                "--background",
                "--python",
                "src/blender_camera/blender_script.py",
                "--",
                "--input_path",
                input_path,
                "--output_path",
                output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            print("Blender stdout:\n", stdout.decode())
            print("Blender stderr:\n", stderr.decode())
            print("Blender exit code:", proc.returncode)

            if proc.returncode != 0:
                raise RuntimeError(
                    f"Blender process failed with exit code {proc.returncode}"
                )

            yield output_path
        finally:
            os.remove(input_path)
            shutil.rmtree(output_path)

    async def render_ply(self, camera: CameraLike) -> bytes:
        async with self._render_frame(camera) as output_path:
            with open(os.path.join(output_path, "frame_color_0001.exr"), "rb") as f:
                return f.read()

    def _convert_exr_to_png(self, exr_path: str) -> bytes:
        """Convert EXR file to PNG format and return as bytes."""
        # Open the EXR file
        exr_file = OpenEXR.InputFile(exr_path)
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
        rgb = np.stack([r, g, b], axis=-1)

        # Tone mapping: clamp and scale to 0-255
        rgb = np.clip(rgb, 0.0, 1.0)
        rgb_8bit = (rgb * 255).astype(np.uint8)

        # Convert to PIL Image and save to bytes
        image = Image.fromarray(rgb_8bit)
        img_bytes = BytesIO()
        image.save(img_bytes, format="PNG")

        return img_bytes.getvalue()

    async def render_png(self, camera: CameraLike) -> bytes:
        async with self._render_frame(camera) as output_path:
            exr_path = os.path.join(output_path, "frame_color_0001.exr")
            return self._convert_exr_to_png(exr_path)
