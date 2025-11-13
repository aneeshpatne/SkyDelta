import "dotenv/config";
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

const worker = new Worker(
  "myQueue",
  async (job) => {
    const value = await client.get("changes");
    const Changes = JSON.parse(value);
    const res = await fetch("http://192.168.1.50/sensors_v2");
    const curData = await res.json();
  },
  { connection }
);

worker.on("completed", (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`Job ${job.id} failed`, err);
});
