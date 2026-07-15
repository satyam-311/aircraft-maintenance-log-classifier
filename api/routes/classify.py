"""
POST /classify — Ticket 8, extended for Ticket 13's correction flow.

Every classified narrative is persisted to `reports` (with predictions cached), even
if it's freshly pasted text rather than an ingested ASRS report. This gives the
frontend a report_id to submit corrections against -- Ticket 13 explicitly requires
"correction flow works end-to-end," which isn't possible without something to
correct against. Ad-hoc submissions get an "adhoc-<uuid>" id, clearly distinguishable
from real ASRS accession numbers.

Error handling follows the Security & Access doc's table exactly:
  - Model service unavailable -> 503, no raw stack trace
  - Empty/near-empty narrative -> 400 with the specified message
  - Narrative exceeds max token length -> truncate, return a visible warning
  - Low-confidence prediction -> still returned (not hidden/blocked), confidence
    exposed so the frontend can flag it (Ticket 13's job, not this endpoint's)
"""
import logging
import sqlite3
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.config import LOW_CONFIDENCE_THRESHOLD, MIN_NARRATIVE_WORDS, DATABASE_URL
from api.services.model_service import model_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ClassifyRequest(BaseModel):
    narrative_text: str = Field(..., description="Raw maintenance/incident narrative text")


class OtherPossibleSystem(BaseModel):
    label: str
    confidence: float


class ClassifyResponse(BaseModel):
    report_id: str
    ata_chapter: str
    ata_confidence: float
    ata_other_possible: list[OtherPossibleSystem]
    severity: str
    severity_confidence: float
    ata_low_confidence: bool
    severity_low_confidence: bool
    warnings: list[str] = []


def _persist_classification(narrative_text: str, result: dict) -> str:
    """Saves the narrative + predictions, returns the asrs_report_id to use for corrections.
    If this exact text was already classified before, reuses that row instead of duplicating."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)

    existing = conn.execute(
        "SELECT asrs_report_id FROM reports WHERE narrative_text = ?", (narrative_text,)
    ).fetchone()

    if existing:
        report_id = existing[0]
        conn.execute(
            "UPDATE reports SET predicted_ata_chapter=?, predicted_severity=?, "
            "ata_confidence=?, severity_confidence=? WHERE asrs_report_id=?",
            (result["ata_chapter"], result["severity"], result["ata_confidence"],
             result["severity_confidence"], report_id),
        )
    else:
        report_id = f"adhoc-{uuid.uuid4().hex[:12]}"
        conn.execute(
            """INSERT INTO reports
               (asrs_report_id, narrative_text, predicted_ata_chapter, predicted_severity,
                ata_confidence, severity_confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (report_id, narrative_text, result["ata_chapter"], result["severity"],
             result["ata_confidence"], result["severity_confidence"]),
        )

    conn.commit()
    conn.close()
    return report_id


@router.post("/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest):
    text = request.narrative_text.strip()

    # Security doc: "Empty or near-empty narrative submitted"
    word_count = len(text.split())
    if word_count < MIN_NARRATIVE_WORDS:
        raise HTTPException(
            status_code=400,
            detail="Please enter a report narrative (at least a few words) to classify.",
        )

    # Security doc: "Model service unavailable / fails to load"
    if not model_service.loaded:
        raise HTTPException(
            status_code=503,
            detail="Classification service temporarily unavailable — please try again shortly.",
        )

    try:
        result = model_service.predict(text)
    except Exception:
        logger.exception("Unexpected error during classification")
        raise HTTPException(
            status_code=503,
            detail="Classification service temporarily unavailable — please try again shortly.",
        )

    report_id = _persist_classification(text, result)

    warnings = []
    if result["text_was_truncated"]:
        warnings.append(
            "Your text was shortened to fit the model's input limit; classification may be less accurate."
        )

    return ClassifyResponse(
        report_id=report_id,
        ata_chapter=result["ata_chapter"],
        ata_confidence=result["ata_confidence"],
        ata_other_possible=result["ata_other_possible"],
        severity=result["severity"],
        severity_confidence=result["severity_confidence"],
        ata_low_confidence=result["ata_confidence"] < LOW_CONFIDENCE_THRESHOLD,
        severity_low_confidence=result["severity_confidence"] < LOW_CONFIDENCE_THRESHOLD,
        warnings=warnings,
    )
