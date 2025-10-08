from prisma import Prisma
import asyncio


db = Prisma()


async def main():
    await db.connect()
    rows = await db.weather_db.find_many()
    for row in rows:
        print(row.id, row.temperature, row.humidity, row.timestamp)
    await db.disconnect()

asyncio.run(main())