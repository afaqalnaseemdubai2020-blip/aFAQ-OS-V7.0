"""Multi-layer Memory System — Episodic, Semantic, Working"""
import json, os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB = "data/agents"
os.makedirs(DB, exist_ok=True)

def _load(f):
    p = os.path.join(DB, f"{f}.json")
    return json.load(open(p)) if os.path.exists(p) else []

def _save(f, d):
    with open(os.path.join(DB, f"{f}.json"), "w") as fp:
        json.dump(d, fp, indent=2, default=str)

class Memory:
    def __init__(self):
        self.episodic = _load("episodic")
        self.semantic = _load("semantic")
        self.working = _load("working")

    def save_episodic(self, lead_id: int, event: str, content: str, meta: Dict = None) -> Dict:
        item = {"id": len(self.episodic)+1, "lead_id": lead_id, "event": event,
                "content": content, "meta": meta or {}, "ts": datetime.now().isoformat()}
        self.episodic.append(item)
        _save("episodic", self.episodic)
        return item

    def get_episodic(self, lead_id: int, limit: int = 20) -> List[Dict]:
        items = [m for m in self.episodic if m.get("lead_id") == lead_id]
        return sorted(items, key=lambda x: x["ts"], reverse=True)[:limit]

    def save_semantic(self, cat: str, key: str, val: str, meta: Dict = None) -> Dict:
        for m in self.semantic:
            if m.get("cat") == cat and m.get("key") == key:
                m["val"] = val; m["meta"] = meta or {}; m["updated"] = datetime.now().isoformat()
                _save("semantic", self.semantic); return m
        item = {"id": len(self.semantic)+1, "cat": cat, "key": key, "val": val,
                "meta": meta or {}, "ts": datetime.now().isoformat(), "updated": datetime.now().isoformat()}
        self.semantic.append(item); _save("semantic", self.semantic); return item

    def get_semantic(self, cat: str = None, q: str = None) -> List[Dict]:
        items = self.semantic
        if cat: items = [m for m in items if m.get("cat") == cat]
        if q: ql = q.lower(); items = [m for m in items if ql in m.get("val","").lower() or ql in m.get("key","").lower()]
        return items

    def save_working(self, lead_id: int, key: str, val: Any, hrs: int = 24) -> Dict:
        self.working = [m for m in self.working if not (m.get("lead_id")==lead_id and m.get("key")==key)]
        item = {"id": len(self.working)+1, "lead_id": lead_id, "key": key, "val": val,
                "exp": (datetime.now()+timedelta(hours=hrs)).isoformat(), "ts": datetime.now().isoformat()}
        self.working.append(item); _save("working", self.working); return item

    def get_working(self, lead_id: int) -> List[Dict]:
        now = datetime.now().isoformat()
        self.working = [m for m in self.working if m.get("exp","") > now]
        return [m for m in self.working if m.get("lead_id") == lead_id]

    def get_context(self, lead_id: int) -> Dict:
        return {"episodic": self.get_episodic(lead_id, 10),
                "working": self.get_working(lead_id)}

memory = Memory()
