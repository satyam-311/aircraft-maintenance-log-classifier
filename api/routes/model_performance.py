"""
GET /model-performance — Ticket 16. Reads the metrics JSON files Ticket 6's
evaluate.py / evaluate_severity.py already exported, no manual copy-pasting.
"""
import json
from pathlib import Path

from fastapi import APIRouter

from api.config import BASE_DIR

router = APIRouter()

ATA_METRICS_PATH = BASE_DIR / "reports" / "ata_classifier" / "metrics.json"
SEVERITY_METRICS_PATH = BASE_DIR / "reports" / "severity_classifier" / "metrics.json"


def _load(path: Path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


@router.get("/model-performance")
def model_performance():
    return {
        "ata_classifier": _load(ATA_METRICS_PATH),
        "severity_classifier": _load(SEVERITY_METRICS_PATH),
    }
