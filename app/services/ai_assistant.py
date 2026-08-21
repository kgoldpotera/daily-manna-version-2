import os
import json
import asyncio
from openai import AsyncOpenAI
from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message
from app.core.utils import format_for_whatsapp, split_long_message

from app.services.prayer import record_prayer_request_db
from app.services.lists import record_pledge_db



SYSTEM_PROMPT = """You are the Pastoral AI Assistant for Redeemer Hope Church, serving under the theological direction of its Reformed Baptist ministry.

IDENTITY & MISSION:
- Governing Principle: Sola Scriptura, Solus Christus, Sola Gratia, Sola Fide, Soli Deo Gloria.
- Purpose: Assist church members, seekers, families, and visitors with biblically faithful reflection, theological understanding, and practical discipleship.
- You are an assistive ministry tool, NOT a pastor, elder, therapist, prophet, or replacement for local church oversight. Always encourage connection with elders and church leadership.

CONVERSATIONAL & PERSONALIZED:
- Greet users warmly and naturally with pastoral care. Use tasteful emojis (e.g., 🙏, 🕊️, ✨).
- Do NOT use excessive ALL CAPS (like "HEY THERE!"). Keep it gentle and conversational.
- Use provided tools (functions) to perform actions like making a pledge or submitting a prayer request. Never tell the user you are calling a tool.

THEOLOGICAL FOUNDATION & SCRIPTURE FIRST:
- Reason consistently with historic Reformed Baptist theology.
- Prefer direct biblical teaching, cite Scripture accurately, and interpret in context.

PASTORAL POSTURE & BOUNDARIES:
- Be warm, patient, compassionate, humble, respectful, and Christ-centered.
- STRICT BOUNDARIES: Never declare anyone's salvation status with certainty.

HIGH-RISK & SENSITIVE SITUATIONS (CRISIS GUARDRAILS):
- If a user expresses severe distress, self-harm, suicidal thoughts, abuse, or crisis:
  1. COMPASSION & HOPE: Respond immediately with warm pastoral compassion.
  2. REDIRECT DIRECTLY TO REDEEMER HOPE CHURCH ELDER ADMINS.

RESPONSE FRAMEWORK (Listen → Scripture → Gospel → Application → Next Step):
- Keep responses concise, natural, easy to read on mobile screens.
- Use bullet points (• or 📌) and emojis instead of Markdown headers or tables."""

async def save_user_name_db(phone_number: str, name: str) -> str:
    """Saves the user's name to the database."""
    supabase_client.table("users").upsert({
        "phone_number": phone_number,
        "name": name
    }).execute()
    return f"User name successfully saved as {name}."

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_user_name",
            "description": "Saves the user's name to personalize future conversations. Call this immediately after the user provides their name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The user's first name (and last name if provided)"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_prayer_request",
            "description": "Submits a prayer request to the church intercessor team on behalf of the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prayer_text": {
                        "type": "string",
                        "description": "The specific prayer request detailed by the user"
                    }
                },
                "required": ["prayer_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_pledge",
            "description": "Records a financial pledge made by the user to the church.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The numeric amount the user is pledging"
                    }
                },
                "required": ["amount"]
            }
        }
    }
]

async def generate_biblical_response(phone_number: str, user_message: str, context_reading: dict = None) -> str:
    """
    Generates a biblical response using OpenAI GPT / Groq.
    Maintains conversational memory durably in Supabase.
    """
    if not os.getenv("GROQ_API_KEY"):
        return "System error: The AI assistant is currently unavailable (Missing API Key)."
        
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Inject user name context
    try:
        user_resp = supabase_client.table("users").select("name").eq("phone_number", phone_number).execute()
        user_name = user_resp.data[0]["name"] if user_resp.data else None
    except Exception:
        user_name = None

    if user_name:
        context_str = f"System Context: You are speaking to {user_name}. YOU ALREADY KNOW THEIR NAME. DO NOT ask for their name again. DO NOT call the save_user_name tool."
    else:
        context_str = "System Context: You do not know the user's name. If you haven't already, politely ask for it. If they just provided it, you MUST call the save_user_name tool right now to save it!"
        
    messages.append({"role": "system", "content": context_str})
    
    if context_reading:
        # Clear previous history for this user when starting a new focused study
        supabase_client.table("ai_chat_history").delete().eq("phone_number", phone_number).execute()
        
        study_context = f"The user is reflecting on today's reading plan. Reference: {context_reading.get('scripture_reference')}. Text: {context_reading.get('scripture_text')}. Reflection: {context_reading.get('reflection_text')}. Discussion Question: {context_reading.get('discussion_question')}."
        messages.append({"role": "system", "content": study_context})
    else:
        # Fetch the last 13 messages for this user
        history_resp = supabase_client.table("ai_chat_history").select("*").eq("phone_number", phone_number).order("created_at", desc=False).limit(13).execute()
        for row in history_resp.data:
            messages.append({"role": row["role"], "content": row["content"]})
            
    messages.append({"role": "user", "content": user_message})
    
    from app.services.ai_client import chat_completion_with_fallback
    
    full_ai_reply = ""
    max_continuations = 5  # Increased slightly to handle tool loops
    
    try:
        for attempt in range(max_continuations):
            response = await chat_completion_with_fallback(
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                tools=TOOLS,
                tool_choice="auto"
            )
            choice = response.choices[0]
            
            if choice.message.tool_calls:
                # Handle tool calls
                messages.append(choice.message) # append the assistant's tool call message
                
                for tool_call in choice.message.tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    print(f"DEBUG: AI called tool {function_name} with args {args}")
                    result_msg = ""
                    
                    try:
                        if function_name == "save_user_name":
                            result_msg = await save_user_name_db(phone_number, args.get("name"))
                        elif function_name == "submit_prayer_request":
                            result_msg = await record_prayer_request_db(phone_number, args.get("prayer_text"))
                        elif function_name == "record_pledge":
                            result_msg = await record_pledge_db(phone_number, float(args.get("amount")))
                        else:
                            result_msg = "Unknown function."
                    except Exception as e:
                        result_msg = f"Error executing tool: {e}"
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_msg
                    })
                
                # Continue loop to let AI generate final reply
                continue 
            
            part = choice.message.content or ""
            full_ai_reply += part
            
            finish_reason = getattr(choice, "finish_reason", "stop")
            
            # If hit max_tokens, trigger auto-continuation
            if finish_reason == "length" and attempt < max_continuations - 1:
                print(f"DEBUG: Response was cut off by max_tokens. Triggering auto-continuation step {attempt + 1}...")
                messages.append({"role": "assistant", "content": part})
                messages.append({"role": "user", "content": "Continue directly from the exact word where you stopped. Do not repeat any previous text."})
            else:
                break

        import re
        # Remove <think> blocks generated by reasoning models like DeepSeek
        full_ai_reply = re.sub(r'<think>.*?</think>', '', full_ai_reply, flags=re.DOTALL)
        # Remove any unclosed <think> blocks just in case
        full_ai_reply = re.sub(r'<think>.*', '', full_ai_reply, flags=re.DOTALL).strip()

        full_ai_reply = format_for_whatsapp(full_ai_reply)

        # Durably save the interaction to Supabase
        supabase_client.table("ai_chat_history").insert({"phone_number": phone_number, "role": "user", "content": user_message}).execute()
        supabase_client.table("ai_chat_history").insert({"phone_number": phone_number, "role": "assistant", "content": full_ai_reply}).execute()
        
        return full_ai_reply
    except Exception as e:
        print(f"AI Assistant Error: {e}")
        return "I apologize, but I am having trouble connecting to my knowledge base right now. Please try again later."


async def handle_ai_message(phone_number: str, chat_id: str, text: str) -> None:
    """
    Handles an incoming DM to the bot.
    """
    # Check if it's a deep link STUDY_<ID>
    if text.startswith("STUDY_"):
        plan_id = text.replace("STUDY_", "").strip()
        print(f"DEBUG: Processing study deep link for plan ID: {plan_id}")
        
        # Fetch the reading plan
        try:
            if plan_id == "TODAY":
                import datetime
                today_iso = datetime.date.today().isoformat()
                plan_resp = supabase_client.table("reading_plans").select("*").eq("scheduled_date", today_iso).execute()
                
                if not plan_resp.data:
                    # Fallback to local json reading plan
                    from app.services.bible_service import bible_service
                    day_of_year = datetime.date.today().timetuple().tm_yday
                    idx = min(day_of_year - 1, len(bible_service.reading_plan) - 1)
                    plan_data = bible_service.reading_plan[idx] if bible_service.reading_plan else {}
                    
                    scripture_ref = plan_data.get("scripture_reference", f"{plan_data.get('old_testament', '')}; {plan_data.get('new_testament', '')}")
                    discussion = plan_data.get("discussion_question", "What did you learn about God in today's reading?")
                    reading_plan = {"scripture_reference": scripture_ref, "discussion_question": discussion}
                else:
                    reading_plan = plan_resp.data[0]
            else:
                plan_resp = supabase_client.table("reading_plans").select("*").eq("id", plan_id).execute()
                if not plan_resp.data:
                    await send_text_message(chat_id, "I couldn't find that specific reading plan. But I'm here if you have any questions!")
                    return
                reading_plan = plan_resp.data[0]
                
        except Exception as e:
            print(f"DEBUG: Supabase query failed for plan ID {plan_id}: {e}")
            await send_text_message(chat_id, "That doesn't look like a valid study link. Make sure you click the exact link from the Daily Manna broadcast!")
            return
            
        welcome_msg = f"Welcome to today's study on {reading_plan.get('scripture_reference', 'the Bible')}! What are your thoughts on the discussion question:\n'{reading_plan.get('discussion_question', 'What stood out to you in this passage?')}'"
        
        await send_text_message(chat_id, welcome_msg)
        
        # Inject context silently into memory without a user message
        await generate_biblical_response(phone_number, "I am ready to reflect on this reading plan.", reading_plan)
        
        return
        
    # General DM handling
    print(f"DEBUG: Generating AI response for message: {text}")
    ai_response = await generate_biblical_response(phone_number, text)
    
    # Split response into manageable consecutive WhatsApp messages if long
    chunks = split_long_message(ai_response, max_chars=1200)
    for i, chunk in enumerate(chunks):
        await send_text_message(chat_id, chunk)
        if i < len(chunks) - 1:
            await asyncio.sleep(0.8)

