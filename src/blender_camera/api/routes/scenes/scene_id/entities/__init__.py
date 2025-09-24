from fastapi import APIRouter

from blender_camera.models.entities.entity import Entity


class EntitiesRouter:
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/entities",
            self._get_entites,
            methods=["GET"],
            response_model=list[Entity],
            responses={200: {"description": "List of cameras"}},
        )

    async def _get_entites(self) -> list[Entity]:
        return []
