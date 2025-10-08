from fastapi import APIRouter, HTTPException

from blender_camera.api.routes.scenes.scene_id.cameras import CamerasRouter
from blender_camera.api.routes.scenes.scene_id.entities import EntitiesRouter
from blender_camera.models import scene
from blender_camera.models.scene import Scene
from blender_camera.models.scene_model import SceneModel


class SceneIdRouter:
    def __init__(
        self, entities: EntitiesRouter, cameras: CamerasRouter, scene_model: SceneModel
    ):
        self._scene_model = scene_model

        self.router = APIRouter(prefix="/{scene_id}")
        self.router.include_router(entities.router)
        self.router.include_router(cameras.router)
        self.router.add_api_route(
            "",
            self._delete_scene,
            methods=["DELETE"],
            responses={
                204: {"description": "Scene deleted"},
                404: {"description": "Scene not found"},
            },
        )

    def _delete_scene(self, scene_id: str) -> None:
        self._scene_model.delete_scene(scene_id)
