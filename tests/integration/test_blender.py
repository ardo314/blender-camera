import pytest

from blender_camera.models.entities.camera import Camera


class TestBlenderRender:
    """Integration tests for Blender rendering functionality using real Blender processes."""

    @pytest.mark.asyncio
    async def test_render_ply_returns_valid_ply_bytes(self, blender):
        """Test that render_ply returns PLY file bytes of expected minimum size."""
        # Arrange
        camera = Camera(
            id="test_camera_ply",
            pose=[
                0.0,
                0.0,
                5.0,
                0.0,
                0.0,
                0.0,
            ],  # Position camera 5 units away on Z-axis
            camera_intrinsics=None,
        )

        # Act
        ply_bytes = await blender.render_ply(camera)

        # Assert
        assert isinstance(ply_bytes, bytes), "render_ply should return bytes"
        assert len(ply_bytes) > 1000, (
            f"PLY file should be at least 1KB, got {len(ply_bytes)} bytes"
        )

        # Check PLY magic bytes (should start with "ply\n")
        ply_magic = b"ply\n"  # PLY file signature
        assert ply_bytes[:4] == ply_magic, "File should have valid PLY magic bytes"

    @pytest.mark.asyncio
    async def test_render_png_returns_valid_png_bytes(self, blender):
        """Test that render_png returns PNG file bytes of expected minimum size."""
        # Arrange
        camera = Camera(
            id="test_camera_png",
            pose=[2.0, 2.0, 3.0, 0.1, 0.0, 0.0],  # Slightly angled camera position
            camera_intrinsics=None,
        )

        # Act
        png_bytes = await blender.render_png(camera)

        # Assert
        assert isinstance(png_bytes, bytes), "render_png should return bytes"
        assert len(png_bytes) > 1000, (
            f"PNG file should be at least 1KB, got {len(png_bytes)} bytes"
        )

        # Check PNG magic bytes (first 8 bytes should be the PNG signature)
        png_magic = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"  # PNG file signature
        assert png_bytes[:8] == png_magic, "File should have valid PNG magic bytes"

    @pytest.mark.asyncio
    async def test_render_ply_with_different_camera_positions(self, blender):
        """Test that render_ply works with various camera positions and produces different results."""
        # Arrange
        camera_front = Camera(
            id="camera_front",
            pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0],
            camera_intrinsics=None,
        )
        camera_side = Camera(
            id="camera_side",
            pose=[5.0, 0.0, 0.0, 0.0, 1.571, 0.0],  # 90 degrees rotation on Y-axis
            camera_intrinsics=None,
        )

        # Act
        ply_bytes_front = await blender.render_ply(camera_front)
        ply_bytes_side = await blender.render_ply(camera_side)

        # Assert
        assert isinstance(ply_bytes_front, bytes), (
            "Front camera render should return bytes"
        )
        assert isinstance(ply_bytes_side, bytes), (
            "Side camera render should return bytes"
        )
        assert len(ply_bytes_front) > 1000, (
            f"Front render should be at least 1KB, got {len(ply_bytes_front)} bytes"
        )
        assert len(ply_bytes_side) > 1000, (
            f"Side render should be at least 1KB, got {len(ply_bytes_side)} bytes"
        )

        # Different camera positions should produce different results
        assert ply_bytes_front != ply_bytes_side, (
            "Different camera positions should produce different renders"
        )

    @pytest.mark.asyncio
    async def test_render_png_with_different_camera_positions(self, blender):
        """Test that render_png works with various camera positions and produces different results."""
        # Arrange
        camera_close = Camera(
            id="camera_close",
            pose=[0.0, 0.0, 2.0, 0.0, 0.0, 0.0],  # Close to object
            camera_intrinsics=None,
        )
        camera_far = Camera(
            id="camera_far",
            pose=[0.0, 0.0, 10.0, 0.0, 0.0, 0.0],  # Far from object
            camera_intrinsics=None,
        )

        # Act
        png_bytes_close = await blender.render_png(camera_close)
        png_bytes_far = await blender.render_png(camera_far)

        # Assert
        assert isinstance(png_bytes_close, bytes), (
            "Close camera render should return bytes"
        )
        assert isinstance(png_bytes_far, bytes), "Far camera render should return bytes"
        assert len(png_bytes_close) > 1000, (
            f"Close render should be at least 1KB, got {len(png_bytes_close)} bytes"
        )
        assert len(png_bytes_far) > 1000, (
            f"Far render should be at least 1KB, got {len(png_bytes_far)} bytes"
        )

        # Different distances should produce different results
        assert png_bytes_close != png_bytes_far, (
            "Different camera distances should produce different renders"
        )

    @pytest.mark.asyncio
    async def test_render_with_extreme_camera_positions(self, blender):
        """Test rendering with edge case camera positions."""
        # Arrange - Camera very close to origin
        camera_origin = Camera(
            id="camera_origin",
            pose=[0.0, 0.0, 0.1, 0.0, 0.0, 0.0],  # Very close to origin
            camera_intrinsics=None,
        )

        # Act
        ply_bytes = await blender.render_ply(camera_origin)
        png_bytes = await blender.render_png(camera_origin)

        # Assert
        assert isinstance(ply_bytes, bytes), "Origin render PLY should return bytes"
        assert isinstance(png_bytes, bytes), "Origin render PNG should return bytes"
        assert len(ply_bytes) > 100, (
            f"PLY from origin should have some data, got {len(ply_bytes)} bytes"
        )
        assert len(png_bytes) > 100, (
            f"PNG from origin should have some data, got {len(png_bytes)} bytes"
        )
