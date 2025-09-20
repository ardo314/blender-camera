import uvicorn

from blender_camera.api import Api
from blender_camera.app_state import AppState
from blender_camera.utils import get_log_level, get_version


class App:
    def __init__(self):
        self._app_state = AppState()

    async def start(self):
        pass

    async def stop(self):
        pass

    async def start_api(self, host: str, port: int):
        api = Api(get_version(), self._app_state)
        config = uvicorn.Config(
            api.app, host=host, port=port, log_level=get_log_level()
        )
        server = uvicorn.Server(config)
        await server.serve()
