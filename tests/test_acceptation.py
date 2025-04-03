import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/health"])
async def test_root(client: AsyncClient, route: str):
    """Test the root endpoint works."""
    response = await client.get(route)
    assert response.status_code == 200
