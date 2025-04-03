from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from rag import get_version, Version
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

    # Add routes for the API
    app.include_router(router=router)

    return app
