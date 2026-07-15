"""
Runs once at API startup (Render). If HF_*_MODEL_REPO env vars are set, downloads
the trained model from Hugging Face Hub into the expected local folder first --
Render has normal internet access, unlike the dev sandbox, so this works there
even though the equivalent Hub download is blocked in local dev.
If the env vars aren't set (local/sandbox), this is a no-op and the code just
reads whatever is already in models/ -- same behavior as today.
"""
import logging

from api.config import (
    ATA_MODEL_PATH, SEVERITY_MODEL_PATH, EMBEDDING_MODEL_PATH,
    HF_ATA_MODEL_REPO, HF_SEVERITY_MODEL_REPO, HF_EMBEDDING_MODEL_REPO,
)

logger = logging.getLogger(__name__)


def _download_if_configured(repo_id: str, local_path):
    if not repo_id:
        return  # local files already in place, nothing to do
    if local_path.exists() and any(local_path.iterdir()):
        logger.info(f"{local_path} already populated, skipping download")
        return
    from huggingface_hub import snapshot_download
    logger.info(f"Downloading {repo_id} -> {local_path}")
    snapshot_download(repo_id=repo_id, local_dir=str(local_path))


def ensure_models_available():
    _download_if_configured(HF_ATA_MODEL_REPO, ATA_MODEL_PATH)
    _download_if_configured(HF_SEVERITY_MODEL_REPO, SEVERITY_MODEL_PATH)
    _download_if_configured(HF_EMBEDDING_MODEL_REPO, EMBEDDING_MODEL_PATH)
