from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message

async def handle_group_registration(from_number: str, group_id: str, group_name: str) -> None:
    """
    Handles the !register command for a WhatsApp group.
    """
    # 1. Verify if the sender is a registered pastor
    response = supabase_client.table("pastors").select("church_id").eq("phone_number", from_number).execute()
    
    if not response.data:
        # Sender is not a registered pastor
        await send_text_message(group_id, "Registration failed: You are not authorized to register groups.")
        return
        
    pastor_data = response.data[0]
    church_id = pastor_data["church_id"]
    
    # 2. Check if group is already registered
    existing_group = supabase_client.table("groups").select("id").eq("whatsapp_group_id", group_id).execute()
    
    if existing_group.data:
        await send_text_message(group_id, f"This group is already registered as '{group_name}'.")
        return
        
    # 3. Register the new group
    new_group = {
        "church_id": church_id,
        "whatsapp_group_id": group_id,
        "name": group_name
    }
    
    insert_response = supabase_client.table("groups").insert(new_group).execute()
    
    if insert_response.data:
        await send_text_message(
            group_id, 
            f"✅ Successfully registered this group ('{group_name}') to your church's Daily Manna broadcast list."
        )
    else:
        await send_text_message(group_id, "❌ Failed to register group due to an internal error.")

async def handle_intercessor_registration(from_number: str, group_id: str) -> None:
    """
    Handles the !register_intercessors command for a WhatsApp group.
    """
    # 1. Verify if the sender is a registered pastor
    response = supabase_client.table("pastors").select("church_id").eq("phone_number", from_number).execute()
    
    if not response.data:
        await send_text_message(group_id, "Registration failed: You are not authorized to configure intercessor groups.")
        return
        
    church_id = response.data[0]["church_id"]
    
    # 2. Update the church's intercessor_group_id
    update_response = supabase_client.table("churches").update({"intercessor_group_id": group_id}).eq("id", church_id).execute()
    
    if update_response.data:
        await send_text_message(group_id, "🙏 This group has been successfully configured as the Intercessor Group for your church. Anonymous prayer requests will be routed here.")
    else:
        await send_text_message(group_id, "❌ Failed to configure intercessor group due to an internal error.")
