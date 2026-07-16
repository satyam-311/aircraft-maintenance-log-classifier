"""
Combines keyword filters (system/severity/date) with semantic ranking, using the
lightweight numpy vector_store (see vector_store.py for why chromadb was replaced).

Per the Security doc: "Vector search unavailable -> Search endpoint falls back to
keyword-only search and tells the user semantic ranking is temporarily degraded."
Implemented as an explicit fallback path, not a silent failure.
"""
import logging
import re
import sqlite3

from api.config import DATABASE_URL
from api.services.embedding_service import embedding_service
from api.services.vector_store import vector_store

logger = logging.getLogger(__name__)

# Common English stopwords stripped from keyword-fallback queries -- they carry no
# search signal and would otherwise dilute the match-count ranking below.
STOPWORDS = {
    "the", "a", "an", "and", "or", "is", "was", "were", "of", "to", "in", "on",
    "for", "at", "by", "with", "as", "from", "that", "this", "it", "be", "are",
    "been", "being", "has", "have", "had", "do", "does", "did", "but", "if",
    "then", "so", "than", "too", "very", "can", "will", "would", "should",
    "could", "may", "might", "must", "shall", "not", "no", "nor", "we", "they",
    "he", "she", "you", "i", "his", "her", "their", "our", "your", "its",
}
_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(query: str) -> list[str]:
    """Lowercase word tokens with stopwords/1-char noise dropped, deduped in
    first-seen order."""
    seen, tokens = set(), []
    for word in _TOKEN_RE.findall(query.lower()):
        if len(word) < 2 or word in STOPWORDS or word in seen:
            continue
        seen.add(word)
        tokens.append(word)
    return tokens


def keyword_fallback_search(query: str, system, severity, limit: int = 20):
    """Degraded path when the vector store is unavailable -- plain SQL LIKE.

    The old version matched the WHOLE query string as one substring pattern, so a
    pasted sentence only matched if it appeared verbatim -- effectively never. This
    tokenizes the query into significant words and ranks candidates (already filtered
    by system/severity in SQL) by how many distinct tokens each narrative contains,
    matching this codebase's own pattern of ranking in Python once the candidate set
    is small (see vector_store.py's brute-force-over-chromadb rationale)."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    sql = """
        SELECT r.asrs_report_id, r.narrative_text, g.ata_chapter_label, g.severity_label
        FROM reports r LEFT JOIN gold_labels g ON r.asrs_report_id = g.asrs_report_id
        WHERE 1=1
    """
    params = []
    if system:
        sql += " AND g.ata_chapter_label = ?"
        params.append(system)
    if severity:
        sql += " AND g.severity_label = ?"
        params.append(severity)
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    tokens = _tokenize(query) if query else []
    if tokens:
        scored = []
        for r in rows:
            narrative_lower = (r[1] or "").lower()
            match_count = sum(1 for t in tokens if t in narrative_lower)
            if match_count > 0:
                scored.append((match_count, r))
        scored.sort(key=lambda x: -x[0])
        rows = [r for _, r in scored[:limit]]
    else:
        rows = rows[:limit]

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
