"""Session Manager"""
import json, os, uuid
from datetime import datetime
from typing import Optional, List

DATA_DIR = "data/whatsapp"
os.makedirs(DATA_DIR, exist_ok=True)

class SessionManager:
    def __init__(self):
        self.sessions = self._load("sessions.json")
        self.messages = self._load("messages.json")
    
    def _load(self, f):
        fp = os.path.join(DATA_DIR, f)
        if os.path.exists(fp):
            return json.load(open(fp))
        return []
    
    def _save(self, f, data):
        fp = os.path.join(DATA_DIR, f)
        json.dump(data, open(fp, "w"), indent=2, ensure_ascii=False)
    
    def get_or_create(self, phone, name=None):
        for s in self.sessions:
            if s["phone"] == phone and s["status"] in ["ai_active", "live_agent"]:
                s["last_activity"] = datetime.now().isoformat()
                s["message_count"] = s.get("message_count", 0) + 1
                self._save("sessions.json", self.sessions)
                return s
        
        session = {
            "session_id": str(uuid.uuid4())[:8],
            "phone": phone,
            "customer_name": name,
            "status": "ai_active",
            "assigned_agent": None,
            "message_count": 1,
            "ai_confidence_avg": 0.0,
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "escalated_at": None,
            "escalation_reason": None
        }
        self.sessions.append(session)
        self._save("sessions.json", self.sessions)
        return session
    
    def get(self, sid):
        return next((s for s in self.sessions if s["session_id"] == sid), None)
    
    def update(self, sid, updates):
        for s in self.sessions:
            if s["session_id"] == sid:
                s.update(updates)
                s["last_activity"] = datetime.now().isoformat()
                self._save("sessions.json", self.sessions)
                return s
    
    def log_msg(self, sid, direction, message, sender="ai", confidence=0):
        msg = {
            "id": str(uuid.uuid4())[:8],
            "session_id": sid,
            "direction": direction,
            "message": message,
            "sender": sender,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(msg)
        if len(self.messages) > 5000:
            self.messages = self.messages[-5000:]
        self._save("messages.json", self.messages)
        return msg
    
    def get_conversation(self, sid, limit=50):
        return [m for m in self.messages if m["session_id"] == sid][-limit:]
    
    def escalate(self, sid, reason):
        session = self.get(sid)
        if not session:
            return {"error": "Session not found"}
        self.update(sid, {
            "status": "escalated",
            "escalated_at": datetime.now().isoformat(),
            "escalation_reason": reason
        })
        return {"status": "escalated", "session_id": sid, "phone": session["phone"], "customer": session.get("customer_name")}
    
    def assign_agent(self, sid, agent_id, agent_name):
        self.update(sid, {"status": "live_agent", "assigned_agent": agent_id})
        return {"status": "assigned", "agent": agent_name, "session_id": sid}
    
    def return_to_ai(self, sid):
        self.update(sid, {"status": "ai_active", "assigned_agent": None, "escalated_at": None})
        return {"status": "returned_to_ai", "session_id": sid}
    
    def get_stats(self):
        active = len([s for s in self.sessions if s["status"] == "ai_active"])
        escalated = len([s for s in self.sessions if s["status"] == "escalated"])
        live = len([s for s in self.sessions if s["status"] == "live_agent"])
        confs = [m["confidence"] for m in self.messages if m.get("confidence", 0) > 0]
        return {
            "total_sessions": len(self.sessions),
            "active_ai": active,
            "escalated": escalated,
            "live_agent": live,
            "total_messages": len(self.messages),
            "avg_confidence": round(sum(confs)/len(confs), 2) if confs else 0
        }

sessions = SessionManager()
