"""
Ticket 3 — Clean & Split Dataset.

Produces train/val/test CSVs (70/15/15) from `reports` LEFT JOIN `gold_labels`.
Split is stratified on a combined key so that:
  - reports with an ATA-chapter label are distributed proportionally across splits
  - reports with only a severity label are distributed proportionally across splits
  - reports with neither label (~49%) are kept too (useful for the semantic-search /
    embeddings ticket later, just not for supervised training) and bucketed together
  - a single asrs_report_id can never appear in more than one split (checked at the end)
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42


def stratify_key(row):
    if pd.notna(row["ata_chapter_label"]):
        return f"ATA_{row['ata_chapter_label']}"
    if pd.notna(row["severity_label"]):
        return f"SEV_{row['severity_label']}"
    return "UNLABELED"


def load_joined(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT r.asrs_report_id, r.narrative_text, r.report_date, r.aircraft_type,
               r.phase_of_flight, g.ata_chapter_label, g.severity_label
        FROM reports r
        LEFT JOIN gold_labels g ON r.asrs_report_id = g.asrs_report_id
        """,
        conn,
    )
    conn.close()
    return df


def split(db_path: str, out_dir: str):
    df = load_joined(db_path)
    df["strat_key"] = df.apply(stratify_key, axis=1)

    # Any class in strat_key with fewer than 2 members can't be split at all -> route to UNLABELED-like
    # bucket instead of crashing. (Not expected given our smallest real class is 11, but defensive.)
    counts = df["strat_key"].value_counts()
    too_small = counts[counts < 2].index.tolist()
    if too_small:
        print(f"WARNING: merging {len(too_small)} tiny strat groups into UNLABELED: {too_small}")
        df.loc[df["strat_key"].isin(too_small), "strat_key"] = "UNLABELED"

    train_df, temp_df = train_test_split(
        df, test_size=0.30, stratify=df["strat_key"], random_state=RANDOM_SEED
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, stratify=temp_df["strat_key"], random_state=RANDOM_SEED
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cols = ["asrs_report_id", "narrative_text", "report_date", "aircraft_type",
            "phase_of_flight", "ata_chapter_label", "severity_label"]
    train_df[cols].to_csv(out / "train.csv", index=False)
    val_df[cols].to_csv(out / "val.csv", index=False)
    test_df[cols].to_csv(out / "test.csv", index=False)

    # ---- Verification ----
    print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}  Total: {len(df)}")

    ids_train = set(train_df["asrs_report_id"])
    ids_val = set(val_df["asrs_report_id"])
    ids_test = set(test_df["asrs_report_id"])
    overlap = (ids_train & ids_val) | (ids_train & ids_test) | (ids_val & ids_test)
    print(f"Cross-split ID overlap (must be 0): {len(overlap)}")

    print()
    print("ATA-chapter label proportions (train / val / test):")
    for split_name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        labeled = split_df["ata_chapter_label"].notna().sum()
        print(f"  {split_name}: {labeled} labeled ({labeled/len(split_df):.1%} of split)")

    print()
    print("Severity label proportions (train / val / test):")
    for split_name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        labeled = split_df["severity_label"].notna().sum()
        print(f"  {split_name}: {labeled} labeled ({labeled/len(split_df):.1%} of split)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/processed/reports.db")
    parser.add_argument("--out", default="data/processed")
    args = parser.parse_args()
    split(args.db, args.out)
