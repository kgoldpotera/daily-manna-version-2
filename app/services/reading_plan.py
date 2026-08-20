import datetime
from app.db.supabase import supabase_client

def seed_sample_reading_plans() -> None:
    """
    Seeds 7 days of sample devotional records into Supabase if the table is empty.
    """
    # Check if table is empty
    response = supabase_client.table("reading_plans").select("id").limit(1).execute()
    if response.data:
        print("Reading plans already exist. Skipping seed.")
        return

    today = datetime.date.today()
    sample_plans = [
        {
            "day_number": 1,
            "scheduled_date": (today + datetime.timedelta(days=0)).isoformat(),
            "scripture_reference": "Psalm 23:1-3",
            "scripture_text": "The LORD is my shepherd; I shall not want. He maketh me to lie down in green pastures: he leadeth me beside the still waters. He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.",
            "reflection_text": "God's provision and guidance are a source of deep comfort. Even in the midst of turmoil, He offers us 'still waters' and a restored soul. When we allow Him to lead, we find true rest.",
            "discussion_question": "How have you experienced God's provision or guidance in a difficult time?"
        },
        {
            "day_number": 2,
            "scheduled_date": (today + datetime.timedelta(days=1)).isoformat(),
            "scripture_reference": "Matthew 6:33",
            "scripture_text": "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you.",
            "reflection_text": "We often worry about our daily needs and future plans. Jesus flips our priorities, asking us to seek God's kingdom above all else, with the promise that He will take care of our earthly needs.",
            "discussion_question": "What is one practical way you can seek God's kingdom first today?"
        },
        {
            "day_number": 3,
            "scheduled_date": (today + datetime.timedelta(days=2)).isoformat(),
            "scripture_reference": "Philippians 4:6-7",
            "scripture_text": "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God. And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus.",
            "reflection_text": "Anxiety is a common human experience, but Paul offers an antidote: prayer mixed with gratitude. When we surrender our worries, God replaces them with His incomprehensible peace.",
            "discussion_question": "What worry do you need to hand over to God in prayer right now?"
        },
        {
            "day_number": 4,
            "scheduled_date": (today + datetime.timedelta(days=3)).isoformat(),
            "scripture_reference": "Isaiah 40:31",
            "scripture_text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint.",
            "reflection_text": "Waiting on God is not passive; it is an active trust in His timing. Those who wait are promised renewed strength to overcome obstacles and endure long seasons.",
            "discussion_question": "How does trusting in God's timing change your perspective on your current struggles?"
        },
        {
            "day_number": 5,
            "scheduled_date": (today + datetime.timedelta(days=4)).isoformat(),
            "scripture_reference": "Proverbs 3:5-6",
            "scripture_text": "Trust in the LORD with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths.",
            "reflection_text": "Our own understanding is limited and often flawed. True wisdom involves a wholehearted reliance on God's direction rather than our own intuition.",
            "discussion_question": "Where are you currently leaning on your own understanding instead of trusting God?"
        },
        {
            "day_number": 6,
            "scheduled_date": (today + datetime.timedelta(days=5)).isoformat(),
            "scripture_reference": "Romans 8:28",
            "scripture_text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
            "reflection_text": "Not all things are good, but God can weave all circumstances—even the painful ones—into a beautiful tapestry for His purpose and our ultimate good.",
            "discussion_question": "Can you recall a time when God used a negative situation for your good?"
        },
        {
            "day_number": 7,
            "scheduled_date": (today + datetime.timedelta(days=6)).isoformat(),
            "scripture_reference": "Lamentations 3:22-23",
            "scripture_text": "It is of the LORD's mercies that we are not consumed, because his compassions fail not. They are new every morning: great is thy faithfulness.",
            "reflection_text": "God's mercy is never exhausted. Every morning brings a fresh supply of His compassion, giving us a new opportunity to experience His faithfulness.",
            "discussion_question": "How have you seen God's fresh mercy in your life this week?"
        }
    ]

    try:
        supabase_client.table("reading_plans").insert(sample_plans).execute()
        print(f"Successfully seeded {len(sample_plans)} reading plans.")
    except Exception as e:
        print(f"Failed to seed reading plans: {e}")
