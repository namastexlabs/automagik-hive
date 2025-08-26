"""
WhatsApp webhook endpoint for jack_retrieval agent
Receives messages from Evolution API and processes via jack_retrieval
"""
import asyncio
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from lib.logging import logger
from lib.utils.version_factory import create_agent

# Global agent instance for WhatsApp conversations
_whatsapp_agent = None

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


async def process_whatsapp_message(message_data: Dict[str, Any]):
    """Process WhatsApp message through jack_retrieval agent"""
    try:
        # Extract message info - handle both conversation and extendedTextMessage
        message = message_data.get("message", {})
        message_text = (
            message.get("conversation", "") or 
            message.get("extendedTextMessage", {}).get("text", "")
        )
        sender_number = message_data.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
        
        if not message_text or not sender_number:
            logger.warning("Invalid message format received")
            return
            
        logger.info(f"📱 Processing WhatsApp message from {sender_number}: {message_text[:50]}...")
        
        # Get or create global agent instance for WhatsApp
        global _whatsapp_agent
        if _whatsapp_agent is None:
            logger.info("🔄 Creating new jack_retrieval agent for WhatsApp conversations")
            _whatsapp_agent = await create_agent("jack_retrieval", debug_mode=True)
        
        # Create session_id for conversation continuity
        session_id = f"whatsapp_{sender_number}"
        
        # Process message through shared agent instance with context parameters
        response = _whatsapp_agent.run(
            message_text,
            user_id=sender_number,  # WhatsApp number as user_id
            session_id=session_id   # Unique session per user
        )
        
        # Send response back via WhatsApp
        await send_whatsapp_response(sender_number, response.content)
        
        logger.info(f"✅ Sent WhatsApp response to {sender_number}")
        
    except Exception as e:
        logger.error(f"❌ Error processing WhatsApp message: {e}")
        # Send error message to user
        error_msg = "Desculpe, ocorreu um erro ao processar sua consulta. Tente novamente em alguns minutos."
        await send_whatsapp_response(sender_number, error_msg)


async def send_whatsapp_response(number: str, message: str):
    """Send response via Evolution API"""
    import aiohttp
    
    url = "http://localhost:8080/message/sendText/jack"
    headers = {
        "Content-Type": "application/json",
        "apikey": "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF"
    }
    payload = {
        "number": f"{number}@s.whatsapp.net",
        "textMessage": {
            "text": message
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 201:
                logger.info(f"📤 WhatsApp message sent successfully to {number}")
            else:
                error_text = await response.text()
                logger.error(f"❌ Failed to send WhatsApp message: {response.status} - {error_text}")


@router.post("/whatsapp/jack")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Evolution API WhatsApp messages
    Processes messages through jack_retrieval agent
    """
    try:
        data = await request.json()
        
        # Log webhook data for debugging (safely)
        event = data.get("event", "unknown")
        sender = data.get("sender", "unknown")
        message_preview = str(data.get("data", {}).get("message", {}))[:100]
        logger.info(f"📥 Webhook received - Event: {event}, Sender: {sender}, Message preview: {message_preview}...")
        
        # Check if it's a text message from user (not from bot)
        message = data.get("data", {}).get("message", {})
        has_text = (
            message.get("conversation") or 
            message.get("extendedTextMessage", {}).get("text")
        )
        
        if (
            data.get("event") == "messages.upsert" and 
            has_text and
            not data.get("data", {}).get("key", {}).get("fromMe", False)
        ):
            # Process message in background to avoid timeout
            background_tasks.add_task(process_whatsapp_message, data.get("data", {}))
            
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/whatsapp/jack/status")
async def webhook_status():
    """Check webhook status"""
    import os
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "NOT_FOUND")
    key_preview = f"{anthropic_key[:10]}..." if anthropic_key != "NOT_FOUND" else "NOT_FOUND"
    
    return {
        "status": "active",
        "agent": "jack_retrieval",
        "endpoint": "/webhook/whatsapp/jack",
        "evolution_instance": "jack",
        "anthropic_key_status": key_preview
    }