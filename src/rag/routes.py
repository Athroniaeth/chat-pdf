from fastapi import APIRouter

from rag import get_version


router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": get_version()}
