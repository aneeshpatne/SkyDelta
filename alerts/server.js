import express from "express";
import cors from "cors";
import redis from "redis";
import { PrismaClient } from "@prisma/client";

const app = express();
app.use(cors());
const client = redis.createClient();
const prisma = new PrismaClient();

client.connect();

app.get("/alerts", async (req, res) => {
  const color = await client.get("alert-color");
  res.json({ alert: color || "green" });
});

app.get("/alerts/remark", async (req, res) => {
  const remark = await client.get("alert-remark");
  res.json({ remark: remark || "All systems operational" });
});

app.get("/pm25/avg", async (req, res) => {
  try {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);

    const result = await prisma.pm25.aggregate({
      _avg: {
        pm25: true,
      },
      where: {
        timestamp: {
          gt: fiveMinutesAgo,
        },
      },
    });

    res.json({ avg_pm25: result._avg.pm25 || 0 });
  } catch (error) {
    console.error("Error fetching PM2.5 average:", error);
    res.status(500).json({ error: "Failed to fetch PM2.5 average" });
  }
});

app.listen(8008, () => {
  console.log("Server Running");
});
