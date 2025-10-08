import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function main() {
  const record = await prisma.weather_db.create({
    data: {
      temperature: 27.8,
      humidity: 61.2,
    },
  });

  console.log("Inserted:", record);
}

main()
  .catch((e) => console.error(e))
  .finally(async () => await prisma.$disconnect());
