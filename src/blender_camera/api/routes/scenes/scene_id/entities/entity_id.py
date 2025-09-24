from fastapi import APIRouter, HTTPException, Response

from blender_camera.models.entities.entity import Entity
from blender_camera.models.pose import Pose, validate_pose


class EntityIdRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/{entity_id}")

        self.router.add_api_route(
            "",
            self._get_entity,
            methods=["GET"],
            response_model=Entity,
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

    def _get_entity_with_http_exception(self, entity_id: str) -> Entity:
        entity = self._app_state.get_entity(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity

    async def _get_entity(self, entity_id: str) -> Entity:
        return self._get_entity_with_http_exception(entity_id)

    async def _delete_entity(self, entity_id: str) -> Response:
        self._get_entity_with_http_exception(entity_id)
        self._app_state.delete_entity(entity_id)
        return Response(status_code=204)

    async def _get_entity_pose(self, entity_id: str) -> Pose:
        entity = self._get_entity_with_http_exception(entity_id)
        return entity.pose

    async def _set_entity_pose(self, entity_id: str, pose: Pose):
        if validate_pose(pose) is False:
            raise HTTPException(status_code=400, detail="Invalid pose format")

        entity = self._app_state.get_entity(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")

        entity.pose = pose
