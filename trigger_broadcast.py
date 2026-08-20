#!/usr/bin/env python3
"""
Trigger script to immediately execute the Daily Manna Scripture Broadcast.
Run this script to test outbound scripture delivery without waiting for 6:00 AM.
"""
import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import io
import os

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scheduler import run_daily_manna_broadcast

async def main():
    print("Triggering immediate Daily Manna Scripture Broadcast test...")
    try:
        await run_daily_manna_broadcast()
        print("Scripture broadcast test executed successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error executing broadcast test: {e}")

if __name__ == "__main__":
    asyncio.run(main())

