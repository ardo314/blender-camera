import asyncio
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from blender_camera.blender import (
    _call_blender_process,
    _write_tmp_state,
    render_img,
    render_ply,
)
from blender_camera.models.entities.camera import Camera


class TestSaveCameraToTmpFile:
    def test_saves_camera_data_to_json_file(self):
        """Test that camera data is correctly saved to a temporary JSON file."""
        camera = Camera(id="test-camera", pose=[1.0, 2.0, 3.0, 0.1, 0.2, 0.3])

        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test_camera.json"
            mock_temp_file.return_value = mock_file

            with patch("builtins.open", mock_open()) as mock_file_open:
                result = _write_tmp_state(camera)

                assert result == "/tmp/test_camera.json"
                mock_temp_file.assert_called_once_with(delete=False, suffix=".json")
                mock_file_open.assert_called_once_with("/tmp/test_camera.json", "w")
                mock_file_open().write.assert_called_once()

                # Verify the JSON content contains camera data
                written_content = mock_file_open().write.call_args[0][0]
                assert '"id":"test-camera"' in written_content
                assert '"pose":[1.0,2.0,3.0,0.1,0.2,0.3]' in written_content


class TestCallBlenderProcess:
    @pytest.mark.asyncio
    async def test_successful_blender_process(self):
        """Test successful blender process execution."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"Blender output", b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            await _call_blender_process("test.blend", "camera.json", "/tmp/output")

            mock_subprocess.assert_called_once_with(
                "blender",
                "test.blend",
                "--background",
                "--python",
                "src/blender_camera/blender_script.py",
                "--",
                "--json_path",
                "camera.json",
                "--output_path",
                "/tmp/output",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            mock_proc.communicate.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_blender_process(self):
        """Test that blender process failure raises RuntimeError."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"Error occurred")
            mock_proc.returncode = 1
            mock_subprocess.return_value = mock_proc

            with pytest.raises(
                RuntimeError, match="Blender process failed with exit code 1"
            ):
                await _call_blender_process("test.blend", "camera.json", "/tmp/output")


class TestRenderPly:
    @pytest.mark.asyncio
    async def test_render_ply_success(self):
        """Test successful PLY rendering with proper file outputs."""
        camera = Camera(id="test-camera", pose=[1.0, 2.0, 3.0, 0.1, 0.2, 0.3])

        # Mock file contents - simulate realistic file sizes
        mock_color_data = b"PNG_COLOR_DATA" + b"\x00" * 1000  # ~1KB color data
        mock_depth_data = b"PNG_DEPTH_DATA" + b"\x00" * 500  # ~500B depth data
        mock_normal_data = b"PNG_NORMAL_DATA" + b"\x00" * 500  # ~500B normal data

        with (
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch(
                "blender_camera.blender._save_camera_to_tmp_file"
            ) as mock_save_camera,
            patch("blender_camera.blender._call_blender_process") as mock_call_blender,
            patch("builtins.open", mock_open()) as mock_file_open,
            patch("os.remove") as mock_remove,
        ):
            mock_temp_dir.return_value.name = "/tmp/test_output"
            mock_save_camera.return_value = "/tmp/camera.json"
            mock_call_blender.return_value = None

            # Configure mock file reads for different files
            file_contents = {
                "/tmp/test_output/color.png": mock_color_data,
                "/tmp/test_output/depth.png": mock_depth_data,
                "/tmp/test_output/normal.png": mock_normal_data,
            }

            def mock_file_open_side_effect(filename, mode="r"):
                if mode == "rb" and filename in file_contents:
                    mock_file = mock_open(
                        read_data=file_contents[filename]
                    ).return_value
                    return mock_file
                return mock_open().return_value

            mock_file_open.side_effect = mock_file_open_side_effect

            result = await render_ply("test_url", camera)

            # Verify the result is the color data
            assert result == mock_color_data
            assert len(result) > 1000  # Should be substantial size

            # Verify all expected files were opened
            expected_calls = [
                (("/tmp/test_output/color.png", "rb"),),
                (("/tmp/test_output/depth.png", "rb"),),
                (("/tmp/test_output/normal.png", "rb"),),
            ]
            for call in expected_calls:
                assert call in mock_file_open.call_args_list

            # Verify cleanup was attempted (though shutil.rmtree is commented out)
            mock_remove.assert_any_call("untitled.blend")
            mock_remove.assert_any_call("/tmp/camera.json")

    @pytest.mark.asyncio
    async def test_render_ply_missing_files(self):
        """Test PLY rendering when expected output files are missing."""
        camera = Camera(id="test-camera", pose=[1.0, 2.0, 3.0, 0.1, 0.2, 0.3])

        with (
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch(
                "blender_camera.blender._save_camera_to_tmp_file"
            ) as mock_save_camera,
            patch("blender_camera.blender._call_blender_process") as mock_call_blender,
            patch("builtins.open", side_effect=FileNotFoundError("No such file")),
            patch("os.remove"),
        ):
            mock_temp_dir.return_value.name = "/tmp/test_output"
            mock_save_camera.return_value = "/tmp/camera.json"
            mock_call_blender.return_value = None

            with pytest.raises(FileNotFoundError):
                await render_ply("test_url", camera)


class TestRenderImg:
    @pytest.mark.asyncio
    async def test_render_img_success(self):
        """Test successful image rendering."""
        camera = Camera(id="test-camera", pose=[1.0, 2.0, 3.0, 0.1, 0.2, 0.3])

        mock_image_data = b"PNG_IMAGE_DATA" + b"\x00" * 2000  # ~2KB image data

        with (
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch(
                "blender_camera.blender._save_camera_to_tmp_file"
            ) as mock_save_camera,
            patch("blender_camera.blender._call_blender_process") as mock_call_blender,
            patch(
                "builtins.open", mock_open(read_data=mock_image_data)
            ) as mock_file_open,
            patch("os.remove") as mock_remove,
            patch("shutil.rmtree") as mock_rmtree,
        ):
            mock_temp_dir.return_value.name = "/tmp/test_output"
            mock_save_camera.return_value = "/tmp/camera.json"
            mock_call_blender.return_value = None

            result = await render_img("test_url", camera)

            # Verify the result
            assert result == mock_image_data
            assert len(result) > 2000  # Should be substantial size

            # Verify color file was opened
            mock_file_open.assert_called_with("/tmp/test_output/color.png", "rb")

            # Verify cleanup
            mock_remove.assert_any_call("untitled.blend")
            mock_remove.assert_any_call("/tmp/camera.json")
            mock_rmtree.assert_called_once_with("/tmp/test_output")

    @pytest.mark.asyncio
    async def test_render_img_missing_color_file(self):
        """Test image rendering when color file is missing."""
        camera = Camera(id="test-camera", pose=[1.0, 2.0, 3.0, 0.1, 0.2, 0.3])

        with (
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch(
                "blender_camera.blender._save_camera_to_tmp_file"
            ) as mock_save_camera,
            patch("blender_camera.blender._call_blender_process") as mock_call_blender,
            patch("builtins.open", side_effect=FileNotFoundError("No such file")),
            patch("os.remove"),
            patch("shutil.rmtree"),
        ):
            mock_temp_dir.return_value.name = "/tmp/test_output"
            mock_save_camera.return_value = "/tmp/camera.json"
            mock_call_blender.return_value = None

            with pytest.raises(FileNotFoundError):
                await render_img("test_url", camera)


class TestFileOutputSizes:
    """Integration-style tests to validate output file characteristics."""

    @pytest.mark.asyncio
    async def test_render_outputs_have_minimum_sizes(self):
        """Test that render outputs meet minimum size requirements."""
        camera = Camera(id="test-camera", pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0])

        # Simulate realistic file sizes based on format and content
        color_size = 15000  # ~15KB for a small PNG image
        depth_size = 5000  # ~5KB for depth data
        normal_size = 8000  # ~8KB for normal data

        mock_color_data = b"PNG_HEADER" + b"\x00" * color_size
        mock_depth_data = b"PNG_HEADER" + b"\x00" * depth_size
        mock_normal_data = b"PNG_HEADER" + b"\x00" * normal_size

        with (
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch(
                "blender_camera.blender._save_camera_to_tmp_file"
            ) as mock_save_camera,
            patch("blender_camera.blender._call_blender_process") as mock_call_blender,
            patch("builtins.open", mock_open()) as mock_file_open,
            patch("os.remove"),
        ):
            mock_temp_dir.return_value.name = "/tmp/test_output"
            mock_save_camera.return_value = "/tmp/camera.json"
            mock_call_blender.return_value = None

            # Configure file reads
            file_contents = {
                "/tmp/test_output/color.png": mock_color_data,
                "/tmp/test_output/depth.png": mock_depth_data,
                "/tmp/test_output/normal.png": mock_normal_data,
            }

            def mock_file_open_side_effect(filename, mode="r"):
                if mode == "rb" and filename in file_contents:
                    return mock_open(read_data=file_contents[filename]).return_value
                return mock_open().return_value

            mock_file_open.side_effect = mock_file_open_side_effect

            result = await render_ply("test_url", camera)

            # Validate color output (what's returned)
            assert len(result) >= 10000, "Color output should be at least 10KB"
            assert result.startswith(b"PNG_HEADER"), "Should have PNG header"

            # Verify all three file types were accessed
            calls = [str(call) for call in mock_file_open.call_args_list]
            assert any("color.png" in call for call in calls), (
                "Color file should be accessed"
            )
            assert any("depth.png" in call for call in calls), (
                "Depth file should be accessed"
            )
            assert any("normal.png" in call for call in calls), (
                "Normal file should be accessed"
            )

    @pytest.mark.asyncio
    async def test_render_img_output_size(self):
        """Test that image render output meets size requirements."""
        camera = Camera(id="test-camera", pose=[0.0, 0.0, 5.0, 0.0, 0.0, 0.0])

        # Simulate a reasonable PNG file size
        image_size = 25000  # ~25KB
        mock_image_data = (
            b"PNG_FILE_HEADER" + b"\x89PNG\r\n\x1a\n" + b"\x00" * image_size
        )

        with (
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch(
                "blender_camera.blender._save_camera_to_tmp_file"
            ) as mock_save_camera,
            patch("blender_camera.blender._call_blender_process") as mock_call_blender,
            patch("builtins.open", mock_open(read_data=mock_image_data)),
            patch("os.remove"),
            patch("shutil.rmtree"),
        ):
            mock_temp_dir.return_value.name = "/tmp/test_output"
            mock_save_camera.return_value = "/tmp/camera.json"
            mock_call_blender.return_value = None

            result = await render_img("test_url", camera)

            # Validate output characteristics
            assert len(result) >= 20000, "Image output should be at least 20KB"
            assert len(result) <= 100000, (
                "Image output should not exceed 100KB for test data"
            )
            assert b"PNG" in result, "Should contain PNG markers"
