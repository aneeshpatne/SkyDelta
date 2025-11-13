import express from "express";

const app = express();

app.get("/alerts", (req, res) => {
  res.json({ alert: "green" });
});

app.listen(8008, () => {
  console.log("Server Running");
});
