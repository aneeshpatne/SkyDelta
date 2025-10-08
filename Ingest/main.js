import cron from "node-cron";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function fetchAndStore() {
  try {
    const res = await fetch("http://192.168.1.50/sensors_v2");
    if (!res.ok) {
      throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    if (!data.temp_c || !data.humidity_pct) {
      throw new Error("Missing temperature or humidity data in response");
    }

    const record = await prisma.weather_db.create({
      data: {
        temperature: data.temp_c,
        humidity: data.humidity_pct,
      },
    });

    console.log(`[${new Date().toISOString()}] Inserted:`, record);
  } catch (err) {
    console.error(`[${new Date().toISOString()}] Error:`, err);
  }
}

cron.schedule("* * * * *", () => {
  console.log(`[${new Date().toISOString()}] Running scheduled task...`);
  fetchAndStore();
});

fetchAndStore();

console.log("Weather monitoring started. Will run every minute.");

process.on("SIGINT", async () => {
  console.log("\nShutting down...");
  await prisma.$disconnect();
  process.exit(0);
});
