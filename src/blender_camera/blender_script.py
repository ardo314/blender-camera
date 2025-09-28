import argparse
import json
import os
import sys
from typing import TypedDict

import bpy
from mathutils import Quaternion, Vector


class SceneState(TypedDict):
    id: str
    pose: list[float]  # [x, y, z, rx, ry, rz]


def _load_scene_state(input_path: str) -> SceneState:
    with open(input_path, "r") as f:
        state = json.load(f)
    return state


def _create_camera(state: SceneState) -> bpy.types.Object:
    cam = bpy.data.cameras.new(name=state["id"])
    cam_obj = bpy.data.objects.new(name=cam.name, object_data=cam)
    bpy.context.collection.objects.link(cam_obj)
    pose = state["pose"]
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


def _setup_passes(view_layer: bpy.types.ViewLayer):
    """Enable the passes we need on the view layer."""
    view_layer.use_pass_normal = True
    view_layer.use_pass_z = True
    # (Color is implicit / via the regular “Image” pass)


def _clear_compositor_nodes(scene: bpy.types.Scene):
    """Remove all nodes in the scene’s compositor tree."""
    scene.use_nodes = True
    tree = scene.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    return tree, tree.nodes, tree.links


def _build_compositor(tree, nodes, links, output_dir, basename="frame"):
    """
    Build compositor nodes:
    - Input: Render Layers
    - Remap depth
    - File Output for color, normal, depth
    Returns the FileOutput nodes (color, normal, depth).
    """
    # Render Layers node
    rl = nodes.new(type="CompositorNodeRLayers")
    rl.location = (0, 0)

    # Map / remap node for depth (optional, to scale Z into displayable range)
    map_depth = nodes.new(type="CompositorNodeMapRange")
    map_depth.location = (200, -200)
    # You may adjust these depending on your scene’s depth range:
    map_depth.inputs["From Min"].default_value = 0.0
    map_depth.inputs["From Max"].default_value = 50.0  # e.g. 50 units away
    map_depth.inputs["To Min"].default_value = 0.0
    map_depth.inputs["To Max"].default_value = 1.0
    # map_depth.clamp = True

    links.new(rl.outputs["Depth"], map_depth.inputs["Value"])

    # File Output: color
    out_color = nodes.new(type="CompositorNodeOutputFile")
    out_color.label = "FileOut_Color"
    out_color.location = (400, 200)
    # File Output: normals
    out_normal = nodes.new(type="CompositorNodeOutputFile")
    out_normal.label = "FileOut_Normal"
    out_normal.location = (400, 0)
    # File Output: depth
    out_depth = nodes.new(type="CompositorNodeOutputFile")
    out_depth.label = "FileOut_Depth"
    out_depth.location = (400, -200)

    # Set base path empty so full path is taken from file_slots paths
    out_color.base_path = ""
    out_normal.base_path = ""
    out_depth.base_path = ""

    # Configure formats (you can choose PNG, EXR, etc.)
    # For depth and normal we often want float formats (EXR)
    for node in (out_color, out_normal, out_depth):
        fmt = node.format
        fmt.file_format = "OPEN_EXR"
        fmt.color_depth = "32"
        # For depth you could also force BW or keep RGBA
        # fmt.color_mode = 'BW'  # optional

    # Link outputs
    links.new(rl.outputs["Image"], out_color.inputs[0])
    links.new(rl.outputs["Normal"], out_normal.inputs[0])
    links.new(map_depth.outputs["Value"], out_depth.inputs[0])

    # Set the path template for naming using default slots (index 0)
    out_color.file_slots[0].path = os.path.abspath(
        os.path.join(output_dir, basename + "_color_")
    )
    out_normal.file_slots[0].path = os.path.abspath(
        os.path.join(output_dir, basename + "_normal_")
    )
    out_depth.file_slots[0].path = os.path.abspath(
        os.path.join(output_dir, basename + "_depth_")
    )

    return out_color, out_normal, out_depth


def _render_frames(output_dir, start=1, end=1, basename="frame"):
    """
    Render frames in the given range, writing color/normal/depth for each frame.
    """
    scene = bpy.context.scene
    rl = scene.view_layers.items()[0][1]
    _setup_passes(rl)

    tree, nodes, links = _clear_compositor_nodes(scene)
    out_color, out_normal, out_depth = _build_compositor(
        tree, nodes, links, output_dir, basename
    )

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # Use a float format globally (EXR) to preserve precision
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.render.use_multiview = False  # unless stereo
    # Use compositing
    scene.use_nodes = True

    for frame in range(start, end + 1):
        scene.frame_set(frame)
        # update the file slot paths (they append frame numbers automatically)
        out_color.file_slots[0].path = os.path.abspath(
            os.path.join(output_dir, f"{basename}_color_")
        )
        out_normal.file_slots[0].path = os.path.abspath(
            os.path.join(output_dir, f"{basename}_normal_")
        )
        out_depth.file_slots[0].path = os.path.abspath(
            os.path.join(output_dir, f"{basename}_depth_")
        )
        bpy.ops.render.render(write_still=True, use_viewport=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", required=True)
    parser.add_argument("--output_path", required=True)
    args, unknown_args = parser.parse_known_args([x for x in sys.argv if x != "--"])
    print("Arguments:", args)
    print("Unknown Arguments:", unknown_args)

    scene_state = _load_scene_state(args.input_path)
    _create_camera(scene_state)

    _render_frames(args.output_path, start=1, end=1, basename="myshot")
