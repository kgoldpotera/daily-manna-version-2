import asyncio
import schedule
import time
from datetime import datetime
from app.services.user_service import user_service
from app.services.bible_service import bible_service
from app.services.whatsapp_service import whatsapp_service

class ReminderScheduler:
    def __init__(self):
        self.running = False
    
    async def send_daily_reminders(self):
        """Send daily reminders to users"""
        current_time = datetime.now().strftime("%H:%M")
        print(f"🕒 Checking for reminders at {current_time}")
        
        try:
            users = await user_service.get_users_for_reminder(current_time)
            print(f"📋 Found {len(users)} users for reminder at {current_time}")
            
            for user_data in users:
                user_id = user_data["user_id"]
                name = user_data.get("name", "Friend")
                
                # Get user's current reading day
                progress = await user_service.get_user_progress(user_id)
                current_day = progress.current_day if progress else 1
                
                # Get reading for the day
                reading_data = bible_service.get_reading_for_day(current_day)
                
                # Send reminder
                success = await whatsapp_service.send_reading_reminder(user_id, name, reading_data)
                
                if success:
                    print(f"✅ Reminder sent to {name} ({user_id})")
                else:
                    print(f"❌ Failed to send reminder to {name} ({user_id})")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Error sending daily reminders: {e}")
    
    def schedule_reminders(self):
        """Schedule reminder checks every minute"""
        # Schedule to run every minute
        schedule.every().minute.do(lambda: asyncio.create_task(self.send_daily_reminders()))
    
    async def start_scheduler(self):
        """Start the reminder scheduler"""
        print("⏰ Starting reminder scheduler...")
        self.running = True
        self.schedule_reminders()
        
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the reminder scheduler"""
        print("🛑 Stopping reminder scheduler...")
        self.running = False

# Global scheduler instance
reminder_scheduler = ReminderScheduler()

# Standalone script to run scheduler
if __name__ == "__main__":
    print("🚀 Starting Daily Manna Reminder Scheduler...")
    try:
        asyncio.run(reminder_scheduler.start_scheduler())
    except KeyboardInterrupt:
        print("👋 Scheduler stopped by user")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")