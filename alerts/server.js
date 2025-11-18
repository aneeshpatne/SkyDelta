import express from "express";
import cors from "cors";
import redis from "redis";

const app = express();
app.use(cors());
const client = redis.createClient();

client.connect();

app.get("/alerts", async (req, res) => {
  const color = await client.get("alert-color");
  res.json({ alert: color || "green" });
});

app.get("/alerts/remark", async (req, res) => {
  const remark = await client.get("alert-remark");
  res.json({ remark: remark || "All systems operational" });
});

app.listen(8008, () => {
  console.log("Server Running");
});
