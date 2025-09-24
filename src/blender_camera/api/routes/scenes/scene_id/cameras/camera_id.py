from fastapi import APIRouter, HTTPException, Response

from blender_camera.models.entities.camera import Camera
from blender_camera.models.pose import Pose, validate_pose


class CameraIdRouter:
    def __init__(self, app_state: AppState):
        self._app_state = app_state

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

    def _get_camera_with_exception(self, camera_id: str) -> Camera:
        camera = self._app_state.get_camera(camera_id)
        if camera is None:
            raise HTTPException(status_code=404, detail="Camera not found")
        return camera

    async def _get_cameras(self) -> list[Camera]:
        return self._app_state.get_cameras()

    async def _create_camera(self) -> Camera:
        return self._app_state.create_camera()

    async def _get_camera(self, camera_id: str) -> Camera:
        return self._get_camera_with_exception(camera_id)

    async def _delete_camera(self, camera_id: str):
        self._app_state.delete_camera(camera_id)

    async def _get_camera_pointcloud(self, blend_url: str, camera_id: str) -> Response:
        camera = self._get_camera_with_exception(camera_id)
        ply_bytes = await render_pointcloud(blend_url, camera)
        return Response(content=ply_bytes, media_type="application/octet-stream")

    async def _get_camera_image(self, blend_url: str, camera_id: str) -> Response:
        camera = self._get_camera_with_exception(camera_id)
        png_bytes = await render_image(blend_url, camera)
        return Response(content=png_bytes, media_type="image/png")
