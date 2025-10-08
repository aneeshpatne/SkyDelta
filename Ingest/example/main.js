import express from "express";

const app = express();

app.use(express.json());

app.post("/insert-into-db", async (req, res) => {
  try {
    const data = req.body;
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return res
        .status(400)
        .json({ success: false, error: "Invalid or missing request body" });
    }
    console.log("Data Saved", data);
    res.json({ success: true });
  } catch (error) {
    console.error("Error saving data:", error);
    res.status(500).json({ success: false, error: "Internal server error" });
  }
});

app.listen(3000, "0.0.0.0", () => {
  console.log("Server Started");
});
