import pytest

from blender_camera.blender import Blender


@pytest.mark.asyncio
async def test_run_blender_should_not_throw(
    blender: Blender,
):
    # Arrange
    # blender fixture is already arranged via dependency injection

    # Act & Assert
    await blender.run()
