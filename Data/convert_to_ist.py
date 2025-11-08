import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "generated"))

from prisma import Prisma
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import os
import pytz

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

db = Prisma()

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')


async def convert_all_timestamps_to_ist():
    """Convert all existing UTC timestamps to IST by adding 5:30 hours"""
    await db.connect()
    
    print("Fetching all records...")
    all_records = await db.weather_db_v2.find_many(order={'timestamp': 'asc'})
    
    if not all_records:
        print("No records found in database.")
        await db.disconnect()
        return
    
    print(f"Found {len(all_records)} records to convert")
    print(f"\nExample timestamps BEFORE conversion:")
    print(f"  First: {all_records[0].timestamp} (UTC)")
    print(f"  Last:  {all_records[-1].timestamp} (UTC)")
    
    # Convert each timestamp from UTC to IST by adding 5:30 hours
    updated_count = 0
    for record in all_records:
        # Get the UTC timestamp
        utc_time = record.timestamp
        
        # If timestamp is naive (no timezone), assume it's UTC
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        
        # Add 5 hours 30 minutes to convert UTC to IST
        ist_time = utc_time + timedelta(hours=5, minutes=30)
        
        # Update the record with IST time (keeping the timezone info)
        await db.weather_db_v2.update(
            where={'id': record.id},
            data={'timestamp': ist_time}
        )
        updated_count += 1
        
        if updated_count % 100 == 0:
            print(f"Converted {updated_count} records...")
    
    print(f"\n✓ Successfully converted {updated_count} timestamps to IST")
    
    # Fetch records again to show the change
    updated_records = await db.weather_db_v2.find_many(
        order={'timestamp': 'asc'},
        take=1
    )
    last_record = await db.weather_db_v2.find_first(order={'timestamp': 'desc'})
    
    print(f"\nExample timestamps AFTER conversion:")
    if updated_records:
        print(f"  First: {updated_records[0].timestamp} (IST - added 5:30)")
    if last_record:
        print(f"  Last:  {last_record.timestamp} (IST - added 5:30)")
    
    await db.disconnect()


if __name__ == "__main__":
    print("=" * 60)
    print("Converting all timestamps from UTC to IST (Asia/Kolkata)")
    print("=" * 60)
    asyncio.run(convert_all_timestamps_to_ist())
