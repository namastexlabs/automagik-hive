"""
Tests for WhatsApp webhook endpoint
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.routes.whatsapp_webhook import router, process_whatsapp_message, send_whatsapp_response

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestWhatsAppWebhook:
    """Test WhatsApp webhook functionality"""
    
    def test_webhook_status_endpoint(self):
        """Should return webhook status"""
        response = client.get("/webhook/whatsapp/jack/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["agent"] == "jack_retrieval"
    
    def test_webhook_endpoint_exists(self):
        """Should accept POST requests to webhook endpoint"""
        # Test with minimal valid data
        test_data = {"event": "test"}
        response = client.post("/webhook/whatsapp/jack", json=test_data)
        assert response.status_code == 200
        assert response.json()["status"] == "received"
    
    def test_webhook_ignores_non_message_events(self):
        """Should ignore non-message events"""
        test_data = {
            "event": "connection.update",
            "data": {"connection": "open"}
        }
        response = client.post("/webhook/whatsapp/jack", json=test_data)
        assert response.status_code == 200
        assert response.json()["status"] == "received"
    
    def test_webhook_ignores_bot_messages(self):
        """Should ignore messages from bot itself"""
        test_data = {
            "event": "messages.upsert",
            "data": {
                "key": {"fromMe": True},
                "message": {"conversation": "Bot message"}
            }
        }
        response = client.post("/webhook/whatsapp/jack", json=test_data)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_process_whatsapp_message_success(self):
        """Should process valid WhatsApp message"""
        message_data = {
            "key": {"remoteJid": "5527981813600@s.whatsapp.net"},
            "message": {"conversation": "Qual o valor total dos CTEs?"}
        }
        
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.content = "O valor total é R$ 42.819,17"
        mock_agent.run = AsyncMock(return_value=mock_response)
        
        with patch('api.routes.whatsapp_webhook.create_agent', return_value=mock_agent):
            with patch('api.routes.whatsapp_webhook.send_whatsapp_response') as mock_send:
                await process_whatsapp_message(message_data)
                
                # Verify agent was called
                mock_agent.run.assert_called_once_with("Qual o valor total dos CTEs?")
                
                # Verify response was sent
                mock_send.assert_called_once_with("5527981813600", "O valor total é R$ 42.819,17")
    
    @pytest.mark.asyncio
    async def test_process_whatsapp_message_invalid_format(self):
        """Should handle invalid message format gracefully"""
        invalid_data = {"invalid": "data"}
        
        # Should not raise exception
        await process_whatsapp_message(invalid_data)
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_response_success(self):
        """Should send response via Evolution API"""
        mock_response = Mock()
        mock_response.status = 201
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            await send_whatsapp_response("5527981813600", "Test message")
    
    @pytest.mark.asyncio 
    async def test_send_whatsapp_response_failure(self):
        """Should handle Evolution API errors gracefully"""
        mock_response = Mock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad request")
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            # Should not raise exception
            await send_whatsapp_response("5527981813600", "Test message")


if __name__ == "__main__":
    pytest.main([__file__])