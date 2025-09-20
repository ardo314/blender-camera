from uuid import uuid4
from blender_camera.models.camera import Camera, Id


class AppState:
    def __init__(self):
        self.cameras: dict[Id, Camera] = {}

    def get_cameras(self) -> list[Camera]:
        return list(self.cameras.values())

    def create_camera(self) -> Camera:
        camera_id = str(uuid4())
        self.cameras[camera_id] = Camera(id=camera_id, pose=[0, 0, 0, 0, 0, 0])
        return self.cameras[camera_id]

    def delete_camera(self, camera_id: Id):
        if camera_id not in self.cameras:
            return
        del self.cameras[camera_id]

    def get_camera(self, camera_id: Id) -> Camera | None:
        if camera_id not in self.cameras:
            return None
        return self.cameras[camera_id]
