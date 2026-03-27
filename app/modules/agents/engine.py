"""Conversation Engine — State machine for autonomous sales"""
import json, os
from datetime import datetime
from typing import Dict, Optional, List

DB = "data/agents"
os.makedirs(DB, exist_ok=True)

def _load(f):
    p = os.path.join(DB, f"{f}.json")
    return json.load(open(p)) if os.path.exists(p) else []

def _save(f, d):
    with open(os.path.join(DB, f"{f}.json"), "w") as fp:
        json.dump(d, fp, indent=2, default=str)

CATALOG = {
    "babyliss": {"name": "Babyliss Pro", "products": ["Nano Titanium","Curling Wand","Dryer"], "price": "AED 150-500"},
    "ghd": {"name": "GHD", "products": ["Platinum+","Helios","Creative Curl"], "price": "AED 400-1200"},
    "wella": {"name": "Wella", "products": ["Koleston","Illumina","Fusion"], "price": "AED 50-300"},
    "dyson": {"name": "Dyson", "products": ["Airwrap","Supersonic","Corrale"], "price": "AED 1500-2500"}
}

SCORES = {"greeting":.05,"general_inquiry":.1,"pricing_inquiry":.2,"availability":.15,
          "comparison":.25,"purchase_intent":.4,"negotiation":.3,"complaint":.0}

class Engine:
    def detect_intent(self, msg: str) -> str:
        m = msg.lower()
        if any(w in m for w in ["price","cost","how much","سعر","كم"]): return "pricing_inquiry"
        if any(w in m for w in ["buy","order","purchase","اشتري","طلب"]): return "purchase_intent"
        if any(w in m for w in ["stock","available","delivery","متوفر","شحن"]): return "availability"
        if any(w in m for w in ["compare","vs","difference","فرق"]): return "comparison"
        if any(w in m for w in ["discount","bulk","wholesale","تخفيض","جملة"]): return "negotiation"
        if any(w in m for w in ["hello","hi","hey","مرحبا","السلام"]): return "greeting"
        if any(w in m for w in ["problem","issue","complaint","شكوى","مشكلة"]): return "complaint"
        return "general_inquiry"

    def detect_lang(self, msg: str) -> str:
        arabic = sum(1 for c in msg if '\u0600' <= c <= '\u06FF')
        return "ar" if arabic > len(msg) * 0.3 else "en"

    def next_state(self, cur: str, intent: str) -> str:
        T = {
            "initial": {"greeting":"discovery","general_inquiry":"discovery","pricing_inquiry":"recommendation","purchase_intent":"quotation","purchase_intent":"quotation"},
            "discovery": {"pricing_inquiry":"recommendation","purchase_intent":"quotation","comparison":"recommendation"},
            "recommendation": {"pricing_inquiry":"quotation","purchase_intent":"quotation","comparison":"recommendation"},
            "quotation": {"negotiation":"negotiation","purchase_intent":"closing"},
            "negotiation": {"purchase_intent":"closing","pricing_inquiry":"quotation"}
        }
        return T.get(cur, {}).get(intent, cur)

    def respond(self, state: str, lang: str, intent: str, msg: str) -> str:
        R = {
            "ar": {
                "discovery": "مرحبا! كيف أقدر أساعدك؟ عندنا أفضل أدوات تصفيف الشعر. وش تبحث عنه؟",
                "recommendation": "أنصحك بـ Babyliss Pro — من أفضل المنتجات. السعر AED 150-500. تبي تفاصيل؟",
                "quotation": "تمام، بجهز لك عرض سعر. كم القطعة تحتاج؟ تبي شحن لدبي؟",
                "negotiation": "بالجملة نقدم خصم خاص. كم المطلوب؟",
                "closing": "ممتاز! بجهز الطلب. بتأكيد العنوان وطريقة الدفع؟"
            },
            "en": {
                "discovery": "Hello! Welcome to AFAQ. We're the leading distributor of hair styling tools in Dubai. What are you looking for?",
                "recommendation": "I recommend Babyliss Pro — our best seller! Price range AED 150-500. Want details?",
                "quotation": "Let me prepare a special quote. How many units? Need delivery in Dubai?",
                "negotiation": "Bulk orders get special discounts. What quantity do you need?",
                "closing": "Excellent! Processing your order. Please confirm address and payment method."
            }
        }
        return R.get(lang, R["en"]).get(state, R.get(lang, R["en"])["discovery"])

    def score_update(self, leads: list, lead_id: int, intent: str) -> list:
        boost = SCORES.get(intent, .05)
        for l in leads:
            if l["id"] == lead_id:
                l["score"] = min(1.0, l.get("score", 0) + boost)
                l["contact_count"] = l.get("contact_count", 0) + 1
                l["last_contact"] = datetime.now().isoformat()
                l["updated_at"] = datetime.now().isoformat()
        return leads

    def process(self, lead_id: int, channel: str, message: str) -> Dict:
        from app.modules.agents.memory import memory
        convs = _load("conversations")
        leads = _load("leads")

        conv = next((c for c in convs if c["lead_id"]==lead_id and c["channel"]==channel), None)
        if not conv:
            conv = {"id": len(convs)+1, "lead_id": lead_id, "channel": channel,
                    "messages": [], "state": "initial", "ts": datetime.now().isoformat()}
            convs.append(conv)

        intent = self.detect_intent(message)
        lang = self.detect_lang(message)
        conv["messages"].append({"id": len(conv["messages"])+1, "dir": "in", "content": message,
                                 "intent": intent, "lang": lang, "ts": datetime.now().isoformat()})
        memory.save_episodic(lead_id, "inbound", message, {"ch": channel, "intent": intent})

        new_state = self.next_state(conv["state"], intent)
        reply = self.respond(new_state, lang, intent, message)
        conv["messages"].append({"id": len(conv["messages"])+1, "dir": "out", "content": reply,
                                 "ts": datetime.now().isoformat()})
        conv["state"] = new_state
        memory.save_episodic(lead_id, "outbound", reply, {"state": new_state})
        leads = self.score_update(leads, lead_id, intent)

        _save("conversations", convs)
        _save("leads", leads)

        return {"response": reply, "state": new_state, "intent": intent, "lang": lang,
                "should_escalate": new_state == "escalation"}

engine = Engine()
