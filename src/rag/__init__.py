import os
import tomllib
from pathlib import Path
from typing import Literal, Tuple

from loguru import logger


type Version = Tuple[int, int, int]


def is_dev():
    """Check if the application is in development mode."""
    return os.getenv("ENVIRONMENT") == "DEV"


def is_prod():
    """Check if the application is in production mode."""
    return os.getenv("ENVIRONMENT") == "PROD"


def setup_environment(environment: Literal["dev", "prod"]):
    """Setup the application in a given mode."""
    environment = environment.upper()
    os.environ["ENVIRONMENT"] = environment
    logger.info(f"Setting up mode: {environment}")


def lint():
    """Run formatter and linter (ruff) on the codebase."""
    import subprocess

    subprocess.run("uv run ruff format .")
    subprocess.run("uv run ruff check . --fix")


def get_version() -> str:
    """Get the version of the application."""
    # Get the version of the pyproject.toml file
    pyproject_path = PROJECT_PATH / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    dict_content = tomllib.loads(content)
    return dict_content["project"]["version"]


def cli():
    """Run the CLI of the application."""
    from rag.__main__ import main

    main()


# Global variables of the project
PROJECT_PATH = Path(__file__).parents[2]
