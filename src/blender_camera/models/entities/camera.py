from blender_camera.models.components.has_pose import HasPose
from blender_camera.models.entities.entity import Entity
from blender_camera.models.pose import Pose


class Camera(Entity, HasPose):
    pose: Pose
