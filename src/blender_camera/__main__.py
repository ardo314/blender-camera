import asyncio
from blender_camera.app import App
from blender_camera.utils import log_banner


async def _main():
    log_banner()

    app = App()
    try:
        await app.start()
        await app.start_api("0.0.0.0", 8080)
    finally:
        await app.stop()


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
