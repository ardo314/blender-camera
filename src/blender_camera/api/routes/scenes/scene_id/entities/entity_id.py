from fastapi import APIRouter, HTTPException, Response

from blender_camera.blender import Blender
from blender_camera.models.components.has_pose import HasPose
from blender_camera.models.entities.entity import Entity
from blender_camera.models.entity_model import EntityModel
from blender_camera.models.id import Id
from blender_camera.models.pose import Pose, validate_pose
from blender_camera.models.scene_model import SceneModel


class EntityIdRouter:
    def __init__(self, scene_model: SceneModel):
        self._scene_model = scene_model

        self.router = APIRouter(prefix="/{entity_id}")
        self.router.add_api_route(
            "",
            self._get_entity,
            methods=["GET"],
            responses={
                200: {"description": "Entity details"},
                404: {"description": "Entity not found"},
            },
        )
        self.router.add_api_route(
            "",
            self._delete_entity,
            methods=["DELETE"],
            responses={
                204: {"description": "Entity deleted"},
                404: {"description": "Entity not found"},
            },
        )
        self.router.add_api_route(
            "/pose",
            self._get_entity_pose,
            methods=["GET"],
            response_model=Pose,
            responses={
                200: {"description": "Entity pose"},
                404: {"description": "Entity not found"},
            },
        )
        self.router.add_api_route(
            "/pose",
            self._set_entity_pose,
            methods=["PUT"],
            response_model=None,
            responses={
                204: {"description": "Pose updated"},
                400: {"description": "Invalid pose format"},
                404: {"description": "Entity not found"},
            },
        )
        self.router.add_api_route(
            "/pointcloud",
            self._get_entity_pointcloud,
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
            self._get_entity_image,
            methods=["GET"],
            response_class=Response,
            responses={
                200: {"description": "Rendered image", "content": {"image/png": {}}},
                404: {"description": "Camera not found"},
            },
        )

    def _get_entity_model_with_http_exception(self, scene_id: Id) -> EntityModel:
        scene = self._scene_model.get_scene(scene_id)
        if scene is None:
            raise HTTPException(status_code=404, detail="Scene not found")
        return scene.entity_model

    def _get_entity_with_http_exception(self, scene_id: Id, entity_id: Id) -> Entity:
        entity_model = self._get_entity_model_with_http_exception(scene_id)
        entity = entity_model.get_entity(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity

    async def _get_entity(self, scene_id: Id, entity_id: Id):
        entity = self._get_entity_with_http_exception(scene_id, entity_id)
        return entity.model_dump()

    async def _delete_entity(self, scene_id: Id, entity_id: Id) -> None:
        entity_model = self._get_entity_model_with_http_exception(scene_id)
        entity_model.delete_entity(entity_id)

    async def _get_entity_pose(self, scene_id: Id, entity_id: Id) -> Pose:
        entity = self._get_entity_with_http_exception(scene_id, entity_id)
        if not isinstance(entity, HasPose):
            raise HTTPException(status_code=400, detail="Entity has no pose")
        return entity.pose

    async def _set_entity_pose(self, scene_id: Id, entity_id: Id, pose: Pose):
        entity = self._get_entity_with_http_exception(scene_id, entity_id)
        if not isinstance(entity, HasPose):
            raise HTTPException(status_code=400, detail="Entity has no pose")

        if not validate_pose(pose):
            raise HTTPException(status_code=400, detail="Invalid pose format")

        entity.pose = pose

    async def _get_entity_pointcloud(self, scene_id: Id, entity_id: Id) -> Response:
        camera = self._get_entity_with_http_exception(scene_id, entity_id)
        blender = Blender("untitled.blend")
        ply_bytes = await blender.render_ply(camera)
        return Response(content=ply_bytes, media_type="application/octet-stream")

    async def _get_entity_image(self, scene_id: Id, entity_id: Id) -> Response:
        camera = self._get_entity_with_http_exception(scene_id, entity_id)
        blender = Blender("untitled.blend")
        png_bytes = await blender.render_png(camera)
        return Response(content=png_bytes, media_type="image/png")
