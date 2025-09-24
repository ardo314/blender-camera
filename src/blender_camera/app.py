from blender_camera.api import Api
from blender_camera.api.routes.scenes import ScenesRouter
from blender_camera.api.routes.scenes.scene_id import SceneIdRouter
from blender_camera.api.routes.scenes.scene_id.cameras import CamerasRouter
from blender_camera.api.routes.scenes.scene_id.cameras.camera_id import CameraIdRouter
from blender_camera.api.routes.scenes.scene_id.entities import EntitiesRouter
from blender_camera.api.routes.scenes.scene_id.entities.entity_id import EntityIdRouter
from blender_camera.models.scene_model import SceneModel
from blender_camera.utils import get_base_path, get_version


class App:
    def __init__(self):
        scene_model = SceneModel()

        scenes_router = ScenesRouter(
            SceneIdRouter(
                EntitiesRouter(EntityIdRouter(scene_model), scene_model),
                CamerasRouter(CameraIdRouter(scene_model), scene_model),
                scene_model,
            ),
            scene_model,
        )
        self._api = Api(get_version(), get_base_path(), scenes_router)

    async def start(self, host: str, port: int):
        await self._api.start(host, port)

    async def stop(self):
        pass
