import asyncio

from loguru import logger


class Blender:
    def __init__(self, scene_path: str):
        self._scene_path = scene_path

    async def run(self, *args: str):
        proc = await asyncio.create_subprocess_exec(
            "blender",
            self._scene_path,
            "--background",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info(f"[blender] stdout: {stdout.decode()}")

        if proc.returncode != 0:
            logger.error(f"[blender] stderr: {stderr.decode()}")

            raise RuntimeError(
                f"Blender process failed with exit code {proc.returncode}"
            )
