import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "generated"))

from prisma import Prisma
import asyncio
from dotenv import load_dotenv
from datetime import timedelta
import os
import pytz

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

db = Prisma()

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')


async def revert_timestamps_from_ist():
    """Revert timestamps back by removing the 5.5 hours that were incorrectly added"""
    await db.connect()
    
    print("Fetching all records...")
    all_records = await db.weather_db_v2.find_many(order={'timestamp': 'asc'})
    
    if not all_records:
        print("No records found in database.")
        await db.disconnect()
        return
    
    print(f"Found {len(all_records)} records to revert")
    print(f"\nFirst record timestamp (before): {all_records[0].timestamp}")
    print(f"Last record timestamp (before): {all_records[-1].timestamp}")
    
    # Revert each timestamp by subtracting 5.5 hours
    updated_count = 0
    for record in all_records:
        # Get the current timestamp (which has +5.5 hours added incorrectly)
        wrong_time = record.timestamp
        
        # Subtract 5.5 hours to get back to IST stored as UTC
        correct_time = wrong_time - timedelta(hours=5, minutes=30)
        
        # Update the record
        await db.weather_db_v2.update(
            where={'id': record.id},
            data={'timestamp': correct_time}
        )
        updated_count += 1
        
        if updated_count % 100 == 0:
            print(f"Reverted {updated_count} records...")
    
    print(f"\n✓ Successfully reverted {updated_count} timestamps")
    
    # Fetch first few records to show the change
    updated_records = await db.weather_db_v2.find_many(
        order={'timestamp': 'asc'},
        take=3
    )
    print("\nFirst 3 records after revert:")
    for rec in updated_records:
        print(f"  {rec.timestamp} - Temp: {rec.temperature}°C")
    
    await db.disconnect()


if __name__ == "__main__":
    print("=" * 60)
    print("Reverting incorrectly converted timestamps")
    print("=" * 60)
    asyncio.run(revert_timestamps_from_ist())
