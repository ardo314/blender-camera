import uvicorn

from blender_camera.utils import get_log_level


class App:
    def __init__(self):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def start_api(self, host: str, port: int):
        config = uvicorn.Config(None, host=host, port=port, log_level=get_log_level())
        server = uvicorn.Server(config)
        await server.serve()
