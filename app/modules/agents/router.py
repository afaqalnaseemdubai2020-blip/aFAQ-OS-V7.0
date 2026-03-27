"""Agents Router — Full autonomous sales agent API"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.modules.agents.models import LeadCreate, LeadUpdate, BulkLeadCreate
from app.modules.agents.crud import crud
from app.modules.agents.engine import engine
from app.modules.agents.memory import memory

agents_router = APIRouter(prefix="/api/agents", tags=["🤖 Agents"])

# ── LEADS ───────────────────────────────
@agents_router.post("/leads", status_code=201)
async def create_lead(lead: LeadCreate): return crud.create(lead)

@agents_router.post("/leads/bulk", status_code=201)
async def bulk_create(bulk: BulkLeadCreate):
    results = [crud.create(l) for l in bulk.leads]
    return {"created": len(results), "leads": results}

@agents_router.get("/leads")
async def list_leads(status: Optional[str]=None, source: Optional[str]=None,
                     min_score: Optional[float]=None, limit: int=Query(50, ge=1, le=200)):
    return crud.list(status=status, source=source, min_score=min_score, limit=limit)

@agents_router.get("/leads/{lid}")
async def get_lead(lid: int):
    lead = crud.get(lid)
    if not lead: raise HTTPException(404, "Lead not found")
    ctx = memory.get_context(lid)
    return {"lead": lead, "context": ctx}

@agents_router.put("/leads/{lid}")
async def update_lead(lid: int, data: LeadUpdate):
    lead = crud.update(lid, data)
    if not lead: raise HTTPException(404, "Lead not found")
    return lead

@agents_router.delete("/leads/{lid}")
async def delete_lead(lid: int):
    if not crud.delete(lid): raise HTTPException(404, "Lead not found")
    return {"deleted": True, "id": lid}

@agents_router.post("/leads/{lid}/score")
async def score_lead(lid: int):
    r = crud.score(lid)
    if "error" in r: raise HTTPException(404, r["error"])
    return r

# ── CONVERSATIONS — SPECIFIC ROUTES FIRST ──
@agents_router.get("/conversations/send")
async def send_message(lead_id: int, channel: str, message: str):
    return engine.process(lead_id, channel, message)

@agents_router.get("/conversations/lead/{lead_id}")
async def get_convos(lead_id: int, channel: Optional[str]=None):
    import json, os
    fp = os.path.join("data/agents","conversations.json")
    convs = json.load(open(fp)) if os.path.exists(fp) else []
    if channel: return next((c for c in convs if c["lead_id"]==lead_id and c["channel"]==channel), {"messages":[]})
    return [c for c in convs if c["lead_id"]==lead_id]

@agents_router.get("/conversations/all")
async def list_all_convos():
    import json, os
    fp = os.path.join("data/agents","conversations.json")
    return json.load(open(fp)) if os.path.exists(fp) else []

# ── MEMORY ─────────────────────────────
@agents_router.get("/memory/context/{lid}")
async def get_ctx(lid: int): return memory.get_context(lid)

@agents_router.get("/memory/episodic/{lid}")
async def get_episodic(lid: int, limit: int=20): return memory.get_episodic(lid, limit)

@agents_router.post("/memory/semantic")
async def store_semantic(cat: str, key: str, val: str): return memory.save_semantic(cat, key, val)

@agents_router.get("/memory/semantic")
async def get_semantic(cat: Optional[str]=None, q: Optional[str]=None):
    return memory.get_semantic(cat=cat, q=q)

# ── DASHBOARD ──────────────────────────
@agents_router.get("/dashboard")
async def dashboard():
    leads = crud.list(limit=200)
    hot = [l for l in leads if l.get("score",0)>=0.7]
    warm = [l for l in leads if 0.4<=l.get("score",0)<0.7]
    cold = [l for l in leads if l.get("score",0)<0.4]
    return {"total": len(leads), "hot": len(hot), "warm": len(warm), "cold": len(cold),
            "avg_score": round(sum(l.get("score",0) for l in leads)/max(len(leads),1),2),
            "top_5": sorted(leads, key=lambda x: x.get("score",0), reverse=True)[:5]}
