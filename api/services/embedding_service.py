"""
Embeds a live search query into the same 384-dim space as the Chroma index (Ticket 7).

Implements the standard sentence-transformers "mean pooling + L2 normalize" approach
manually with plain `transformers`, rather than the `sentence-transformers` package's
special model format -- this lets us reuse the exact same "download 4 files from HF,
point a local path at them" pattern that already worked for DistilBERT (Tickets 4/5),
instead of dealing with the sentence-transformers library's different folder layout.
"""
import logging

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

from api.config import BASE_DIR, MODEL_DIR

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_PATH = BASE_DIR / MODEL_DIR / "embedding_model"


def _mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)


class EmbeddingService:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.loaded = False
        self.load_error = None

    def load(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(str(EMBEDDING_MODEL_PATH), local_files_only=True)
            self.model = AutoModel.from_pretrained(str(EMBEDDING_MODEL_PATH), local_files_only=True, low_cpu_mem_usage=True)
            self.model.eval()
            self.loaded = True
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            self.loaded = False
            self.load_error = str(e)
            logger.error(f"Embedding model loading failed: {e}")

    def embed(self, text: str) -> list[float]:
        if not self.loaded:
            raise RuntimeError(self.load_error or "Embedding model not loaded")
        inputs = self.tokenizer([text], padding=True, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad():
            output = self.model(**inputs)
        pooled = _mean_pooling(output, inputs["attention_mask"])
        normalized = F.normalize(pooled, p=2, dim=1)
        return normalized[0].tolist()


embedding_service = EmbeddingService()
