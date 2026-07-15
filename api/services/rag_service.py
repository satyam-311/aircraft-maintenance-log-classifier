"""
Ticket 11 — RAG service. Retrieval always runs locally (reuses Ticket 9's search).
Generation calls Groq's OpenAI-compatible chat completions endpoint.

Per Security doc: if the LLM call fails/times out, the endpoint must still return the
retrieved sources with a graceful message -- retrieval never depends on generation
succeeding.
"""
import logging

import requests

from api.config import LLM_API_KEY

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # fast, free-tier friendly
REQUEST_TIMEOUT_SECONDS = 15


def retrieve_context(question: str, top_k: int = 5):
    """Reuses the same semantic search built in Ticket 9 -- retrieval doesn't
    depend on the LLM at all, so it always works even if generation fails."""
    from api.services.vector_store import vector_store
    from api.services.embedding_service import embedding_service
    if not vector_store.loaded or not embedding_service.loaded:
        return []
    query_embedding = embedding_service.embed(question)
    return vector_store.query(query_embedding, system=None, severity=None, limit=top_k)


def _build_prompt(question: str, sources: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[Source {i+1}, Report {s['report_id']}]: {s['excerpt']}"
        for i, s in enumerate(sources)
    )
    return (
        "You are an aviation maintenance analyst assistant. Answer the question using "
        "ONLY the report excerpts below. Cite sources as [Source N]. If the excerpts "
        "don't contain enough information, say so plainly rather than guessing.\n\n"
        f"Report excerpts:\n{context_block}\n\n"
        f"Question: {question}\n\nAnswer:"
    )


def ask(question: str, top_k: int = 5):
    sources = retrieve_context(question, top_k)

    if not LLM_API_KEY:
        return {
            "answer": None,
            "sources": sources,
            "generation_error": "No LLM API key configured — showing retrieved sources only.",
        }

    if not sources:
        return {
            "answer": None,
            "sources": [],
            "generation_error": "No relevant reports found for this question.",
        }

    prompt = _build_prompt(question, sources)

    try:
        response = requests.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        return {"answer": answer, "sources": sources, "generation_error": None}

    except Exception as e:
        # Security doc: retrieval still returns even if generation fails
        logger.error(f"LLM generation failed: {e}")
        return {
            "answer": None,
            "sources": sources,
            "generation_error": "Answer generation is temporarily unavailable — showing the most relevant reports instead.",
        }
