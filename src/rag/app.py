from contextlib import asynccontextmanager

from chainlit.utils import mount_chainlit
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from rag import get_version, STATIC_PATH
from rag.routes import router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Create and close the global HTTP client."""
    logger.info("Starting FastAPI application lifecycle")
    yield
    logger.info("Shutting down FastAPI application lifecycle")


def create_app(
    title: str = "Chatbot API",
    version: str = get_version(),
    description: str = "API for Chatbot",
    lifespan: asynccontextmanager = _lifespan,
):
    """Create a new instance of the application."""
    app = FastAPI(
        title=title,
        version=version,
        description=description,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add static files
    app.mount("/public", StaticFiles(directory=STATIC_PATH), name="static")

    # Add routes for the API
    app.include_router(router=router)

    # Mount Chainlit application
    mount_chainlit(app=app, target="src/rag/interface.py", path="/")

    return app
