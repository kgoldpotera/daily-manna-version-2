import re
from datetime import datetime
from typing import Dict, Any
from app.services.user_service import user_service
from app.services.bible_service import bible_service
from app.services.whatsapp_service import whatsapp_service
from app.models.user import User

class MessageHandler:
    def __init__(self):
        self.commands = {
            "START": self._handle_start,
            "READ": self._handle_read,
            "REFLECT": self._handle_reflect,
            "STATS": self._handle_stats,
            "REMIND": self._handle_remind,
            "STOP REMINDER": self._handle_stop_reminder,
            "HELP": self._handle_help,
            "TODAY": self._handle_today_reading,
            "RESET": self._handle_reset
        }
        self.bible_versions = ["KJV", "NIV", "ESV"]
    
    async def handle_message(self, user_data: Dict[str, Any]) -> bool:
        """Main message handling logic"""
        try:
            user_id = user_data["user_id"]
            message = user_data["message"]
            name = user_data["name"]
            command = message.upper().strip()
            
            print(f"📨 Processing: '{command}' from {user_id}")
            
            # Prevent message loops
            if self._is_bot_message(message):
                print("🛑 Preventing bot message loop")
                return True
            
            # Handle specific commands
            for cmd, handler in self.commands.items():
                if command.startswith(cmd):
                    return await handler(user_id, message, name)
            
            # Handle Bible version selection
            if command in self.bible_versions:
                return await self._handle_bible_version(user_id, command)
            
            # Handle time format (e.g., "6:30 AM" or "18:00")
            if self._is_time_format(message):
                return await self._handle_time_setting(user_id, message)
            
            # Default fallback
            return await self._handle_unknown_command(user_id)
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            return False
    
    def _is_bot_message(self, message: str) -> bool:
        """Check if message is from bot to prevent loops"""
        bot_signatures = [
            "I didn't understand that",
            "Daily Manna",
            "Welcome to Daily Manna",
            "Good morning"
        ]
        return any(sig.lower() in message.lower() for sig in bot_signatures)
    
    def _is_time_format(self, message: str) -> bool:
        """Check if message is a time format"""
        time_pattern = re.compile(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])\s?(AM|PM)?$", re.IGNORECASE)
        return bool(time_pattern.match(message.strip()))
    
    async def _handle_start(self, user_id: str, message: str, name: str) -> bool:
        """Handle START command"""
        user = User(
            user_id=user_id,
            name=name,
            phone=user_id.replace("@c.us", ""),
            created_at=datetime.utcnow()
        )
        
        result = await user_service.register_user(user)
        
        if result["success"]:
            welcome_msg = f"""{result["message"]}

🙏 Welcome to Daily Manna! Your daily Bible reading companion.

📖 Commands you can use:
• TODAY - Get today's reading
• READ - Mark today's reading as complete
• REFLECT <your thoughts> - Save a reflection
• STATS - View your progress
• REMIND 7:00 - Set daily reminder time
• HELP - Show all commands

Ready to start your spiritual journey? Send TODAY to get your first reading! 🌟"""
            
            return await whatsapp_service.send_message(user_id, welcome_msg)
        else:
            return await whatsapp_service.send_message(user_id, result["message"])
    
    async def _handle_read(self, user_id: str, message: str, name: str) -> bool:
        """Handle READ command"""
        success = await user_service.update_reading_progress(user_id)
        if success:
            progress = await user_service.get_user_progress(user_id)
            days = progress.days_completed if progress else 1
            
            response = f"""✅ Excellent! Your reading has been recorded.

📊 Progress: {days} day(s) completed
🎯 Keep building that daily habit!

💭 Want to reflect on what you read? Send: REFLECT <your thoughts>"""
            
            return await whatsapp_service.send_message(user_id, response)
        else:
            return await whatsapp_service.send_message(user_id, "❌ Failed to record your reading. Please try again.")
    
    async def _handle_reflect(self, user_id: str, message: str, name: str) -> bool:
        """Handle REFLECT command"""
        reflection_text = message[7:].strip()  # Remove "REFLECT" prefix
        
        if not reflection_text:
            return await whatsapp_service.send_message(user_id, "💭 Please include your reflection. Example: REFLECT This passage taught me about faith...")
        
        progress = await user_service.get_user_progress(user_id)
        current_day = progress.current_day if progress else 1
        
        success = await user_service.save_reflection(user_id, reflection_text, current_day)
        
        if success:
            response = f"""📝 Your reflection has been saved! 

"{reflection_text}"

🙏 Thank you for taking time to meditate on God's word. These reflections will help you grow spiritually."""
            return await whatsapp_service.send_message(user_id, response)
        else:
            return await whatsapp_service.send_message(user_id, "❌ Failed to save your reflection. Please try again.")
    
    async def _handle_stats(self, user_id: str, message: str, name: str) -> bool:
        """Handle STATS command"""
        progress = await user_service.get_user_progress(user_id)
        
        if progress:
            days_completed = progress.days_completed
            current_day = progress.current_day
            last_read = progress.last_read_date.strftime("%B %d, %Y") if progress.last_read_date else "Never"
            
            # Calculate streak and percentage
            percentage = min((days_completed / 365) * 100, 100)
            
            response = f"""📊 *Your Daily Manna Progress*

✅ Days completed: {days_completed}
📅 Current day: {current_day}
📖 Last reading: {last_read}
📈 Progress: {percentage:.1f}% of yearly goal

🎯 {"Amazing consistency! Keep it up!" if days_completed > 7 else "Great start! Build that daily habit!"}

💪 Remember: "Your word is a lamp for my feet, a light on my path." - Psalm 119:105"""
        else:
            response = """📊 *Your Daily Manna Progress*

✅ Days completed: 0
📖 No readings recorded yet

🌟 Ready to start? Send TODAY to get your first reading, then READ to mark it complete!"""
        
        return await whatsapp_service.send_message(user_id, response)
    
    async def _handle_remind(self, user_id: str, message: str, name: str) -> bool:
        """Handle REMIND command"""
        # Extract time from message like "REMIND 6:30"
        match = re.search(r"REMIND\s+(\d{1,2}):(\d{2})", message.upper())
        if match:
            hour, minute = match.groups()
            reminder_time = f"{int(hour):02d}:{minute}"
            
            success = await user_service.update_user_settings(
                user_id, 
                reminder_time=reminder_time, 
                reminder_active=True
            )
            
            if success:
                response = f"""⏰ Perfect! Daily reminders set for *{reminder_time}*

You'll receive your Daily Manna reading every day at this time.

🔕 To stop reminders: STOP REMINDER
⏰ To change time: REMIND <new_time>"""
                return await whatsapp_service.send_message(user_id, response)
        
        return await whatsapp_service.send_message(user_id, "❌ Invalid format. Use: REMIND 6:30 (24-hour format)")
    
    async def _handle_stop_reminder(self, user_id: str, message: str, name: str) -> bool:
        """Handle STOP REMINDER command"""
        success = await user_service.update_user_settings(user_id, reminder_active=False)
        
        if success:
            response = """🔕 Daily reminders have been turned off.

You can still get readings anytime by sending TODAY.

⏰ To turn reminders back on: REMIND <time>"""
            return await whatsapp_service.send_message(user_id, response)
        else:
            return await whatsapp_service.send_message(user_id, "❌ Failed to update reminder settings.")
    
    async def _handle_today_reading(self, user_id: str, message: str, name: str) -> bool:
        """Handle TODAY command"""
        user = await user_service.get_user(user_id)
        if not user:
            return await whatsapp_service.send_message(user_id, "❌ Please send START first to register.")
        
        progress = await user_service.get_user_progress(user_id)
        current_day = progress.current_day if progress else 1
        
        reading_data = bible_service.get_reading_for_day(current_day)
        formatted_message = bible_service.format_reading_message(reading_data, user.name)
        
        return await whatsapp_service.send_message(user_id, formatted_message)
    
    async def _handle_help(self, user_id: str, message: str, name: str) -> bool:
        """Handle HELP command"""
        help_text = """📖 *Daily Manna Commands*

🌟 *Getting Started:*
• START - Register for Daily Manna
• TODAY - Get today's Bible reading

📚 *Reading & Progress:*
• READ - Mark today's reading complete
• STATS - View your reading progress
• REFLECT <text> - Save your thoughts

⏰ *Reminders:*
• REMIND 7:00 - Set daily reminder time
• STOP REMINDER - Turn off reminders

📖 *Bible Versions:*
• ESV, NIV, KJV - Set preferred version

🔧 *Other:*
• HELP - Show this menu
• RESET - Reset all your data

Need help? Just send any of these commands! 🙏"""
        
        return await whatsapp_service.send_message(user_id, help_text)
    
    async def _handle_reset(self, user_id: str, message: str, name: str) -> bool:
        """Handle RESET command - for testing purposes"""
        try:
            # Delete user data
            if user_service.db:
                user_service.db.table("users").delete().eq("user_id", user_id).execute()
                user_service.db.table("progress").delete().eq("user_id", user_id).execute()
                user_service.db.table("reflections").delete().eq("user_id", user_id).execute()
            
            response = """🔄 Your Daily Manna data has been reset.

Send START to begin again! 🌟"""
            return await whatsapp_service.send_message(user_id, response)
        except Exception as e:
            print(f"❌ Error resetting user data: {e}")
            return await whatsapp_service.send_message(user_id, "❌ Failed to reset data.")
    
    async def _handle_bible_version(self, user_id: str, version: str) -> bool:
        """Handle Bible version selection"""
        success = await user_service.update_user_settings(user_id, preferred_version=version)
        
        if success:
            response = f"""✅ Bible version set to *{version}*

Your reading links will now use the {version} translation.

📖 Send TODAY to get your reading in {version}!"""
            return await whatsapp_service.send_message(user_id, response)
        else:
            return await whatsapp_service.send_message(user_id, "❌ Failed to update Bible version.")
    
    async def _handle_time_setting(self, user_id: str, message: str) -> bool:
        """Handle time format messages like '6:30 AM' or '18:00'"""
        time_pattern = re.compile(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])\s?(AM|PM)?$", re.IGNORECASE)
        match = time_pattern.match(message.strip())
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            meridian = match.group(3)
            
            # Convert to 24-hour format
            if meridian:
                meridian = meridian.upper()
                if meridian == "PM" and hour != 12:
                    hour += 12
                elif meridian == "AM" and hour == 12:
                    hour = 0
            
            reminder_time = f"{hour:02d}:{minute:02d}"
            
            success = await user_service.update_user_settings(
                user_id, 
                reminder_time=reminder_time, 
                reminder_active=True
            )
            
            if success:
                response = f"""⏰ Reminder time updated to *{reminder_time}*

You'll receive your Daily Manna every day at this time! 🌅

🔕 To stop: STOP REMINDER"""
                return await whatsapp_service.send_message(user_id, response)
        
        return await whatsapp_service.send_message(user_id, "❌ Invalid time format. Use: 6:30 AM or 18:00")
    
    async def _handle_unknown_command(self, user_id: str) -> bool:
        """Handle unknown commands"""
        response = """❓ I didn't understand that command.

📖 *Quick Commands:*
• TODAY - Get today's reading
• READ - Mark reading complete
• STATS - View progress
• HELP - Show all commands

Try one of these! 🙏"""
        
        return await whatsapp_service.send_message(user_id, response)

# Global handler instance
message_handler = MessageHandler()