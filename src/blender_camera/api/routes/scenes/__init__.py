from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

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
            responses={
                201: {"description": "Scene created"},
                400: {"description": "Invalid file format"},
            },
        )

    async def get_scenes(self) -> list[Id]:
        return [scene.id for scene in self._scene_model.get_scenes()]

    async def create_scene(
        self,
        blend_file: Annotated[UploadFile, File(description="Blender file (.blend)")],
    ) -> Id:
        if not blend_file.filename or not blend_file.filename.endswith(".blend"):
            raise HTTPException(status_code=400, detail="File must be a .blend file")

        blend_bytes = await blend_file.read()
        scene = self._scene_model.create_scene(blend_bytes=blend_bytes)

        return scene.id
