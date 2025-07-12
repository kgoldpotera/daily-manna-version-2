import httpx
from typing import Optional
from app.config import settings

class WhatsAppService:
    def __init__(self):
        self.api_url = settings.ultramsg_api_url
        self.token = settings.ULTRAMSG_TOKEN
    
    async def send_message(self, to: str, message: str) -> bool:
        """Send a WhatsApp message via UltraMsg API"""
        if not self.token or not settings.ULTRAMSG_INSTANCE_ID:
            print("❌ Missing UltraMsg configuration")
            return False
        
        payload = {
            "to": to,
            "body": message,
            "priority": 10,
            "referenceId": "daily-manna"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}?token={self.token}",
                    data=payload
                )
                
                if response.status_code == 200:
                    print(f"✅ Message sent to {to}")
                    return True
                else:
                    print(f"❌ Failed to send message. Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            print("❌ Timeout while sending WhatsApp message")
            return False
        except Exception as e:
            print(f"❌ Error sending WhatsApp message: {e}")
            return False
    
    async def send_reading_reminder(self, to: str, user_name: str, reading_data: dict) -> bool:
        """Send a daily reading reminder"""
        from app.services.bible_service import bible_service
        message = bible_service.format_reading_message(reading_data, user_name)
        return await self.send_message(to, message)
    
    def extract_user_data(self, payload: dict) -> Optional[dict]:
        """Extract user data from WhatsApp webhook payload"""
        try:
            data = payload.get("data", {})
            event_type = payload.get("event_type")
            
            # Only process incoming messages from users
            if event_type != "message_received":
                return None
            
            # Ignore bot messages and non-chat messages
            if (data.get("fromMe") or 
                data.get("self") or 
                data.get("ack") or 
                data.get("type") != "chat"):
                return None
            
            raw_id = data.get("author") or data.get("from")
            if not raw_id:
                return None
            
            user_id = raw_id if "@c.us" in raw_id else raw_id + "@c.us"
            message = data.get("body", "").strip()
            name = data.get("pushname", "Friend")
            
            return {
                "user_id": user_id,
                "message": message,
                "name": name,
                "raw_payload": data
            }
        except Exception as e:
            print(f"❌ Error extracting user data: {e}")
            return None

# Global service instance
whatsapp_service = WhatsAppService()