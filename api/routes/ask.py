"""
POST /ask — Ticket 11 (RAG stretch).
"""
from fastapi import APIRouter
from pydantic import BaseModel

from api.services import rag_service

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    report_id: str
    excerpt: str
    ata_chapter: str | None
    severity: str | None
    score: float | None


class AskResponse(BaseModel):
    answer: str | None
    sources: list[SourceItem]
    generation_error: str | None = None


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    result = rag_service.ask(request.question)
    return AskResponse(**result)
