"""
AFAQ-OS v7.0 — Main Application Entry Point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.audit import AuditMiddleware
from app.core.module_registry import module_registry
from app.core.infrastructure.module_loader import discover_modules
from app.core.infrastructure.health_check import get_health_status
from app.modules.wiki import get_router as get_wiki_router
from app.modules.agents import get_router as get_agents_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    discover_modules()
    await module_registry.startup_all()
    yield
    await module_registry.shutdown_all()
    logger.info("Shutdown complete.")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/api/health")
async def health():
    return await get_health_status()

@app.get("/api/modules")
async def list_modules():
    return {"active": [m.to_dict() for m in module_registry.get_active_modules()],
            "coming_soon": [m.to_dict() for m in module_registry.get_coming_soon_modules()]}

# Register module routers
app.include_router(get_wiki_router())
app.include_router(get_agents_router())

@app.get("/api/features")
async def list_features():
    from app.core.feature_flags import feature_flags
    return feature_flags.get_all()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    modules = module_registry.get_all_modules()
    return templates.TemplateResponse("base.html", {"request": request, "modules": modules})
