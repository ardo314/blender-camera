import pytest

from blender_camera.models.entities.camera import Camera


class TestBlenderRender:
    """Integration tests for Blender rendering functionality using real Blender processes."""

    @pytest.mark.asyncio
    async def test_render_ply_returns_valid_exr_bytes(self, blender):
        """Test that render_ply returns EXR file bytes of expected minimum size."""
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
        )

        # Act
        ply_bytes = await blender.render_ply(camera)

        # Assert
        assert isinstance(ply_bytes, bytes), "render_ply should return bytes"
        assert len(ply_bytes) > 1000, (
            f"EXR file should be at least 1KB, got {len(ply_bytes)} bytes"
        )

        # Check EXR magic bytes (first 4 bytes should be the EXR signature)
        exr_magic = b"\x76\x2f\x31\x01"  # EXR file signature
        assert ply_bytes[:4] == exr_magic, "File should have valid EXR magic bytes"

    @pytest.mark.asyncio
    async def test_render_img_returns_valid_png_bytes(self, blender):
        """Test that render_img returns EXR file bytes of expected minimum size.

        Note: Currently both render_ply and render_img return EXR format since that's
        what the Blender script generates. This could be modified to return PNG if needed.
        """
        # Arrange
        camera = Camera(
            id="test_camera_img",
            pose=[2.0, 2.0, 3.0, 0.1, 0.0, 0.0],  # Slightly angled camera position
        )

        # Act
        img_bytes = await blender.render_img(camera)

        # Assert
        assert isinstance(img_bytes, bytes), "render_img should return bytes"
        assert len(img_bytes) > 1000, (
            f"EXR file should be at least 1KB, got {len(img_bytes)} bytes"
        )

        # Check EXR magic bytes (both methods should return EXR for now)
        exr_magic = b"\x76\x2f\x31\x01"  # EXR file signature
        assert img_bytes[:4] == exr_magic, "File should have valid EXR magic bytes"

    @pytest.mark.asyncio
    async def test_render_ply_with_different_camera_positions(self, blender):
        """Test that render_ply works with various camera positions and produces different results."""
        # Arrange
        camera_front = Camera(id="camera_front", pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0])
        camera_side = Camera(
            id="camera_side",
            pose=[5.0, 0.0, 0.0, 0.0, 1.571, 0.0],  # 90 degrees rotation on Y-axis
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
    async def test_render_img_with_different_camera_positions(self, blender):
        """Test that render_img works with various camera positions and produces different results."""
        # Arrange
        camera_close = Camera(
            id="camera_close",
            pose=[0.0, 0.0, 2.0, 0.0, 0.0, 0.0],  # Close to object
        )
        camera_far = Camera(
            id="camera_far",
            pose=[0.0, 0.0, 10.0, 0.0, 0.0, 0.0],  # Far from object
        )

        # Act
        img_bytes_close = await blender.render_img(camera_close)
        img_bytes_far = await blender.render_img(camera_far)

        # Assert
        assert isinstance(img_bytes_close, bytes), (
            "Close camera render should return bytes"
        )
        assert isinstance(img_bytes_far, bytes), "Far camera render should return bytes"
        assert len(img_bytes_close) > 1000, (
            f"Close render should be at least 1KB, got {len(img_bytes_close)} bytes"
        )
        assert len(img_bytes_far) > 1000, (
            f"Far render should be at least 1KB, got {len(img_bytes_far)} bytes"
        )

        # Different distances should produce different results
        assert img_bytes_close != img_bytes_far, (
            "Different camera distances should produce different renders"
        )

    @pytest.mark.asyncio
    async def test_render_ply_and_img_consistency(self, blender):
        """Test that render_ply and render_img work consistently with the same camera."""
        # Arrange
        camera = Camera(id="consistency_test", pose=[1.0, 1.0, 4.0, 0.2, 0.1, 0.0])

        # Act
        ply_bytes = await blender.render_ply(camera)
        img_bytes = await blender.render_img(camera)

        # Assert
        # Both should return valid data
        assert isinstance(ply_bytes, bytes), "PLY render should return bytes"
        assert isinstance(img_bytes, bytes), "IMG render should return bytes"
        assert len(ply_bytes) > 1000, (
            f"PLY should be at least 1KB, got {len(ply_bytes)} bytes"
        )
        assert len(img_bytes) > 1000, (
            f"IMG should be at least 1KB, got {len(img_bytes)} bytes"
        )

        # Should have correct file signatures (both are EXR for now)
        assert ply_bytes[:4] == b"\x76\x2f\x31\x01", "PLY should have EXR signature"
        assert img_bytes[:4] == b"\x76\x2f\x31\x01", "IMG should have EXR signature"

    @pytest.mark.asyncio
    async def test_render_with_extreme_camera_positions(self, blender):
        """Test rendering with edge case camera positions."""
        # Arrange - Camera very close to origin
        camera_origin = Camera(
            id="camera_origin",
            pose=[0.0, 0.0, 0.1, 0.0, 0.0, 0.0],  # Very close to origin
        )

        # Act
        ply_bytes = await blender.render_ply(camera_origin)
        img_bytes = await blender.render_img(camera_origin)

        # Assert
        assert isinstance(ply_bytes, bytes), "Origin render PLY should return bytes"
        assert isinstance(img_bytes, bytes), "Origin render IMG should return bytes"
        assert len(ply_bytes) > 100, (
            f"PLY from origin should have some data, got {len(ply_bytes)} bytes"
        )
        assert len(img_bytes) > 100, (
            f"IMG from origin should have some data, got {len(img_bytes)} bytes"
        )
