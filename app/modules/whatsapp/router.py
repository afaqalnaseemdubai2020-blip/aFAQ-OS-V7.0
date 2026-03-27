"""WhatsApp Bot Router - whatsapp-web.js bridge powered"""
from fastapi import APIRouter, Query, Request
from app.modules.whatsapp.classifier import classifier
from app.modules.whatsapp.session import session_manager
from app.modules.whatsapp.ai_provider import generate_ai_response
from app.modules.whatsapp.ultramsg import send_message, get_status
from datetime import datetime

whatsapp_router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp Bot"])

# ============================================
# WEBHOOK - Receive from Node.js bridge
# ============================================

@whatsapp_router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Receive messages from whatsapp-web.js bridge"""
    try:
        payload = await request.json()
        
        phone = payload.get("from", "")
        message_text = payload.get("body", "")
        contact_name = payload.get("pushname", "Guest")
        
        if not phone or not message_text:
            return {"reply": None}
        
        # Clean phone number
        phone = phone.replace("@c.us", "").replace("@g.us", "")
        
        # Get/create session
        session = session_manager.get_session(phone)
        if not session:
            session = session_manager.create_session(phone, contact_name)
        
        session.last_activity = datetime.now()
        session.message_count += 1
        
        # Classify message
        result = classifier.classify(message_text)
        category = result["category"]
        confidence = result["confidence"]
        
        response_text = None
        
        # High confidence → template
        if confidence >= 0.85:
            response_text = result["response"]
            session.template_hits += 1
        else:
            # Try DeepSeek AI
            ai_response = await generate_ai_response(message_text)
            if ai_response:
                response_text = ai_response
                session.ai_hits += 1
            else:
                response_text = result["response"]
        
        # Escalation check
        if category == "complaint":
            session_manager.escalate(phone)
            response_text = (
                f"{response_text}\n\n"
                "💬 تم تحويلك لممثل خدمة العملاء\n"
                "Transferring to live agent..."
            )
        
        # Save to history
        session.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": message_text,
            "assistant": response_text,
            "category": category,
            "confidence": confidence
        })
        
        # Return reply to bridge
        return {"reply": response_text}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"reply": None}


# ============================================
# API ENDPOINTS
# ============================================

@whatsapp_router.get("/status")
async def status():
    """Check WhatsApp bridge status"""
    bridge = await get_status()
    return {
        "bridge": bridge,
        "deepseek_configured": bool(__import__('os').getenv("DEEPSEEK_API_KEY"))
    }

@whatsapp_router.get("/send")
async def send_api(
    phone: str = Query(...),
    message: str = Query(...)
):
    """Direct send endpoint"""
    result = await send_message(phone, message)
    return result

@whatsapp_router.get("/chat")
async def chat_api(
    phone: str = Query(...),
    message: str = Query(...),
    name: str = Query(default="Guest")
):
    """Test chat endpoint"""
    
    session = session_manager.get_session(phone)
    if not session:
        session = session_manager.create_session(phone, name)
    
    session.last_activity = datetime.now()
    session.message_count += 1
    
    result = classifier.classify(message)
    category = result["category"]
    confidence = result["confidence"]
    
    if confidence >= 0.85:
        response_text = result["response"]
    else:
        ai_response = await generate_ai_response(message)
        response_text = ai_response if ai_response else result["response"]
    
    send_result = await send_message(phone, response_text)
    
    return {
        "sent": send_result.get("status") == "sent",
        "response": response_text,
        "category": category,
        "confidence": confidence
    }

@whatsapp_router.get("/dashboard")
async def whatsapp_dashboard():
    """Dashboard"""
    stats = session_manager.get_stats()
    training = classifier.get_training_summary()
    bridge = await get_status()
    return {
        "bridge": bridge,
        "sessions": stats,
        "training": training
    }

@whatsapp_router.get("/agent/queue")
async def agent_queue():
    """Escalated sessions"""
    escalated = session_manager.get_escalated_sessions()
    return {
        "total": len(escalated),
        "sessions": [
            {
                "phone": s.phone[-4:],
                "name": s.name,
                "messages": s.message_count,
                "escalated_at": s.escalated_at.isoformat() if s.escalated_at else None
            }
            for s in escalated
        ]
    }

@whatsapp_router.post("/agent/resolve/{phone}")
async def agent_resolve(phone: str):
    """Mark resolved"""
    session = session_manager.get_session(phone)
    if session:
        session.status = "resolved"
        return {"status": "resolved"}
    return {"status": "not_found"}
