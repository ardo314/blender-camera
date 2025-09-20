import os
import subprocess

from blender_camera.models.camera import Camera
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


async def render_pointcloud(blend_url: str, camera: Camera) -> bytes:
    """Renders a point cloud in ply format and returns the binary data."""
    blend_file_path = await _load_blend_file(blend_url)
    json_path = _save_camera_to_tmp_file(camera)

    try:
        subprocess.run(
            [
                "blender",
                blend_file_path,
                "--background",
                "--python",
                "this_script.py",
                "--",
                "--json_path",
                json_path,
            ]
        )
    finally:
        os.remove(blend_file_path)
        os.remove(json_path)


async def render_image(blend_url: str, camera: Camera) -> bytes:
    """Renders an image in PNG format and returns the binary data."""
    blend_file_path = await _load_blend_file(blend_url)
    json_path = _save_camera_to_tmp_file(camera)

    try:
        output_path = "/tmp/rendered_image.png"
        subprocess.run(
            [
                "blender",
                blend_file_path,
                "--background",
                "--python",
                "this_script.py",
                "--",
                "--json_path",
                json_path,
                "--output_path",
                output_path,
            ]
        )
    finally:
        os.remove(blend_file_path)
        os.remove(json_path)

        if os.path.exists(output_path):
            os.remove(output_path)
