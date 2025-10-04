from uuid import uuid4

from blender_camera.models.camera_intrinsics import CameraIntrinsics
from blender_camera.models.entities.camera import Camera
from blender_camera.models.entity_model import EntityModel
from blender_camera.models.pose import Pose


class CameraModel:
    def __init__(self, entity_model: EntityModel):
        self.entity_model = entity_model

    def create_camera(
        self,
        pose: Pose | None = None,
        camera_intrinsics: CameraIntrinsics | None = None,
    ) -> Camera:
        return self.entity_model.add_entity(
            Camera(
                id=str(uuid4()),
                pose=pose or [0, 0, 0, 0, 0, 0],
                camera_intrinsics=camera_intrinsics,
            )
        )
