"""
Ticket 1 — Ingest ASRS Dataset.

Loads a CSV (synthetic sample OR a real ASRS Database Online export) into a
normalized SQLite `reports` table, per the schema in the Technical Architecture doc.

Design note: the real official ASRS CSV export uses column names like
"ACN", "Date / Local Time Of Day", "Aircraft 1 / Make Model Name",
"Aircraft 1 / Flight Phase", "Report 1 / Narrative", etc. (see the qge/ASRS
schema dump for the exact field names). COLUMN_MAP below is the single place
to adjust if the real export's column headers differ slightly from what's
listed here — nothing else in this script should need to change.

Usage:
    python training/preprocess.py --input data/raw/asrs_sample.csv --db data/processed/reports.db
"""
import argparse
import csv
import html
import re
import sqlite3
from pathlib import Path

# Map: our normalized field -> possible source column names (checked in order)
# Confirmed against the real ASRS Database Online CSV export header (July 2026).
COLUMN_MAP = {
    "asrs_report_id": ["ACN", "__ACN", "Person_1__ASRS_Report_Number.Accession_Number"],
    "narrative_text": ["Narrative", "Report_1__Narrative"],
    "report_date": ["Date", "Time__Date"],
    "aircraft_type": ["Make Model Name", "Aircraft_Make_Model", "Aircraft_1__Make_Model_Name"],
    "phase_of_flight": ["Flight Phase", "Flight_Phase", "Aircraft_1__Flight_Phase"],
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asrs_report_id TEXT UNIQUE NOT NULL,
    narrative_text TEXT NOT NULL,
    report_date TEXT,
    aircraft_type TEXT,
    phase_of_flight TEXT,
    predicted_ata_chapter TEXT,
    predicted_severity TEXT,
    ata_confidence REAL,
    severity_confidence REAL,
    embedding_id TEXT
);
"""


def clean_text(raw: str) -> str:
    """Strip HTML entities/tags and normalize whitespace from a raw narrative."""
    if raw is None:
        return ""
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", " ", text)          # strip stray HTML tags
    text = re.sub(r"\s+", " ", text).strip()       # collapse whitespace
    return text


def find_column(row_keys, candidates):
    for c in candidates:
        if c in row_keys:
            return c
    return None


def is_official_export(input_file: Path) -> bool:
    """Detect the real ASRS Database Online export: first data cell of row 1 is
    blank (category header row), and row 2's first field is 'ACN'."""
    with input_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            row0 = next(reader)
            row1 = next(reader)
        except StopIteration:
            return False
    return len(row0) > 1 and row0[0].strip() == "" and row1 and row1[0].strip() == "ACN"


def parse_official_date(raw: str):
    """Official export dates are 'YYYYMM' (e.g. '202101') -> '2021-01-01'."""
    raw = (raw or "").strip()
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-01"
    return raw or None


def ingest_official(input_file: Path, conn: sqlite3.Connection):
    """Ingest the real ASRS Database Online CSV export (two-row header,
    duplicate column names like 'Narrative' appearing for each reporter)."""
    with input_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    field_row = rows[1]  # row 0 is the category header, row 1 is field names
    data_rows = [r for r in rows[2:] if any(cell.strip() for cell in r)]

    def idx(name):
        try:
            return field_row.index(name)  # first occurrence = primary reporter's field
        except ValueError:
            return None

    i_acn = idx("ACN")
    i_date = idx("Date")
    i_aircraft = idx("Make Model Name")
    i_phase = idx("Flight Phase")
    i_narrative = idx("Narrative")

    if i_acn is None or i_narrative is None:
        raise ValueError("Could not find required 'ACN' or 'Narrative' columns in official export.")

    inserted, skipped_dupe, skipped_empty = 0, 0, 0
    for row in data_rows:
        if len(row) <= max(i_acn, i_narrative):
            skipped_empty += 1
            continue

        asrs_id = row[i_acn].strip()
        narrative = clean_text(row[i_narrative])
        if not asrs_id or not narrative:
            skipped_empty += 1
            continue

        report_date = parse_official_date(row[i_date]) if i_date is not None and i_date < len(row) else None
        aircraft_type = row[i_aircraft].strip() if i_aircraft is not None and i_aircraft < len(row) else None
        phase = row[i_phase].strip() if i_phase is not None and i_phase < len(row) else None

        try:
            conn.execute(
                """INSERT INTO reports
                   (asrs_report_id, narrative_text, report_date, aircraft_type, phase_of_flight)
                   VALUES (?, ?, ?, ?, ?)""",
                (asrs_id, narrative, report_date, aircraft_type, phase),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped_dupe += 1

    return inserted, skipped_dupe, skipped_empty


def ingest(input_path: str, db_path: str):
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_file}")

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE_SQL)

    if is_official_export(input_file):
        print("Detected official ASRS Database Online export format.")
        inserted, skipped_dupe, skipped_empty = ingest_official(input_file, conn)
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        conn.close()
        print(f"Inserted: {inserted}")
        print(f"Skipped (duplicate asrs_report_id): {skipped_dupe}")
        print(f"Skipped (empty id/narrative): {skipped_empty}")
        print(f"Total rows now in reports table: {total}")
        return

    inserted, skipped_dupe, skipped_empty = 0, 0, 0

    with input_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        row_keys = reader.fieldnames or []

        resolved = {}
        for field, candidates in COLUMN_MAP.items():
            col = find_column(row_keys, candidates)
            if col is None and field in ("asrs_report_id", "narrative_text"):
                raise ValueError(
                    f"Required field '{field}' not found. Looked for: {candidates}. "
                    f"Found columns: {row_keys}"
                )
            resolved[field] = col

        for row in reader:
            asrs_id = str(row.get(resolved["asrs_report_id"], "")).strip()
            narrative = clean_text(row.get(resolved["narrative_text"], ""))

            if not asrs_id or not narrative:
                skipped_empty += 1
                continue

            report_date = row.get(resolved["report_date"]) if resolved["report_date"] else None
            aircraft_type = row.get(resolved["aircraft_type"]) if resolved["aircraft_type"] else None
            phase = row.get(resolved["phase_of_flight"]) if resolved["phase_of_flight"] else None

            try:
                conn.execute(
                    """INSERT INTO reports
                       (asrs_report_id, narrative_text, report_date, aircraft_type, phase_of_flight)
                       VALUES (?, ?, ?, ?, ?)""",
                    (asrs_id, narrative, report_date, aircraft_type, phase),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # UNIQUE constraint on asrs_report_id -> duplicate, upsert-by-skip
                skipped_dupe += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    conn.close()

    print(f"Inserted: {inserted}")
    print(f"Skipped (duplicate asrs_report_id): {skipped_dupe}")
    print(f"Skipped (empty id/narrative): {skipped_empty}")
    print(f"Total rows now in reports table: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/asrs_sample.csv")
    parser.add_argument("--db", default="data/processed/reports.db")
    args = parser.parse_args()
    ingest(args.input, args.db)
