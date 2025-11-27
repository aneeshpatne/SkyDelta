import dotenv from "dotenv";
dotenv.config();

import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function fetchAndStorePollution() {
  try {
    console.log("[SERVER] Server Started");
    console.info("[FETCH] Fetching started");
    const res = await fetch("http://192.168.1.45/api", {
      signal: AbortSignal.timeout(2000),
    });
    const data = await res.json();
    const now = new Date();
    const istTime = new Date(
      now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
    );
    await prisma.pm25.create({
      data: {
        timestamp: istTime,
        "pm2.5": data.pm25,
      },
    });
  } catch (e) {}
}
async function fetchAndStore() {
  try {
    console.info("[SERVER] Server started");
    console.info("[FETCH] Fetching started");
    const res = await fetch("http://192.168.1.50/sensors_v2", {
      signal: AbortSignal.timeout(2000),
    });
    const data = await res.json();

    // Get current time and manually format as IST
    // This prevents Node.js from converting to UTC
    const now = new Date();
    const istTime = new Date(
      now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
    );

    const entry = await prisma.weather_db_v2.create({
      data: {
        temperature: data.temp_c,
        humidity: data.humidity_pct,
        pressure: data.pressure_hpa,
        timestamp: istTime,
      },
    });
    console.info(
      "[FETCH] Data Logged at",
      istTime.toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })
    );
  } catch (e) {
    console.error("[FETCH] Fetching Failed", e);
  }
}

fetchAndStore();
fetchAndStorePollution();
setInterval(() => {
  fetchAndStore();
  console.log("[FETCH] Saved Successfully");
}, 60000);

setInterval(() => {
  fetchAndStorePollution();
  console.log("[FETCH] Saved Pollution Successfully");
}, 5000);
