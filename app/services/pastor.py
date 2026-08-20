import asyncio
from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message

async def handle_pastor_message(phone_number: str, chat_id: str, text: str) -> bool:
    """
    Handles regular text messages sent by a pastor to the bot (Command Center).
    Prompts the pastor with a confirmation button to broadcast.
    Returns True if the sender is a pastor, False otherwise.
    """
    # 1. Verify sender is a pastor
    response = supabase_client.table("pastors").select("church_id").eq("phone_number", phone_number).execute()
    if not response.data:
        # Not a pastor
        return False
        
    # Strip the !broadcast command
    broadcast_msg = text.replace("!broadcast", "").strip()
    if not broadcast_msg:
        await send_text_message(chat_id, "Please provide a message to broadcast. Example: !broadcast Choir practice is canceled.")
        return True
        
    # 2. Store the pending broadcast in Supabase state
    state_payload = {
        "phone_number": phone_number,
        "message_text": broadcast_msg
    }
    supabase_client.table("broadcast_state").upsert(state_payload).execute()
    
    confirmation_text = f"You are about to broadcast the following message to all your groups:\n\n\"{broadcast_msg}\"\n\nReply with:\n1️⃣ to Send to All Groups\n2️⃣ to Cancel"
    await send_text_message(chat_id, confirmation_text)
    return True

async def execute_broadcast(phone_number: str, chat_id: str, message_snippet: str) -> None:
    """
    Executes the broadcast to all groups associated with the pastor's church.
    """
    
    # 1. Get pastor's church_id
    pastor_resp = supabase_client.table("pastors").select("church_id").eq("phone_number", phone_number).execute()
    if not pastor_resp.data:
        return
        
    church_id = pastor_resp.data[0]["church_id"]
    
    # 2. Get all groups for this church
    groups_resp = supabase_client.table("groups").select("whatsapp_group_id").eq("church_id", church_id).execute()
    if not groups_resp.data:
        await send_text_message(chat_id, "Broadcast failed: No groups registered for your church.")
        return
        
    # In Phase 1, we are just mocking the text to send since we couldn't easily pass full text in the ID.
    # We will simulate a broadcast of the snippet.
    broadcast_text = f"📢 Pastoral Announcement:\n\n{message_snippet}..."
    
    await send_text_message(chat_id, f"Starting broadcast to {len(groups_resp.data)} groups...")
    
    # 3. Loop through groups and send
    for group in groups_resp.data:
        group_id = group["whatsapp_group_id"]
        try:
            await send_text_message(group_id, broadcast_text)
            await asyncio.sleep(2) # Respect rate limits
        except Exception as e:
            print(f"Failed to send to {group_id}: {e}")
            
    await send_text_message(chat_id, "✅ Broadcast completed successfully.")
