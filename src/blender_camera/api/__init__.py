from fastapi import FastAPI


class Api:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_api_route("/", self.root, methods=["GET"])
        self.app.add_api_route("/health", self.health, methods=["GET"])

    async def root(self):
        return {"message": "Welcome to Blender Camera API"}

    async def health(self):
        return {"status": "ok"}
