import pytest

from blender_camera.models.camera_intrinsics import CameraIntrinsics
from blender_camera.models.entities.camera import Camera
from blender_camera.models.entities.entity import Entity
from blender_camera.models.entity_model import EntityModel


class MockEntity(Entity):
    """Mock entity class for testing."""

    pass


class MockCamera(Camera):
    """Mock camera class for testing."""

    pose: list[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    camera_intrinsics: CameraIntrinsics | None = None


@pytest.fixture
def entity_model():
    """Create a fresh EntityModel instance for testing."""
    return EntityModel()


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    return MockEntity(id="test-entity-1")


@pytest.fixture
def sample_camera():
    """Create a sample camera entity for testing."""
    return MockCamera(id="test-camera-1")


class TestEntityModel:
    """Test cases for the EntityModel class."""

    def test_entity_model_initialization_should_create_empty_entities_dict(self):
        """Test that EntityModel initializes with an empty entities dictionary."""
        # Arrange & Act
        entity_model = EntityModel()

        # Assert
        assert entity_model._entities == {}
        assert isinstance(entity_model._entities, dict)

    def test_get_entities_with_empty_model_should_return_empty_list(
        self, entity_model: EntityModel
    ):
        """Test that get_entities returns empty list when no entities exist."""
        # Arrange
        # entity_model fixture is already arranged

        # Act
        entities = entity_model.get_entities()

        # Assert
        assert entities == []
        assert isinstance(entities, list)

    def test_add_entity_should_store_entity_and_return_it(
        self, entity_model: EntityModel, sample_entity: MockEntity
    ):
        """Test that add_entity stores the entity and returns it."""
        # Arrange
        # Fixtures already arranged

        # Act
        result = entity_model.add_entity(sample_entity)

        # Assert
        assert result is sample_entity
        assert sample_entity.id in entity_model._entities
        assert entity_model._entities[sample_entity.id] is sample_entity

    def test_get_entities_after_adding_entities_should_return_all_entities(
        self, entity_model: EntityModel
    ):
        """Test that get_entities returns all added entities."""
        # Arrange
        entity1 = MockEntity(id="entity-1")
        entity2 = MockEntity(id="entity-2")
        entity_model.add_entity(entity1)
        entity_model.add_entity(entity2)

        # Act
        entities = entity_model.get_entities()

        # Assert
        assert len(entities) == 2
        assert entity1 in entities
        assert entity2 in entities

    def test_get_entities_by_type_should_return_only_matching_type(
        self, entity_model: EntityModel
    ):
        """Test that get_entities_by_type returns only entities of the specified type."""
        # Arrange
        entity = MockEntity(id="entity-1")
        camera = MockCamera(id="camera-1")
        entity_model.add_entity(entity)
        entity_model.add_entity(camera)

        # Act
        cameras = entity_model.get_entities_by_type(MockCamera)
        entities = entity_model.get_entities_by_type(MockEntity)

        # Assert
        assert len(cameras) == 1
        assert camera in cameras
        assert entity not in cameras

        # MockEntity type only returns MockEntity instances
        assert len(entities) == 1
        assert entity in entities
        assert camera not in entities

    def test_get_entities_by_type_with_no_matching_entities_should_return_empty_list(
        self, entity_model: EntityModel, sample_entity: MockEntity
    ):
        """Test that get_entities_by_type returns empty list when no entities match."""
        # Arrange
        entity_model.add_entity(sample_entity)

        # Act
        cameras = entity_model.get_entities_by_type(MockCamera)

        # Assert
        assert cameras == []

    def test_get_entity_with_existing_id_should_return_entity(
        self, entity_model: EntityModel, sample_entity: MockEntity
    ):
        """Test that get_entity returns the correct entity for an existing ID."""
        # Arrange
        entity_model.add_entity(sample_entity)

        # Act
        retrieved_entity = entity_model.get_entity(sample_entity.id)

        # Assert
        assert retrieved_entity is sample_entity
        assert retrieved_entity.id == sample_entity.id

    def test_get_entity_with_nonexistent_id_should_return_none(
        self, entity_model: EntityModel
    ):
        """Test that get_entity returns None for non-existent entity ID."""
        # Arrange
        nonexistent_id = "nonexistent-id"

        # Act
        result = entity_model.get_entity(nonexistent_id)

        # Assert
        assert result is None

    def test_delete_entity_should_remove_entity_from_dict(
        self, entity_model: EntityModel, sample_entity: MockEntity
    ):
        """Test that delete_entity removes the entity from the internal dictionary."""
        # Arrange
        entity_model.add_entity(sample_entity)
        entity_id = sample_entity.id

        # Verify entity exists before deletion
        assert entity_id in entity_model._entities

        # Act
        entity_model.delete_entity(entity_id)

        # Assert
        assert entity_id not in entity_model._entities

    def test_delete_entity_with_nonexistent_id_should_not_raise_error(
        self, entity_model: EntityModel
    ):
        """Test that delete_entity handles non-existent IDs gracefully."""
        # Arrange
        nonexistent_id = "nonexistent-id"

        # Act & Assert (should not raise)
        entity_model.delete_entity(nonexistent_id)

    def test_add_multiple_entities_of_different_types(self, entity_model: EntityModel):
        """Test adding multiple entities of different types."""
        # Arrange
        entity1 = MockEntity(id="entity-1")
        entity2 = MockEntity(id="entity-2")
        camera1 = MockCamera(id="camera-1")
        camera2 = MockCamera(id="camera-2")

        # Act
        entity_model.add_entity(entity1)
        entity_model.add_entity(entity2)
        entity_model.add_entity(camera1)
        entity_model.add_entity(camera2)

        # Assert
        all_entities = entity_model.get_entities()
        cameras = entity_model.get_entities_by_type(MockCamera)
        mock_entities = entity_model.get_entities_by_type(MockEntity)
        base_entities = entity_model.get_entities_by_type(Entity)

        assert len(all_entities) == 4
        assert len(cameras) == 2
        assert camera1 in cameras
        assert camera2 in cameras
        assert len(mock_entities) == 2
        assert entity1 in mock_entities
        assert entity2 in mock_entities
        assert len(base_entities) == 4  # All inherit from Entity
        assert entity1 in base_entities
        assert entity2 in base_entities
        assert camera1 in base_entities
        assert camera2 in base_entities

    def test_entity_model_maintains_type_information(self, entity_model: EntityModel):
        """Test that the entity model maintains proper type information."""
        # Arrange
        camera = MockCamera(id="camera-1")
        entity_model.add_entity(camera)

        # Act
        retrieved = entity_model.get_entity("camera-1")
        cameras = entity_model.get_entities_by_type(MockCamera)

        # Assert
        assert isinstance(retrieved, MockCamera)
        assert isinstance(retrieved, Camera)
        assert isinstance(retrieved, Entity)
        assert len(cameras) == 1
        assert isinstance(cameras[0], MockCamera)
