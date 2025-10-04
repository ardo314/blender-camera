from unittest.mock import patch

import pytest

from blender_camera.models.camera_intrinsics import CameraIntrinsics
from blender_camera.models.camera_model import CameraModel
from blender_camera.models.entities.camera import Camera
from blender_camera.models.entities.entity import Entity
from blender_camera.models.entity_model import EntityModel


class MockEntity(Entity):
    """Mock non-camera entity for testing."""

    pass


@pytest.fixture
def entity_model():
    """Create a mock EntityModel for testing."""
    return EntityModel()


@pytest.fixture
def camera_model(entity_model: EntityModel):
    """Create a CameraModel instance for testing."""
    return CameraModel(entity_model)


@pytest.fixture
def sample_pose():
    """Sample pose data for testing."""
    return [1.0, 2.0, 3.0, 0.5, 1.5, 2.5]


@pytest.fixture
def sample_camera_intrinsics():
    """Sample camera intrinsics for testing."""
    return CameraIntrinsics(fx=1000.0, fy=1000.0, cx=960.0, cy=540.0)


class TestCameraModel:
    """Test cases for the CameraModel class."""

    def test_camera_model_initialization_should_store_entity_model(self, entity_model):
        """Test that CameraModel stores the entity model reference."""
        # Arrange & Act
        camera_model = CameraModel(entity_model)

        # Assert
        assert camera_model.entity_model is entity_model

    def test_create_camera_with_default_parameters_should_create_camera_with_defaults(
        self, camera_model
    ):
        """Test that create_camera with no parameters creates camera with default values."""
        # Arrange
        # camera_model fixture is already arranged

        # Act
        camera = camera_model.create_camera()

        # Assert
        assert isinstance(camera, Camera)
        assert camera.id is not None
        assert isinstance(camera.id, str)
        assert len(camera.id) > 0
        assert camera.pose == [0, 0, 0, 0, 0, 0]
        assert camera.camera_intrinsics is None

    def test_create_camera_with_pose_should_create_camera_with_specified_pose(
        self, camera_model, sample_pose
    ):
        """Test that create_camera with pose parameter creates camera with specified pose."""
        # Arrange
        # Fixtures already arranged

        # Act
        camera = camera_model.create_camera(pose=sample_pose)

        # Assert
        assert isinstance(camera, Camera)
        assert camera.pose == sample_pose
        assert camera.camera_intrinsics is None

    def test_create_camera_with_intrinsics_should_create_camera_with_specified_intrinsics(
        self, camera_model, sample_camera_intrinsics
    ):
        """Test that create_camera with intrinsics creates camera with specified intrinsics."""
        # Arrange
        # Fixtures already arranged

        # Act
        camera = camera_model.create_camera(camera_intrinsics=sample_camera_intrinsics)

        # Assert
        assert isinstance(camera, Camera)
        assert camera.pose == [0, 0, 0, 0, 0, 0]
        assert camera.camera_intrinsics is sample_camera_intrinsics

    def test_create_camera_with_both_parameters_should_create_camera_with_both(
        self, camera_model, sample_pose, sample_camera_intrinsics
    ):
        """Test that create_camera with both parameters creates camera with both values."""
        # Arrange
        # Fixtures already arranged

        # Act
        camera = camera_model.create_camera(
            pose=sample_pose, camera_intrinsics=sample_camera_intrinsics
        )

        # Assert
        assert isinstance(camera, Camera)
        assert camera.pose == sample_pose
        assert camera.camera_intrinsics is sample_camera_intrinsics

    def test_create_camera_should_add_camera_to_entity_model(self, camera_model):
        """Test that create_camera adds the camera to the entity model."""
        # Arrange
        initial_entities = camera_model.entity_model.get_entities()

        # Act
        camera = camera_model.create_camera()

        # Assert
        entities = camera_model.entity_model.get_entities()
        assert len(entities) == len(initial_entities) + 1
        assert camera in entities

    @patch("blender_camera.models.camera_model.uuid4")
    def test_create_camera_uses_uuid_for_id_generation(self, mock_uuid4, camera_model):
        """Test that create_camera uses uuid4 for ID generation."""
        # Arrange
        expected_id = "test-camera-uuid-id"
        mock_uuid4.return_value = expected_id

        # Act
        camera = camera_model.create_camera()

        # Assert
        assert camera.id == expected_id
        mock_uuid4.assert_called_once()

    def test_create_multiple_cameras_should_have_unique_ids(self, camera_model):
        """Test that multiple cameras created have unique IDs."""
        # Arrange & Act
        camera1 = camera_model.create_camera()
        camera2 = camera_model.create_camera()
        camera3 = camera_model.create_camera()

        # Assert
        ids = {camera1.id, camera2.id, camera3.id}
        assert len(ids) == 3  # All IDs should be unique

    def test_camera_model_delegates_to_entity_model_correctly(self, entity_model):
        """Test that CameraModel properly delegates operations to EntityModel."""
        # Arrange
        camera_model = CameraModel(entity_model)

        # Act
        camera = camera_model.create_camera()
        cameras_from_entity_model = entity_model.get_entities_by_type(Camera)

        # Assert
        assert len(cameras_from_entity_model) == 1
        assert camera in cameras_from_entity_model
        assert camera in entity_model.get_entities()
