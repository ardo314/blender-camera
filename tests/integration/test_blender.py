import pytest

from blender_camera.blender import Blender


@pytest.mark.asyncio
async def test_run_blender_should_return_output_with_blender_text_and_no_errors(
    blender: Blender,
):
    # Arrange
    # blender fixture is already arranged via dependency injection

    # Act
    stdout, stderr = await blender.run()

    # Assert
    assert "Blender" in stdout
    assert stderr == ""
