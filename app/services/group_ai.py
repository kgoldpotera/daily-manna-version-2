import os
import asyncio
from openai import AsyncOpenAI
from app.services.whatsapp import send_text_message, get_bot_phone_number
from app.core.utils import format_for_whatsapp, split_long_message
from app.services.ai_assistant import SYSTEM_PROMPT



GROUP_AI_PROMPT = SYSTEM_PROMPT + """

IMPORTANT INSTRUCTIONS FOR GROUP CHAT MESSAGES:
- Keep group responses very concise, clear, and encouraging (under 120 words).
- Focus specifically on the daily scripture reading or theological question being discussed.
- Maintain a warm, welcoming, pastoral tone suitable for a church fellowship group.
- Do NOT use Markdown headers (#, ##) or Markdown tables. Use clean emojis and bullet points if needed."""


BIBLE_BOOKS = [
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua", "judges", "ruth",
    "samuel", "kings", "chronicles", "ezra", "nehemiah", "esther", "job", "psalm", "psalms",
    "proverbs", "ecclesiastes", "song of solomon", "isaiah", "jeremiah", "lamentations",
    "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah", "jonah", "micah", "nahum",
    "habakkuk", "zephaniah", "haggai", "zechariah", "malachi", "matthew", "mark", "luke",
    "john", "acts", "romans", "corinthians", "galatians", "ephesians", "philippians",
    "colossians", "thessalonians", "timothy", "titus", "philemon", "hebrews", "james",
    "peter", "jude", "revelation"
]

def should_respond_to_group_message(data: dict, text_body: str) -> bool:
    """
    Determines if the bot should respond to a message sent in a WhatsApp group.
    Returns True if the message interacts with Daily Manna scripture, quotes a message,
    mentions a Bible book/passage, or tags the bot/user in a reflection context.
    Returns False for unrelated general group chatter (e.g., choir logistics).
    """
    text_lower = text_body.lower()
    
    # 1. Any message quoting another message in the group
    if data.get("hasQuotedMsg"):
        return True

    # 2. Direct tag (@bot, @dailymanna, @Musandu, or any @ mention) or ! command
    if "@" in text_lower or text_body.startswith("!"):
        return True

    # 3. Bible book mention (e.g., Proverbs 3:6, John 3:16, Psalm 23)
    if any(book in text_lower for book in BIBLE_BOOKS):
        return True

    # 4. Verse reference pattern (e.g. 3:6, 14:1-3)
    import re
    if re.search(r'\b\d+:\d+\b', text_lower):
        return True

    # 5. Scripture reflection keywords
    study_keywords = [
        "today's reading", "todays reading", "daily manna", "today's scripture", 
        "today's passage", "today's devotional", "scripture reflection", 
        "what does this verse", "bible reading", "what does", "meaning of", 
        "scripture", "devotional", "god's word"
    ]
    if any(keyword in text_lower for keyword in study_keywords):
        return True

    # Otherwise, ignore general group chatter
    return False


async def handle_group_message(actual_sender: str, group_id: str, text_body: str, data: dict) -> None:
    """
    Handles incoming messages inside a WhatsApp group.
    Only responds if the message interacts with the Daily Manna scripture discussion.
    """
    if not should_respond_to_group_message(data, text_body):
        print(f"DEBUG: Ignoring general group chatter in {group_id}: '{text_body[:30]}...'")
        return

    if not os.getenv("GROQ_API_KEY"):
        return

    print(f"DEBUG: Processing Daily Manna group interaction from {actual_sender} in {group_id}")

    messages = [
        {"role": "system", "content": GROUP_AI_PROMPT},
        {"role": "user", "content": text_body}
    ]

    from app.services.ai_client import chat_completion_with_fallback

    try:
        response = await chat_completion_with_fallback(
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        ai_reply = response.choices[0].message.content or ""
        ai_reply = format_for_whatsapp(ai_reply)

        # Get bot number for private DM link
        bot_phone = await get_bot_phone_number()
        if bot_phone:
            dm_link = f"https://wa.me/{bot_phone}?text=STUDY_TODAY"
        else:
            dm_link = f"https://wa.me/?text=STUDY_TODAY"

        full_message = f"{ai_reply}\n\n----------------------------------\n💡 *Want to reflect privately in DM?*\nTap here to chat with AI Assistant:\n{dm_link}"

        # Send response to the group
        chunks = split_long_message(full_message, max_chars=1200)
        for chunk in chunks:
            await send_text_message(group_id, chunk)
            await asyncio.sleep(0.5)

    except Exception as e:
        print(f"Error handling group AI message: {e}")


async def handle_group_join(group_id: str, joined_phone: str = None) -> None:
    """
    Sends a warm welcome message when a new member joins a WhatsApp group.
    """
    bot_phone = await get_bot_phone_number()
    if bot_phone:
        dm_link = f"https://wa.me/{bot_phone}?text=STUDY_TODAY"
    else:
        dm_link = f"https://wa.me/?text=STUDY_TODAY"

    welcome_msg = (
        "👋 *Welcome to Redeemer Hope Church Daily Manna Group!* 📖\n\n"
        "We are glad to have you with us as we journey through God's Word together. "
        "Every morning at 06:00, we share our daily scripture reading and devotional guide.\n\n"
        "💡 *Want to reflect privately or ask questions in DM?*\n"
        f"Tap here to start a private study:\n{dm_link}"
    )

    try:
        await send_text_message(group_id, welcome_msg)
    except Exception as e:
        print(f"Failed to send group join welcome to {group_id}: {e}")
