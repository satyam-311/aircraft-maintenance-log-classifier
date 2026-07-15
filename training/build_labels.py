"""
Ticket 2 — Build ATA Chapter & Severity Label Set.

1. Creates the frozen `ata_chapters` reference table (per Technical Architecture doc).
2. Maps the real ASRS "Aircraft Component" field -> our 12 ATA chapters via keyword matching.
3. Derives a severity label from ASRS's own "Anomaly" and "Result" fields (documented heuristic
   below) rather than manual labeling, since ASRS has no direct severity field.
4. Writes a `gold_labels` table: (asrs_report_id, ata_chapter_label, severity_label, label_source)
   — this is BOOTSTRAP training data, not model output. It stays separate from the
   predicted_ata_chapter / predicted_severity columns on `reports`, which are populated
   by the trained model in later tickets.

Coverage is reported at the end — not every report will get a confident label; unlabeled
reports are simply excluded from the training set (Ticket 3), not dropped from `reports`.
"""
import argparse
import re
import sqlite3
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# 1. Frozen ATA chapter label set (matches Technical Architecture doc examples,
#    extended to the chapters actually present in the real ASRS "Aircraft Component" data)
# ---------------------------------------------------------------------------
# FROZEN 2026-07-14. Chapters 73 (Engine Fuel and Control, 7 examples) and 56 (Windows,
# 6 examples) were merged into 71 and 21 respectively — too little real training data to
# support them as standalone classes. See COMPONENT_TO_ATA below: fuel-metering/pump
# keywords now route to "71", window/windshield keywords now route to "21".
ATA_CHAPTERS = [
    ("21", "Air Conditioning / Pressurization / Windows"),
    ("24", "Electrical Power"),
    ("25", "Equipment / Furnishings"),
    ("27", "Flight Controls"),
    ("28", "Fuel"),
    ("29", "Hydraulic Power"),
    ("32", "Landing Gear"),
    ("34", "Navigation"),
    ("35", "Oxygen"),
    ("36", "Pneumatic"),
    ("49", "Airborne Auxiliary Power (APU)"),
    ("52", "Doors"),
    ("71", "Powerplant / Engine Fuel and Control"),
    ("78", "Engine Exhaust"),
    ("79", "Oil"),
    ("25-EM", "Emergency Equipment"),  # escape slides, emergency exits — not a real ATA# but needed
]

# Keyword -> ATA code. Checked as case-insensitive substring against "Aircraft Component".
# First match wins, so more specific keywords are listed before general ones.
COMPONENT_TO_ATA = [
    (r"escape slide|emergency exit|life vest|smoke detector|fire ext", "25-EM"),
    (r"oxygen", "35"),
    (r"pitot|static system|air data|altimeter|flight director|ils|nav\b|gps", "34"),
    (r"window|windshield", "21"),  # merged into 21 per Ticket 2 decision (too few standalone examples)
    (r"door", "52"),
    (r"pressurization|air conditioning|pack valve|outflow valve|cabin press", "21"),
    (r"pneumatic|bleed", "36"),
    (r"apu", "49"),
    (r"hydraulic", "29"),
    (r"landing gear|main gear|nose gear|wheel|tire|brake|gear extend|gear door", "32"),
    (r"flap|aileron|rudder|elevator|spoiler|trim|flight control", "27"),
    (r"fuel filler|fuel quantity|fuel tank|fuel gauge", "28"),
    (r"fuel pump|fuel metering|fuel transmitter|fuel low pressure|fuel control", "71"),  # merged into 71
    (r"generator|alternator|battery|electrical wiring|circuit breaker|dc bus|ac bus", "24"),
    (r"exhaust|thrust reverser", "78"),
    (r"turbine engine|fan blade|engine mount|cowling|powerplant|engine\b", "71"),
    (r"oil filler|oil cooler|oil pressure|oil quantity", "79"),
    (r"seat|galley|lavatory|cargo|furnishing", "25"),
]


def map_component_to_ata(component: str):
    if not isinstance(component, str) or not component.strip():
        return None
    text = component.lower()
    for pattern, ata_code in COMPONENT_TO_ATA:
        if re.search(pattern, text):
            return ata_code
    return None


# ---------------------------------------------------------------------------
# 2. Severity heuristic v2 — multi-signal scoring, not a single-field first-match.
#    v1 (Anomaly + Result only) scored 45.7% test accuracy / 0.367 macro-F1,
#    well under the 0.70 target -- too little signal per report. v2 adds three
#    more ASRS fields that carry real severity information:
#      - Were Passengers Involved In Event (Y/N)   -> direct safety relevance
#      - When Detected (In-flight vs Routine Inspection) -> urgency of discovery
#      - Maintenance Status.Maintenance Deferred (Y/N)   -> deferred-under-MEL
#        items were judged non-urgent enough to keep flying -> pulls toward Low
#    Each signal adds/subtracts points; final score is bucketed into 4 levels.
#    This is still a heuristic, not ground truth -- documented, not hidden.
# ---------------------------------------------------------------------------
def derive_severity(anomaly, result, passengers_involved, when_detected, maint_deferred):
    anomaly = anomaly if isinstance(anomaly, str) else ""
    result = result if isinstance(result, str) else ""
    passengers_involved = passengers_involved if isinstance(passengers_involved, str) else ""
    when_detected = when_detected if isinstance(when_detected, str) else ""
    maint_deferred = maint_deferred if isinstance(maint_deferred, str) else ""

    # If literally none of the source fields had any content, we can't score at all.
    if not (anomaly or result or passengers_involved or when_detected or maint_deferred):
        return None

    score = 0

    if re.search(r"physical injury|incapacitation|emergency condition|evasive action", result, re.I):
        score += 4
    if passengers_involved.strip().upper() == "Y":
        score += 2
    if "Aircraft Equipment Problem Critical" in anomaly:
        score += 2
    if re.search(r"in-flight", when_detected, re.I):
        score += 1
    if re.search(r"aircraft damaged|flight cancelled|returned to departure|returned to gate", result, re.I):
        score += 1

    if maint_deferred.strip().upper() == "Y":
        score -= 1
    if "Aircraft Equipment Problem Less Severe" in anomaly:
        score -= 1
    if re.search(r"^general maintenance action$", result.strip(), re.I):
        score -= 1

    if score >= 3:
        return "High"  # Safety-Critical merged into High (2026-07-14): only ~60 examples
                        # total, model scored 0.00 F1 on it standalone -- structurally too
                        # small to learn as its own class at this dataset size.
    if score >= 1:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
def build(csv_path: str, db_path: str):
    conn = sqlite3.connect(db_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ata_chapters (
            ata_code TEXT PRIMARY KEY,
            system_name TEXT NOT NULL
        );
    """)
    conn.executemany(
        "INSERT OR REPLACE INTO ata_chapters (ata_code, system_name) VALUES (?, ?)", ATA_CHAPTERS
    )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS gold_labels (
            asrs_report_id TEXT PRIMARY KEY,
            ata_chapter_label TEXT,
            severity_label TEXT,
            label_source TEXT NOT NULL,
            FOREIGN KEY (asrs_report_id) REFERENCES reports(asrs_report_id)
        );
    """)

    df = pd.read_csv(csv_path, low_memory=False)
    rows = []
    for _, row in df.iterrows():
        acn = str(row.get("ACN", "")).strip()
        if not acn:
            continue
        ata_label = map_component_to_ata(row.get("Aircraft Component"))
        severity_label = derive_severity(
            row.get("Anomaly"),
            row.get("Result"),
            row.get("Were Passengers Involved In Event"),
            row.get("When Detected"),
            row.get("Maintenance Status.Maintenance Deferred"),
        )
        if ata_label or severity_label:
            rows.append((acn, ata_label, severity_label, "asrs_field_heuristic_v2"))

    conn.executemany(
        """INSERT OR REPLACE INTO gold_labels (asrs_report_id, ata_chapter_label, severity_label, label_source)
           VALUES (?, ?, ?, ?)""",
        rows,
    )
    conn.commit()

    # ---- Coverage report ----
    total_reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    both = conn.execute(
        "SELECT COUNT(*) FROM gold_labels WHERE ata_chapter_label IS NOT NULL AND severity_label IS NOT NULL"
    ).fetchone()[0]
    ata_only = conn.execute(
        "SELECT COUNT(*) FROM gold_labels WHERE ata_chapter_label IS NOT NULL"
    ).fetchone()[0]
    sev_only = conn.execute(
        "SELECT COUNT(*) FROM gold_labels WHERE severity_label IS NOT NULL"
    ).fetchone()[0]

    print(f"Total reports in DB: {total_reports}")
    print(f"Reports with an ATA-chapter label: {ata_only} ({ata_only/total_reports:.1%})")
    print(f"Reports with a severity label: {sev_only} ({sev_only/total_reports:.1%})")
    print(f"Reports with BOTH labels (usable for both classifiers): {both} ({both/total_reports:.1%})")
    print()
    print("ATA-chapter label distribution:")
    dist = conn.execute("""
        SELECT ata_chapter_label, COUNT(*) c FROM gold_labels
        WHERE ata_chapter_label IS NOT NULL GROUP BY ata_chapter_label ORDER BY c DESC
    """).fetchall()
    for code, count in dist:
        name = dict(ATA_CHAPTERS).get(code, "?")
        print(f"  {code} ({name}): {count}")
    print()
    print("Severity label distribution:")
    dist = conn.execute("""
        SELECT severity_label, COUNT(*) c FROM gold_labels
        WHERE severity_label IS NOT NULL GROUP BY severity_label ORDER BY c DESC
    """).fetchall()
    for label, count in dist:
        print(f"  {label}: {count}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/raw/asrs_real_merged.csv")
    parser.add_argument("--db", default="data/processed/reports.db")
    args = parser.parse_args()
    build(args.csv, args.db)
