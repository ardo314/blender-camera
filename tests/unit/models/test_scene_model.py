import os
from unittest.mock import Mock, patch

from blender_camera.models.scene import Scene
from blender_camera.models.scene_model import SceneModel


class TestSceneModel:
    """Test cases for the SceneModel class."""

    def test_scene_model_initialization_should_create_empty_scenes_dict(self):
        """Test that SceneModel initializes with an empty scenes dictionary."""
        # Arrange & Act
        scene_model = SceneModel()

        # Assert
        assert scene_model._scenes == {}
        assert isinstance(scene_model._scenes, dict)

    def test_get_scenes_with_empty_model_should_return_empty_list(
        self, scene_model: SceneModel
    ):
        """Test that get_scenes returns empty list when no scenes exist."""
        # Arrange
        # scene_model fixture is already arranged

        # Act
        scenes = scene_model.get_scenes()

        # Assert
        assert scenes == []
        assert isinstance(scenes, list)

    def test_create_scene_should_return_scene_with_valid_id_and_path(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that create_scene creates a scene with valid ID and blend file path."""
        # Arrange
        # Fixtures already arranged

        # Act
        scene = scene_model.create_scene(sample_blend_data)

        # Assert
        assert isinstance(scene, Scene)
        assert scene.id is not None
        assert isinstance(scene.id, str)
        assert len(scene.id) > 0
        assert scene.blend_path.endswith(".blend")
        assert os.path.exists(scene.blend_path)

        # Cleanup
        if os.path.exists(scene.blend_path):
            os.remove(scene.blend_path)

    def test_create_scene_should_write_blend_data_to_file(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that create_scene writes the blend data to the file system."""
        # Arrange
        # Fixtures already arranged

        # Act
        scene = scene_model.create_scene(sample_blend_data)

        # Assert
        with open(scene.blend_path, "rb") as f:
            content = f.read()
        assert content == sample_blend_data

        # Cleanup
        if os.path.exists(scene.blend_path):
            os.remove(scene.blend_path)

    def test_create_scene_should_add_scene_to_internal_dict(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that create_scene adds the scene to the internal scenes dictionary."""
        # Arrange
        # Fixtures already arranged

        # Act
        scene = scene_model.create_scene(sample_blend_data)

        # Assert
        assert scene.id in scene_model._scenes
        assert scene_model._scenes[scene.id] is scene

        # Cleanup
        if os.path.exists(scene.blend_path):
            os.remove(scene.blend_path)

    def test_get_scenes_after_creating_scenes_should_return_all_scenes(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that get_scenes returns all created scenes."""
        # Arrange
        scene1 = scene_model.create_scene(sample_blend_data)
        scene2 = scene_model.create_scene(sample_blend_data)

        # Act
        scenes = scene_model.get_scenes()

        # Assert
        assert len(scenes) == 2
        assert scene1 in scenes
        assert scene2 in scenes

        # Cleanup
        for scene in scenes:
            if os.path.exists(scene.blend_path):
                os.remove(scene.blend_path)

    def test_get_scene_with_existing_id_should_return_scene(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that get_scene returns the correct scene for an existing ID."""
        # Arrange
        scene = scene_model.create_scene(sample_blend_data)

        # Act
        retrieved_scene = scene_model.get_scene(scene.id)

        # Assert
        assert retrieved_scene is scene
        assert retrieved_scene.id == scene.id

        # Cleanup
        if os.path.exists(scene.blend_path):
            os.remove(scene.blend_path)

    def test_get_scene_with_nonexistent_id_should_return_none(
        self, scene_model: SceneModel
    ):
        """Test that get_scene returns None for non-existent scene ID."""
        # Arrange
        nonexistent_id = "nonexistent-id"

        # Act
        result = scene_model.get_scene(nonexistent_id)

        # Assert
        assert result is None

    def test_delete_scene_should_remove_scene_from_dict_and_delete_file(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that delete_scene removes the scene and deletes the blend file."""
        # Arrange
        scene = scene_model.create_scene(sample_blend_data)
        scene_id = scene.id
        blend_path = scene.blend_path

        # Verify file exists before deletion
        assert os.path.exists(blend_path)
        assert scene_id in scene_model._scenes

        # Act
        scene_model.delete_scene(scene_id)

        # Assert
        assert scene_id not in scene_model._scenes
        assert not os.path.exists(blend_path)

    def test_delete_scene_with_nonexistent_id_should_not_raise_error(
        self, scene_model: SceneModel
    ):
        """Test that delete_scene handles non-existent IDs gracefully."""
        # Arrange
        nonexistent_id = "nonexistent-id"

        # Act & Assert (should not raise)
        scene_model.delete_scene(nonexistent_id)

    def test_delete_scene_with_missing_file_should_not_raise_error(
        self, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that delete_scene handles missing blend files gracefully."""
        # Arrange
        scene = scene_model.create_scene(sample_blend_data)
        scene_id = scene.id

        # Manually delete the file to simulate missing file
        os.remove(scene.blend_path)

        # Act & Assert (should not raise)
        scene_model.delete_scene(scene_id)
        assert scene_id not in scene_model._scenes

    @patch("blender_camera.models.scene_model.uuid4")
    def test_create_scene_uses_uuid_for_id_generation(
        self, mock_uuid4, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that create_scene uses uuid4 for ID generation."""
        # Arrange
        expected_id = "test-uuid-id"
        mock_uuid4.return_value = expected_id

        # Act
        scene = scene_model.create_scene(sample_blend_data)

        # Assert
        assert scene.id == expected_id
        mock_uuid4.assert_called_once()

        # Cleanup
        if os.path.exists(scene.blend_path):
            os.remove(scene.blend_path)

    @patch("blender_camera.models.scene_model.tempfile.NamedTemporaryFile")
    def test_create_scene_uses_named_temporary_file(
        self, mock_tempfile, scene_model: SceneModel, sample_blend_data: bytes
    ):
        """Test that create_scene uses NamedTemporaryFile for blend file creation."""
        # Arrange
        mock_file = Mock()
        mock_file.name = "/tmp/test_blend_file.blend"
        mock_tempfile.return_value = mock_file
        test_path = mock_file.name

        # Act
        scene = scene_model.create_scene(sample_blend_data)

        # Assert
        mock_tempfile.assert_called_once_with(delete=False, suffix=".blend")
        assert scene.blend_path == test_path

        # Cleanup
        if os.path.exists(test_path):
            os.remove(test_path)
