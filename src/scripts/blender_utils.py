from typing import TypedDict
import bpy
import json
from mathutils import Quaternion, Vector


class BlenderCameraData(TypedDict):
    id: str
    pose: list[float]  # [x, y, z, rx, ry, rz]


def load_camera_data(json_path) -> BlenderCameraData:
    with open(json_path, "r") as f:
        data = json.load(f)
    return data


def create_camera(camera_data: BlenderCameraData) -> bpy.types.Object:
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

    # Create a light (flash) that faces the same way as the camera
    light_data = bpy.data.lights.new(name="CameraFlash", type="POINT")
    light_obj = bpy.data.objects.new(name="CameraFlash", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = cam_obj.location
    # Point light doesn't have rotation, but if you use a SPOT light:
    # light_data.type = 'SPOT'
    # light_obj.rotation_mode = cam_obj.rotation_mode
    # light_obj.rotation_quaternion = cam_obj.rotation_quaternion
    # For POINT, just place at camera location

    return cam_obj
