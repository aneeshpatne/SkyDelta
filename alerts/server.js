import dotenv from "dotenv";
dotenv.config();

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

    res.json({ avg_pm25: result._avg.pm25 ? parseFloat(result._avg.pm25.toFixed(2)) : 0 });
  } catch (error) {
    console.error("Error fetching PM2.5 average:", error);
    res.status(500).json({ error: "Failed to fetch PM2.5 average" });
  }
});

app.get("/pm25/avg/15min", async (req, res) => {
  try {
    const fifteenMinutesAgo = new Date(Date.now() - 15 * 60 * 1000);

    const result = await prisma.pm25.aggregate({
      _avg: {
        pm25: true,
      },
      where: {
        timestamp: {
          gt: fifteenMinutesAgo,
        },
      },
    });

    res.json({ avg_pm25: result._avg.pm25 || 0 });
  } catch (error) {
    console.error("Error fetching PM2.5 15-min average:", error);
    res.status(500).json({ error: "Failed to fetch PM2.5 15-min average" });
  }
});

app.get("/aqi/alert", async (req, res) => {
  const color = await client.get("aqi-alert-color");
  const remark = await client.get("aqi-alert-remark");
  res.json({
    color: color || "green",
    remark: remark || "Air quality normal",
  });
});

app.listen(8008, () => {
  console.log("Server Running");
});
