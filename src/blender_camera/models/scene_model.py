from uuid import uuid4

from blender_camera.models.id import Id
from blender_camera.models.scene import Scene


class SceneModel:
    def __init__(self):
        self._scenes: dict[Id, Scene] = {}

    def get_scenes(self) -> list[Scene]:
        return list(self._scenes.values())

    def create_scene(self) -> Scene:
        id = str(uuid4())
        self._scenes[id] = Scene(id=id)
        return self._scenes[id]

    def get_scene(self, scene_id: Id) -> Scene | None:
        if scene_id not in self._scenes:
            return None
        return self._scenes[scene_id]

    def delete_scene(self, scene_id: Id):
        if scene_id not in self._scenes:
            return
        del self._scenes[scene_id]
