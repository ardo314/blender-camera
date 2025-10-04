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
    light_data.energy = 1000.0  # Increase light power significantly
    light_obj = bpy.data.objects.new(name="CameraFlash", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)

    # Position light slightly offset from camera for better illumination
    light_obj.location = (
        cam_obj.location.x + 1,
        cam_obj.location.y + 1,
        cam_obj.location.z + 1,
    )

    # Also add a sun light for overall scene illumination
    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.energy = 5.0
    sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (0, 0, 10)
    sun_obj.rotation_euler = (0.785, 0, 0.785)  # 45 degrees on X and Z axes

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
    - File Output for color, normal, depth (EXR for precision)
    - Additional PNG outputs for color and normal (for easy verification)
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

    # Additional PNG outputs for easy verification
    out_color_png = nodes.new(type="CompositorNodeOutputFile")
    out_color_png.label = "FileOut_Color_PNG"
    out_color_png.location = (600, 200)

    out_normal_png = nodes.new(type="CompositorNodeOutputFile")
    out_normal_png.label = "FileOut_Normal_PNG"
    out_normal_png.location = (600, 0)

    # Set base path to the output directory
    out_color.base_path = output_dir
    out_normal.base_path = output_dir
    out_depth.base_path = output_dir
    out_color_png.base_path = output_dir
    out_normal_png.base_path = output_dir

    # Configure formats (you can choose PNG, EXR, etc.)
    # For depth and normal we often want float formats (EXR)
    for node in (out_color, out_normal, out_depth):
        fmt = node.format
        fmt.file_format = "OPEN_EXR"
        fmt.color_depth = "32"
        # For depth you could also force BW or keep RGBA
        # fmt.color_mode = 'BW'  # optional

    # Configure PNG formats for easy verification
    for node in (out_color_png, out_normal_png):
        fmt = node.format
        fmt.file_format = "PNG"
        fmt.color_depth = "8"
        fmt.color_mode = "RGBA"

    # Link outputs
    links.new(rl.outputs["Image"], out_color.inputs[0])
    links.new(rl.outputs["Normal"], out_normal.inputs[0])
    links.new(map_depth.outputs["Value"], out_depth.inputs[0])

    # Link PNG outputs
    links.new(rl.outputs["Image"], out_color_png.inputs[0])
    links.new(rl.outputs["Normal"], out_normal_png.inputs[0])

    # Set the filename patterns for naming using default slots (index 0)
    out_color.file_slots[0].path = basename + "_color_"
    out_normal.file_slots[0].path = basename + "_normal_"
    out_depth.file_slots[0].path = basename + "_depth_"
    out_color_png.file_slots[0].path = basename + "_color_png_"
    out_normal_png.file_slots[0].path = basename + "_normal_png_"

    return out_color, out_normal, out_depth


def _setup_materials():
    """Ensure all objects have materials that respond to lighting."""
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data:
            # If object has no materials, create a basic one
            if not obj.data.materials:
                mat = bpy.data.materials.new(name=f"{obj.name}_Material")
                mat.use_nodes = True

                # Get the principled BSDF node (default in new materials)
                nodes = mat.node_tree.nodes
                principled = nodes.get("Principled BSDF")
                if principled:
                    # Set a neutral color and proper roughness
                    principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
                    principled.inputs["Roughness"].default_value = 0.5
                    principled.inputs["Metallic"].default_value = 0.0

                obj.data.materials.append(mat)
            else:
                # Ensure existing materials use nodes
                for mat in obj.data.materials:
                    if mat:
                        mat.use_nodes = True


def _render_frames(output_dir: str, start: int, end: int, basename: str):
    """
    Render frames in the given range, writing color/normal/depth for each frame.
    """
    scene = bpy.context.scene

    # Set render engine to Cycles for better lighting
    scene.render.engine = "CYCLES"

    # Configure Cycles settings for good quality
    scene.cycles.samples = 128  # Reasonable sample count
    scene.cycles.use_denoising = (
        False  # Disable denoising since build doesn't support it
    )

    # Ensure proper world lighting if no world material exists
    if not scene.world:
        world = bpy.data.worlds.new("World")
        scene.world = world

    # Set up a basic world shader for ambient lighting
    if scene.world and not scene.world.use_nodes:
        scene.world.use_nodes = True
        world_nodes = scene.world.node_tree.nodes
        world_links = scene.world.node_tree.links

        # Clear existing nodes
        for node in world_nodes:
            world_nodes.remove(node)

        # Add Background shader
        bg_node = world_nodes.new(type="ShaderNodeBackground")
        bg_node.inputs["Color"].default_value = (
            0.2,
            0.2,
            0.2,
            1.0,
        )  # Dim ambient light
        bg_node.inputs["Strength"].default_value = 0.5

        # Add World Output
        output_node = world_nodes.new(type="ShaderNodeOutputWorld")

        # Connect them
        world_links.new(bg_node.outputs["Background"], output_node.inputs["Surface"])

    rl = scene.view_layers.items()[0][1]
    _setup_passes(rl)

    tree, nodes, links = _clear_compositor_nodes(scene)
    out_color, out_normal, out_depth = _build_compositor(
        tree, nodes, links, output_dir, basename
    )

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # Disable the default render output since we're using compositor File Output nodes
    scene.render.filepath = ""

    # Use a float format globally (EXR) to preserve precision
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.render.use_multiview = False  # unless stereo
    # Use compositing
    scene.use_nodes = True

    for frame in range(start, end + 1):
        scene.frame_set(frame)
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
    _setup_materials()  # Ensure proper materials for lighting

    _render_frames(args.output_path, 1, 1, "frame")
