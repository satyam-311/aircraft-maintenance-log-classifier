---
license: mit
library_name: transformers
base_model: nreimers/MiniLM-L6-H384-uncased
pipeline_tag: feature-extraction
tags:
- aviation
- maintenance
- sentence-embeddings
- semantic-search
- bert
- mean-pooling
---

# Maintenance Narrative Embedding Model

Produces 384-dimensional sentence embeddings for aviation maintenance narratives, used to power semantic (meaning-based, not just keyword) search over a maintenance-report corpus.

## Model details

- **Base checkpoint:** `nreimers/MiniLM-L6-H384-uncased` — confirmed directly from this model's `config.json` (`_name_or_path`), a 6-layer, 384-hidden-dim BERT-family model (`architectures: ["BertModel"]`, `num_hidden_layers: 6`, `hidden_size: 384`, `vocab_size: 30522`).
- **No domain-specific fine-tuning script exists in the source repository** — this model is used as the base checkpoint for embedding generation, not fine-tuned further on the maintenance-narrative corpus. Stated plainly rather than assumed.
- **Not packaged in `sentence-transformers` format** — there's no `modules.json` / `sentence_bert_config.json` / `1_Pooling/` folder. It's loaded with plain `transformers.AutoModel` + a manual mean-pooling and L2-normalization step (see Example usage below), not the `sentence-transformers` package.

## Task

Feature extraction / sentence embeddings for semantic similarity search. Given a text (a maintenance narrative or a search query), produces one 384-dim L2-normalized vector; cosine similarity between vectors approximates semantic similarity between narratives.

## Training / usage data

Used (without further fine-tuning) to embed narratives from the FAA/NASA Aviation Safety Reporting System (ASRS) corpus — 2,742 narratives were embedded to build the source project's search index (`training/build_embeddings.py`, `data/processed/embeddings.npy`).

## Intended use

Component of a portfolio/research project ([Maintenance Log Classifier](https://github.com/satyam-311/aircraft-maintenance-log-classifier) — FastAPI + React app), powering its `/search` and `/ask` (retrieval-augmented) features. **This is not a certified aviation safety tool** — intended for demonstration and research over public, de-identified data.

## Example usage

The embedding logic must match exactly (same tokenization, same pooling, same normalization) between however you embed documents and however you embed queries, or cosine similarity comparisons become meaningless. This snippet mirrors the source project's `api/services/embedding_service.py` exactly:

```python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("Satyam311/maintenance-embedding-model")
model = AutoModel.from_pretrained("Satyam311/maintenance-embedding-model")
model.eval()

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)

text = "hydraulic pressure loss during approach"
inputs = tokenizer([text], padding=True, truncation=True, max_length=256, return_tensors="pt")

with torch.no_grad():
    output = model(**inputs)

embedding = F.normalize(mean_pooling(output, inputs["attention_mask"]), p=2, dim=1)
# embedding.shape == (1, 384), L2-normalized -- cosine similarity == dot product
```
