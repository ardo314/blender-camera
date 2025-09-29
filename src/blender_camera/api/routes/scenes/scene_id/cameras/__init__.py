from fastapi import APIRouter, HTTPException

from blender_camera.models.entities.camera import Camera
from blender_camera.models.scene import Scene
from blender_camera.models.scene_model import SceneModel


class CamerasRouter:
    def __init__(self, scene_model: SceneModel):
        self._scene_model = scene_model

        self.router = APIRouter(prefix="/cameras")
        self.router.add_api_route(
            "",
            self._create_camera,
            methods=["POST"],
            response_model=Camera,
            responses={201: {"description": "Camera created"}},
        )

    def _get_scene_with_exception(self, scene_id: str) -> Scene:
        scene = self._scene_model.get_scene(scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        return scene

    async def _create_camera(self, scene_id: str) -> Camera:
        return self._get_scene_with_exception(scene_id).camera_model.create_camera()
