import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();
async function fetchAndStore() {
  try {
    console.info("[SERVER] Server started");
    console.info("[FETCH] Fetching started");
    const res = await fetch("http://192.168.1.50/sensors_v2", {
      signal: AbortSignal.timeout(2000),
    });
    const data = await res.json();
    const entry = await prisma.weather_db.create({
      data: {
        temperature: data.temp_c,
        humidity: data.humidity_pct,
      },
    });
    console.info("[FETCH] Data Logged");
  } catch (e) {
    console.error("[FETCH] Fetching Failed", e);
  }
}

fetchAndStore();

setInterval(() => {
  fetchAndStore();
  console.log("[FETCH] Saved Successfully");
}, 60000);
