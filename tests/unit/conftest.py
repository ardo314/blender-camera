import pytest

from blender_camera.models.camera_model import CameraModel
from blender_camera.models.entity_model import EntityModel
from blender_camera.models.scene_model import SceneModel


@pytest.fixture
def scene_model() -> SceneModel:
    """Create a fresh SceneModel instance for testing."""
    return SceneModel()


@pytest.fixture
def sample_blend_data() -> bytes:
    """Sample blend file data for testing."""
    return b"fake blend file content"


@pytest.fixture
def entity_model() -> EntityModel:
    return EntityModel()


@pytest.fixture
def camera_model(entity_model: EntityModel) -> CameraModel:
    return CameraModel(entity_model)
