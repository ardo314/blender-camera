import asyncio
import os
import shutil
import tempfile
from contextlib import asynccontextmanager

from blender_camera.models.entities.camera import Camera


class Blender:
    def __init__(self, scene: str):
        self._scene = scene

    def _write_tmp_state(self, camera: Camera) -> str:
        """Saves camera data to a temporary JSON file and returns the file path."""
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(tmp_file.name, "w") as f:
            f.write(camera.model_dump_json())
        return tmp_file.name

    @asynccontextmanager
    async def _render_frame(self, camera: Camera):
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

    async def render_ply(self, camera: Camera) -> bytes:
        async with self._render_frame(camera) as output_path:
            with open(os.path.join(output_path, "frame_color_0001.exr"), "rb") as f:
                return f.read()

    async def render_img(self, camera: Camera) -> bytes:
        async with self._render_frame(camera) as output_path:
            with open(os.path.join(output_path, "frame_color_0001.exr"), "rb") as f:
                return f.read()
