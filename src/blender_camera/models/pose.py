Pose = list[float]  # [x, y, z, rx, ry, rz]


def validate_pose(pose: Pose) -> bool:
    """Validate that the pose is a list of 6 floats."""
    return (
        isinstance(pose, list)
        and len(pose) == 6
        and all(isinstance(x, float) for x in pose)
    )
