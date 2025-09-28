import asyncio
import os
import subprocess
import tempfile

import aiohttp

from blender_camera.models.entities.camera import Camera


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


async def _call_blender_process(
    blend_file_path: str, json_path: str, output_path: str, render_type: str
):
    proc = await asyncio.create_subprocess_exec(
        "blender",
        blend_file_path,
        "--background",
        "--python",
        "src/blender_camera/blender_script.py",
        "--",
        "--json_path",
        json_path,
        "--output_path",
        output_path,
        "--type",
        render_type,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    print("Blender stdout:\n", stdout.decode())
    print("Blender stderr:\n", stderr.decode())
    print("Blender exit code:", proc.returncode)

    if proc.returncode != 0:
        raise RuntimeError(f"Blender process failed with exit code {proc.returncode}")


async def render_pointcloud(blend_url: str, camera: Camera) -> bytes:
    """Renders a point cloud in ply format and returns the binary data."""
    blend_file_path = "untitled.blend"
    json_path = _save_camera_to_tmp_file(camera)
    output_path = tempfile.TemporaryDirectory(delete=False).name

    try:
        await _call_blender_process(blend_file_path, json_path, output_path, "ply")
    finally:
        os.remove(blend_file_path)
        os.remove(json_path)
        os.remove(output_path)


async def render_image(blend_url: str, camera: Camera) -> bytes:
    """Renders an image in PNG format and returns the binary data."""
    blend_file_path = "./untitled.blend"  # await _load_blend_file(blend_url)
    json_path = _save_camera_to_tmp_file(camera)
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

    try:
        await _call_blender_process(blend_file_path, json_path, output_path, "image")
        with open(output_path, "rb") as f:
            return f.read()
    finally:
        os.remove(blend_file_path)
        os.remove(json_path)
        os.remove(output_path)
