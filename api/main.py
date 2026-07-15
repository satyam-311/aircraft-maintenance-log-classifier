import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import IS_PRODUCTION, FRONTEND_URL
from api.routes.classify import router as classify_router
from api.routes.search import router as search_router
from api.routes.corrections import router as corrections_router
from api.routes.ask import router as ask_router
from api.routes.stats import router as stats_router
from api.routes.model_performance import router as model_performance_router
from api.services.model_service import model_service
from api.services.embedding_service import embedding_service
from api.services.vector_store import vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maintenance Log Classifier API", version="0.1.0")

# CORS: permissive in dev to make local frontend work painlessly; tighten before any
# real deployment (per Security doc's "ENV toggles debug logging and CORS rules")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not IS_PRODUCTION else ([FRONTEND_URL] if FRONTEND_URL else []),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_models_on_startup():
    from api.services.model_downloader import ensure_models_available
    ensure_models_available()

    logger.info("Loading models...")
    model_service.load()
    if not model_service.loaded:
        logger.error(f"Models failed to load: {model_service.load_error}")

    embedding_service.load()
    if not embedding_service.loaded:
        logger.warning(f"Embedding model failed to load (search will degrade): {embedding_service.load_error}")

    vector_store.load()
    if not vector_store.loaded:
        logger.warning(f"Vector store failed to load (search will degrade): {vector_store.load_error}")


@app.get("/health")
def health():
    return {
        "status": "ok" if model_service.loaded else "degraded",
        "models_loaded": model_service.loaded,
    }


app.include_router(classify_router)
app.include_router(search_router)
app.include_router(corrections_router)
app.include_router(ask_router)
app.include_router(stats_router)
app.include_router(model_performance_router)

from fastapi.staticfiles import StaticFiles
from api.config import BASE_DIR
_reports_dir = BASE_DIR / "reports"
if _reports_dir.exists():
    app.mount("/reports", StaticFiles(directory=str(_reports_dir)), name="reports")
