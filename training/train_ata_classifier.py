"""
Ticket 4 — Fine-tune DistilBERT for ATA Chapter Classification.

Trains distilbert-base-uncased as a multi-class classifier over the frozen 16-chapter
ATA label set (Ticket 2), using only the rows in train/val CSVs that have an
ata_chapter_label (the rest are unlabeled and excluded from this classifier's training,
per Ticket 3's design).

Usage:
    python training/train_ata_classifier.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset

MODEL_NAME = "models/base/distilbert-base-uncased"  # local checkpoint (Hugging Face Hub unreachable from sandbox)
TRAIN_CSV = "data/processed/train.csv"
VAL_CSV = "data/processed/val.csv"
OUTPUT_DIR = "models/ata_classifier"
MAX_LENGTH = 256  # narratives are a few sentences; 256 tokens covers the vast majority


def load_labeled(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["ata_chapter_label"].notna()].reset_index(drop=True)
    return df


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    acc = accuracy_score(labels, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    return {"accuracy": acc, "macro_f1": f1, "macro_precision": precision, "macro_recall": recall}


def main():
    train_df = load_labeled(TRAIN_CSV)
    val_df = load_labeled(VAL_CSV)
    print(f"Training examples: {len(train_df)}  Validation examples: {len(val_df)}")

    labels = sorted(train_df["ata_chapter_label"].unique().tolist())
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for label, i in label2id.items()}
    print(f"Classes ({len(labels)}): {labels}")

    train_df["label"] = train_df["ata_chapter_label"].map(label2id)
    val_df["label"] = val_df["ata_chapter_label"].map(label2id)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)

    def tokenize(batch):
        return tokenizer(
            batch["narrative_text"], truncation=True, max_length=MAX_LENGTH, padding="max_length"
        )

    train_ds = Dataset.from_pandas(train_df[["narrative_text", "label"]])
    val_ds = Dataset.from_pandas(val_df[["narrative_text", "label"]])
    train_ds = train_ds.map(tokenize, batched=True)
    val_ds = val_ds.map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(labels), id2label=id2label, label2id=label2id, local_files_only=True
    )

    args = TrainingArguments(
        output_dir="training_runs/ata_classifier",
        num_train_epochs=8,           # small dataset -> more epochs, watched via eval_strategy
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        learning_rate=2e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_steps=10,
        report_to=[],  # no W&B account needed -- plain console/JSON logging only
        use_cpu=True,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    final_metrics = trainer.evaluate()
    print("Final validation metrics:", final_metrics)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    with open(f"{OUTPUT_DIR}/label_map.json", "w") as f:
        json.dump({"label2id": label2id, "id2label": id2label}, f, indent=2)

    with open(f"{OUTPUT_DIR}/val_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"Saved model + tokenizer + label map to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
