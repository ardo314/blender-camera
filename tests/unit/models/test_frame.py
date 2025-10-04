from io import BytesIO
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image

from blender_camera.models.frame import Frame, _to_8bit_png


@pytest.fixture
def mock_camera():
    """Mock camera object for testing."""
    return Mock()


@pytest.fixture
def sample_depth_data():
    """Sample 2D depth data."""
    return np.array([[0.1, 0.5], [0.8, 1.0]], dtype=np.float32)


@pytest.fixture
def sample_normal_data():
    """Sample 3D normal data (height, width, 3)."""
    return np.array(
        [[[0.0, 0.0, 1.0], [0.5, 0.5, 0.7]], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]],
        dtype=np.float32,
    )


@pytest.fixture
def sample_color_data():
    """Sample 3D color data (height, width, 3)."""
    return np.array(
        [[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], [[0.0, 0.0, 1.0], [1.0, 1.0, 0.0]]],
        dtype=np.float32,
    )


@pytest.fixture
def frame(mock_camera, sample_depth_data, sample_normal_data, sample_color_data):
    """Create a Frame instance for testing."""
    return Frame(
        camera=mock_camera,
        depth=sample_depth_data,
        normal=sample_normal_data,
        color=sample_color_data,
    )


class TestFrame:
    def test_frame_initialization(
        self, mock_camera, sample_depth_data, sample_normal_data, sample_color_data
    ):
        """Test Frame initialization with proper data types."""
        # Arrange
        # All fixtures are already arranged

        # Act
        frame = Frame(
            camera=mock_camera,
            depth=sample_depth_data,
            normal=sample_normal_data,
            color=sample_color_data,
        )

        # Assert
        assert frame._camera is mock_camera
        assert np.array_equal(frame._depth, sample_depth_data)
        assert np.array_equal(frame._normal, sample_normal_data)
        assert np.array_equal(frame._color, sample_color_data)

    def test_to_depth_png_bytes_returns_valid_png(self, frame: Frame):
        """Test that depth data is converted to valid PNG bytes."""
        # Arrange
        # frame fixture is already arranged

        # Act
        png_bytes = frame.to_depth_png_bytes()

        # Assert
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

        # Verify it's a valid PNG by loading it back
        image = Image.open(BytesIO(png_bytes))
        assert image.format == "PNG"
        assert image.size == (2, 2)  # width, height from our sample data

    def test_to_normal_png_bytes_returns_valid_png(self, frame: Frame):
        """Test that normal data is converted to valid PNG bytes."""
        # Arrange
        # frame fixture is already arranged

        # Act
        png_bytes = frame.to_normal_png_bytes()

        # Assert
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

        # Verify it's a valid PNG by loading it back
        image = Image.open(BytesIO(png_bytes))
        assert image.format == "PNG"
        assert image.size == (2, 2)  # width, height from our sample data

    def test_to_color_png_bytes_returns_valid_png(self, frame: Frame):
        """Test that color data is converted to valid PNG bytes."""
        # Arrange
        # frame fixture is already arranged

        # Act
        png_bytes = frame.to_color_png_bytes()

        # Assert
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

        # Verify it's a valid PNG by loading it back
        image = Image.open(BytesIO(png_bytes))
        assert image.format == "PNG"
        assert image.size == (2, 2)  # width, height from our sample data

    def test_depth_values_are_clipped_correctly(self, mock_camera):
        """Test that depth values outside [0,1] range are clipped properly."""
        # Arrange
        depth_with_outliers = np.array([[-0.5, 0.5], [1.5, 0.8]], dtype=np.float32)
        normal_data = np.zeros((2, 2, 3), dtype=np.float32)
        color_data = np.zeros((2, 2, 3), dtype=np.float32)
        frame = Frame(mock_camera, depth_with_outliers, normal_data, color_data)

        # Act
        png_bytes = frame.to_depth_png_bytes()

        # Assert
        # Load the image back and verify clipping
        image = Image.open(BytesIO(png_bytes))
        image_array = np.array(image)

        # Check that negative values became 0 (black) and >1 values became 255 (white)
        # Note: PIL/numpy array indexing is [row, col] where our array is [[row0], [row1]]
        assert image_array[0, 0] == 0  # -0.5 clipped to 0
        assert image_array[0, 1] == 127  # 0.5 -> 127 (0.5 * 255 = 127.5 -> 127)
        assert image_array[1, 0] == 255  # 1.5 clipped to 1.0 -> 255
        assert image_array[1, 1] == 204  # 0.8 -> 204 (0.8 * 255 = 204)

    def test_color_values_are_clipped_correctly(self, mock_camera):
        """Test that color values outside [0,1] range are clipped properly."""
        # Arrange
        depth_data = np.zeros((2, 2), dtype=np.float32)
        normal_data = np.zeros((2, 2, 3), dtype=np.float32)
        color_with_outliers = np.array(
            [[[-0.5, 0.5, 1.5], [0.0, 1.0, 0.5]], [[0.2, 0.8, 0.3], [1.2, -0.1, 0.9]]],
            dtype=np.float32,
        )
        frame = Frame(mock_camera, depth_data, normal_data, color_with_outliers)

        # Act
        png_bytes = frame.to_color_png_bytes()

        # Assert
        # Load the image back and verify clipping
        image = Image.open(BytesIO(png_bytes))
        image_array = np.array(image)

        # Check specific pixel values (note: PIL uses (row, col) indexing)
        # First pixel: [-0.5, 0.5, 1.5] -> [0, 127, 255]
        assert image_array[0, 0, 0] == 0  # -0.5 -> 0
        assert image_array[0, 0, 1] == 127  # 0.5 -> 127
        assert image_array[0, 0, 2] == 255  # 1.5 -> 255


class TestTo8bitPng:
    """Test the _to_8bit_png helper function."""

    def test_converts_float_to_8bit_correctly(self):
        """Test conversion from float [0,1] to 8-bit [0,255]."""
        # Arrange
        float_image = np.array(
            [
                [[0.0, 0.5, 1.0]],  # Should become [0, 127, 255]
            ],
            dtype=np.float32,
        )

        # Act
        png_bytes = _to_8bit_png(float_image)

        # Assert
        image = Image.open(BytesIO(png_bytes))
        image_array = np.array(image)

        assert image_array[0, 0, 0] == 0  # 0.0 -> 0
        assert image_array[0, 0, 1] == 127  # 0.5 -> 127
        assert image_array[0, 0, 2] == 255  # 1.0 -> 255

    def test_clips_values_outside_range(self):
        """Test that values outside [0,1] are clipped."""
        # Arrange
        float_image = np.array(
            [
                [[-0.5, 1.5, 0.5]],  # Should become [0, 255, 127]
            ],
            dtype=np.float32,
        )

        # Act
        png_bytes = _to_8bit_png(float_image)

        # Assert
        image = Image.open(BytesIO(png_bytes))
        image_array = np.array(image)

        assert image_array[0, 0, 0] == 0  # -0.5 clipped to 0
        assert image_array[0, 0, 1] == 255  # 1.5 clipped to 255
        assert image_array[0, 0, 2] == 127  # 0.5 -> 127

    def test_handles_grayscale_images(self):
        """Test that grayscale (2D) images are handled correctly."""
        # Arrange
        grayscale_image = np.array([[0.0, 0.5], [1.0, 0.25]], dtype=np.float32)

        # Act
        png_bytes = _to_8bit_png(grayscale_image)

        # Assert
        image = Image.open(BytesIO(png_bytes))
        image_array = np.array(image)

        assert image_array[0, 0] == 0  # 0.0 -> 0
        assert image_array[0, 1] == 127  # 0.5 -> 127
        assert image_array[1, 0] == 255  # 1.0 -> 255
        assert image_array[1, 1] == 63  # 0.25 -> 63

    def test_returns_bytes(self):
        """Test that the function returns bytes."""
        # Arrange
        simple_image = np.array([[0.5]], dtype=np.float32)

        # Act
        result = _to_8bit_png(simple_image)

        # Assert
        assert isinstance(result, bytes)
        assert len(result) > 0
