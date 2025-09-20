import bpy
import json
import argparse


def load_camera_data(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return data


def create_camera(camera_data):
    cam = bpy.data.cameras.new(name=camera_data.get("id", "Camera"))
    cam_obj = bpy.data.objects.new(name=cam.name, object_data=cam)
    bpy.context.collection.objects.link(cam_obj)
    pose = camera_data["pose"]
    cam_obj.location = pose[:3]
    cam_obj.rotation_euler = pose[3:]
    bpy.context.scene.camera = cam_obj
    return cam_obj


def render_image(output_path):
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", required=True)
    parser.add_argument("--output_path", required=True)
    args, unknown = parser.parse_known_args()

    camera_data = load_camera_data(args.json_path)
    create_camera(camera_data)
    render_image(args.output_path)
