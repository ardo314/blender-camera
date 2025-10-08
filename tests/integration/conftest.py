from pathlib import Path

import pytest

from blender_camera.blender import Blender


@pytest.fixture
def blender() -> Blender:
    test_scene_path = Path(__file__).parent / "resources" / "cube.blend"
    return Blender(str(test_scene_path))
