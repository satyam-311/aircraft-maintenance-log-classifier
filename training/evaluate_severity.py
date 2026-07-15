"""
Ticket 6 (severity half) — Evaluation & Confusion Matrix Report.
Same approach as evaluate.py, applied to the severity classifier.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_DIR = "models/severity_classifier"
TEST_CSV = "data/processed/test.csv"
MAX_LENGTH = 256
OUT_DIR = "reports/severity_classifier"


def main():
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, local_files_only=True)
    model.eval()

    with open(f"{MODEL_DIR}/label_map.json") as f:
        label_map = json.load(f)
    id2label = {int(k): v for k, v in label_map["id2label"].items()}
    label2id = label_map["label2id"]

    df = pd.read_csv(TEST_CSV)
    df = df[df["severity_label"].notna()].reset_index(drop=True)
    print(f"Test examples (severity-labeled): {len(df)}")
    print(df["severity_label"].value_counts())

    true_labels = df["severity_label"].astype(str).tolist()
    y_true = [label2id[t] for t in true_labels]

    y_pred = []
    with torch.no_grad():
        for text in df["narrative_text"].tolist():
            inputs = tokenizer(text, truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
            logits = model(**inputs).logits
            pred_id = int(torch.argmax(logits, dim=1).item())
            y_pred.append(pred_id)

    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)

    print(f"\n=== TEST SET RESULTS ===")
    print(f"Accuracy: {acc:.1%}")
    print(f"Macro F1: {f1:.3f}   (PRD target: >=0.70)")
    print(f"Macro Precision: {precision:.3f}   Macro Recall: {recall:.3f}")

    labels_present = sorted(set(y_true) | set(y_pred))
    target_names = [id2label[i] for i in labels_present]
    report_dict = classification_report(
        y_true, y_pred, labels=labels_present, target_names=target_names, zero_division=0, output_dict=True
    )
    print("\nPer-class report:")
    print(classification_report(y_true, y_pred, labels=labels_present, target_names=target_names, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=labels_present)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Oranges")
    ax.set_xticks(range(len(target_names)))
    ax.set_yticks(range(len(target_names)))
    ax.set_xticklabels(target_names, rotation=45, ha="right")
    ax.set_yticklabels(target_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Severity Classifier — Confusion Matrix (Test Set)")
    for i in range(len(target_names)):
        for j in range(len(target_names)):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/confusion_matrix.png", dpi=150)
    print(f"\nSaved confusion matrix to {OUT_DIR}/confusion_matrix.png")

    metrics_out = {
        "test_accuracy": acc,
        "test_macro_f1": f1,
        "test_macro_precision": precision,
        "test_macro_recall": recall,
        "n_test_examples": len(df),
        "per_class": report_dict,
        "prd_target_macro_f1": 0.70,
        "meets_prd_target": f1 >= 0.70,
    }
    with open(f"{OUT_DIR}/metrics.json", "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"Saved metrics JSON to {OUT_DIR}/metrics.json")


if __name__ == "__main__":
    main()
