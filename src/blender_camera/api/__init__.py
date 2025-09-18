from fastapi import FastAPI


class Api:
    def __init__(self, version: str):
        self.app = FastAPI(
            title="Blender Camera API",
            description="API for controlling Blender camera operations",
            version=version,
            docs_url="/docs",
            swagger_ui_parameters={"tryItOutEnabled": True},
        )
        self.app.add_api_route("/", self.root, methods=["GET"])
        self.app.add_api_route("/cameras", self.get_cameras, methods=["GET"])
        self.app.add_api_route("/cameras", self.create_camera, methods=["POST"])
        self.app.add_api_route("/cameras/{camera_id}", self.get_camera, methods=["GET"])
        self.app.add_api_route(
            "/cameras/{camera_id}", self.delete_camera, methods=["DELETE"]
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/pose", self.set_camera_pose, methods=["PUT"]
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/pointcloud", self.get_pointcloud, methods=["GET"]
        )
        self.app.add_api_route(
            "/cameras/{camera_id}/image", self.get_image, methods=["GET"]
        )

    async def root(self):
        return {"message": "Welcome to Blender Camera API"}

    async def get_cameras(self):
        return {"cameras": []}

    async def create_camera(self):
        return {"camera": "created"}

    async def get_camera(self, camera_id: str):
        return {"camera": camera_id}

    async def delete_camera(self, camera_id: str):
        return {"camera": "deleted"}

    async def set_camera_pose(self, camera_id: str):
        return {"camera": "pose set"}

    async def get_pointcloud(self):
        return {"pointcloud": "data"}

    async def get_image(self):
        return {"image": "data"}
