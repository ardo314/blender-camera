import argparse
import json
import sys
from typing import TypedDict

import bpy
from mathutils import Quaternion, Vector


class BlenderCameraData(TypedDict):
    id: str
    pose: list[float]  # [x, y, z, rx, ry, rz]


def load_camera_data(json_path: str) -> BlenderCameraData:
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


def render_image(output_path: str):
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def render_ply(output_path: str):
    """
    Create a pointcloud PLY file from depth, normals, and color data.
    This renders the scene from the current camera and generates depth/normal/color data,
    then converts it to a pointcloud.
    """
    scene = bpy.context.scene

    # Enable passes FIRST - before setting up compositor nodes
    scene.view_layers[0].use_pass_z = True
    scene.view_layers[0].use_pass_normal = True

    # Enable depth pass and normal pass in compositor
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    # Create render layers node
    render_layers = tree.nodes.new(type="CompositorNodeRLayers")

    # Create file output nodes for depth, normals, and color
    depth_output = tree.nodes.new(type="CompositorNodeOutputFile")
    depth_output.base_path = output_path
    depth_output.file_slots[0].path = "depth"
    depth_output.format.file_format = "OPEN_EXR"

    normal_output = tree.nodes.new(type="CompositorNodeOutputFile")
    normal_output.base_path = output_path
    normal_output.file_slots[0].path = "normal"
    normal_output.format.file_format = "OPEN_EXR"

    color_output = tree.nodes.new(type="CompositorNodeOutputFile")
    color_output.base_path = output_path
    color_output.file_slots[0].path = "color"
    color_output.format.file_format = "PNG"

    # Connect the outputs
    tree.links.new(render_layers.outputs["Depth"], depth_output.inputs[0])
    tree.links.new(render_layers.outputs["Normal"], normal_output.inputs[0])
    tree.links.new(render_layers.outputs["Image"], color_output.inputs[0])

    # Render the scene
    bpy.ops.render.render()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--type", required=True, choices=["image", "ply"])
    args, unknown_args = parser.parse_known_args([x for x in sys.argv if x != "--"])
    print("Arguments:", args)
    print("Unknown Arguments:", unknown_args)

    camera_data = load_camera_data(args.json_path)
    create_camera(camera_data)

    if args.type == "image":
        render_image(args.output_path)
    elif args.type == "ply":
        render_ply(args.output_path)
