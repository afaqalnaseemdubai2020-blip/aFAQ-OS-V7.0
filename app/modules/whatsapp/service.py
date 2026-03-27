"""WhatsApp Service"""
from app.modules.whatsapp.config import config
from app.modules.whatsapp.training import training
from app.modules.whatsapp.sessions import sessions

class WhatsAppService:
    async def send_message(self, phone, message):
        if not config.is_configured:
            return {"status": "demo_mode", "phone": phone, "message": message}
        import httpx
        url = f"{config.base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=config.headers, json=payload)
            return resp.json() if resp.status_code == 200 else {"error": resp.text}
    
    async def process_incoming(self, phone, message, name=None):
        session = sessions.get_or_create(phone, name)
        sid = session["session_id"]
        sessions.log_msg(sid, "inbound", message, sender="customer")
        
        if session["status"] == "live_agent":
            return {"status": "live_agent_handled", "session_id": sid}
        
        result = training.get_response(message)
        
        if result.get("should_escalate"):
            esc = sessions.escalate(sid, result.get("category", "low_confidence"))
            fallback = result.get("response") or "Let me connect you with our support team."
            sessions.log_msg(sid, "outbound_ai", fallback, sender="ai", confidence=result.get("confidence", 0))
            await self.send_message(phone, fallback)
            return {
                "status": "escalated",
                "session_id": sid,
                "response": fallback,
                "confidence": result.get("confidence", 0),
                "needs_agent": True
            }
        
        response = result.get("response", "How can I help you?")
        sessions.log_msg(sid, "outbound_ai", response, sender="ai", confidence=result.get("confidence", 0))
        await self.send_message(phone, response)
        
        return {
            "status": "ai_responded",
            "session_id": sid,
            "response": response,
            "confidence": result.get("confidence", 0),
            "category": result.get("category")
        }
    
    async def process_webhook(self, payload):
        results = []
        try:
            entry = payload.get("entry", [{}])[0]
            value = entry.get("changes", [{}])[0].get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            name = contacts[0].get("profile", {}).get("name") if contacts else None
            
            for msg in messages:
                phone = msg.get("from", "")
                if msg.get("type") == "text":
                    text = msg.get("text", {}).get("body", "")
                    r = await self.process_incoming(phone, text, name)
                    results.append(r)
        except Exception as e:
            return {"error": str(e)}
        return {"processed": len(results), "results": results}
    
    async def agent_takeover(self, sid, agent_id, agent_name):
        return sessions.assign_agent(sid, agent_id, agent_name)
    
    async def agent_reply(self, sid, agent_name, message):
        session = sessions.get(sid)
        if not session:
            return {"error": "Not found"}
        sessions.log_msg(sid, "outbound_agent", message, sender=f"agent:{agent_name}")
        await self.send_message(session["phone"], f"{agent_name}: {message}")
        return {"status": "sent"}
    
    async def return_to_ai(self, sid):
        result = sessions.return_to_ai(sid)
        session = sessions.get(sid)
        if session:
            msg = "Our AI assistant is back! How can I help?"
            sessions.log_msg(sid, "outbound_ai", msg, sender="ai")
            await self.send_message(session["phone"], msg)
        return result

service = WhatsAppService()
