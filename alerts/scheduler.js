import { Queue, Worker } from "bullmq";

const connection = { host: "127.0.0.1", port: 6379 };

const queue = new Queue("myQueue", { connection });

await queue.add("myTask", {}, { repeat: { cron: "15 7 * * *" } });

console.log("Inital Task Added In queue");

await queue.add("myTask", {}, { repeat: { cron: "0 8-10 * * *" } });

console.log("Concurrent Task Added In queue");

const worker = new Worker(
  "myQueue",
  async (job) => {
    console.log("Job Started Executing");
  },
  { connection }
);

worker.on("completed", (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`Job ${job.id} failed`, err);
});
