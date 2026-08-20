import os
from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message

async def _get_default_church() -> dict:
    """Helper to get a default church since we don't have a members table yet."""
    resp = supabase_client.table("churches").select("*").limit(1).execute()
    if resp.data:
        return resp.data[0]
    return None

async def handle_prayer(phone_number: str, chat_id: str, text: str) -> None:
    """Handles !pray <message>"""
    # Extract prayer text
    prayer_msg = text.replace("!pray", "").strip()
    if not prayer_msg:
        await send_text_message(chat_id, "Please include your prayer request. Example: !pray Please pray for my family's health.")
        return
        
    church = await _get_default_church()
    if not church:
        await send_text_message(chat_id, "System error: No church configured.")
        return
        
    church_id = church["id"]
    
    payload = {
        "church_id": church_id,
        "original_sender": phone_number,
        "anonymized_text": prayer_msg
    }
    
    # Save the request
    supabase_client.table("prayer_requests").insert(payload).execute()
    
    # Route to intercessor group
    intercessor_group_id = church.get("intercessor_group_id")
    if not intercessor_group_id:
        intercessor_group_id = os.getenv("TEST_INTERCESSOR_GROUP_ID")
        
    if intercessor_group_id:
        dispatch_text = f"🙏 *Anonymous Prayer Request*\n\n\"{prayer_msg}\"\n\nPlease join in praying for this request."
        await send_text_message(intercessor_group_id, dispatch_text)
        
    await send_text_message(chat_id, "Your prayer request has been received anonymously and shared with the intercessor team.")

async def record_prayer_request_db(phone_number: str, prayer_msg: str) -> str:
    """Saves prayer request and routes it to intercessors, returns status message for AI."""
    church = await _get_default_church()
    if not church:
        return "Failed to record prayer request: No church configured."
        
    church_id = church["id"]
    payload = {
        "church_id": church_id,
        "original_sender": phone_number,
        "anonymized_text": prayer_msg
    }
    
    supabase_client.table("prayer_requests").insert(payload).execute()
    
    intercessor_group_id = church.get("intercessor_group_id")
    if not intercessor_group_id:
        intercessor_group_id = os.getenv("TEST_INTERCESSOR_GROUP_ID")
        
    if intercessor_group_id:
        dispatch_text = f"🙏 *Anonymous Prayer Request*\n\n\"{prayer_msg}\"\n\nPlease join in praying for this request."
        await send_text_message(intercessor_group_id, dispatch_text)
        
    return "Prayer request has been successfully recorded and shared with the intercessors."
