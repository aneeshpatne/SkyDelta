import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "generated"))

from prisma import Prisma
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging


env_path = os.path.join(os.path.dirname(__file__), '.env')

load_dotenv(dotenv_path=env_path)

db = Prisma()

async def load_last_30_days_data():
    await db.connect()
    delta = datetime.now() - timedelta(days= 30)
    logging.info(f"Fetching Data from {delta.date} to {datetime.now().date()}")
    data = await db.weather_db_v2.find_many(
        where={
            'timestamp':{
                'gte' : delta
            }
        },
        order={
            'timestamp': 'asc'
        }
    )
    logging.info(f"Retrived Data: {len(data)}")

async def main():
    await load_last_30_days_data()

asyncio.run(main())
