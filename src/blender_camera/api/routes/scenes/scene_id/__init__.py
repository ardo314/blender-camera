from fastapi import APIRouter, HTTPException

from blender_camera.api.routes.scenes.scene_id.cameras import CamerasRouter
from blender_camera.api.routes.scenes.scene_id.entities import EntitiesRouter
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

    def get_scene_with_http_exception(self, scene_id: str) -> Scene:
        scene = self._scene_model.get_scene(scene_id)
        if scene is None:
            raise HTTPException(status_code=404, detail="Scene not found")
        return scene

    def get_scene_id(self, scene_id: str) -> str:
        scene = self.get_scene_with_http_exception(scene_id)
        return scene.id
