from typing import TypedDict
import bpy
import json
import argparse
from mathutils import Quaternion, Vector
import sys


class BlenderCameraData(TypedDict):
    id: str
    pose: list[float]  # [x, y, z, rx, ry, rz]


def load_camera_data(json_path) -> BlenderCameraData:
    with open(json_path, "r") as f:
        data = json.load(f)
    return data


def create_camera(camera_data: BlenderCameraData):
    cam = bpy.data.cameras.new(name=camera_data["id"])
    cam_obj = bpy.data.objects.new(name=cam.name, object_data=cam)
    bpy.context.collection.objects.link(cam_obj)
    pose = camera_data["pose"]
    x, y, z = pose[:3]
    rx, ry, rz = pose[3:]
    cam_obj.location = (x, y, z)

    # Convert rotation vector (axis-angle) to quaternion
    rot_vec = Vector((rx, ry, rz))
    angle = rot_vec.length
    axis = rot_vec.normalized() if angle != 0 else Vector((0, 0, 1))

    cam_obj.rotation_mode = "QUATERNION"
    cam_obj.rotation_quaternion = Quaternion(axis, angle)

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
    args, unknown_args = parser.parse_known_args([x for x in sys.argv if x != "--"])
    print("Arguments:", args)
    print("Unknown Arguments:", unknown_args)

    camera_data = load_camera_data(args.json_path)
    create_camera(camera_data)
    render_image(args.output_path)
