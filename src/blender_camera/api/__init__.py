import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from blender_camera.api.routes.scenes import ScenesRouter
from blender_camera.utils import get_log_level


class Api:
    def __init__(self, version: str, base_path: str, scenes: ScenesRouter):
        self._version = version
        self._base_path = base_path

        self._api = FastAPI(
            title="Blender Camera API",
            description="API for controlling Blender camera operations",
            version=version,
            root_path=base_path,
            docs_url="/docs",
            swagger_ui_parameters={"tryItOutEnabled": True},
        )
        self._api.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._api.include_router(scenes.router)
        self._api.add_api_route(
            "",
            self._root,
            methods=["GET"],
            response_model=dict,
            responses={200: {"description": "API root message"}},
        )

    async def start(self, host: str, port: int):
        config = uvicorn.Config(
            self._api, host=host, port=port, log_level=get_log_level()
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def _root(self):
        return {"message": "Welcome to Blender Camera API"}
