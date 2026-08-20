import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.supabase import supabase_client
from app.services.whatsapp import send_text_message
from app.config import settings
import os

scheduler = AsyncIOScheduler()

async def generate_dynamic_devotional(scripture_ref: str) -> dict:
    """
    Calls the AI model to dynamically generate a rich, deep, contextually accurate 
    7-part devotional for the specific scripture reading of the day.
    """
    if not os.getenv("GROQ_API_KEY"):
        return {}

    prompt = f"""You are an expert, biblically grounded pastoral scholar.
Given today's assigned Bible reading passage: '{scripture_ref}', generate a deep, contextually accurate 7-part devotional guide strictly in JSON format.

JSON keys required:
- what_we_read: (Detailed 3-4 sentences summarizing major events, arguments, themes, people, and movements in {scripture_ref})
- teaches_about_god: (What {scripture_ref} specifically reveals about God's holiness, grace, sovereignty, justice, or faithfulness)
- seeing_christ: (How {scripture_ref} contributes to the redemptive storyline and points toward Christ or the gospel without forcing symbolic interpretations)
- take_to_heart: (3 bullet points • of practical applications for believers today based on {scripture_ref})
- todays_prayer: (Short 2-3 sentence scripture-shaped prayer arising naturally from {scripture_ref})
- verse_to_remember: (Exact quote of one significant verse from {scripture_ref})
- verse_reference: (Exact reference for the quoted verse, e.g. {scripture_ref.split(';')[0]})
"""
    try:
        from app.services.ai_client import chat_completion_with_fallback
        import json
        
        response = await chat_completion_with_fallback(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,
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
    and format the devotional broadcast card using the 7-part Daily Reading Structure.
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

    # Extract 7-part reading fields
    day_num = reading_plan.get("day_number", reading_plan.get("day", day_of_year))
    date_str = reading_plan.get("date", today_dt.strftime("%B %d").upper())
    scripture_ref = reading_plan.get("scripture_reference", "Mark 1-3")
    
    what_we_read = reading_plan.get("what_we_read", "")
    teaches_about_god = reading_plan.get("teaches_about_god", "")
    seeing_christ = reading_plan.get("seeing_christ", "")
    take_to_heart = reading_plan.get("take_to_heart", "")
    todays_prayer = reading_plan.get("todays_prayer", "")
    verse_quote = reading_plan.get("verse_to_remember", "")
    verse_ref = reading_plan.get("verse_reference", scripture_ref.split(';')[0] if ';' in scripture_ref else scripture_ref)
    plan_id = reading_plan.get("id", f"DAY_{day_num}")

    # Dynamically generate deep AI devotional content if generic or empty
    if not what_we_read or "scheduled passages" in what_we_read:
        print(f"Generating dynamic deep AI devotional for passage: '{scripture_ref}'...")
        ai_dev = await generate_dynamic_devotional(scripture_ref)
        if ai_dev:
            what_we_read = ai_dev.get("what_we_read", what_we_read)
            teaches_about_god = ai_dev.get("teaches_about_god", teaches_about_god)
            seeing_christ = ai_dev.get("seeing_christ", seeing_christ)
            take_to_heart = ai_dev.get("take_to_heart", take_to_heart)
            todays_prayer = ai_dev.get("todays_prayer", todays_prayer)
            verse_quote = ai_dev.get("verse_to_remember", verse_quote)
            verse_ref = ai_dev.get("verse_reference", verse_ref)


    # Build bot phone number for direct DM link
    from app.services.whatsapp import get_bot_phone_number
    bot_phone_number = await get_bot_phone_number()

    if bot_phone_number:
        dm_link = f"https://wa.me/{bot_phone_number}?text=STUDY_{plan_id}"
    else:
        dm_link = f"https://wa.me/?text=STUDY_{plan_id}"

    # Generate BibleGateway NIV Link
    clean_ref = scripture_ref.replace("; ", ",").replace(" ", "+")
    bible_gateway_url = f"https://www.biblegateway.com/passage/?search={clean_ref}&version=NIV"

    broadcast_text = f"""📖 DAY {day_num}/365 — {date_str}

Today's Reading:
{scripture_ref}

🔎 What We Read
{what_we_read}

💡 What It Teaches Us About God
{teaches_about_god}

✝️ Seeing Christ and the Gospel
{seeing_christ}

❤️ What Should We Take to Heart?
{take_to_heart}

🙏 Today's Prayer
{todays_prayer}

📌 Verse to Remember
"{verse_quote}" — {verse_ref}

----------------------------------
🔗 Read the full chapters here: 
{bible_gateway_url}

💡 Want to study deeper? 
Tap here to reflect with the AI Bible Assistant: 
{dm_link}"""

    from app.core.utils import split_long_message
    chunks = split_long_message(broadcast_text, max_chars=1200)

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


def start_scheduler():
    # Use environment variable for schedule time, defaulting to 06:00
    cron_hour = int(os.getenv("BROADCAST_HOUR", "6"))
    cron_minute = int(os.getenv("BROADCAST_MINUTE", "0"))
    
    scheduler.add_job(
        run_daily_manna_broadcast,
        trigger=CronTrigger(hour=cron_hour, minute=cron_minute),
        id="daily_manna_job",
        replace_existing=True
    )
    scheduler.start()
    print(f"Scheduler started. Next broadcast scheduled for {cron_hour:02d}:{cron_minute:02d} daily.")
