import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class BibleService:
    def __init__(self):
        self.reading_plan = self._load_reading_plan()
    
    def _load_reading_plan(self) -> list:
        """Load the Bible reading plan from JSON file"""
        try:
            plan_file = Path("reading_plan.json")
            if plan_file.exists():
                with open(plan_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # Fallback plan if file doesn't exist
                return self._create_fallback_plan()
        except Exception as e:
            print(f"❌ Error loading reading plan: {e}")
            return self._create_fallback_plan()
    
    def _create_fallback_plan(self) -> list:
        """Create a simple fallback reading plan"""
        return [
            {
                "day": i,
                "date": f"Day {i}",
                "old_testament": "Genesis 1",
                "new_testament": "Matthew 1",
                "psalm_or_gospel": "Psalm 1"
            } for i in range(1, 366)
        ]
    
    def get_reading_for_day(self, day: int) -> Dict[str, Any]:
        """Get Bible reading for a specific day"""
        try:
            if 1 <= day <= len(self.reading_plan):
                plan_item = self.reading_plan[day - 1]
                reading_text = f"{plan_item['old_testament']}; {plan_item['new_testament']}; {plan_item['psalm_or_gospel']}"
                
                return {
                    "day": day,
                    "date": plan_item.get("date", f"Day {day}"),
                    "reading": reading_text,
                    "old_testament": plan_item["old_testament"],
                    "new_testament": plan_item["new_testament"],
                    "psalm_or_gospel": plan_item["psalm_or_gospel"],
                    "link": self._generate_bible_link(reading_text, "ESV")
                }
            else:
                return {
                    "day": day,
                    "date": f"Day {day}",
                    "reading": "🎉 Congratulations! You've completed the reading plan!",
                    "link": "https://www.bible.com"
                }
        except Exception as e:
            print(f"❌ Error getting reading for day {day}: {e}")
            return self._get_fallback_reading(day)
    
    def get_today_reading(self) -> Dict[str, Any]:
        """Get today's Bible reading"""
        day_of_year = datetime.now().timetuple().tm_yday
        return self.get_reading_for_day(day_of_year)
    
    def _generate_bible_link(self, reference: str, version: str = "ESV") -> str:
        """Generate a link to read the Bible passage online"""
        try:
            # Clean up the reference for URL
            clean_ref = reference.replace("; ", ",").replace(" ", "+")
            
            if version.upper() == "ESV":
                return f"https://www.esv.org/{clean_ref}/"
            elif version.upper() == "NIV":
                return f"https://www.biblegateway.com/passage/?search={clean_ref}&version=NIV"
            elif version.upper() == "KJV":
                return f"https://www.biblegateway.com/passage/?search={clean_ref}&version=KJV"
            else:
                return f"https://www.biblegateway.com/passage/?search={clean_ref}&version=ESV"
        except Exception:
            return "https://www.bible.com"
    
    def _get_fallback_reading(self, day: int) -> Dict[str, Any]:
        """Fallback reading when there's an error"""
        return {
            "day": day,
            "date": f"Day {day}",
            "reading": "John 3:16 - For God so loved the world that he gave his one and only Son...",
            "link": "https://www.bible.com"
        }
    
    def format_reading_message(self, reading_data: Dict[str, Any], user_name: str = "Friend") -> str:
        """Format the reading into a WhatsApp message"""
        return f"""📖 *Daily Manna - Day {reading_data['day']}*

Good morning {user_name}! 🌅

Today's Reading:
{reading_data['reading']}

🔗 Read online: {reading_data['link']}

💭 After reading, send: REFLECT <your thoughts>
✅ Mark as complete: READ

Have a blessed day! 🙏"""

# Global service instance
bible_service = BibleService()