from blender_camera.api import Api
from blender_camera.api.routes import RootRouter
from blender_camera.api.routes.scenes import ScenesRouter
from blender_camera.api.routes.scenes.scene_id import SceneIdRouter
from blender_camera.api.routes.scenes.scene_id.cameras import CamerasRouter
from blender_camera.api.routes.scenes.scene_id.entities import EntitiesRouter
from blender_camera.models.app_state import AppState
from blender_camera.utils import get_base_path, get_version


class App:
    def __init__(self):
        self._app_state = AppState()

        root_router = RootRouter(
            ScenesRouter(SceneIdRouter(EntitiesRouter()), CamerasRouter())
        )
        self._api = Api(get_version(), get_base_path(), root_router)

    async def start(self, host: str, port: int):
        await self._api.start(host, port)

    async def stop(self):
        pass
