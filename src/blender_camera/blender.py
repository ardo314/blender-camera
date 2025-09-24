import asyncio
import json
import os
import subprocess

from blender_camera.entities.camera import Camera
import aiohttp
import tempfile


async def _load_blend_file(url: str) -> str:
    """Downloads a scene file from a URL and returns the local file path."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".blend")
    with open(tmp_file.name, "wb") as f:
        f.write(content)
    return tmp_file.name


def _save_camera_to_tmp_file(camera: Camera) -> str:
    """Saves camera data to a temporary JSON file and returns the file path."""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(tmp_file.name, "w") as f:
        f.write(camera.model_dump_json())
    return tmp_file.name


def _get_image_path() -> str:
    """Generates a temporary file path for the rendered image."""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    return tmp_file.name


async def render_pointcloud(blend_url: str, camera: Camera) -> bytes:
    """Renders a point cloud in ply format and returns the binary data."""
    blend_file_path = "untitled.blend"  # await _load_blend_file(blend_url)
    json_path = _save_camera_to_tmp_file(camera)

    try:
        cmd = [
            "blender",
            blend_file_path,
            "--background",
            "--python",
            "this_script.py",
            "--",
            "--json_path",
            json_path,
        ]
        print("Running Blender command:", " ".join(cmd))
        subprocess.run(cmd)
    finally:
        os.remove(blend_file_path)
        os.remove(json_path)


async def render_image(blend_url: str, camera: Camera) -> bytes:
    """Renders an image in PNG format and returns the binary data."""
    blend_file_path = "./untitled.blend"  # await _load_blend_file(blend_url)
    json_path = _save_camera_to_tmp_file(camera)
    output_path = "image.png"

    try:
        proc = await asyncio.create_subprocess_exec(
            "blender",
            blend_file_path,
            "--background",
            "--python",
            "src/scripts/render_png.py",
            "--",
            "--json_path",
            json_path,
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

        with open(output_path, "rb") as f:
            return f.read()
    finally:
        os.remove(blend_file_path)
        os.remove(json_path)

        if os.path.exists(output_path):
            os.remove(output_path)
