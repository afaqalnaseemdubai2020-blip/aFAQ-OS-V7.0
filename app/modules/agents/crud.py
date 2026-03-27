"""Agents CRUD"""
import json, os
from datetime import datetime
from typing import List, Dict, Optional

DB = "data/agents"
F = os.path.join(DB, "leads.json")
os.makedirs(DB, exist_ok=True)

def _load():
    return json.load(open(F)) if os.path.exists(F) else []

def _save(d):
    with open(F, "w") as fp: json.dump(d, fp, indent=2, default=str)

class CRUD:
    def create(self, lead) -> Dict:
        leads = _load()
        item = {"id": max([l["id"] for l in leads], default=0)+1,
                "name": lead.name, "email": lead.email, "phone": lead.phone,
                "whatsapp": lead.whatsapp, "company": lead.company,
                "source": lead.source, "status": "new", "score": 0.1,
                "interested_products": lead.interested_products,
                "notes": lead.notes, "language": lead.language,
                "last_contact": None, "contact_count": 0,
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
        leads.append(item); _save(leads); return item

    def list(self, status=None, source=None, min_score=None, limit=50) -> List[Dict]:
        leads = _load()
        if status: leads = [l for l in leads if l.get("status")==status]
        if source: leads = [l for l in leads if l.get("source")==source]
        if min_score is not None: leads = [l for l in leads if l.get("score",0)>=min_score]
        return sorted(leads, key=lambda x: x.get("score",0), reverse=True)[:limit]

    def get(self, lid: int) -> Optional[Dict]:
        return next((l for l in _load() if l["id"]==lid), None)

    def update(self, lid: int, data) -> Optional[Dict]:
        leads = _load()
        lead = next((l for l in leads if l["id"]==lid), None)
        if not lead: return None
        for k,v in data.model_dump(exclude_unset=True).items(): lead[k]=v
        lead["updated_at"]=datetime.now().isoformat(); _save(leads); return lead

    def delete(self, lid: int) -> bool:
        leads = _load(); nl = [l for l in leads if l["id"]!=lid]
        if len(nl)==len(leads): return False
        _save(nl); return True

    def score(self, lid: int) -> Dict:
        lead = self.get(lid)
        if not lead: return {"error":"not found"}
        s = lead.get("score",0.1)
        if lead.get("email"): s+=0.1
        if lead.get("phone"): s+=0.1
        if lead.get("whatsapp"): s+=0.05
        if lead.get("company"): s+=0.15
        if lead.get("interested_products"): s+=0.1
        if lead.get("contact_count",0)>3: s+=0.2
        s = min(1.0,s); lead["score"]=s; lead["updated_at"]=datetime.now().isoformat()
        leads = [l if l["id"]!=lid else lead for l in _load()]
        _save(leads)
        status = "HOT" if s>=0.7 else "WARM" if s>=0.4 else "COLD"
        return {"id": lid, "score": s, "status": status}

crud = CRUD()
