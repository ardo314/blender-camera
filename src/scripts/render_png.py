from typing import TypedDict
import bpy
import json
import argparse
from mathutils import Quaternion


class BlenderCameraData(TypedDict):
    id: str
    position: list[float]  # [x, y, z]
    rotation: list[float]  # [w, x, y, z]


def load_camera_data(json_path) -> BlenderCameraData:
    with open(json_path, "r") as f:
        data = json.load(f)
    return data


def create_camera(camera_data: BlenderCameraData):
    cam = bpy.data.cameras.new(name=camera_data["id"])
    cam_obj = bpy.data.objects.new(name=cam.name, object_data=cam)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = camera_data["position"]
    cam_obj.rotation_mode = "QUATERNION"
    cam_obj.rotation_quaternion = Quaternion(
        (
            camera_data["rotation"][0],
            camera_data["rotation"][1],
            camera_data["rotation"][2],
            camera_data["rotation"][3],
        )
    )
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
