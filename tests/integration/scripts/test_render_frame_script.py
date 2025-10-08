import tempfile
from pathlib import Path

import numpy as np
import pytest

from blender_camera.blender import Blender
from blender_camera.models.camera_intrinsics import CameraIntrinsics
from blender_camera.models.entities.camera import Camera
from blender_camera.models.frame import Frame
from blender_camera.scripts.render_frame_script import (
    RenderFrameScript,
    _write_tmp_state,
)


@pytest.fixture
def sample_camera() -> Camera:
    """Create a sample camera for testing."""
    return Camera(
        id="test_camera",
        pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0],  # Position at (0, 0, 5) with no rotation
        camera_intrinsics=CameraIntrinsics(fx=50.0, fy=50.0, cx=320.0, cy=240.0),
    )


@pytest.fixture
def sample_camera_rotated() -> Camera:
    """Create a sample camera with rotation for testing normal transformation."""
    return Camera(
        id="test_camera_rotated",
        pose=[2.0, 2.0, 5.0, 0.2, 0.3, 0.1],  # Position at (2, 2, 5) with rotation
        camera_intrinsics=CameraIntrinsics(fx=50.0, fy=50.0, cx=320.0, cy=240.0),
    )


@pytest.fixture
def render_frame_script(blender: Blender) -> RenderFrameScript:
    """Create a RenderFrameScript instance using the blender fixture."""
    return RenderFrameScript(blender)


class TestRenderFrameScript:
    """Integration tests for RenderFrameScript."""

    @pytest.mark.asyncio
    async def test_execute_should_return_frame_with_valid_data(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that execute returns a Frame with valid numpy arrays."""
        # Act
        frame = await render_frame_script.execute(sample_camera)

        # Assert
        assert isinstance(frame, Frame)
        assert frame._camera == sample_camera
        assert isinstance(frame._depth, np.ndarray)
        assert isinstance(frame._normal, np.ndarray)
        assert isinstance(frame._color, np.ndarray)

        # Check array shapes and types
        assert frame._depth.dtype == np.float32
        assert frame._normal.dtype == np.float32
        assert frame._color.dtype == np.float32

        # Check that arrays have reasonable dimensions
        assert len(frame._depth.shape) == 2  # (height, width)
        assert len(frame._normal.shape) == 3  # (height, width, 3)
        assert len(frame._color.shape) == 3  # (height, width, 3)

        # Normal and color should have 3 channels
        assert frame._normal.shape[2] == 3
        assert frame._color.shape[2] == 3

        # All arrays should have the same height and width
        height, width = frame._depth.shape
        assert frame._normal.shape[:2] == (height, width)
        assert frame._color.shape[:2] == (height, width)

    @pytest.mark.asyncio
    async def test_execute_should_produce_valid_depth_values(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that depth values are reasonable."""
        # Act
        frame = await render_frame_script.execute(sample_camera)

        # Assert
        depth = frame._depth

        # Depth values should be positive (or zero for background)
        assert np.all(depth >= 0.0)

        # Should have some non-zero depth values (objects in scene)
        assert np.any(depth > 0.0)

        # Depth values should be finite
        assert np.all(np.isfinite(depth))

    @pytest.mark.asyncio
    async def test_execute_should_produce_valid_normal_vectors(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that normal vectors are valid and reasonable."""
        # Act
        frame = await render_frame_script.execute(sample_camera)

        # Assert
        normals = frame._normal

        # Normals should be finite
        assert np.all(np.isfinite(normals))

        # Should have some non-zero normals (geometry in scene)
        assert np.any(np.linalg.norm(normals, axis=2) > 0.0)

        # For pixels with valid geometry, normals should have reasonable magnitude
        # (not necessarily unit length, but should be reasonable values)
        magnitudes = np.linalg.norm(normals, axis=2)
        valid_pixels = magnitudes > 0.01  # Filter out background/invalid pixels

        if np.any(valid_pixels):
            valid_magnitudes = magnitudes[valid_pixels]
            # Valid normals should have reasonable magnitude (allowing for various encodings)
            assert np.all(valid_magnitudes <= 2.0)  # Should not be excessively large
            assert np.all(valid_magnitudes >= 0.01)  # Should not be too small

    @pytest.mark.asyncio
    async def test_execute_should_produce_valid_color_values(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that color values are in valid range."""
        # Act
        frame = await render_frame_script.execute(sample_camera)

        # Assert
        color = frame._color

        # Color values should be finite
        assert np.all(np.isfinite(color))

        # Color values should be non-negative
        assert np.all(color >= 0.0)

        # Should have some color variation (not all black)
        assert np.any(color > 0.0)

    @pytest.mark.asyncio
    async def test_execute_with_camera_intrinsics_should_work(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that camera intrinsics are properly handled."""
        # Arrange
        camera_with_intrinsics = Camera(
            id="test_camera_intrinsics",
            pose=[0.0, 0.0, 3.0, 0.0, 0.0, 0.0],
            camera_intrinsics=CameraIntrinsics(fx=100.0, fy=100.0, cx=320.0, cy=240.0),
        )

        # Act
        frame = await render_frame_script.execute(camera_with_intrinsics)

        # Assert
        assert isinstance(frame, Frame)
        assert frame._camera == camera_with_intrinsics

        # Verify that the camera intrinsics are accessible
        assert hasattr(frame._camera, "camera_intrinsics")
        assert frame._camera.camera_intrinsics is not None
        assert frame._camera.camera_intrinsics.fx == 100.0

    @pytest.mark.asyncio
    async def test_execute_with_rotated_camera_should_transform_normals(
        self, render_frame_script: RenderFrameScript, sample_camera_rotated: Camera
    ):
        """Test that normals are properly transformed for rotated cameras."""
        # Act
        frame_rotated = await render_frame_script.execute(sample_camera_rotated)

        # Also render with unrotated camera for comparison
        unrotated_camera = Camera(
            id="test_camera_unrotated",
            pose=[2.0, 2.0, 5.0, 0.0, 0.0, 0.0],  # Same position, no rotation
            camera_intrinsics=sample_camera_rotated.camera_intrinsics,
        )
        frame_unrotated = await render_frame_script.execute(unrotated_camera)

        # Assert
        normals_rotated = frame_rotated._normal
        normals_unrotated = frame_unrotated._normal

        # Both should be valid
        assert np.all(np.isfinite(normals_rotated))
        assert np.all(np.isfinite(normals_unrotated))

        # For a rotated camera, normals should be different from unrotated case
        # (at least for some pixels where there's actual geometry)
        valid_mask = (np.linalg.norm(normals_rotated, axis=2) > 0.1) & (
            np.linalg.norm(normals_unrotated, axis=2) > 0.1
        )

        if np.any(valid_mask):
            # The normals should be different due to the coordinate transformation
            diff = np.abs(normals_rotated[valid_mask] - normals_unrotated[valid_mask])
            assert np.any(diff > 0.01)  # Should have noticeable differences

    @pytest.mark.asyncio
    async def test_execute_should_handle_camera_without_intrinsics(
        self, render_frame_script: RenderFrameScript
    ):
        """Test that cameras without intrinsics are handled gracefully."""
        # Arrange
        camera_no_intrinsics = Camera(
            id="test_camera_no_intrinsics",
            pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0],
            camera_intrinsics=None,
        )

        # Act
        frame = await render_frame_script.execute(camera_no_intrinsics)

        # Assert
        assert isinstance(frame, Frame)
        assert frame._camera == camera_no_intrinsics
        assert frame._camera.camera_intrinsics is None

        # Frame data should still be valid
        assert isinstance(frame._depth, np.ndarray)
        assert isinstance(frame._normal, np.ndarray)
        assert isinstance(frame._color, np.ndarray)

    @pytest.mark.asyncio
    async def test_execute_should_cleanup_temporary_files(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that temporary files are properly cleaned up."""
        # Arrange
        initial_temp_files = set(Path(tempfile.gettempdir()).iterdir())

        # Act
        frame = await render_frame_script.execute(sample_camera)

        # Assert
        assert isinstance(frame, Frame)

        # Check that no new temporary files are left behind
        final_temp_files = set(Path(tempfile.gettempdir()).iterdir())
        new_temp_files = final_temp_files - initial_temp_files

        # Filter out files that might be created by other processes
        our_temp_files = [
            f
            for f in new_temp_files
            if f.suffix in [".json", ".exr"] or "frame" in f.name
        ]

        # Should not have left behind any of our temporary files
        assert len(our_temp_files) == 0

    def test_write_tmp_state_should_create_valid_json(self, sample_camera: Camera):
        """Test that _write_tmp_state creates a valid JSON file."""
        # Act
        tmp_path = _write_tmp_state(sample_camera)

        try:
            # Assert
            assert Path(tmp_path).exists()
            assert tmp_path.endswith(".json")

            # File should contain valid JSON with camera data
            with open(tmp_path, "r") as f:
                content = f.read()

            assert "test_camera" in content
            assert "pose" in content
            assert "5.0" in content  # Z position

        finally:
            # Cleanup
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    @pytest.mark.asyncio
    async def test_execute_should_produce_consistent_results(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that multiple renders of the same camera produce consistent results."""
        # Act
        frame1 = await render_frame_script.execute(sample_camera)
        frame2 = await render_frame_script.execute(sample_camera)

        # Assert
        # Results should be identical (or very close due to floating point precision)
        assert np.allclose(frame1._depth, frame2._depth, rtol=1e-5)
        assert np.allclose(frame1._normal, frame2._normal, rtol=1e-5)
        assert np.allclose(frame1._color, frame2._color, rtol=1e-5)


class TestRenderFrameScriptConversionFunctions:
    """Test the individual conversion functions in isolation."""

    @pytest.mark.asyncio
    async def test_frame_conversion_methods_should_work(
        self, render_frame_script: RenderFrameScript, sample_camera: Camera
    ):
        """Test that Frame conversion methods work with rendered data."""
        # Arrange
        frame = await render_frame_script.execute(sample_camera)

        # Act & Assert - test PNG conversion methods
        depth_png = frame.to_depth_png_bytes()
        normal_png = frame.to_normal_png_bytes()
        color_png = frame.to_color_png_bytes()
        ply_bytes = frame.to_ply_bytes()

        # All should return bytes
        assert isinstance(depth_png, bytes)
        assert isinstance(normal_png, bytes)
        assert isinstance(color_png, bytes)
        assert isinstance(ply_bytes, bytes)

        # All should have reasonable size
        assert len(depth_png) > 100
        assert len(normal_png) > 100
        assert len(color_png) > 100
        assert len(ply_bytes) > 100

        # PLY should contain valid PLY header
        ply_str = ply_bytes.decode("utf-8")
        assert "ply" in ply_str
        assert "element vertex" in ply_str
        assert "property float x" in ply_str
