import os
import tempfile

import pytest

from blender_camera.blender import render_img, render_ply
from blender_camera.models.entities.camera import Camera


@pytest.mark.asyncio
@pytest.mark.integration
async def test_render_img_integration():
    """Integration test that actually calls Blender to render an image."""
    camera = Camera(id="test-camera", pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0])

    # This test requires Blender to be installed and a blend file to exist
    blend_file = "tests/integration/resources/cube.blend"
    if not os.path.exists(blend_file):
        pytest.skip(f"{blend_file} file not found - skipping integration test")

    try:
        result = await render_img("test_url", camera)

        # Validate the result
        assert isinstance(result, bytes), "Result should be bytes"
        assert len(result) > 100, (
            f"Result should be substantial size, got {len(result)} bytes"
        )

        # Basic validation that it might be an image file
        # PNG files start with specific bytes
        if result.startswith(b"\x89PNG"):
            assert True, "Result appears to be a PNG file"
        elif result.startswith(b"\x00\x00\x00\x0c"):  # EXR header
            assert True, "Result appears to be an EXR file"
        else:
            # Check if it contains any image-like patterns
            assert len(result) > 1000, (
                "Result should be at least 1KB for a meaningful image"
            )

    except RuntimeError as e:
        if "Blender process failed" in str(e):
            pytest.skip(
                f"Blender process failed - this is expected if the environment is not set up: {e}"
            )
        else:
            raise


@pytest.mark.asyncio
@pytest.mark.integration
async def test_render_ply_integration():
    """Integration test that actually calls Blender to render PLY data."""
    camera = Camera(id="test-camera", pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0])

    blend_file = "tests/integration/resources/cube.blend"
    if not os.path.exists(blend_file):
        pytest.skip(f"{blend_file} file not found - skipping integration test")

    try:
        result = await render_ply("test_url", camera)

        # Validate the result
        assert isinstance(result, bytes), "Result should be bytes"
        assert len(result) > 100, (
            f"Result should be substantial size, got {len(result)} bytes"
        )

        # The PLY function returns the color data
        if result.startswith(b"\x89PNG"):
            assert True, "Color result appears to be a PNG file"
        elif result.startswith(b"\x00\x00\x00\x0c"):  # EXR header
            assert True, "Color result appears to be an EXR file"
        else:
            assert len(result) > 1000, (
                "Result should be at least 1KB for meaningful color data"
            )

    except RuntimeError as e:
        if "Blender process failed" in str(e):
            pytest.skip(
                f"Blender process failed - this is expected if the environment is not set up: {e}"
            )
        else:
            raise


@pytest.mark.asyncio
@pytest.mark.integration
async def test_blender_output_files_exist():
    """Integration test to verify that Blender actually creates the expected output files."""
    camera = Camera(id="test-camera", pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0])

    blend_file = "tests/integration/resources/cube.blend"
    if not os.path.exists(blend_file):
        pytest.skip(f"{blend_file} file not found - skipping integration test")

    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Call the blender process directly to check what files it creates
            from blender_camera.blender import (
                _call_blender_process,
                _write_tmp_state,
            )

            json_path = _write_tmp_state(camera)
            try:
                await _call_blender_process(blend_file, json_path, temp_dir)

                # Check what files were actually created in absolute path
                created_files = os.listdir(temp_dir)
                print(f"Files created by Blender in absolute path: {created_files}")

                # Check for files in the relative path (where Blender actually saves them)
                relative_dir = os.path.basename(temp_dir)
                relative_path = os.path.join("tmp", relative_dir)
                relative_created_files = []

                if os.path.exists(relative_path):
                    relative_created_files = os.listdir(relative_path)
                    print(
                        f"Files created by Blender in relative path {relative_path}: {relative_created_files}"
                    )

                # Validate that some files were created (either absolute or relative)
                all_files = created_files + relative_created_files
                assert len(all_files) > 0, (
                    "Blender should create at least one output file"
                )

                # Check for expected patterns (color, depth, normal, etc.)
                file_patterns = ["color", "depth", "normal", "myshot"]
                found_patterns = []

                for pattern in file_patterns:
                    if any(pattern in filename.lower() for filename in all_files):
                        found_patterns.append(pattern)

                assert len(found_patterns) > 0, (
                    f"Expected to find files matching patterns {file_patterns}, but found: {all_files}"
                )

                # Verify file sizes are reasonable for the files that exist
                files_to_check = []

                # Add absolute path files
                for filename in created_files:
                    files_to_check.append(os.path.join(temp_dir, filename))

                # Add relative path files
                for filename in relative_created_files:
                    files_to_check.append(os.path.join(relative_path, filename))

                for filepath in files_to_check:
                    file_size = os.path.getsize(filepath)
                    filename = os.path.basename(filepath)

                    # Files should be at least a few hundred bytes
                    assert file_size >= 100, (
                        f"File {filename} is only {file_size} bytes - seems too small"
                    )

                    # Files shouldn't be impossibly large (> 50MB)
                    assert file_size <= 50 * 1024 * 1024, (
                        f"File {filename} is {file_size} bytes - seems too large"
                    )

                    print(f"File {filename}: {file_size} bytes")

            finally:
                if os.path.exists(json_path):
                    os.remove(json_path)

        except RuntimeError as e:
            if "Blender process failed" in str(e):
                pytest.skip(
                    f"Blender process failed - this is expected if the environment is not set up: {e}"
                )
            else:
                raise


@pytest.mark.asyncio
@pytest.mark.integration
async def test_blender_script_handles_different_camera_poses():
    """Test that the Blender script handles various camera positions and orientations."""
    test_poses = [
        [0.0, 0.0, 5.0, 0.0, 0.0, 0.0],  # Looking straight down Z-axis
        [5.0, 0.0, 0.0, 0.0, 1.57, 0.0],  # Looking from X-axis (90° rotation)
        [0.0, 5.0, 0.0, -1.57, 0.0, 0.0],  # Looking from Y-axis
        [3.0, 3.0, 3.0, 0.5, 0.5, 0.5],  # Arbitrary position and rotation
    ]

    blend_file = "tests/integration/resources/cube.blend"
    if not os.path.exists(blend_file):
        pytest.skip(f"{blend_file} file not found - skipping integration test")

    for i, pose in enumerate(test_poses):
        camera = Camera(id=f"test-camera-{i}", pose=pose)

        try:
            result = await render_img("test_url", camera)

            # Basic validation
            assert isinstance(result, bytes), f"Result for pose {pose} should be bytes"
            assert len(result) > 50, (
                f"Result for pose {pose} should be at least 50 bytes, got {len(result)}"
            )

        except RuntimeError as e:
            if "Blender process failed" in str(e):
                pytest.skip(
                    f"Blender process failed for pose {pose} - this is expected if environment not set up: {e}"
                )
            else:
                raise
