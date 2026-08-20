import httpx
from app.config import settings

async def send_text_message(to: str, text: str) -> dict:
    """Helper function to send a simple text message via OpenWA."""
    url = f"{settings.OPENWA_URL}/api/sendText"
    
    payload = {
        "chatId": to,
        "text": text,
        "session": "default"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to send text message to {to}: {e}")
            return {}

async def send_interactive_button_message(to: str, body_text: str, buttons: list) -> dict:
    """Helper function to send an interactive button message via OpenWA."""
    url = f"{settings.OPENWA_URL}/api/sendButtons"
    
    # Format buttons for OpenWA: [{"id": "...", "text": "..."}]
    formatted_buttons = []
    for btn in buttons:
        formatted_buttons.append({
            "id": btn["id"],
            "text": btn["title"]
        })
        
    payload = {
        "chatId": to,
        "title": "Action Required",
        "text": body_text,
        "footer": "Daily Manna",
        "buttons": formatted_buttons,
        "session": "default"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to send button message to {to}: {e}")
            return {}

import os
import re

async def get_bot_phone_number() -> str:
    """Helper function to fetch connected bot phone number dynamically."""
    env_num = os.getenv("BOT_PHONE_NUMBER", "").strip()
    if env_num:
        return re.sub(r'\D', '', env_num)
        
    url = f"{settings.OPENWA_URL}/api/getBotInfo"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                bot_num = resp.json().get("botNumber")
                if bot_num:
                    clean_num = re.sub(r'\D', '', bot_num)
                    os.environ["BOT_PHONE_NUMBER"] = clean_num
                    return clean_num
    except Exception as e:
        print(f"Could not fetch bot phone number dynamically: {e}")
        
    return ""

