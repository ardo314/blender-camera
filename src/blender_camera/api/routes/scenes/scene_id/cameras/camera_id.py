from fastapi import APIRouter, HTTPException, Response

from blender_camera.blender import Blender
from blender_camera.models.camera_model import CameraModel
from blender_camera.models.entities.camera import Camera
from blender_camera.models.id import Id
from blender_camera.models.scene_model import SceneModel


class CameraIdRouter:
    def __init__(self, scene_model: SceneModel):
        self._scene_model = scene_model

        self.router = APIRouter(prefix="/{camera_id}")
        self.router.add_api_route(
            "",
            self._get_camera,
            methods=["GET"],
            response_model=Camera,
            responses={
                200: {"description": "Camera details"},
                404: {"description": "Camera not found"},
            },
        )
        self.router.add_api_route(
            "/pointcloud",
            self._get_camera_pointcloud,
            methods=["GET"],
            response_class=Response,
            responses={
                200: {
                    "description": "Pointcloud data",
                    "content": {"application/octet-stream": {}},
                },
                404: {"description": "Camera not found"},
            },
        )
        self.router.add_api_route(
            "/image",
            self._get_camera_image,
            methods=["GET"],
            response_class=Response,
            responses={
                200: {"description": "Rendered image", "content": {"image/png": {}}},
                404: {"description": "Camera not found"},
            },
        )

    def _get_camera_model_with_http_exception(self, scene_id: Id) -> CameraModel:
        scene = self._scene_model.get_scene(scene_id)
        if scene is None:
            raise HTTPException(status_code=404, detail="Scene not found")
        return scene.camera_model

    def _get_camera_with_http_exception(self, scene_id: Id, camera_id: Id) -> Camera:
        camera_model = self._get_camera_model_with_http_exception(scene_id)
        camera = camera_model.get_camera(camera_id)
        if camera is None:
            raise HTTPException(status_code=404, detail="Camera not found")
        return camera

    async def _get_camera(self, scene_id: Id, camera_id: Id) -> Camera:
        return self._get_camera_with_http_exception(scene_id, camera_id)

    async def _get_camera_pointcloud(self, scene_id: Id, camera_id: Id) -> Response:
        camera = self._get_camera_with_http_exception(scene_id, camera_id)
        blender = Blender("untitled.blend")
        ply_bytes = await blender.render_ply(camera)
        return Response(content=ply_bytes, media_type="application/octet-stream")

    async def _get_camera_image(self, scene_id: Id, camera_id: Id) -> Response:
        camera = self._get_camera_with_http_exception(scene_id, camera_id)
        blender = Blender("untitled.blend")
        png_bytes = await blender.render_png(camera)
        return Response(content=png_bytes, media_type="image/png")
