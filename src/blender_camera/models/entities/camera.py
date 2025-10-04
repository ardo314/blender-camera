from typing import Optional, Union

from blender_camera.models.camera_intrinsics import CameraIntrinsics
from blender_camera.models.components.has_camera_intrinsics import HasCameraIntrinsics
from blender_camera.models.components.has_id import HasId
from blender_camera.models.components.has_pose import HasPose
from blender_camera.models.entities.entity import Entity
from blender_camera.models.pose import Pose

CameraLike = Union[HasId, HasPose, Optional[HasCameraIntrinsics]]


class Camera(Entity):
    pose: Pose
    camera_intrinsics: CameraIntrinsics | None
