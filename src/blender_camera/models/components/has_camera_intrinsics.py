from typing import Protocol, runtime_checkable

from blender_camera.models.camera_intrinsics import CameraIntrinsics


@runtime_checkable
class HasCameraIntrinsics(Protocol):
    camera_intrinsics: CameraIntrinsics
