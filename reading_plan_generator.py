import json
from datetime import datetime, timedelta

def generate_reading_plan():
    """Generate a 365-day Bible reading plan"""
    
    # This is a simplified version - you can expand this with a real reading plan
    old_testament_books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
        "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
        "Ecclesiastes", "Song of Songs", "Isaiah", "Jeremiah",
        "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
        "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
        "Zephaniah", "Haggai", "Zechariah", "Malachi"
    ]
    
    new_testament_books = [
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
        "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
        "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
        "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
        "Jude", "Revelation"
    ]
    
    plan = []
    start_date = datetime(2024, 1, 1)
    
    for day in range(1, 366):
        current_date = start_date + timedelta(days=day-1)
        
        # Simple rotation through books (this is just an example)
        ot_book = old_testament_books[(day - 1) % len(old_testament_books)]
        nt_book = new_testament_books[(day - 1) % len(new_testament_books)]
        
        # Generate chapter numbers (simplified)
        ot_chapter = ((day - 1) % 10) + 1
        nt_chapter = ((day - 1) % 5) + 1
        psalm_num = ((day - 1) % 150) + 1
        
        plan_item = {
            "day": day,
            "date": current_date.strftime("%B %d"),
            "old_testament": f"{ot_book} {ot_chapter}",
            "new_testament": f"{nt_book} {nt_chapter}",
            "psalm_or_gospel": f"Psalm {psalm_num}"
        }
        
        plan.append(plan_item)
    
    return plan

def save_reading_plan():
    """Generate and save the reading plan to JSON file"""
    plan = generate_reading_plan()
    
    with open("reading_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated reading plan with {len(plan)} days")
    print("📁 Saved to reading_plan.json")

if __name__ == "__main__":
    save_reading_plan()