from prisma import Prisma
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from parent directory's .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

db = Prisma()


async def main():
    await db.connect()
    rows = await db.weather_db.find_many()
    for row in rows:
        print(row.id, row.temperature, row.humidity, row.timestamp)
    await db.disconnect()

asyncio.run(main())