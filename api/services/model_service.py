"""
Loads the fine-tuned ATA-chapter and severity models ONCE at import time (not per-request
-- reloading a transformer per request would blow past the 2-second latency target), and
exposes simple predict functions for the route handlers to call.
"""
import json
import logging

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from api.config import ATA_MODEL_PATH, SEVERITY_MODEL_PATH, MAX_NARRATIVE_TOKENS

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self):
        self.ata_tokenizer = None
        self.ata_model = None
        self.ata_id2label = None
        self.severity_tokenizer = None
        self.severity_model = None
        self.severity_id2label = None
        self.loaded = False
        self.load_error = None

    def load(self):
        """Called once at API startup. Failure here is what triggers the 503 responses
        described in the Security doc ('Model service unavailable / fails to load')."""
        try:
            self.ata_tokenizer = AutoTokenizer.from_pretrained(str(ATA_MODEL_PATH), local_files_only=True)
            self.ata_model = AutoModelForSequenceClassification.from_pretrained(
                str(ATA_MODEL_PATH), local_files_only=True, low_cpu_mem_usage=True
            )
            self.ata_model.eval()
            with open(ATA_MODEL_PATH / "label_map.json") as f:
                self.ata_id2label = {int(k): v for k, v in json.load(f)["id2label"].items()}

            self.severity_tokenizer = AutoTokenizer.from_pretrained(
                str(SEVERITY_MODEL_PATH), local_files_only=True
            )
            self.severity_model = AutoModelForSequenceClassification.from_pretrained(
                str(SEVERITY_MODEL_PATH), local_files_only=True, low_cpu_mem_usage=True
            )
            self.severity_model.eval()
            with open(SEVERITY_MODEL_PATH / "label_map.json") as f:
                self.severity_id2label = {int(k): v for k, v in json.load(f)["id2label"].items()}

            self.loaded = True
            logger.info("Both models loaded successfully.")
        except Exception as e:
            self.loaded = False
            self.load_error = str(e)
            logger.error(f"Model loading failed: {e}")

    def _predict_single(self, tokenizer, model, id2label, text: str, top_k: int = 1):
        was_truncated = False
        token_count = len(tokenizer.encode(text))
        if token_count > MAX_NARRATIVE_TOKENS:
            was_truncated = True

        inputs = tokenizer(text, truncation=True, max_length=MAX_NARRATIVE_TOKENS, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits, dim=1)[0]

        top_probs, top_ids = torch.topk(probs, k=min(top_k, len(id2label)))
        results = [
            {"label": id2label[int(idx)], "confidence": float(p)}
            for p, idx in zip(top_probs.tolist(), top_ids.tolist())
        ]
        return results, was_truncated

    def predict(self, text: str):
        if not self.loaded:
            raise RuntimeError(self.load_error or "Models not loaded")

        # top 3 for ATA so the API can expose "other possible systems" per the
        # Security doc's ambiguous multi-system report handling
        ata_results, ata_truncated = self._predict_single(
            self.ata_tokenizer, self.ata_model, self.ata_id2label, text, top_k=3
        )
        severity_results, severity_truncated = self._predict_single(
            self.severity_tokenizer, self.severity_model, self.severity_id2label, text, top_k=1
        )

        return {
            "ata_chapter": ata_results[0]["label"],
            "ata_confidence": ata_results[0]["confidence"],
            "ata_other_possible": ata_results[1:],  # next-highest scoring classes
            "severity": severity_results[0]["label"],
            "severity_confidence": severity_results[0]["confidence"],
            "text_was_truncated": ata_truncated or severity_truncated,
        }


# Singleton -- one instance shared across all requests, loaded once at startup
model_service = ModelService()
