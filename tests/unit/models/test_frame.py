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

    def test_to_ply_bytes_returns_valid_ply(self, frame: Frame):
        """Test that frame data is converted to valid PLY bytes."""
        # Arrange
        # frame fixture is already arranged

        # Act
        ply_bytes = frame.to_ply_bytes()

        # Assert
        assert isinstance(ply_bytes, bytes)
        assert len(ply_bytes) > 0

        # Decode and verify PLY format
        ply_content = ply_bytes.decode("utf-8")
        lines = ply_content.strip().split("\n")

        # Check header
        assert lines[0] == "ply"
        assert lines[1] == "format ascii 1.0"
        assert "element vertex" in lines[2]
        assert "property float x" in ply_content
        assert "property float y" in ply_content
        assert "property float z" in ply_content
        assert "property float nx" in ply_content
        assert "property float ny" in ply_content
        assert "property float nz" in ply_content
        assert "property uchar red" in ply_content
        assert "property uchar green" in ply_content
        assert "property uchar blue" in ply_content
        assert "end_header" in ply_content

    def test_to_ply_bytes_with_camera_intrinsics(
        self, sample_depth_data, sample_normal_data, sample_color_data
    ):
        """Test PLY generation with camera intrinsics."""
        # Arrange
        mock_camera = Mock()
        mock_intrinsics = Mock()
        mock_intrinsics.fx = 100.0
        mock_intrinsics.fy = 100.0
        mock_intrinsics.cx = 1.0  # Half of width (2)
        mock_intrinsics.cy = 1.0  # Half of height (2)
        mock_camera.camera_intrinsics = mock_intrinsics

        frame = Frame(
            camera=mock_camera,
            depth=sample_depth_data,
            normal=sample_normal_data,
            color=sample_color_data,
        )

        # Act
        ply_bytes = frame.to_ply_bytes()

        # Assert
        assert isinstance(ply_bytes, bytes)
        ply_content = ply_bytes.decode("utf-8")

        # Verify we have the expected number of valid points (all depth values > 0)
        lines = ply_content.strip().split("\n")
        header_end = -1
        for i, line in enumerate(lines):
            if line == "end_header":
                header_end = i
                break

        assert header_end >= 0
        data_lines = lines[header_end + 1 :]
        # Filter out empty lines
        data_lines = [line for line in data_lines if line.strip()]

        # All 4 pixels have positive depth values, so we should have 4 points
        assert len(data_lines) == 4

        # Check that each data line has the correct format (x, y, z, nx, ny, nz, r, g, b)
        for line in data_lines:
            parts = line.split()
            assert len(parts) == 9  # x, y, z, nx, ny, nz, r, g, b

            # Check that coordinates are floats
            for i in range(6):  # x, y, z, nx, ny, nz
                float(parts[i])  # Should not raise exception

            # Check that colors are integers in [0, 255]
            for i in range(6, 9):  # r, g, b
                color_val = int(parts[i])
                assert 0 <= color_val <= 255

    def test_to_ply_bytes_without_camera_intrinsics(
        self, sample_depth_data, sample_normal_data, sample_color_data
    ):
        """Test PLY generation without camera intrinsics (uses defaults)."""
        # Arrange
        mock_camera = Mock()
        # Simulate no camera intrinsics
        mock_camera.camera_intrinsics = None

        frame = Frame(
            camera=mock_camera,
            depth=sample_depth_data,
            normal=sample_normal_data,
            color=sample_color_data,
        )

        # Act
        ply_bytes = frame.to_ply_bytes()

        # Assert
        assert isinstance(ply_bytes, bytes)
        ply_content = ply_bytes.decode("utf-8")

        # Should still produce valid PLY data
        assert "ply" in ply_content
        assert "end_header" in ply_content

    def test_to_ply_bytes_skips_invalid_depth(
        self, mock_camera, sample_normal_data, sample_color_data
    ):
        """Test that invalid depth values (<=0, inf, nan) are skipped."""
        # Arrange
        depth_with_invalid = np.array([[0.1, -0.5], [np.inf, np.nan]], dtype=np.float32)
        frame = Frame(
            camera=mock_camera,
            depth=depth_with_invalid,
            normal=sample_normal_data,
            color=sample_color_data,
        )

        # Act
        ply_bytes = frame.to_ply_bytes()

        # Assert
        ply_content = ply_bytes.decode("utf-8")
        lines = ply_content.strip().split("\n")

        # Find the number of vertices in header
        vertex_count = None
        for line in lines:
            if line.startswith("element vertex"):
                vertex_count = int(line.split()[-1])
                break

        assert vertex_count == 1  # Only one valid depth value (0.1)

        # Count actual data lines
        header_end = -1
        for i, line in enumerate(lines):
            if line == "end_header":
                header_end = i
                break

        data_lines = [line for line in lines[header_end + 1 :] if line.strip()]
        assert len(data_lines) == 1

    def test_to_ply_bytes_coordinate_calculation(self):
        """Test that PLY coordinates are calculated correctly."""
        # Arrange
        mock_camera = Mock()
        mock_intrinsics = Mock()
        mock_intrinsics.fx = 100.0
        mock_intrinsics.fy = 100.0
        mock_intrinsics.cx = 0.5  # Center x
        mock_intrinsics.cy = 0.5  # Center y
        mock_camera.camera_intrinsics = mock_intrinsics

        # Single pixel at (0, 0) with depth 1.0
        depth_data = np.array([[1.0]], dtype=np.float32)
        normal_data = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        color_data = np.array(
            [[[1.0, 0.5, 0.0]]], dtype=np.float32
        )  # Red=255, Green=127, Blue=0

        frame = Frame(
            camera=mock_camera,
            depth=depth_data,
            normal=normal_data,
            color=color_data,
        )

        # Act
        ply_bytes = frame.to_ply_bytes()

        # Assert
        ply_content = ply_bytes.decode("utf-8")
        lines = ply_content.strip().split("\n")

        # Find the data line
        header_end = -1
        for i, line in enumerate(lines):
            if line == "end_header":
                header_end = i
                break

        data_line = lines[header_end + 1]
        parts = data_line.split()

        # Expected coordinates: x = (0 - 0.5) * 1.0 / 100.0 = -0.005
        #                      y = (0 - 0.5) * 1.0 / 100.0 = -0.005
        #                      z = 1.0
        assert float(parts[0]) == pytest.approx(-0.005, abs=1e-6)  # x
        assert float(parts[1]) == pytest.approx(-0.005, abs=1e-6)  # y
        assert float(parts[2]) == pytest.approx(1.0, abs=1e-6)  # z

        # Normal should be [0.0, 0.0, 1.0]
        assert float(parts[3]) == pytest.approx(0.0, abs=1e-6)  # nx
        assert float(parts[4]) == pytest.approx(0.0, abs=1e-6)  # ny
        assert float(parts[5]) == pytest.approx(1.0, abs=1e-6)  # nz

        # Colors should be [255, 127, 0]
        assert int(parts[6]) == 255  # red
        assert int(parts[7]) == 127  # green
        assert int(parts[8]) == 0  # blue


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
