import subprocess


def render():
    subprocess.run(
        ["blender", "-b", "scene.blend", "-o", "//render_", "-F", "PNG", "-f", "1"]
    )
