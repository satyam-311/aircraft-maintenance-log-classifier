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

# Maintenance Severity Classifier

Single-label text classifier that predicts a severity level (Low / Medium / High) for an aviation maintenance/incident narrative, based on the safety-relevant signals present in the text.

## Model details

- **Base checkpoint:** the saved `config.json` architecture (`DistilBertForSequenceClassification`, 6 layers, 768 hidden dim, 30522 vocab) is identical to standard `distilbert-base-uncased`, strongly suggesting that's the fine-tuning base — **but the training script for this specific model is not present in the source repository** (only its evaluation script, `training/evaluate_severity.py`, is checked in). This model was trained by a process not reproducible from the current repo snapshot. Stated plainly rather than guessed.
- **Task:** single-label text classification, 3 classes.
- **Fine-tuned on:** narratives from the FAA/NASA Aviation Safety Reporting System (ASRS), a public, de-identified dataset.

## Label set

3 classes (project note: an original 4th class, "Safety-Critical", was merged into "High" — it had too few training examples, ~60, to learn as a standalone class at this dataset's scale):

| Label | id |
|---|---|
| Low | 0 |
| Medium | 1 |
| High | 2 |

Severity labels were derived from a documented multi-signal heuristic over several ASRS fields (passenger involvement, in-flight vs. routine detection, MEL-deferred status, anomaly/result text) — not manually annotated ground truth. See `training/build_labels.py` in the source repo for the exact scoring rules.

## Training data

Same ASRS narrative corpus as the ATA classifier. The held-out **test set contained 411 labeled examples**. Exact train/validation split sizes aren't reproducible from this snapshot (split files are regenerated per run, not checked in).

## Evaluation results (held-out test set)

From `reports/severity_classifier/metrics.json`:

| Metric | Value |
|---|---|
| Accuracy | 48.9% |
| Macro F1 | 0.464 |
| Macro Precision | 0.464 |
| Macro Recall | 0.464 |
| Test examples | 411 |

**This model does not meet the project's target (macro F1 ≥ 0.70) — it falls substantially short (0.464).** Per-class F1: Low 0.587, Medium 0.475, High 0.330. This is a known, disclosed limitation: the severity label itself is a derived heuristic rather than ground truth, which caps how learnable it is, and this is reflected honestly here rather than hidden.

## Intended use

Component of a portfolio/research project ([Maintenance Log Classifier](https://github.com/satyam-311/aircraft-maintenance-log-classifier) — FastAPI + React app). **This is not a certified aviation safety tool**, and given the evaluation results above, its severity predictions should be treated as a rough, low-confidence signal at best — not a substitute for human safety triage. Trained on public, de-identified voluntary reports for demonstration and research purposes only.

## Example usage

```python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("Satyam311/maintenance-severity-classifier")
model = AutoModelForSequenceClassification.from_pretrained("Satyam311/maintenance-severity-classifier")
model.eval()

text = "Crew reported hydraulic leak near landing gear during pre-flight inspection."
inputs = tokenizer(text, truncation=True, max_length=256, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits
    probs = F.softmax(logits, dim=1)[0]

pred_id = int(torch.argmax(probs))
print(model.config.id2label[pred_id], float(probs[pred_id]))
# e.g. "High" 0.973
```

This mirrors exactly how the source project's `api/services/model_service.py` loads and runs the model in production (`truncation=True, max_length=256`, softmax over logits, top prediction only for this task).
