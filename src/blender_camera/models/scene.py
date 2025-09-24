from blender_camera.models.camera_model import CameraModel
from blender_camera.models.entity_model import EntityModel


class Scene:
    def __init__(self, id: str):
        self.id = id
        self.entity_model = EntityModel()
        self.camera_model = CameraModel(self.entity_model)
