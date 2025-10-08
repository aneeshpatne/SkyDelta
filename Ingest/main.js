import { PrismaClient } from "@prisma/client";

let isRunning = false;

async function fetchAndStore() {
  if (isRunning) {
    console.log(
      `[${new Date().toISOString()}] Skipping - previous task still running`
    );
    return;
  }

  isRunning = true;
  const startTime = Date.now();
  const prisma = new PrismaClient();

  try {
    const res = await fetch("http://192.168.1.50/sensors_v2", {
      signal: AbortSignal.timeout(30000),
    });

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

    const duration = Date.now() - startTime;
    console.log(
      `[${new Date().toISOString()}] Inserted (${duration}ms):`,
      record
    );
  } catch (err) {
    const duration = Date.now() - startTime;
    console.error(
      `[${new Date().toISOString()}] Error (${duration}ms):`,
      err.message
    );
  } finally {
    await prisma.$disconnect();
    isRunning = false;
  }
}

fetchAndStore();

const interval = setInterval(fetchAndStore, 60000);

console.log("Weather monitoring started. Will run every 60 seconds.");

process.on("SIGINT", async () => {
  console.log("\nShutting down...");
  clearInterval(interval);

  while (isRunning) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  process.exit(0);
});

process.on("unhandledRejection", (err) => {
  console.error(`[${new Date().toISOString()}] Unhandled rejection:`, err);
});
