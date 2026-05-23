const express = require("express");
const path = require("path");
const { Pool } = require("pg");

const app = express();
const port = Number(process.env.PORT || 3000);

const pool = new Pool({
  host: process.env.PGHOST || "bio-postgres",
  port: Number(process.env.PGPORT || 5432),
  database: process.env.PGDATABASE || "bio",
  user: process.env.PGUSER || "bio",
  password: process.env.PGPASSWORD || "bioanalysis",
  max: 4,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 4000
});

const staticDir = path.join(__dirname, "public");

app.use(express.json());
app.use(express.static(staticDir));

function classifyTable(tableName) {
  const name = tableName.toLowerCase();
  const cancerTerms = [
    "cancer",
    "tcga",
    "gdc",
    "tumor",
    "mutation",
    "variant",
    "clinical",
    "survival",
    "cnv",
    "gene",
    "patient",
    "sample"
  ];
  const chemicalTerms = [
    "chem",
    "drug",
    "compound",
    "molecule",
    "smiles",
    "pubchem",
    "chembl",
    "tox",
    "admet",
    "ligand"
  ];

  if (cancerTerms.some((term) => name.includes(term))) return "cancer";
  if (chemicalTerms.some((term) => name.includes(term))) return "chemical";
  return "analysis";
}

function quoteIdentifier(value) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

async function listTables() {
  const { rows } = await pool.query(`
    SELECT
      table_schema,
      table_name,
      obj_description(format('%I.%I', table_schema, table_name)::regclass) AS description
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE'
      AND table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name
  `);

  return rows.map((row) => ({
    schema: row.table_schema,
    name: row.table_name,
    description: row.description || "",
    category: classifyTable(row.table_name)
  }));
}

async function estimateRows(table) {
  const { rows } = await pool.query(
    `
      SELECT GREATEST(c.reltuples, 0)::bigint AS count
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = $1 AND c.relname = $2
    `,
    [table.schema, table.name]
  );
  return Number(rows[0]?.count || 0);
}

async function getColumns(table) {
  const { rows } = await pool.query(
    `
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_schema = $1 AND table_name = $2
      ORDER BY ordinal_position
    `,
    [table.schema, table.name]
  );
  return rows.map((row) => ({
    name: row.column_name,
    type: row.data_type,
    nullable: row.is_nullable === "YES"
  }));
}

async function buildTableSummary(table) {
  const [rowCount, columns] = await Promise.all([estimateRows(table), getColumns(table)]);
  return {
    ...table,
    rowCount,
    rowCountLabel: "estimated",
    columns,
    columnCount: columns.length
  };
}

app.get("/api/health", async (_req, res) => {
  try {
    const started = Date.now();
    const { rows } = await pool.query(`
      SELECT
        current_database() AS database,
        current_user AS "user",
        inet_server_addr()::text AS host,
        inet_server_port() AS port,
        version() AS version
    `);

    res.json({
      ok: true,
      latencyMs: Date.now() - started,
      postgres: rows[0],
      node: {
        port,
        env: process.env.NODE_ENV || "development"
      }
    });
  } catch (error) {
    res.status(503).json({
      ok: false,
      message: error.message
    });
  }
});

app.get("/api/tables", async (req, res) => {
  try {
    const category = String(req.query.category || "all");
    const tables = await listTables();
    const filtered = category === "all" ? tables : tables.filter((table) => table.category === category);
    const summaries = await Promise.all(filtered.map(buildTableSummary));
    res.json({ tables: summaries });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

app.get("/api/tables/:schema/:name/sample", async (req, res) => {
  try {
    const tables = await listTables();
    const table = tables.find((item) => item.schema === req.params.schema && item.name === req.params.name);
    if (!table) {
      res.status(404).json({ message: "Table not found" });
      return;
    }

    const limit = Math.min(Number(req.query.limit || 25), 100);
    const schema = quoteIdentifier(table.schema);
    const name = quoteIdentifier(table.name);
    const { rows } = await pool.query(`SELECT * FROM ${schema}.${name} LIMIT $1`, [limit]);
    res.json({ table, rows });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

app.get("/api/analysis/overview", async (_req, res) => {
  try {
    const tables = await listTables();
    const summaries = await Promise.all(tables.map(buildTableSummary));
    const totalRows = summaries.reduce((sum, table) => sum + table.rowCount, 0);
    const categories = summaries.reduce(
      (acc, table) => {
        acc[table.category].tables += 1;
        acc[table.category].rows += table.rowCount;
        return acc;
      },
      {
        cancer: { tables: 0, rows: 0 },
        chemical: { tables: 0, rows: 0 },
        analysis: { tables: 0, rows: 0 }
      }
    );

    const widestTables = [...summaries]
      .sort((a, b) => b.columnCount - a.columnCount)
      .slice(0, 5)
      .map(({ schema, name, category, columnCount, rowCount }) => ({
        schema,
        name,
        category,
        columnCount,
        rowCount
      }));

    res.json({
      generatedAt: new Date().toISOString(),
      totalTables: summaries.length,
      totalRows,
      categories,
      widestTables
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

app.get("*", (_req, res) => {
  res.sendFile(path.join(staticDir, "index.html"));
});

app.listen(port, "0.0.0.0", () => {
  console.log(`Cancer data console listening on port ${port}`);
});
