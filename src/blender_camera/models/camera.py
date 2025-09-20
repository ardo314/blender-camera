from pydantic import BaseModel

from blender_camera.models.id import Id
from blender_camera.models.pose import Pose


class Camera(BaseModel):
    id: Id
    pose: Pose
