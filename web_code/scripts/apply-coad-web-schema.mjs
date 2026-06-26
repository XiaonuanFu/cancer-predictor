import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";

const { Pool } = pg;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sqlPath = path.join(__dirname, "..", "db", "coad_web_schema.sql");

function databaseConfig() {
  if (process.env.DATABASE_URL) {
    return { connectionString: process.env.DATABASE_URL };
  }

  return {
    host: process.env.PGHOST || "bio-postgres",
    port: Number(process.env.PGPORT || 5432),
    database: process.env.PGDATABASE || "bio",
    user: process.env.PGUSER || "bio",
    password: process.env.PGPASSWORD
  };
}

async function main() {
  const sql = await readFile(sqlPath, "utf8");
  const pool = new Pool(databaseConfig());
  const started = Date.now();

  try {
    console.log("Building compact coad_web schema...");
    await pool.query(sql);
    console.log(`coad_web schema refreshed in ${((Date.now() - started) / 1000).toFixed(1)}s.`);
  } finally {
    await pool.end();
  }
}

main().catch((error) => {
  console.error("Unable to build coad_web schema.");
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
