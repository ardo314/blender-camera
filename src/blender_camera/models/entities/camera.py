from blender_camera.models.camera_intrinsics import CameraIntrinsics
from blender_camera.models.entities.entity import Entity
from blender_camera.models.pose import Pose


class Camera(Entity):
    pose: Pose
    camera_intrinsics: CameraIntrinsics | None
