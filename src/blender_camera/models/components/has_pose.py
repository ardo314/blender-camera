from typing import Protocol, runtime_checkable

from blender_camera.models.pose import Pose


@runtime_checkable
class HasPose(Protocol):
    pose: Pose
