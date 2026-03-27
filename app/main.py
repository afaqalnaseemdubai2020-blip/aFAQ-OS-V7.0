"""AFAQ OS V7.0 — Main Application"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os

app = FastAPI(title="AFAQ OS V7.0", version="7.0.0", docs_url="/docs")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Mount data
os.makedirs("data/agents", exist_ok=True)
os.makedirs("data/wiki", exist_ok=True)
os.makedirs("data/shopify", exist_ok=True)
os.makedirs("data/whatsapp", exist_ok=True)

# ── Routers ────────────────────────────
from app.modules.agents.router import agents_router
from app.modules.wiki.router import wiki_router
from app.modules.shopify.router import shopify_router
from app.modules.whatsapp.router import whatsapp_router

app.include_router(agents_router)
app.include_router(wiki_router)
app.include_router(shopify_router)
app.include_router(whatsapp_router)

# ── Pages ──────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/crm", response_class=HTMLResponse)
async def crm_page(request: Request):
    return templates.TemplateResponse("crm/dashboard.html", {"request": request})

# ── Health ─────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "running", "version": "7.0.0", "modules": ["agents", "wiki", "shopify"]}

# ── Global Error Handler ───────────────
@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})
