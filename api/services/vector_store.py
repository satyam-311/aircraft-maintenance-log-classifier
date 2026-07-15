"""
Lightweight in-memory vector search — replaces chromadb (Ticket 7's original choice).

Why the change: chromadb pulls in a huge dependency tree (kubernetes client,
opentelemetry, onnxruntime, grpcio, aiohttp...) meant for running a full client-server
vector database. At our actual scale (2,736 vectors x 384 dims = ~4MB), that's wildly
disproportionate -- it was the direct cause of Render's free-tier 512MB build running
out of memory. Brute-force cosine similarity via numpy does the identical job in
~2 milliseconds (measured), with zero extra dependencies.

Loads once at startup from the same embeddings.npy / report_ids.json Ticket 7 already
produced -- no data or embeddings were regenerated, only how they're queried changed.
"""
import json
import logging
import sqlite3

import numpy as np

from api.config import BASE_DIR, DATABASE_URL

logger = logging.getLogger(__name__)

EMBEDDINGS_PATH = BASE_DIR / "data" / "processed" / "embeddings.npy"
REPORT_IDS_PATH = BASE_DIR / "data" / "processed" / "report_ids.json"


class VectorStore:
    def __init__(self):
        self.embeddings = None  # (N, 384) float32, L2-normalized
        self.report_ids = None  # list[str], same order as embeddings rows
        self.metadata = {}      # report_id -> {narrative_text, ata_chapter_label, severity_label, ...}
        self.loaded = False
        self.load_error = None

    def load(self):
        try:
            self.embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
            with open(REPORT_IDS_PATH) as f:
                self.report_ids = [str(x) for x in json.load(f)]

            db_path = DATABASE_URL.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            rows = conn.execute("""
                SELECT r.asrs_report_id, r.narrative_text, g.ata_chapter_label, g.severity_label
                FROM reports r LEFT JOIN gold_labels g ON r.asrs_report_id = g.asrs_report_id
            """).fetchall()
            conn.close()

            self.metadata = {
                rid: {"narrative_text": text, "ata_chapter_label": ata, "severity_label": sev}
                for rid, text, ata, sev in rows
            }
            self.loaded = True
            logger.info(f"Vector store loaded: {len(self.report_ids)} vectors")
        except Exception as e:
            self.loaded = False
            self.load_error = str(e)
            logger.error(f"Vector store load failed: {e}")

    def query(self, query_embedding, system=None, severity=None, limit=20):
        if not self.loaded:
            raise RuntimeError(self.load_error or "Vector store not loaded")

        q = np.asarray(query_embedding, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-9)
        scores = self.embeddings @ q  # cosine similarity, since both sides are L2-normalized

        # Apply metadata filters BEFORE ranking, same semantics as the old Chroma `where` clause
        candidate_idx = np.arange(len(self.report_ids))
        if system or severity:
            keep = []
            for i in candidate_idx:
                meta = self.metadata.get(self.report_ids[i], {})
                if system and meta.get("ata_chapter_label") != system:
                    continue
                if severity and meta.get("severity_label") != severity:
                    continue
                keep.append(i)
            candidate_idx = np.array(keep, dtype=int)

        if len(candidate_idx) == 0:
            return []

        candidate_scores = scores[candidate_idx]
        top_n = min(limit, len(candidate_idx))
        top_order = np.argsort(-candidate_scores)[:top_n]
        top_idx = candidate_idx[top_order]

        results = []
        for i in top_idx:
            rid = self.report_ids[i]
            meta = self.metadata.get(rid, {})
            results.append({
                "report_id": rid,
                "excerpt": (meta.get("narrative_text") or "")[:300],
                "ata_chapter": meta.get("ata_chapter_label"),
                "severity": meta.get("severity_label"),
                "score": round(float(scores[i]), 4),
            })
        return results

    def filter_only(self, system=None, severity=None, limit=20):
        """No query vector at all -- just metadata filtering, no ranking."""
        if not self.loaded:
            raise RuntimeError(self.load_error or "Vector store not loaded")

        results = []
        for rid, meta in self.metadata.items():
            if system and meta.get("ata_chapter_label") != system:
                continue
            if severity and meta.get("severity_label") != severity:
                continue
            results.append({
                "report_id": rid,
                "excerpt": (meta.get("narrative_text") or "")[:300],
                "ata_chapter": meta.get("ata_chapter_label"),
                "severity": meta.get("severity_label"),
                "score": None,
            })
            if len(results) >= limit:
                break
        return results


vector_store = VectorStore()
