from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import os
from app.config import settings
from app.services.whatsapp import send_text_message
from app.services.groups import handle_group_registration, handle_intercessor_registration
from app.services.pastor import handle_pastor_message, execute_broadcast
from app.services.ai_assistant import handle_ai_message
from app.core.utils import normalize_phone_number
from app.services.lists import handle_pledge, handle_volunteer, handle_list
from app.services.prayer import handle_prayer
from app.db.supabase import supabase_client

from app.services.group_ai import handle_group_message, handle_group_join

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handles incoming webhook payloads from OpenWA.
    """
    secret = request.headers.get("x-webhook-secret")
    if secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
        
        event = payload.get("event")
        data = payload.get("data", {})
        
        # Handle new member joining a WhatsApp group
        if event == "onGroupJoin":
            group_id = data.get("groupId")
            joined_user = data.get("joinedUser")
            if group_id:
                await handle_group_join(group_id, joined_user)
            return {"status": "success"}

        if event == "onMessage" or event == "onAnyMessage":
            sender_id = data.get("from", "")
            text_body = data.get("body", "").strip()
            
            # Dynamically extract bot number and store for scheduler fallback
            bot_number = data.get("botNumber")
            if bot_number:
                os.environ["BOT_PHONE_NUMBER"] = bot_number
                
            # Extract the sender ID reliably (using the resolved author from our Node server)
            raw_sender = data.get("author") or data.get("from", "")
            actual_sender = normalize_phone_number(raw_sender)
                
            if not text_body:
                return {"status": "success"}

            # Opt-out logic
            opt_out_check = supabase_client.table("opt_outs").select("phone_number").eq("phone_number", actual_sender).execute()
            if opt_out_check.data:
                return {"status": "ignored", "message": "User has opted out."}

            if text_body.upper() in ["STOP", "!STOP"]:
                supabase_client.table("opt_outs").insert({"phone_number": actual_sender}).execute()
                await send_text_message(sender_id, "You have successfully opted out. You will no longer receive automated broadcasts or AI messages.")
                return {"status": "success"}

            # Handle Text Messages
            if text_body:
                
                # Check for pending confirmations (1 or 2) in Supabase state
                if text_body in ["1", "2"]:
                    state_resp = supabase_client.table("broadcast_state").select("message_text").eq("phone_number", actual_sender).execute()
                    if state_resp.data:
                        if text_body == "1":
                            snippet = state_resp.data[0]["message_text"]
                            supabase_client.table("broadcast_state").delete().eq("phone_number", actual_sender).execute()
                            background_tasks.add_task(execute_broadcast, actual_sender, sender_id, snippet)
                            return {"status": "success"}
                        elif text_body == "2":
                            supabase_client.table("broadcast_state").delete().eq("phone_number", actual_sender).execute()
                            await send_text_message(sender_id, "Broadcast cancelled.")
                            return {"status": "success"}
                    
                print(f"DEBUG: Processing message from phone number: '{actual_sender}' (isGroup={data.get('isGroupMsg', False)})")
                
                # Check if it's a Group Message vs Direct Message
                is_group = data.get("isGroupMsg", False)

                if is_group:
                    # Group Commands & Interactive Reflections
                    if text_body.startswith("!register"):
                        if text_body == "!register_intercessors":
                            await handle_intercessor_registration(actual_sender, sender_id)
                        else:
                            parts = text_body.split(" ", 1)
                            group_name = parts[1] if len(parts) > 1 else "Unnamed Group"
                            await handle_group_registration(actual_sender, sender_id, group_name)
                    else:
                        # Process group discussion (only responds if interacting with Daily Manna scripture)
                        await handle_group_message(actual_sender, sender_id, text_body, data)
                
                else:
                    # Direct Message Handling
                    upper_text = text_body.upper()
                    
                    if upper_text in ["MENU", "HELP", "HI", "HELLO", "START"]:
                        menu_text = (
                            "Welcome to *Redeemer Hope Church*! 🕊️✨\n\n"
                            "I am your Pastoral AI Assistant, and I'm so glad you're here. You can chat with me naturally about anything on your heart, or ask me to:\n\n"
                            "📖 *Share a devotional thought*\n"
                            "🙏 *Submit a prayer request*\n"
                            "🤝 *Make a pledge or volunteer*\n\n"
                            "Just reply normally and let me know how I can serve you today! 😊"
                        )
                        await send_text_message(sender_id, menu_text)
                    elif text_body.startswith("STUDY_"):
                        await handle_ai_message(actual_sender, sender_id, text_body)
                    elif text_body.startswith("!broadcast"):
                        is_pastor = await handle_pastor_message(actual_sender, sender_id, text_body)
                        if not is_pastor:
                            await send_text_message(sender_id, "You are not authorized to send broadcasts.")
                    elif text_body.startswith("!list"):
                        await handle_list(actual_sender, sender_id, text_body)
                    else:
                        # Regular conversational message in DM
                        await handle_ai_message(actual_sender, sender_id, text_body)

        return {"status": "success"}
    except Exception as e:
        print(f"Error processing OpenWA webhook: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/test-broadcast")
@router.post("/test-broadcast")
async def trigger_test_broadcast():
    """
    Manually triggers the Daily Manna Scripture Broadcast for testing without waiting for 6:00 AM.
    """
    from app.services.scheduler import run_daily_manna_broadcast
    try:
        await run_daily_manna_broadcast()
        return {"status": "success", "message": "Daily Manna Scripture Broadcast triggered successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


