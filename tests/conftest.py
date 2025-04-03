import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from rag.app import create_app


@pytest_asyncio.fixture
async def client():
    """Return an async client to test the application."""
    app = create_app()
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    await client.aclose()  # Cleanup
