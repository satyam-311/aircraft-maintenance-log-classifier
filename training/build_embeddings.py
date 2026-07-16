"""
Ticket 7 — Build semantic search embeddings.

Reads every narrative in the `reports` table, embeds each with the SAME
EmbeddingService used at query time (api/services/embedding_service.py), and
writes data/processed/embeddings.npy + data/processed/report_ids.json for
api/services/vector_store.py to load.

Deliberately reuses EmbeddingService instead of a separate sentence-transformers
call: EmbeddingService wraps the local MiniLM checkpoint with a specific manual
mean-pooling + L2-normalize implementation. Building the index any other way
risks a mismatch between how these vectors were computed and how a live query
is embedded at search time -- cosine similarity would then silently compare
vectors that aren't really in the same space.

Usage:
    python training/build_embeddings.py --db data/processed/reports.db --out data/processed
"""
import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

# Running this file directly puts training/ on sys.path[0], not the repo root --
# `from api...` fails with ModuleNotFoundError otherwise.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.services.embedding_service import embedding_service


def load_narratives(db_path: str):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT asrs_report_id, narrative_text FROM reports").fetchall()
    conn.close()

    report_ids, narratives, skipped = [], [], 0
    for report_id, narrative in rows:
        if not narrative or not narrative.strip():
            skipped += 1
            continue
        report_ids.append(str(report_id))
        narratives.append(narrative)
    return report_ids, narratives, skipped


def build_embeddings(db_path: str, out_dir: str):
    start = time.time()

    report_ids, narratives, skipped = load_narratives(db_path)
    print(f"Loaded {len(narratives)} narrative(s) to embed, skipped {skipped} empty/null row(s).")

    if not narratives:
        raise SystemExit(
            "No embeddable narratives found (0 non-empty narrative_text rows) -- "
            "refusing to write empty embeddings.npy / report_ids.json. "
            "Check --db points at a populated reports table."
        )

    embedding_service.load()
    if not embedding_service.loaded:
        raise SystemExit(f"Embedding model failed to load: {embedding_service.load_error}")

    vectors = []
    for i, text in enumerate(narratives, start=1):
        vectors.append(embedding_service.embed(text))
        if i % 200 == 0 or i == len(narratives):
            print(f"  embedded {i}/{len(narratives)}")

    # embed() already L2-normalizes internally; vector_store.py does NOT
    # renormalize on load, so verify rather than trust it here.
    embeddings = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "embed() output was not L2-normalized as expected"

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    embeddings_path = out_path / "embeddings.npy"
    report_ids_path = out_path / "report_ids.json"

    np.save(embeddings_path, embeddings)
    with report_ids_path.open("w", encoding="utf-8") as f:
        json.dump(report_ids, f)

    elapsed = time.time() - start
    print(f"Embedded: {len(narratives)}")
    print(f"Skipped (empty narrative_text): {skipped}")
    print(f"Wrote {embeddings_path} ({embeddings_path.stat().st_size / 1024:.1f} KB), shape {embeddings.shape}")
    print(f"Wrote {report_ids_path} ({report_ids_path.stat().st_size / 1024:.1f} KB), {len(report_ids)} ids")
    print(f"Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/processed/reports.db")
    parser.add_argument("--out", default="data/processed")
    args = parser.parse_args()
    build_embeddings(args.db, args.out)
