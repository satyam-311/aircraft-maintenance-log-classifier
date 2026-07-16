---
license: mit
library_name: transformers
base_model: distilbert-base-uncased
pipeline_tag: text-classification
tags:
- aviation
- maintenance
- text-classification
- distilbert
---

# Maintenance ATA Chapter Classifier

Single-label text classifier that predicts the ATA (Air Transport Association) chapter — the aircraft system a maintenance narrative is about (e.g. Hydraulic Power, Landing Gear, Flight Controls) — from free-text maintenance/incident report narratives.

## Model details

- **Base checkpoint:** `distilbert-base-uncased` (confirmed from the training script: `training/train_ata_classifier.py` loads a local `distilbert-base-uncased` checkpoint before fine-tuning; the saved model's `config.json` architecture — `DistilBertForSequenceClassification`, 6 layers, 768 hidden dim, 30522 vocab — matches the standard `distilbert-base-uncased` config exactly).
- **Task:** single-label text classification, 16 classes.
- **Fine-tuned on:** narratives from the FAA/NASA Aviation Safety Reporting System (ASRS), a public, de-identified dataset of voluntarily submitted aviation safety reports.

## Label set

16 ATA chapter codes (from this project's frozen reference table). Note `25-EM` is a project-defined bucket, not a standard ATA chapter number — it groups emergency-equipment narratives (escape slides, emergency exits, life vests, smoke detectors, fire extinguishers) that don't map cleanly to one real ATA chapter.

| Code | System |
|---|---|
| 21 | Air Conditioning / Pressurization / Windows |
| 24 | Electrical Power |
| 25 | Equipment / Furnishings |
| 25-EM | Emergency Equipment (project-defined, not a standard ATA chapter) |
| 27 | Flight Controls |
| 28 | Fuel |
| 29 | Hydraulic Power |
| 32 | Landing Gear |
| 34 | Navigation |
| 35 | Oxygen |
| 36 | Pneumatic |
| 49 | Airborne Auxiliary Power (APU) |
| 52 | Doors |
| 71 | Powerplant / Engine Fuel and Control |
| 78 | Engine Exhaust |
| 79 | Oil |

## Training data

Fine-tuned on maintenance narratives from ASRS, mapped to ATA chapters via a keyword-based heuristic over ASRS's own "Aircraft Component" field (see `training/build_labels.py` in the source repo). The held-out **test set contained 228 labeled examples**. Exact train/validation split sizes aren't reproducible from this snapshot (the split files are regenerated per training run and not checked into the repo), so they aren't quoted here to avoid guessing.

## Evaluation results (held-out test set, never used for training or checkpoint selection)

From `reports/ata_classifier/metrics.json`:

| Metric | Value |
|---|---|
| Accuracy | 79.8% |
| Macro F1 | 0.750 |
| Macro Precision | 0.780 |
| Macro Recall | 0.745 |
| Test examples | 228 |

Project target was ≥80% accuracy; this model reaches 79.8% — just under target.

Per-class F1 ranges from 0.33 (chapter 79, Oil — only 3 test examples) to 0.92 (chapter 32, Landing Gear — 44 test examples); performance on classes with few test examples should be treated as noisy rather than representative.

## Intended use

Component of a portfolio/research project ([Maintenance Log Classifier](https://github.com/satyam-311/aircraft-maintenance-log-classifier) — FastAPI + React app) that classifies, searches, and answers questions over maintenance narratives. **This is not a certified aviation safety tool.** It is trained on public, de-identified voluntary reports and is intended for demonstration, research, and triage-assistance use only — not for real-world airworthiness or maintenance decisions.

## Example usage

```python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("Satyam311/maintenance-ata-classifier")
model = AutoModelForSequenceClassification.from_pretrained("Satyam311/maintenance-ata-classifier")
model.eval()

text = "Crew reported hydraulic leak near landing gear during pre-flight inspection."
inputs = tokenizer(text, truncation=True, max_length=256, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits
    probs = F.softmax(logits, dim=1)[0]

pred_id = int(torch.argmax(probs))
print(model.config.id2label[pred_id], float(probs[pred_id]))
# e.g. "29" 0.595   (ATA 29 = Hydraulic Power)
```

This mirrors exactly how the source project's `api/services/model_service.py` loads and runs the model in production (`truncation=True, max_length=256`, softmax over logits, top prediction plus next-highest classes surfaced as "other possible systems").
