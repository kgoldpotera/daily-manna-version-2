import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message
from app.config import settings
import os
from dotenv import load_dotenv

scheduler = AsyncIOScheduler()

async def generate_dynamic_devotional(scripture_ref: str) -> dict:
    """
    Calls the AI model to dynamically generate a rich, deep, contextually accurate 
    7-part devotional for the specific scripture reading of the day.
    """
    if not os.getenv("GROQ_API_KEY"):
        return {}

    prompt = f"""You are an expert, biblically grounded pastoral scholar.
Given today's assigned Bible reading passage: '{scripture_ref}', generate a concise daily devotional guide strictly in JSON format.

JSON keys required:
- todays_focus: (A 2-3 sentence key theme or focus point of the reading)
- verse_to_remember: (Exact quote of ONE single, specific verse from {scripture_ref} that contains a call to action for the users to think about. DO NOT quote an entire chapter.)
- verse_reference: (Exact reference for the quoted verse, including the specific chapter AND verse number, e.g. Matthew 3:2, NOT just Matthew 3)
- todays_prayer: (Short 2-3 sentence scripture-shaped prayer arising naturally from {scripture_ref})
- go_deeper_question: (A single thought-provoking question based on the reading for further reflection)
"""
    try:
        from app.services.ai_client import chat_completion_with_fallback
        import json
        
        response = await chat_completion_with_fallback(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        raw_json = response.choices[0].message.content
        return json.loads(raw_json)
    except Exception as e:
        print(f"Error generating dynamic devotional for {scripture_ref}: {e}")
        return {}

async def run_daily_manna_broadcast() -> None:
    """
    Query reading_plans for today's entry, query registered groups, 
    and format the devotional broadcast card using the condensed structure.
    """
    print("Starting Daily Manna Broadcast...")
    today_dt = datetime.date.today()
    today_iso = today_dt.isoformat()
    day_of_year = today_dt.timetuple().tm_yday
    
    reading_plan = None
    try:
        plan_resp = supabase_client.table("reading_plans").select("*").eq("scheduled_date", today_iso).execute()
        if plan_resp.data:
            reading_plan = plan_resp.data[0]
    except Exception as e:
        print(f"Supabase query error: {e}")

    if not reading_plan:
        from app.services.bible_service import bible_service
        plan_list = bible_service.reading_plan
        if plan_list:
            idx = min(day_of_year - 1, len(plan_list) - 1)
            reading_plan = plan_list[idx]

    if not reading_plan:
        print("No reading plan available. Broadcast cancelled.")
        return

    # 2. Query all registered groups
    groups_resp = supabase_client.table("groups").select("whatsapp_group_id").execute()
    if not groups_resp.data:
        print("No registered groups found. Broadcast cancelled.")
        return

    # Extract required fields
    day_num = reading_plan.get("day_number", reading_plan.get("day", day_of_year))
    date_str = reading_plan.get("date", today_dt.strftime("%B %d").upper())
    scripture_ref = reading_plan.get("scripture_reference", "Mark 1-3")
    
    todays_prayer = reading_plan.get("todays_prayer", "")
    verse_quote = reading_plan.get("verse_to_remember", "")
    verse_ref = reading_plan.get("verse_reference", scripture_ref.split(';')[0] if ';' in scripture_ref else scripture_ref)
    plan_id = reading_plan.get("id", f"DAY_{day_num}")

    # Dynamically generate deep AI devotional content if generic or empty
    if not todays_prayer or not verse_quote:
        print(f"Generating dynamic concise AI devotional for passage: '{scripture_ref}'...")
        ai_dev = await generate_dynamic_devotional(scripture_ref)
        if ai_dev:
            todays_prayer = ai_dev.get("todays_prayer", todays_prayer)
            verse_quote = ai_dev.get("verse_to_remember", verse_quote)
            verse_ref = ai_dev.get("verse_reference", verse_ref)
            todays_focus = ai_dev.get("todays_focus", "Focus on what God is saying through today's reading.")
            go_deeper_question = ai_dev.get("go_deeper_question", "What is God speaking to you through this passage?")
        else:
            todays_focus = "Focus on what God is saying through today's reading."
            go_deeper_question = "What is God speaking to you through this passage?"
    else:
        todays_focus = reading_plan.get("todays_focus", "Focus on what God is saying through today's reading.")
        go_deeper_question = reading_plan.get("go_deeper_question", "What is God speaking to you through this passage?")


    # Build bot phone number for direct DM link
    from app.services.whatsapp import get_bot_phone_number
    bot_phone_number = await get_bot_phone_number()

    if bot_phone_number:
        dm_link = f"https://wa.me/{bot_phone_number}?text=STUDY_{plan_id}"
    else:
        dm_link = f"https://wa.me/?text=STUDY_{plan_id}"

    # Generate BibleGateway ESV Link
    clean_ref = scripture_ref.replace("; ", ",").replace(" ", "+")
    bible_gateway_url = f"https://www.biblegateway.com/passage/?search={clean_ref}&version=ESV"

    formatted_scripture = scripture_ref.replace(';', '\n📖')

    broadcast_text = f"""📖 DAY {day_num}/365 — {date_str}

Today’s Reading
📜 {formatted_scripture}

🔗 Read the full chapters:
{bible_gateway_url}

💡 TODAY’S FOCUS
{todays_focus}

📌 VERSE TO REMEMBER
"{verse_quote}"
— {verse_ref}

🙏 TODAY’S PRAYER
{todays_prayer}

💡 GO DEEPER
{go_deeper_question}

Ask the AI Bible Assistant about today's reading. Explore the Scriptures, ask questions, and reflect on how God's Word applies to your life.

👉 {dm_link}

━━━━━━━━━━━━━━━━━━
📖 365 DAYS • ONE BIBLE • ONE JOURNEY
Keep reading. Keep walking. Keep growing."""

    from app.core.utils import split_long_message
    chunks = split_long_message(broadcast_text, max_chars=4096)

    print(f"Broadcasting to {len(groups_resp.data)} groups ({len(chunks)} message parts)...")
    
    # 4. Iterate through registered groups and trigger outbound delivery
    for group in groups_resp.data:
        group_id = group["whatsapp_group_id"]
        try:
            for i, chunk in enumerate(chunks):
                await send_text_message(group_id, chunk)
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.8)
            await asyncio.sleep(2) # Prevent rate limiting between groups
        except Exception as e:
            print(f"Failed to send broadcast to group {group_id}: {e}")
            
    print("Daily Manna Broadcast completed.")


def print_countdown():
    """Prints a countdown to the terminal so the user knows exactly when the broadcast will run."""
    job = scheduler.get_job("daily_manna_job")
    if job and job.next_run_time:
        now = datetime.datetime.now(job.next_run_time.tzinfo)
        diff = job.next_run_time - now
        minutes_left = int(diff.total_seconds() / 60)
        
        if 0 < minutes_left <= 5:
            print(f"⏳ COUNTDOWN: Daily Manna broadcast will send in {minutes_left} minute(s)! (Target: {job.next_run_time.strftime('%H:%M %Z')})", flush=True)
        elif minutes_left == 0:
            print(f"🚀 COUNTDOWN: Sending broadcast NOW!", flush=True)

def start_scheduler():
    # Force reload of .env to completely bypass PM2's environment caching
    load_dotenv(override=True)
    
    # Use environment variable for schedule time, defaulting to 06:00
    cron_hour = int(os.getenv("BROADCAST_HOUR", "6"))
    cron_minute = int(os.getenv("BROADCAST_MINUTE", "0"))
    
    scheduler.add_job(
        run_daily_manna_broadcast,
        trigger=CronTrigger(hour=cron_hour, minute=cron_minute, timezone="Africa/Nairobi"),
        id="daily_manna_job",
        replace_existing=True
    )
    
    # Add the countdown ticker to run every 1 minute
    scheduler.add_job(
        print_countdown,
        trigger="interval",
        minutes=1,
        id="countdown_job",
        replace_existing=True
    )
    
    scheduler.start()
    
    job = scheduler.get_job("daily_manna_job")
    if job and job.next_run_time:
        print(f"✅ Scheduler started! Next broadcast is locked in for exactly: {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')}", flush=True)
