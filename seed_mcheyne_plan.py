import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Missing Supabase credentials!")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# The Bible chapters count per book
BIBLE_BOOKS = [
    ("Genesis", 50, "OT"), ("Exodus", 40, "OT"), ("Leviticus", 27, "OT"), ("Numbers", 36, "OT"),
    ("Deuteronomy", 34, "OT"), ("Joshua", 24, "OT"), ("Judges", 21, "OT"), ("Ruth", 4, "OT"),
    ("1 Samuel", 31, "OT"), ("2 Samuel", 24, "OT"), ("1 Kings", 22, "OT"), ("2 Kings", 25, "OT"),
    ("1 Chronicles", 29, "OT"), ("2 Chronicles", 36, "OT"), ("Ezra", 10, "OT"), ("Nehemiah", 13, "OT"),
    ("Esther", 10, "OT"), ("Job", 42, "OT"), ("Psalms", 150, "Wisdom"), ("Proverbs", 31, "Wisdom"),
    ("Ecclesiastes", 12, "Wisdom"), ("Song of Solomon", 8, "Wisdom"), ("Isaiah", 66, "OT"),
    ("Jeremiah", 52, "OT"), ("Lamentations", 5, "OT"), ("Ezekiel", 48, "OT"), ("Daniel", 12, "OT"),
    ("Hosea", 14, "OT"), ("Joel", 3, "OT"), ("Amos", 9, "OT"), ("Obadiah", 1, "OT"),
    ("Jonah", 4, "OT"), ("Micah", 7, "OT"), ("Nahum", 3, "OT"), ("Habakkuk", 3, "OT"),
    ("Zephaniah", 3, "OT"), ("Haggai", 2, "OT"), ("Zechariah", 14, "OT"), ("Malachi", 4, "OT"),
    ("Matthew", 28, "NT"), ("Mark", 16, "NT"), ("Luke", 24, "NT"), ("John", 21, "NT"),
    ("Acts", 28, "NT"), ("Romans", 16, "NT"), ("1 Corinthians", 16, "NT"), ("2 Corinthians", 13, "NT"),
    ("Galatians", 6, "NT"), ("Ephesians", 6, "NT"), ("Philippians", 4, "NT"), ("Colossians", 4, "NT"),
    ("1 Thessalonians", 5, "NT"), ("2 Thessalonians", 3, "NT"), ("1 Timothy", 6, "NT"),
    ("2 Timothy", 4, "NT"), ("Titus", 3, "NT"), ("Philemon", 1, "NT"), ("Hebrews", 13, "NT"),
    ("James", 5, "NT"), ("1 Peter", 5, "NT"), ("2 Peter", 3, "NT"), ("1 John", 5, "NT"),
    ("2 John", 1, "NT"), ("3 John", 1, "NT"), ("Jude", 1, "NT"), ("Revelation", 22, "NT")
]

# Flatten all chapters into their categories
ot_chapters = []
nt_chapters = []
wisdom_chapters = []

for book, chapters, category in BIBLE_BOOKS:
    for ch in range(1, chapters + 1):
        if category == "OT":
            ot_chapters.append(f"{book} {ch}")
        elif category == "NT":
            nt_chapters.append(f"{book} {ch}")
        elif category == "Wisdom":
            wisdom_chapters.append(f"{book} {ch}")

# Total chapters: OT=709, NT=260, Wisdom=220
# To fit 365 days, roughly: 2 OT, 1 NT, 1 Wisdom per day.
# Some days will double up or skip to fit exactly 365.

plan_365 = []
ot_idx = 0
nt_idx = 0
wis_idx = 0

start_date = datetime.now().date()

print("Generating 365-day Structured Plan starting from today...")

for day in range(1, 366):
    daily_refs = []
    
    # 2 OT chapters per day
    for _ in range(2):
        if ot_idx < len(ot_chapters):
            daily_refs.append(ot_chapters[ot_idx])
            ot_idx += 1
            
    # 1 NT chapter per day
    if nt_idx < len(nt_chapters):
        daily_refs.append(nt_chapters[nt_idx])
        nt_idx += 1
        
    # 1 Wisdom chapter per day (spread 220 over 365)
    if day % 2 != 0 or wis_idx < (day * 220 // 365):
        if wis_idx < len(wisdom_chapters):
            daily_refs.append(wisdom_chapters[wis_idx])
            wis_idx += 1

    # Join with semicolons
    ref_string = "; ".join(daily_refs)
    
    # Calculate date
    sched_date = start_date + timedelta(days=day - 1)
    
    plan_365.append({
        "day_number": day,
        "scheduled_date": sched_date.isoformat(),
        "scripture_reference": ref_string,
        "scripture_text": "" # Required by schema
    })

print(f"Generated {len(plan_365)} days.")
print("Clearing old plans from database...")

# Because of RLS or delete policies, let's just delete everything and insert
# Or better yet, we might have to delete one by one if there are limits, but simple delete works if admin.
supabase.table("reading_plans").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

print("Inserting new 365-day plan...")
for i in range(0, len(plan_365), 50):
    batch = plan_365[i:i+50]
    supabase.table("reading_plans").insert(batch).execute()

print("✅ Successfully seeded 365-day reading plan into Supabase!")
