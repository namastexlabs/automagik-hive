"""FastAPI router exposing Genie wish catalog metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies.wish import WishMetadata, get_wish_catalog
from lib.auth.dependencies import require_api_key


class WishCatalogResponse(BaseModel):
    """Response model encapsulating wish metadata entries."""

    wishes: list[WishMetadata]


wish_router = APIRouter(
    prefix="/wishes",
    tags=["wishes"],
    dependencies=[Depends(require_api_key)],
)


@wish_router.get(
    "",
    response_model=WishCatalogResponse,
    summary="List available Genie wishes",
)
async def list_wishes(
    catalog: list[WishMetadata] = Depends(get_wish_catalog),
) -> WishCatalogResponse:
    """Return the curated wish catalog sourced from Genie workspace."""

    return WishCatalogResponse(wishes=catalog)
