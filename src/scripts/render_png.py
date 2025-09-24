import bpy
import argparse
import sys

from .blender_utils import load_camera_data, create_camera


def render_image(output_path: str):
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", required=True)
    parser.add_argument("--output_path", required=True)
    args, unknown_args = parser.parse_known_args([x for x in sys.argv if x != "--"])
    print("Arguments:", args)
    print("Unknown Arguments:", unknown_args)

    camera_data = load_camera_data(args.json_path)
    create_camera(camera_data)
    render_image(args.output_path)
