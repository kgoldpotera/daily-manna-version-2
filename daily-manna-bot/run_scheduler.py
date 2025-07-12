#!/usr/bin/env python3
"""
Standalone script to run the reminder scheduler.
This should be run as a separate process from the main API.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.scheduler.reminder_scheduler import reminder_scheduler

async def main():
    """Main function to run the scheduler"""
    print("🚀 Starting Daily Manna Reminder Scheduler...")
    print("📅 This will send daily Bible reading reminders to users")
    print("⏰ Checking for reminders every minute...")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        await reminder_scheduler.start_scheduler()
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user")
        reminder_scheduler.stop_scheduler()
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)