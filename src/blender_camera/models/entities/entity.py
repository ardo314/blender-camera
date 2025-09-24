from pydantic import BaseModel

from blender_camera.models.components.has_id import HasId
from blender_camera.models.id import Id


class Entity(BaseModel):
    id: Id
