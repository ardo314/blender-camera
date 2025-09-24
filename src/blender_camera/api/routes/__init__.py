from fastapi import APIRouter

from blender_camera.api.routes.scenes import ScenesRouter


class RootRouter:
    def __init__(self, scenes: ScenesRouter):
        self.router = APIRouter()
        self.router.include_router(scenes.router)
        self.router.add_api_route(
            "",
            self._root,
            methods=["GET"],
            response_model=dict,
            responses={200: {"description": "API root message"}},
        )

    async def _root(self):
        return {"message": "Welcome to Blender Camera API"}
