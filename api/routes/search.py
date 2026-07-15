"""
GET /search — Ticket 9.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from api.services import search_service

router = APIRouter()


class SearchResult(BaseModel):
    report_id: str
    excerpt: str
    ata_chapter: str | None
    severity: str | None
    score: float | None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    degraded: bool
    degraded_message: str | None = None


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query("", description="Natural-language search query"),
    system: str | None = Query(None, description="ATA chapter code to filter by"),
    severity: str | None = Query(None, description="Severity level to filter by"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(20, le=100),
):
    results, degraded = search_service.search(q, system, severity, limit)

    return SearchResponse(
        results=results,
        degraded=degraded,
        degraded_message=(
            "Semantic ranking is temporarily degraded — showing keyword matches only."
            if degraded else None
        ),
    )
