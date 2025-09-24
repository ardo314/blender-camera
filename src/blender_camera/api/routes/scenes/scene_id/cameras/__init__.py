from fastapi import APIRouter, HTTPException, Response

from blender_camera.api.routes.scenes.scene_id.cameras.camera_id import CameraIdRouter
from blender_camera.models.entities.camera import Camera
from blender_camera.models.scene import Scene
from blender_camera.models.scene_model import SceneModel


class CamerasRouter:
    def __init__(self, camera_id: CameraIdRouter, scene_model: SceneModel):
        self._scene_model = scene_model

        self.router = APIRouter()
        self.router.include_router(camera_id.router)
        self.router.add_api_route(
            "/cameras",
            self._get_cameras,
            methods=["GET"],
            response_model=list[Camera],
            responses={200: {"description": "List of cameras"}},
        )
        self.router.add_api_route(
            "/cameras",
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

    async def _get_cameras(self, scene_id: str) -> list[Camera]:
        return self._get_scene_with_exception(scene_id).camera_model.get_cameras()

    async def _create_camera(self, scene_id: str) -> Camera:
        return self._get_scene_with_exception(scene_id).camera_model.create_camera()
