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
    return data


async def get_hourly_average(data):
    avg = defaultdict(lambda : {"temp" :[], "humidity":[], "pressure": []})
    for d in data:
        hour = d.timestamp.hour
        avg[hour]["temp"].append(d.temperature)
        avg[hour]["humidity"].append(d.humidity)
        avg[hour]["pressure"].append(d.pressure)
    hourly_avg = {}
    for hour in range(24):
        if hour in avg and avg[hour]["temp"]:
            hourly_avg[hour] = {
                "avg_temp" : sum(avg[hour]["temp"]) / len(avg[hour]["temp"]),
                "avg_humidity" :sum(avg[hour]["humidity"]) / len(avg[hour]["humidity"]),
                "avg_pressure" : sum(avg[hour]["pressure"]) / len(avg[hour]["pressure"]),
            }
    return hourly_avg


async def main():
    data = await load_last_30_days_data()
    avg = await get_hourly_average(data)
    logging.info(avg)

asyncio.run(main())
