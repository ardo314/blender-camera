from typing import Protocol, runtime_checkable

from blender_camera.models.id import Id


@runtime_checkable
class HasId(Protocol):
    id: Id
