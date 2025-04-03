import os
import sys
from enum import StrEnum
from typing import Annotated, Literal

import typer
from loguru import logger
from typer import Typer


class Level(StrEnum):
    """
    Log levels used to trace application execution.

    Attributes:
        TRACE   : Very fine-grained details for deep debugging.
        DEBUG   : Debugging information for developers.
        INFO    : General operational events.
        WARNING : Unexpected behavior that doesn't stop execution.
        ERROR   : Critical issues that affect functionality.
    """

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


LoggingLevel = Annotated[
    Level, typer.Option("--logging-level", "-l", help="Log level of the application.")
]

cli = Typer(
    name="rag",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    help="CLI for the FastAPI application.",
)


def _get_workers(expected_workers: int):
    """Get the number of workers to use."""

    max_workers = os.cpu_count()

    if expected_workers <= 0:
        logger.info(f"Uvicorn will use all possible hearts ({max_workers})")
        return max_workers

    workers = min(expected_workers, max_workers)
    logger.info(f"Uvicorn will use {workers} workers")
    return workers


def _run(
    host: str,
    port: int,
    source: str,
    workers: int = 1,
    reload: bool = False,
    environment: Literal["dev", "prod"] = "dev",
):
    """Run the server using uvicorn."""
    import uvicorn
    from rag import setup_environment

    logger.info(f"Running server on {host}:{port}")

    # Set up env var environment
    setup_environment(environment)

    # Get the amount workers available
    workers = _get_workers(workers)

    # Launch uvicorn in factory mode
    uvicorn.run(
        source,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        factory=True,
        log_level="warning",  # Disable uvicorn logs
    )


@cli.callback()
def callback(level: LoggingLevel = Level.INFO):
    """Callback to run before any command."""
    from dotenv import load_dotenv

    # Load envvars from dotenv file
    load_dotenv()

    # Remove default logger and add a linked to stdout
    logger.remove(0)

    # Restore default logger with correct log level
    logger.add(sys.stdout, level=level)


@cli.command()
def run(
    source: str = "rag.app:create_app",
    host: str = typer.Option("localhost", envvar="HOST"),
    port: int = typer.Option(8000, envvar="PORT"),
    workers: int = 1,
):
    """Run the server in production mode."""
    _run(
        host=host,
        port=port,
        source=source,
        workers=workers,
        environment="prod",
    )


@cli.command()
def dev(
    source: str = "rag.app:create_app",
    host: str = typer.Option("localhost", envvar="HOST"),
    port: int = typer.Option(8000, envvar="PORT"),
):
    """Run the server in development mode."""
    _run(
        host=host,
        port=port,
        reload=True,
        source=source,
        environment="dev",
    )
