from uuid import uuid4

from blender_camera.models.entities.camera import Camera
from blender_camera.models.entity_model import EntityModel
from blender_camera.models.id import Id
from blender_camera.models.pose import Pose


class CameraModel:
    def __init__(self, entity_model: EntityModel):
        self.entity_model = entity_model

    def get_cameras(self) -> list[Camera]:
        return self.entity_model.get_entities_by_type(Camera)

    def create_camera(self, pose: Pose | None = None) -> Camera:
        return self.entity_model.add_entity(
            Camera(id=str(uuid4()), pose=pose or [0, 0, 0, 0, 0, 0])
        )

    def delete_camera(self, camera_id: Id):
        self.entity_model.delete_entity(camera_id)

    def get_camera(self, camera_id: Id) -> Camera | None:
        entity = self.entity_model.get_entity(camera_id)
        if not entity or not isinstance(entity, Camera):
            return None
        return entity
