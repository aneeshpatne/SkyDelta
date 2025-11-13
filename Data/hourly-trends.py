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
import requests

logging.basicConfig(level=logging.INFO)

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

def fetch_data():
    data = requests.get("http://192.168.1.50/sensors_v2", timeout=2)
    return data.json()

def calcn_change(data_now, avg):
    h = datetime.now().hour
    temp_now = data_now.get('temp_c')
    humi_now = data_now.get('humidity')
    press_now = data_now.get('pressure')
    
    if h not in avg:
        return None  # or handle appropriately
    
    change_temp = (temp_now - avg[h]["avg_temp"]) if temp_now is not None else None
    percent_change_temp = (change_temp / avg[h]["avg_temp"] * 100) if change_temp is not None else None
    
    change_humi = (humi_now - avg[h]["avg_humidity"]) if humi_now is not None else None
    percent_change_humi = (change_humi / avg[h]["avg_humidity"] * 100) if change_humi is not None else None
    
    change_pressure = (press_now - avg[h]["avg_pressure"]) if press_now is not None else None
    percent_change_pressure = (change_pressure / avg[h]["avg_pressure"] * 100) if change_pressure is not None else None
    
    return {
        'temp_change': change_temp,
        'temp_percent_change': percent_change_temp,
        'humidity_change': change_humi,
        'humidity_percent_change': percent_change_humi,
        'pressure_change': change_pressure,
        'pressure_percent_change': percent_change_pressure
    }
    

async def main():
    data = await load_last_30_days_data()
    avg = await get_hourly_average(data)
    logging.info(avg)
    data_now = fetch_data()
    logging.info(data_now)
    changes = calcn_change(data_now, avg)
    logging.info(changes)

asyncio.run(main())
