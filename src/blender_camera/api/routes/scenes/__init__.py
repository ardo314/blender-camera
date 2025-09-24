from fastapi import APIRouter

from blender_camera.api.routes.scenes.scene_id import SceneIdRouter
from blender_camera.models.id import Id
from blender_camera.models.scene_model import SceneModel


class ScenesRouter:
    def __init__(self, sceneId: SceneIdRouter, scene_model: SceneModel):
        self._scene_model = scene_model

        self.router = APIRouter(prefix="/scenes")
        self.router.include_router(sceneId.router)
        self.router.add_api_route(
            "",
            self.get_scenes,
            methods=["GET"],
            response_model=list[Id],
            responses={200: {"description": "List of scene IDs"}},
        )
        self.router.add_api_route(
            "",
            self.create_scene,
            methods=["POST"],
            response_model=Id,
            responses={201: {"description": "Scene created"}},
        )

    async def get_scenes(self) -> list[Id]:
        return [scene.id for scene in self._scene_model.get_scenes()]

    async def create_scene(self) -> Id:
        scene = self._scene_model.create_scene()
        return scene.id
