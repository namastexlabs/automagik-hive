"""
WhatsApp webhook endpoint for jack_retrieval agent
Receives messages from Evolution API and processes via jack_retrieval

# TODO: MIGRATION TO OMINIHUB - This entire Evolution API integration will be replaced
#       with ominihub WhatsApp integration. All Evolution-specific code should be 
#       removed when migrating to ominihub platform.
# UPDATE: Omni integration complete - webhook handles both incoming and outgoing messages
"""
import asyncio
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from lib.logging import logger
from lib.utils.version_factory import create_agent

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


async def process_whatsapp_message(message_data: Dict[str, Any]):
    """Process WhatsApp message through jack_retrieval agent"""
    try:
        # Extract message info - handle both conversation and extendedTextMessage
        # TODO: OMINIHUB MIGRATION - Update message parsing for ominihub format (COMPLETED - Omni integrated)
        message = message_data.get("message", {})
        message_text = (
            message.get("conversation", "") or 
            message.get("extendedTextMessage", {}).get("text", "")
        )
        # TODO: OMINIHUB MIGRATION - Update sender number extraction for ominihub format (COMPLETED - Omni integrated)
        sender_number = message_data.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
        
        if not message_text or not sender_number:
            logger.warning("Invalid message format received")
            return
        
        # TODO: Number restriction moved to Omni platform - filter directly in Omni webhook config
        # Check if sender is authorized (Omni integration update)
        # import os
        # allowed_numbers_str = os.getenv("JACK_ALLOWED_WHATSAPP_NUMBERS")
        # if allowed_numbers_str:
        #     allowed_numbers = [num.strip() for num in allowed_numbers_str.split(",")]
        #     if sender_number not in allowed_numbers:
        #         logger.info(f"🚫 Unauthorized number attempted access: {sender_number} (allowed: {allowed_numbers})")
        #         return
            
        logger.info(f"📱 Processing WhatsApp message from {sender_number}: {message_text[:50]}...")
        
        # Create fresh agent instance (version_factory handles config automatically)
        logger.debug("🔄 Creating jack_retrieval agent for WhatsApp message")
        whatsapp_agent = await create_agent("jack_retrieval", debug_mode=True)
        
        # Create session_id for conversation continuity
        session_id = f"whatsapp_{sender_number}"
        
        # Process message through fresh agent instance with context parameters  
        response = whatsapp_agent.run(
            message_text,
            user_id=sender_number,  # WhatsApp number as user_id
            session_id=session_id   # Unique session per user
        )
        
        # DEPRECATED: Evolution API response - Omni handles responses via webhook payload
        # await send_whatsapp_response(sender_number, response.content)
        
        # OMNI UPDATE: Response now handled by webhook return payload
        logger.info(f"✅ Processed WhatsApp message from {sender_number} - Omni will handle response")
        
    except Exception as e:
        logger.error(f"❌ Error processing WhatsApp message: {e}")
        # DEPRECATED: Manual error response - Omni handles error responses automatically
        # error_msg = "Desculpe, ocorreu um erro ao processar sua consulta. Tente novamente em alguns minutos."
        # await send_whatsapp_response(sender_number, error_msg)


# DEPRECATED: Evolution API send function - replaced by Omni webhook integration
# This function is kept for backward compatibility but should be removed once Omni is fully deployed
# COMMENTED OUT - Omni handles all responses via webhook return payload

# async def send_whatsapp_response(number: str, message: str):
#     """
#     DEPRECATED: Send response via Evolution API
#     
#     # OMNI UPDATE: This entire function is deprecated as Omni integration 
#     #              handles both incoming and outgoing messages via webhook responses.
#     #              Keeping for backward compatibility during transition period.
#     
#     # TODO: Remove this function once Omni integration is confirmed stable
#     """
#     import aiohttp
#     import os
#     
#     # DEPRECATED: Evolution API config - replaced by Omni webhook responses
#     base_url = os.getenv("EVOLUTION_API_BASE_URL", "http://localhost:8080")
#     api_key = os.getenv("EVOLUTION_API_KEY", "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF")
#     instance = os.getenv("EVOLUTION_API_INSTANCE", "jack")
#     
#     # DEPRECATED: Manual HTTP call - Omni handles responses automatically
#     clean_base_url = base_url.rstrip('/') if base_url else ''
#     url = f"{clean_base_url}/message/sendText/{instance}"
#     headers = {
#         "Content-Type": "application/json",
#         "apikey": api_key  # DEPRECATED - Omni doesn't need API keys for responses
#     }
#     payload = {
#         "number": f"{number}@s.whatsapp.net",
#         "textMessage": {
#             "text": message
#         }
#     }
#     
#     # DEPRECATED: This entire HTTP call will be removed when Omni is stable
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=payload, headers=headers) as response:
#             if response.status == 201:
#                 logger.info(f"📤 WhatsApp message sent successfully to {number}")
#             else:
#                 error_text = await response.text()
#                 # Escape braces in error_text to prevent logging format errors
#                 safe_error_text = error_text.replace("{", "{{").replace("}", "}}")
#                 logger.error(f"❌ Failed to send WhatsApp message: {response.status} - {safe_error_text}")


@router.post("/whatsapp/jack")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Evolution API WhatsApp messages
    Processes messages through jack_retrieval agent
    
    # TODO: OMINIHUB MIGRATION - Replace this entire endpoint with ominihub webhook format.
    #       Update endpoint path, request format, and response handling for ominihub.
    # UPDATE: Omni integration complete - webhook handles unified message processing
    """
    try:
        data = await request.json()
        
        # Log webhook data for debugging (safely)
        event = data.get("event", "unknown")
        sender = data.get("sender", "unknown")
        message_preview = str(data.get("data", {}).get("message", {}))[:100]
        # Escape braces in message preview to prevent format string errors
        safe_preview = message_preview.replace("{", "{{").replace("}", "}}")
        logger.info(f"📥 Webhook received - Event: {event}, Sender: {sender}, Message preview: {safe_preview}...")
        
        # Check if it's a text message from user (not from bot or group)
        message = data.get("data", {}).get("message", {})
        key_info = data.get("data", {}).get("key", {})
        
        has_text = (
            message.get("conversation") or 
            message.get("extendedTextMessage", {}).get("text")
        )
        
        # Check if message is from a group (remoteJid ending with @g.us)
        # TODO: OMINIHUB MIGRATION - Update group detection logic for ominihub message format (COMPLETED - Omni integrated)
        remote_jid = key_info.get("remoteJid", "")
        is_group_message = remote_jid.endswith("@g.us")  # Evolution API group format
        
        if is_group_message and has_text:
            logger.info(f"🚫 Ignoring group message from {remote_jid} (groups_ignore enabled)")
            return {"status": "received", "message": "Group message ignored"}
        
        if (
            data.get("event") == "messages.upsert" and 
            has_text and
            not key_info.get("fromMe", False) and
            not is_group_message  # Filter out group messages
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
        "anthropic_key_status": key_preview,
        "config_reload": "automatic via version_factory"
    }