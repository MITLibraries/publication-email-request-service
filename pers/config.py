import logging
import os
from collections.abc import Iterable
from typing import Any


class Config:
    REQUIRED_ENV_VARS: Iterable[str] = [
        # "WORKSPACE",
        # "SENTRY_DSN",
        "ELEMENTS_ENDPOINT",
        "ELEMENTS_USER",
        "ELEMENTS_PASSWORD",
        "QUOTAGUARD_STATIC_URL",
        "PERS_DATABASE_CONNECTION_STRING",
    ]

    OPTIONAL_ENV_VARS: Iterable[str] = ["LOG_LEVEL"]

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Provide dot notation access to configurations and env vars on this class."""
        if name in self.REQUIRED_ENV_VARS or name in self.OPTIONAL_ENV_VARS:
            return os.getenv(name)
        message = f"'{name}' not a valid configuration variable"
        raise AttributeError(message)

    def check_required_env_vars(self) -> None:
        """Method to raise exception if required env vars not set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            message = f"Missing required environment variables: {', '.join(missing_vars)}"
            raise OSError(message)

    def configure_logger(self, verbose: bool) -> str:  # noqa: FBT001
        root_logger = logging.getLogger()
        if verbose:
            logging.basicConfig(
                format="%(asctime)s %(levelname)s %(name)s.%(funcName)s() "
                "line %(lineno)d: %(message)s",
            )
            root_logger.setLevel(logging.DEBUG)
            for handler in logging.root.handlers:
                handler.addFilter(logging.Filter("pers"))
        else:
            logging.basicConfig(
                format=("%(asctime)s %(levelname)s %(name)s.%(funcName)s(): %(message)s")
            )
            root_logger.setLevel(
                level=logging.INFO,
            )
        return (
            f"Logger '{root_logger.name}' configured with level="
            f"{logging.getLevelName(root_logger.getEffectiveLevel())}"
        )
