import asyncio


class Blender:
    def __init__(self, scene_path: str):
        self._scene_path = scene_path

    async def run(self, *args: str) -> tuple[str, str]:
        proc = await asyncio.create_subprocess_exec(
            "blender",
            self._scene_path,
            "--background",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Blender process failed with exit code {proc.returncode}"
            )

        return stdout.decode(), stderr.decode()
