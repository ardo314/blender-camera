from fastapi import FastAPI, HTTPException

from blender_camera.app_state import AppState, Camera
from blender_camera.blender import render_image, render_pointcloud
from blender_camera.models.pose import Pose, validate_pose


class Api:
    def __init__(self, version: str, app_state: AppState):
        self._app_state = app_state

        self.app = FastAPI(
            title="Blender Camera API",
            description="API for controlling Blender camera operations",
            version=version,
            docs_url="/docs",
            swagger_ui_parameters={"tryItOutEnabled": True},
        )
        self.app.add_api_route("/", self.root, methods=["GET"])
        self.app.add_api_route("/cameras", self.get_cameras, methods=["GET"])
        self.app.add_api_route("/cameras", self.create_camera, methods=["POST"])
        self.app.add_api_route("/cameras/{camera_id}", self.get_camera, methods=["GET"])
        self.app.add_api_route(
            "/cameras/{camera_id}", self.delete_camera, methods=["DELETE"]
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/pose", self.get_camera_pose, methods=["GET"]
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/pose", self.set_camera_pose, methods=["PUT"]
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/pointcloud",
            self.get_camera_pointcloud,
            methods=["GET"],
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/image", self.get_camera_image, methods=["GET"]
        )

    def _get_camera_with_exception(self, camera_id: str) -> Camera:
        camera = self._app_state.get_camera(camera_id)
        if camera is None:
            raise HTTPException(status_code=404, detail="Camera not found")
        return camera

    async def root(self):
        return {"message": "Welcome to Blender Camera API"}

    async def get_cameras(self) -> list[Camera]:
        return self._app_state.get_cameras()

    async def create_camera(self) -> Camera:
        return self._app_state.create_camera()

    async def get_camera(self, camera_id: str) -> Camera:
        return self._get_camera_with_exception(camera_id)

    async def delete_camera(self, camera_id: str):
        self._app_state.delete_camera(camera_id)

    async def get_camera_pose(self, camera_id: str) -> Pose:
        camera = self._get_camera_with_exception(camera_id)
        return camera.pose

    async def set_camera_pose(self, camera_id: str, pose: Pose):
        if validate_pose(pose) is False:
            raise HTTPException(status_code=400, detail="Invalid pose format")

        camera = self._get_camera_with_exception(camera_id)
        camera.pose = pose

    async def get_camera_pointcloud(self, camera_id: str) -> bytes:
        camera = self._get_camera_with_exception(camera_id)
        ply_bytes = render_pointcloud(camera)
        return ply_bytes

    async def get_camera_image(self, camera_id: str) -> bytes:
        camera = self._get_camera_with_exception(camera_id)
        png_bytes = render_image(camera)
        return png_bytes
