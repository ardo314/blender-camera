from fastapi import APIRouter, HTTPException

from blender_camera.api.routes.scenes.scene_id.entities.entity_id import EntityIdRouter
from blender_camera.models.entities.entity import Entity
from blender_camera.models.entity_model import EntityModel
from blender_camera.models.id import Id
from blender_camera.models.scene_model import SceneModel


class EntitiesRouter:
    def __init__(self, entity_id: EntityIdRouter, scene_model: SceneModel):
        self._entity_id = entity_id
        self._scene_model = scene_model

        self.router = APIRouter(prefix="/entities")
        self.router.include_router(entity_id.router)
        self.router.add_api_route(
            "",
            self._get_entities,
            methods=["GET"],
            responses={
                200: {"description": "List of entities"},
                404: {"description": "Scene not found"},
            },
        )

    def _get_entity_model_with_http_exception(self, scene_id: Id) -> EntityModel:
        scene = self._scene_model.get_scene(scene_id)
        if scene is None:
            raise HTTPException(status_code=404, detail="Scene not found")
        return scene.entity_model

    async def _get_entities(self, scene_id: str):
        entity_model = self._get_entity_model_with_http_exception(scene_id)
        entities = entity_model.get_entities()
        return [entity.model_dump() for entity in entities]
