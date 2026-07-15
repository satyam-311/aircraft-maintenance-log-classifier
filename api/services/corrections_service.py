"""
Ticket 10 support logic.

corrections.report_id is the INTERNAL integer id (per the Technical Architecture doc's
schema: "report_id integer, foreign key -> reports.id"), but the public API accepts the
human-facing asrs_report_id string -- this module handles that translation.
"""
import sqlite3
from datetime import datetime, timezone

from api.config import DATABASE_URL
from api.services.model_service import model_service

VALID_FIELDS = {"ata_chapter", "severity"}

CREATE_CORRECTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    field_corrected TEXT NOT NULL,
    original_prediction TEXT,
    corrected_value TEXT NOT NULL,
    corrected_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports(id)
);
"""


def _get_db():
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_CORRECTIONS_TABLE_SQL)
    return conn


class ReportNotFoundError(Exception):
    pass


class InvalidFieldError(Exception):
    pass


def submit_correction(asrs_report_id: str, field_corrected: str, corrected_value: str):
    if field_corrected not in VALID_FIELDS:
        raise InvalidFieldError(f"field_corrected must be one of {VALID_FIELDS}")

    conn = _get_db()
    row = conn.execute(
        "SELECT id, narrative_text, predicted_ata_chapter, predicted_severity FROM reports WHERE asrs_report_id = ?",
        (asrs_report_id,),
    ).fetchone()

    if row is None:
        conn.close()
        raise ReportNotFoundError()

    internal_id, narrative_text, predicted_ata, predicted_severity = row

    stored_prediction = predicted_ata if field_corrected == "ata_chapter" else predicted_severity

    if stored_prediction:
        original_prediction = stored_prediction
    else:
        # Never classified before -- compute live and cache it, so the next lookup
        # (or the dashboard/API) doesn't need to recompute it.
        result = model_service.predict(narrative_text)
        original_prediction = (
            result["ata_chapter"] if field_corrected == "ata_chapter" else result["severity"]
        )
        conn.execute(
            "UPDATE reports SET predicted_ata_chapter = ?, predicted_severity = ?, "
            "ata_confidence = ?, severity_confidence = ? WHERE id = ?",
            (
                result["ata_chapter"], result["severity"],
                result["ata_confidence"], result["severity_confidence"],
                internal_id,
            ),
        )

    conn.execute(
        """INSERT INTO corrections (report_id, field_corrected, original_prediction, corrected_value, corrected_at)
           VALUES (?, ?, ?, ?, ?)""",
        (internal_id, field_corrected, original_prediction, corrected_value, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
