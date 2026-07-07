import os

from .settings import *  # noqa: F403


DATABASES["default"].setdefault("TEST", {})["NAME"] = os.getenv(  # noqa: F405
    "TEST_DATABASE_NAME",
    "test_pethome_isolated",
)
