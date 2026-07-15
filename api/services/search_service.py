"""
Combines keyword filters (system/severity/date) with semantic ranking, using the
lightweight numpy vector_store (see vector_store.py for why chromadb was replaced).

Per the Security doc: "Vector search unavailable -> Search endpoint falls back to
keyword-only search and tells the user semantic ranking is temporarily degraded."
Implemented as an explicit fallback path, not a silent failure.
"""
import logging
import sqlite3

from api.config import DATABASE_URL
from api.services.embedding_service import embedding_service
from api.services.vector_store import vector_store

logger = logging.getLogger(__name__)


def keyword_fallback_search(query: str, system, severity, limit: int = 20):
    """Degraded path when the vector store is unavailable -- plain SQL LIKE."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    sql = """
        SELECT r.asrs_report_id, r.narrative_text, g.ata_chapter_label, g.severity_label
        FROM reports r LEFT JOIN gold_labels g ON r.asrs_report_id = g.asrs_report_id
        WHERE 1=1
    """
    params = []
    if query:
        sql += " AND r.narrative_text LIKE ?"
        params.append(f"%{query}%")
    if system:
        sql += " AND g.ata_chapter_label = ?"
        params.append(system)
    if severity:
        sql += " AND g.severity_label = ?"
        params.append(severity)
    sql += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [
        {"report_id": r[0], "excerpt": (r[1] or "")[:300], "ata_chapter": r[2], "severity": r[3], "score": None}
        for r in rows
    ]


def search(query, system, severity, limit: int = 20):
    query = (query or "").strip()

    if not vector_store.loaded:
        return keyword_fallback_search(query, system, severity, limit), True

    try:
        if query and embedding_service.loaded:
            query_embedding = embedding_service.embed(query)
            results = vector_store.query(query_embedding, system, severity, limit)
            return results, False
        elif query and not embedding_service.loaded:
            return keyword_fallback_search(query, system, severity, limit), True
        else:
            results = vector_store.filter_only(system, severity, limit)
            return results, False
    except Exception:
        logger.exception("Search failed, falling back to keyword search")
        return keyword_fallback_search(query, system, severity, limit), True
