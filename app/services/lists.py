from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message
import re

async def _get_default_church_id() -> str:
    """Helper to get a default church ID for members since we don't have a members table yet."""
    resp = supabase_client.table("churches").select("id").limit(1).execute()
    if resp.data:
        return resp.data[0]["id"]
    return None

async def handle_pledge(phone_number: str, chat_id: str, text: str) -> None:
    """Handles !pledge <amount>"""
    # Extract amount
    amount_match = re.search(r'\d+', text)
    if not amount_match:
        await send_text_message(chat_id, "Please provide an amount. Example: !pledge 500")
        return
        
    amount = float(amount_match.group())
    church_id = await _get_default_church_id()
    
    payload = {
        "church_id": church_id,
        "list_type": "pledge",
        "member_number": phone_number,
        "amount_pledged": amount
    }
    
    supabase_client.table("dynamic_lists").insert(payload).execute()
    await send_text_message(chat_id, f"Thank you! Your pledge of {amount} has been successfully recorded.")

async def record_pledge_db(phone_number: str, amount: float) -> str:
    """Saves pledge and returns status message for AI."""
    church_id = await _get_default_church_id()
    
    payload = {
        "church_id": church_id,
        "list_type": "pledge",
        "member_number": phone_number,
        "amount_pledged": amount
    }
    
    supabase_client.table("dynamic_lists").insert(payload).execute()
    return f"Pledge of {amount} has been successfully recorded."

async def handle_volunteer(phone_number: str, chat_id: str) -> None:
    """Handles !volunteer"""
    church_id = await _get_default_church_id()
    
    # Check if already volunteered
    check_resp = supabase_client.table("dynamic_lists").select("id").eq("member_number", phone_number).eq("list_type", "volunteer").execute()
    if check_resp.data:
        await send_text_message(chat_id, "You are already on the volunteer list. Thank you for your service!")
        return
        
    payload = {
        "church_id": church_id,
        "list_type": "volunteer",
        "member_number": phone_number
    }
    
    supabase_client.table("dynamic_lists").insert(payload).execute()
    await send_text_message(chat_id, "Thank you! You have been added to the volunteer list. The church administration will contact you soon.")

async def handle_list(phone_number: str, chat_id: str, text: str) -> None:
    """Handles !list <type> (For Pastors only)"""
    # Verify sender is a pastor
    pastor_resp = supabase_client.table("pastors").select("church_id").eq("phone_number", phone_number).execute()
    if not pastor_resp.data:
        await send_text_message(chat_id, "You are not authorized to view church lists.")
        return
        
    church_id = pastor_resp.data[0]["church_id"]
    parts = text.split(" ")
    list_type = parts[1].lower() if len(parts) > 1 else "all"
    
    if list_type not in ["pledge", "volunteer"]:
        await send_text_message(chat_id, "Please specify a valid list type: '!list pledge' or '!list volunteer'.")
        return
        
    list_resp = supabase_client.table("dynamic_lists").select("*").eq("church_id", church_id).eq("list_type", list_type).execute()
    records = list_resp.data
    
    if list_type == "pledge":
        total_pledged = sum(r.get("amount_pledged") or 0 for r in records)
        count = len(records)
        report = f"📊 *Pledge Report*\nTotal Pledges: {count}\nTotal Amount: {total_pledged}"
    else:
        count = len(records)
        report = f"🤝 *Volunteer Report*\nTotal Volunteers: {count}"
        
    await send_text_message(chat_id, report)
