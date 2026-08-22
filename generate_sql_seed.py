#!/usr/bin/env python3
"""
Generator for a Complete 365-Day Whole-Bible Reading Plan to SQL.
Covers 100% of all 66 books and 1,189 chapters of the Bible (Genesis 1:1 to Revelation 22:21).
Outputs a `seed_reading_plans.sql` file starting from Jan 1st of the current year.
"""
from datetime import datetime, timedelta

def build_whole_bible_schedule():
    """
    Constructs a 365-day schedule mapping all 1,189 chapters of the Bible.
    Old Testament: 39 books, 929 chapters (~2.5 chapters/day)
    New Testament: 27 books, 260 chapters (~0.7 chapters/day)
    """
    ot_chapters = [
        ("Genesis", 50), ("Exodus", 40), ("Leviticus", 27), ("Numbers", 36), ("Deuteronomy", 34),
        ("Joshua", 24), ("Judges", 21), ("Ruth", 4), ("1 Samuel", 31), ("2 Samuel", 24),
        ("1 Kings", 22), ("2 Kings", 25), ("1 Chronicles", 29), ("2 Chronicles", 36),
        ("Ezra", 10), ("Nehemiah", 13), ("Esther", 10), ("Job", 42), ("Psalms", 150), ("Proverbs", 31),
        ("Ecclesiastes", 12), ("Song of Solomon", 8), ("Isaiah", 66), ("Jeremiah", 52),
        ("Lamentations", 5), ("Ezekiel", 48), ("Daniel", 12), ("Hosea", 14), ("Joel", 3),
        ("Amos", 9), ("Obadiah", 1), ("Jonah", 4), ("Micah", 7), ("Nahum", 3), ("Habakkuk", 3),
        ("Zephaniah", 3), ("Haggai", 2), ("Zechariah", 14), ("Malachi", 4)
    ]
    
    nt_chapters = [
        ("Matthew", 28), ("Mark", 16), ("Luke", 24), ("John", 21), ("Acts", 28), ("Romans", 16),
        ("1 Corinthians", 16), ("2 Corinthians", 13), ("Galatians", 6), ("Ephesians", 6),
        ("Philippians", 4), ("Colossians", 4), ("1 Thessalonians", 5), ("2 Thessalonians", 3),
        ("1 Timothy", 6), ("2 Timothy", 4), ("Titus", 3), ("Philemon", 1), ("Hebrews", 13),
        ("James", 5), ("1 Peter", 5), ("2 Peter", 3), ("1 John", 5), ("2 John", 1), ("3 John", 1),
        ("Jude", 1), ("Revelation", 22)
    ]

    # Expand into individual chapter tokens
    all_ot = []
    for book, count in ot_chapters:
        for c in range(1, count + 1):
            all_ot.append((book, c))
            
    all_nt = []
    for book, count in nt_chapters:
        for c in range(1, count + 1):
            all_nt.append((book, c))

    plan = []
    current_year = datetime.now().year
    start_date = datetime(current_year, 1, 1)

    ot_index = 0
    nt_index = 0

    total_ot = len(all_ot)
    total_nt = len(all_nt)

    for day in range(1, 366):
        curr_date = start_date + timedelta(days=day-1)

        # Allocate OT portion (~2-3 chapters/day)
        ot_target = int(round(day * (total_ot / 365.0)))
        ot_portion_list = all_ot[ot_index:ot_target]
        ot_index = ot_target

        # Allocate NT portion (~0-1 chapter/day)
        nt_target = int(round(day * (total_nt / 365.0)))
        nt_portion_list = all_nt[nt_index:nt_target]
        nt_index = nt_target

        # Format OT ref
        if ot_portion_list:
            b_name = ot_portion_list[0][0]
            start_c = ot_portion_list[0][1]
            end_c = ot_portion_list[-1][1]
            ot_ref = f"{b_name} {start_c}" if start_c == end_c else f"{b_name} {start_c}-{end_c}"
        else:
            ot_ref = ""

        # Format NT ref
        if nt_portion_list:
            b_name = nt_portion_list[0][0]
            start_c = nt_portion_list[0][1]
            end_c = nt_portion_list[-1][1]
            nt_ref = f"{b_name} {start_c}" if start_c == end_c else f"{b_name} {start_c}-{end_c}"
        else:
            nt_ref = ""

        # Combine scripture reference
        refs = [r for r in [ot_ref, nt_ref] if r]
        scripture_ref = "; ".join(refs) if refs else "Psalms 119"

        entry = {
            "day": day,
            "scheduled_date": curr_date.strftime("%Y-%m-%d"),
            "scripture_reference": scripture_ref,
        }

        plan.append(entry)

    return plan

def main():
    plan = build_whole_bible_schedule()
    out_file = "seed_reading_plans.sql"
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("-- Complete 365-Day Whole-Bible Reading Plan\n")
        f.write("-- Start Date: January 1st\n\n")
        f.write("-- Clear out old plans to ensure no duplicates or misaligned dates\n")
        f.write("DELETE FROM reading_plans;\n\n")
        
        f.write("-- Insert 365 daily records\n")
        f.write("INSERT INTO reading_plans (day_number, scheduled_date, scripture_reference, scripture_text)\nVALUES\n")
        
        # Format the values
        for i, entry in enumerate(plan):
            day_num = entry['day']
            sched_date = entry['scheduled_date']
            ref = entry['scripture_reference']
            # Escape single quotes in scripture_reference just in case, though there shouldn't be any
            ref = ref.replace("'", "''")
            
            # The schema requires scripture_text, we pass an empty string
            line = f"    ({day_num}, '{sched_date}', '{ref}', '')"
            
            if i == len(plan) - 1:
                line += ";"
            else:
                line += ","
                
            f.write(line + "\n")
            
    print(f"Generated 365-Day Whole-Bible Plan SQL script in {out_file}.")

if __name__ == "__main__":
    main()
