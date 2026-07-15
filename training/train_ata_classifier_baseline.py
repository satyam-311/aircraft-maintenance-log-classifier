"""
Ticket 4 (INTERIM BASELINE) — ATA Chapter Classifier via TF-IDF + Logistic Regression.

Why this exists: the Technical Architecture doc specifies DistilBERT fine-tuning, but
that requires downloading pretrained weights from huggingface.co, which is blocked by
the current sandbox network allowlist. This classic-NLP baseline needs no external
model download at all (scikit-learn only) and is a legitimate approach at this dataset
size (578 labeled training examples across 16 classes).

This is a documented SUBSTITUTE, not a permanent architecture change. See
models/ata_classifier_baseline/README.md for the swap-back plan once the DistilBERT
weights are available (via network allowlist update or manual upload).

Usage:
    python training/train_ata_classifier_baseline.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV

TRAIN_CSV = "data/processed/train.csv"
VAL_CSV = "data/processed/val.csv"
TEST_CSV = "data/processed/test.csv"
OUTPUT_DIR = "models/ata_classifier_baseline"


def load_labeled(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df[df["ata_chapter_label"].notna()].reset_index(drop=True)


def main():
    train_df = load_labeled(TRAIN_CSV)
    val_df = load_labeled(VAL_CSV)
    test_df = load_labeled(TEST_CSV)
    print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}")

    vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        stop_words="english",
    )
    X_train = vectorizer.fit_transform(train_df["narrative_text"])
    X_val = vectorizer.transform(val_df["narrative_text"])
    X_test = vectorizer.transform(test_df["narrative_text"])

    y_train = train_df["ata_chapter_label"]
    y_val = val_df["ata_chapter_label"]
    y_test = test_df["ata_chapter_label"]

    # Small grid search on C (regularization strength) using train, validated manually on val set
    # since our val set is small (124 examples) -- avoid k-fold CV eating into it further.
    best_model, best_f1, best_c = None, -1, None
    for c in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
        clf = LogisticRegression(max_iter=2000, C=c, class_weight="balanced")
        clf.fit(X_train, y_train)
        preds = clf.predict(X_val)
        _, _, f1, _ = precision_recall_fscore_support(y_val, preds, average="macro", zero_division=0)
        print(f"  C={c}: val macro-F1={f1:.3f}")
        if f1 > best_f1:
            best_model, best_f1, best_c = clf, f1, c

    print(f"\nBest C={best_c} (val macro-F1={best_f1:.3f})")

    # Final test-set evaluation (held out, never touched during tuning)
    test_preds = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, test_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, test_preds, average="macro", zero_division=0
    )
    print(f"\nTEST SET -- accuracy: {test_acc:.3f}  macro-F1: {f1:.3f}")
    print("\nPer-class report (test set):")
    report = classification_report(y_test, test_preds, zero_division=0)
    print(report)

    out = Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, out / "vectorizer.joblib")
    joblib.dump(best_model, out / "model.joblib")

    with open(out / "test_metrics.json", "w") as f:
        json.dump(
            {"accuracy": test_acc, "macro_f1": f1, "macro_precision": precision,
             "macro_recall": recall, "best_C": best_c},
            f, indent=2,
        )

    with open(out / "README.md", "w") as f:
        f.write(
            "# ATA Chapter Classifier -- INTERIM BASELINE\n\n"
            "This is a TF-IDF + Logistic Regression model, substituted for the "
            "DistilBERT fine-tune specified in the Technical Architecture doc because "
            "huggingface.co is not reachable from the current sandbox network allowlist.\n\n"
            "**To swap back to DistilBERT:** once model weights are available "
            "(network allowlist update, or manually uploaded `distilbert-base-uncased` "
            "files), run `training/train_ata_classifier.py` instead -- it reads the same "
            "train/val CSVs and writes to `models/ata_classifier/`, no other code changes "
            "needed. Update `api/services/model_service.py` to point at whichever "
            "directory is active.\n"
        )

    print(f"\nSaved vectorizer + model + metrics to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
