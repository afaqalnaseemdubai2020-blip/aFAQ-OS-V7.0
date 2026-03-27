"""WhatsApp Bridge Client (Node.js bridge)"""
import httpx
import os

BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3000")

async def send_message(to: str, message: str) -> dict:
    """Send WhatsApp message via bridge"""
    
    # Clean phone number
    to = to.replace("+", "").replace(" ", "").replace("-", "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BRIDGE_URL}/send",
                json={"to": to, "message": message},
                timeout=15.0
            )
            
            if response.status_code == 200:
                return {"status": "sent", "data": response.json()}
            else:
                return {"status": "error", "code": response.status_code}
                
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def send_typing(to: str) -> dict:
    """Typing indicator (not supported in whatsapp-web.js)"""
    return {"status": "not_supported"}

async def get_status() -> dict:
    """Get bridge status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BRIDGE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return {"status": "unreachable"}
    except:
        return {"status": "offline"}
