import os
from loguru import logger
from importlib.metadata import version


def get_version() -> str:
    try:
        return version("blender_camera")
    except Exception:
        return "undefined"


def log_banner():
    logger.info(r"""
Blender Camera Service
======================
""")


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "info")


def get_base_path() -> str:
    base_path = os.getenv("BASE_PATH", "")
    if base_path:
        base_path = "/" + base_path.lstrip("/")
        base_path = base_path.rstrip("/")

    return base_path
