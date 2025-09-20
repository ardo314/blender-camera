import subprocess

from blender_camera.models.camera import Camera


def render_pointcloud(camera: Camera) -> bytes:
    """Renders a point cloud in ply format and returns the binary data."""
    subprocess.run(
        ["blender", "-b", "scene.blend", "-o", "//render_", "-F", "PNG", "-f", "1"]
    )


def render_image(camera: Camera) -> bytes:
    """Renders an image in PNG format and returns the binary data."""
    subprocess.run(
        ["blender", "-b", "scene.blend", "-o", "//render_", "-F", "PNG", "-f", "1"]
    )
