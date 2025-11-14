import dotenv from "dotenv";
dotenv.config({ path: "../.env" });
import { Queue, Worker } from "bullmq";
import { createClient } from "redis";
import { openai } from "@ai-sdk/openai";
import { generateObject } from "ai";
import { z } from "zod";

const client = createClient();

client.on("error", (err) => console.error("Redis Client Error", err));

await client.connect();

const connection = { host: "127.0.0.1", port: 6379 };

const queue = new Queue("myQueue", { connection });

await queue.add("myTask", {}, { repeat: { cron: "15 7 * * *" } });

console.log("Inital Task Added In queue");

await queue.add("myTask", {}, { repeat: { cron: "0 8-10 * * *" } });

console.log("Concurrent Task Added In queue");

// await queue.add("myTask", {});

// console.log("ASAP Task Added In queue");

const worker = new Worker(
  "myQueue",
  async (job) => {
    const value = await client.get("changes");
    const changes = JSON.parse(value);
    const res = await fetch("http://192.168.1.50/sensors_v2");
    const curData = await res.json();
    const { object } = await generateObject({
      model: openai("gpt-4.1-mini"),
      schema: z.object({
        alert: z.object({
          color: z.string(),
          remarks: z.string().describe("Can be maximum of 5 words only."),
        }),
      }),
      prompt: `You are a weather monitoring system. Based on the following weather data changes and current sensor readings, determine an appropriate alert color: green (normal conditions), yellow (caution - moderate changes or anomalies), orange (warning - significant changes), or red (danger - extreme conditions).

Changes in the last period:
- Temperature change: ${changes.temp_change}°C (${
        changes.temp_percent_change ? changes.temp_percent_change + "%" : "N/A"
      })
- Humidity change: ${changes.humidity_change}% (${
        changes.humidity_percent_change
          ? changes.humidity_percent_change + "%"
          : "N/A"
      })
- Pressure change: ${changes.pressure_change} hPa (${
        changes.pressure_percent_change
          ? changes.pressure_percent_change + "%"
          : "N/A"
      })

Current sensor data:
- Temperature: ${curData.temp_c}°C
- Humidity: ${curData.humidity_pct}%
- Pressure: ${curData.pressure_hpa} hPa
- Light: ${curData.light_lux} lux

Analyze the changes and current conditions to assess if there's any significant weather event or anomaly that requires attention. Consider rapid changes, extreme values, or unusual patterns as potential alerts. Provide only the color based on your analysis.`,
    });
    console.log(object.alert.color);
    console.log(object.alert.remarks);
    await client.set("alert-color", object.alert.color);
    await client.set("alert-remark", object.alert.remarks);
    await fetch("http://192.168.1.50/alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alert: object.alert.color }),
    });
  },
  { connection }
);

worker.on("completed", (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`Job ${job.id} failed`, err);
});
