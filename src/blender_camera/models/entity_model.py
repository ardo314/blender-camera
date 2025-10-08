from blender_camera.models.entities.entity import Entity
from blender_camera.models.id import Id


class EntityModel:
    def __init__(self):
        self._entities: dict[Id, Entity] = {}

    def get_entities(self) -> list[Entity]:
        return list(self._entities.values())

    def get_entities_by_type[T: Entity](self, entity_type: type[T]) -> list[T]:
        return [
            entity
            for entity in self._entities.values()
            if isinstance(entity, entity_type)
        ]

    def add_entity[T: Entity](self, entity: T):
        self._entities[entity.id] = entity
        return entity

    def get_entity(self, entity_id: Id) -> Entity | None:
        if entity_id not in self._entities:
            return None
        return self._entities[entity_id]

    def delete_entity(self, entity_id: Id):
        if entity_id not in self._entities:
            return
        del self._entities[entity_id]
