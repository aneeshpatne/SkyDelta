-- CreateTable
CREATE TABLE "weather_db_v2" (
    "id" TEXT NOT NULL,
    "timestamp" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "temperature" DOUBLE PRECISION NOT NULL,
    "humidity" DOUBLE PRECISION NOT NULL,
    "pressure" DOUBLE PRECISION NOT NULL,

    CONSTRAINT "weather_db_v2_pkey" PRIMARY KEY ("id")
);
