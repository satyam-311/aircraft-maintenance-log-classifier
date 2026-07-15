"""
GET /stats — supports Ticket 12 (Dashboard page), which explicitly depends on
"a basic /stats-style read endpoint" per the ticket list.
"""
import sqlite3

from fastapi import APIRouter
from pydantic import BaseModel

from api.config import DATABASE_URL

router = APIRouter()


class SystemBreakdown(BaseModel):
    ata_chapter: str
    count: int


class SeverityByMonth(BaseModel):
    month: str  # YYYYMM, matches ASRS's de-identified date precision
    severity: str
    count: int


class StatsResponse(BaseModel):
    total_reports: int
    total_classified: int
    system_breakdown: list[SystemBreakdown]
    severity_over_time: list[SeverityByMonth]


@router.get("/stats", response_model=StatsResponse)
def stats():
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)

    total_reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    total_classified = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE predicted_ata_chapter IS NOT NULL"
    ).fetchone()[0]

    system_rows = conn.execute("""
        SELECT ata_chapter_label, COUNT(*) c FROM gold_labels
        WHERE ata_chapter_label IS NOT NULL
        GROUP BY ata_chapter_label ORDER BY c DESC
    """).fetchall()

    severity_rows = conn.execute("""
        SELECT r.report_date, g.severity_label, COUNT(*) c
        FROM reports r JOIN gold_labels g ON r.asrs_report_id = g.asrs_report_id
        WHERE g.severity_label IS NOT NULL AND r.report_date IS NOT NULL
        GROUP BY r.report_date, g.severity_label
        ORDER BY r.report_date
    """).fetchall()

    conn.close()

    return StatsResponse(
        total_reports=total_reports,
        total_classified=total_classified,
        system_breakdown=[SystemBreakdown(ata_chapter=r[0], count=r[1]) for r in system_rows],
        severity_over_time=[
            SeverityByMonth(month=str(r[0]), severity=r[1], count=r[2]) for r in severity_rows
        ],
    )
