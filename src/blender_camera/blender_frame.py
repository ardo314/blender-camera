import os


class BlenderFrame:
    def __init__(self, color: str, depth: str, normal: str):
        self._color = color
        self._depth = depth
        self._normal = normal

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for filepath in [self._color, self._depth, self._normal]:
            if os.path.exists(filepath):
                os.remove(filepath)
