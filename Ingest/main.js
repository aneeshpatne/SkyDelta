import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const res = await fetch("http://192.168.1.50/sensors_v2");

const data = await res.json();

const record = await prisma.weather_db.create({
  data: {
    temperature: data.temp_c,
    humidity: humidity_pct,
  },
});

console.log("Inserted:", record);
