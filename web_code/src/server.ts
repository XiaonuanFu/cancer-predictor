import express, { type Request, type Response } from "express";
import { readFile } from "node:fs/promises";
import path from "node:path";

interface HealthResponse {
  ok: true;
  mode: "read-only";
  app: string;
  generatedAt: string;
}

interface ContactResponse {
  mode: "mailto";
  email: string;
  message: string;
}

interface ErrorResponse {
  message: string;
  detail?: string;
}

interface ProjectSummary {
  name: string;
  shortName: string;
  description: string;
  disclaimer: string;
  contactEmail: string;
}

interface DatasetSummaryItem {
  key: string;
  label: string;
  title: string;
  description: string;
  plainDefinition: string;
  sampleCount?: number;
  featureCount?: number;
  note: string;
}

interface SiteData {
  project: ProjectSummary;
  datasetSummary: DatasetSummaryItem[];
  workflowSteps: unknown[];
  model: Record<string, unknown>;
  proteins: unknown[];
  mutationTargets: unknown[];
  compounds: unknown[];
  glossary: unknown[];
  references: unknown[];
}

const app = express();
const port = Number(process.env.PORT || 3000);
const staticDir = path.join(__dirname, "..", "public");
const siteDataPath = path.join(staticDir, "data", "coad-project-data.json");

app.use(express.json({ limit: "16kb" }));
app.use(express.static(staticDir));

async function readSiteData(): Promise<SiteData> {
  const raw = await readFile(siteDataPath, "utf8");
  return JSON.parse(raw) as SiteData;
}

function errorDetail(error: unknown): string | undefined {
  if (process.env.NODE_ENV === "production") return undefined;
  return error instanceof Error ? error.message : String(error);
}

app.get("/api/health", (_req: Request, res: Response<HealthResponse>) => {
  res.json({
    ok: true,
    mode: "read-only",
    app: "COAD Cancer Predictor",
    generatedAt: new Date().toISOString()
  });
});

app.get("/api/site-data", async (_req: Request, res: Response<SiteData | ErrorResponse>) => {
  try {
    const siteData = await readSiteData();
    res.json(siteData);
  } catch (error) {
    res.status(500).json({
      message: "Unable to load curated website data.",
      detail: errorDetail(error)
    });
  }
});

app.get("/api/contact", (_req: Request, res: Response<ContactResponse>) => {
  const email = process.env.CONTACT_EMAIL || "contact@example.com";
  res.json({
    mode: "mailto",
    email,
    message: "The v1 contact flow opens the visitor's email app. No message is stored by this website."
  });
});

app.all(["/api/tables", "/api/tables/*", "/api/analysis/overview"], (_req: Request, res: Response<ErrorResponse>) => {
  res.status(410).json({
    message: "Raw database browsing is disabled. This website exposes only curated read-only project summaries."
  });
});

app.get("*", (_req: Request, res: Response) => {
  res.sendFile(path.join(staticDir, "index.html"));
});

app.listen(port, "0.0.0.0", () => {
  console.log(`COAD Cancer Predictor listening on port ${port}`);
});
