import os
import subprocess

from blender_camera.models.camera import Camera
import requests
import tempfile


def _save_camera_to_tmp_file(camera: Camera) -> str:
    """Saves camera data to a temporary JSON file and returns the file path."""
    import json
    import tempfile

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(tmp_file.name, "w") as f:
        json.dump(camera.model_dump(), f)
    return tmp_file.name


async def _load_scene(url: str) -> str:
    """Downloads a scene file from a URL and returns the local file path."""

    response = requests.get(url)
    response.raise_for_status()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".blend")
    with open(tmp_file.name, "wb") as f:
        f.write(response.content)
    return tmp_file.name


async def render_pointcloud(camera: Camera) -> bytes:
    """Renders a point cloud in ply format and returns the binary data."""
    try:
        json_path = _save_camera_to_tmp_file(camera)
        subprocess.run(
            [
                "blender",
                "--background",
                "--python",
                "this_script.py",
                "--",
                "--json_path",
                json_path,
            ]
        )
    finally:
        os.remove(json_path)


async def render_image(camera: Camera) -> bytes:
    """Renders an image in PNG format and returns the binary data."""
    try:
        json_path = _save_camera_to_tmp_file(camera)
        output_path = "/tmp/rendered_image.png"
        subprocess.run(
            [
                "blender",
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
        os.remove(json_path)
        if os.path.exists(output_path):
            os.remove(output_path)
