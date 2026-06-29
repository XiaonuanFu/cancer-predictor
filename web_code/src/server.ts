import express, { type NextFunction, type Request, type Response } from "express";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { Pool, type QueryResultRow } from "pg";

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

interface MutationGeneResponse {
  geneSymbol: string;
  mutationRecords: number;
  mutatedSampleCount: number;
  mutatedSamplePercent: number;
  topVariantClassification: string | null;
  displayOrder: number;
}

interface MutationGeneDetailResponse extends MutationGeneResponse {
  protein: {
    proteinName: string;
    uniprotId: string;
    alphafoldUrl: string;
    proteinLength: number | null;
    projectReason: string;
    structureNote: string;
  } | null;
}

interface MutationHotspotResponse {
  geneSymbol: string;
  proteinChange: string;
  aminoAcidPosition: number | null;
  aminoAcids: string | null;
  mutationLabel: string;
  sampleCount: number;
  mutationRecords: number;
  variantClassification: string | null;
  cbioportalMutationMapperUrl: string;
  displayOrder: number;
}

interface MutationTypeResponse {
  variantClassification: string;
  mutationRecords: number;
  mutatedSampleCount: number;
  affectedGeneCount: number;
  displayOrder: number;
}

interface MutationDetailResponse {
  mutationDetailId: number;
  geneSymbol: string;
  proteinChange: string;
  aminoAcidPosition: number | null;
  aminoAcids: string | null;
  variantClassification: string;
  mutatedSampleCount: number;
  mutationRecords: number;
  protein: {
    proteinName: string;
    uniprotId: string;
    alphafoldUrl: string;
    proteinLength: number | null;
    structureNote: string;
  } | null;
}

interface MutationDetailPageResponse {
  items: MutationDetailResponse[];
  totalRows: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

interface DrugListResponse {
  drugSlug: string;
  drugName: string;
  nciDrugUrl: string;
  nciCancerType: string;
  evidenceLabel: string;
  compoundName: string | null;
  chemblId: string | null;
  molecularFormula: string | null;
  moleculeType: string | null;
  sourceName: string;
  sourceUrl: string;
}

interface DrugDetailResponse extends DrugListResponse {
  canonicalSmiles: string | null;
  standardInchiKey: string | null;
  maxPhase: number | null;
  structureImageUrlOrSvg: string | null;
  chemblSourceNote: string | null;
  indications: Array<{
    indicationText: string | null;
    meshHeading: string | null;
    efoTerm: string | null;
  }>;
}

interface AlphaFoldPrediction {
  entryId?: string;
  pdbUrl?: string;
  latestVersion?: number;
}

interface CachedProteinStructure {
  data: Buffer;
  sourceUrl: string;
  fetchedAt: number;
  contentType: string;
  structureFormat: "pdb" | "bcif";
  entryId: string;
  fragmentStart?: number;
  fragmentEnd?: number;
  selectedResidueLocal?: number;
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

interface CoadDataMetric {
  label: string;
  value: number | string;
  note: string;
}

interface CoadDataChart {
  id: string;
  type: string;
  title: string;
  takeaway: string;
  xLabel?: string;
  yLabel?: string;
  data?: unknown[];
  categories?: string[];
  series?: unknown[];
  imageSrc?: string;
  imageAlt?: string;
}

interface CoadDataSection {
  key: string;
  label: string;
  title: string;
  sourceReport: string;
  notebookUrl: string;
  summary: string;
  plainDefinition: string;
  metrics: CoadDataMetric[];
  charts: CoadDataChart[];
}

interface SiteData {
  project: ProjectSummary;
  datasetSummary: DatasetSummaryItem[];
  coadDataPage: {
    sections: CoadDataSection[];
  };
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
const nglBundlePath = path.join(__dirname, "..", "node_modules", "ngl", "dist", "ngl.js");
const proteinStructureCache = new Map<string, CachedProteinStructure>();
const proteinStructureCacheLifetimeMs = 24 * 60 * 60 * 1000;
let pool: Pool | null = null;

app.use(express.json({ limit: "16kb" }));
app.get("/vendor/ngl.js", (_req: Request, res: Response, next: NextFunction) => {
  res.sendFile(nglBundlePath, (error) => {
    if (error) next(error);
  });
});
app.use(express.static(staticDir));

async function readSiteData(): Promise<SiteData> {
  const raw = await readFile(siteDataPath, "utf8");
  return JSON.parse(raw) as SiteData;
}

function errorDetail(error: unknown): string | undefined {
  if (process.env.NODE_ENV === "production") return undefined;
  return error instanceof Error ? error.message : String(error);
}

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

function getPool(): Pool {
  if (!pool) {
    pool = new Pool(databaseConfig());
  }
  return pool;
}

async function queryRows<T extends QueryResultRow>(sql: string, params: unknown[] = []): Promise<T[]> {
  const result = await getPool().query<T>(sql, params);
  return result.rows;
}

function numeric(value: unknown): number {
  return Number(value ?? 0);
}

function nullableNumeric(value: unknown): number | null {
  return value === null || value === undefined ? null : Number(value);
}

function normalizeGeneSymbol(value: string): string | null {
  const geneSymbol = value.trim().toUpperCase();
  return /^[A-Z0-9_.-]{1,40}$/.test(geneSymbol) ? geneSymbol : null;
}

function normalizeChemblId(value: string): string | null {
  const chemblId = value.trim().toUpperCase();
  return /^CHEMBL[0-9]+$/.test(chemblId) ? chemblId : null;
}

function normalizeUniprotId(value: string): string | null {
  const uniprotId = value.trim().toUpperCase();
  return /^[A-Z0-9]{6,10}$/.test(uniprotId) ? uniprotId : null;
}

function requestedProteinPosition(req: Request): number | null {
  const raw = typeof req.query.position === "string" ? Number(req.query.position) : NaN;
  if (!Number.isFinite(raw)) return null;
  const position = Math.trunc(raw);
  return position > 0 && position < 100000 ? position : null;
}

function rcsbAlphaFoldId(uniprotId: string, position: number | null): {
  entryId: string;
  fragmentStart: number;
  fragmentEnd: number;
  selectedResidueLocal: number | null;
} {
  const fragmentIndex = position ? Math.max(Math.floor((position - 1) / 200) + 1, 1) : 1;
  const fragmentStart = (fragmentIndex - 1) * 200 + 1;
  const fragmentEnd = fragmentStart + 1399;
  return {
    entryId: `AF_AF${uniprotId}F${fragmentIndex}`,
    fragmentStart,
    fragmentEnd,
    selectedResidueLocal: position ? position - fragmentStart + 1 : null
  };
}

function setStructureHeaders(res: Response, cached: CachedProteinStructure) {
  res.set({
    "Cache-Control": "public, max-age=86400",
    "Content-Type": cached.contentType,
    "X-Structure-Format": cached.structureFormat,
    "X-Structure-Entry": cached.entryId,
    "X-Structure-Source": cached.sourceUrl
  });
  if (cached.fragmentStart) res.set("X-Fragment-Start", String(cached.fragmentStart));
  if (cached.fragmentEnd) res.set("X-Fragment-End", String(cached.fragmentEnd));
  if (cached.selectedResidueLocal) res.set("X-Selected-Residue-Local", String(cached.selectedResidueLocal));
}

function sendDatabaseError(res: Response<ErrorResponse>, error: unknown, message = "Unable to load mutation analysis data.") {
  res.status(503).json({
    message,
    detail: errorDetail(error)
  });
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
  const email = process.env.CONTACT_EMAIL || "nancy.fu.2027@this.edu.cn";
  res.json({
    mode: "mailto",
    email,
    message: "The v1 contact flow opens the visitor's email app. No message is stored by this website."
  });
});

app.get("/api/mutation-analysis/genes", async (_req: Request, res: Response<MutationGeneResponse[] | ErrorResponse>) => {
  try {
    const rows = await queryRows<{
      gene_symbol: string;
      mutation_records: number;
      mutated_sample_count: number;
      mutated_sample_percent: string;
      top_variant_classification: string | null;
      display_order: number;
    }>(`
      SELECT
        gene_symbol,
        mutation_records,
        mutated_sample_count,
        mutated_sample_percent,
        top_variant_classification,
        display_order
      FROM coad_web.mutation_gene_frequencies
      ORDER BY display_order, mutated_sample_count DESC
    `);

    res.json(rows.map((row) => ({
      geneSymbol: row.gene_symbol,
      mutationRecords: numeric(row.mutation_records),
      mutatedSampleCount: numeric(row.mutated_sample_count),
      mutatedSamplePercent: numeric(row.mutated_sample_percent),
      topVariantClassification: row.top_variant_classification,
      displayOrder: numeric(row.display_order)
    })));
  } catch (error) {
    sendDatabaseError(res, error);
  }
});

app.get("/api/mutation-analysis/mutation-types", async (_req: Request, res: Response<MutationTypeResponse[] | ErrorResponse>) => {
  try {
    const rows = await queryRows<{
      variant_classification: string;
      mutation_records: number;
      mutated_sample_count: number;
      affected_gene_count: number;
      display_order: number;
    }>(`
      SELECT
        variant_classification,
        mutation_records,
        mutated_sample_count,
        affected_gene_count,
        display_order
      FROM coad_web.mutation_type_frequencies
      ORDER BY display_order
    `);

    res.json(rows.map((row) => ({
      variantClassification: row.variant_classification,
      mutationRecords: numeric(row.mutation_records),
      mutatedSampleCount: numeric(row.mutated_sample_count),
      affectedGeneCount: numeric(row.affected_gene_count),
      displayOrder: numeric(row.display_order)
    })));
  } catch (error) {
    sendDatabaseError(res, error, "Unable to load mutation type summary.");
  }
});

app.get("/api/mutation-analysis/mutations", async (req: Request, res: Response<MutationDetailPageResponse | ErrorResponse>) => {
  const geneValue = typeof req.query.geneSymbol === "string" ? req.query.geneSymbol : "";
  const geneSymbol = geneValue ? normalizeGeneSymbol(geneValue) : null;
  if (geneValue && !geneSymbol) {
    res.status(400).json({ message: "Invalid gene symbol." });
    return;
  }

  const variantClassification = typeof req.query.variantClassification === "string"
    ? req.query.variantClassification.trim()
    : "";
  if (variantClassification.length > 100) {
    res.status(400).json({ message: "Invalid mutation type." });
    return;
  }

  const requestedPage = Number(req.query.page || 1);
  const page = Number.isFinite(requestedPage) ? Math.max(Math.trunc(requestedPage), 1) : 1;
  const requestedPageSize = Number(req.query.pageSize || 50);
  const pageSize = Number.isFinite(requestedPageSize)
    ? Math.min(Math.max(Math.trunc(requestedPageSize), 10), 500)
    : 50;
  const offset = (page - 1) * pageSize;

  try {
    const countRows = await queryRows<{ total_rows: number }>(`
      SELECT COUNT(*)::int AS total_rows
      FROM coad_web.mutation_details d
      WHERE ($1::text IS NULL OR d.gene_symbol = $1)
        AND ($2::text IS NULL OR d.variant_classification = $2)
    `, [geneSymbol, variantClassification || null]);
    const totalRows = countRows.length ? numeric(countRows[0].total_rows) : 0;
    const totalPages = Math.max(Math.ceil(totalRows / pageSize), 1);
    const currentPage = Math.min(page, totalPages);
    const currentOffset = (currentPage - 1) * pageSize;

    const rows = await queryRows<{
      mutation_detail_id: number;
      gene_symbol: string;
      protein_change: string;
      amino_acid_position: number | null;
      amino_acids: string | null;
      variant_classification: string;
      mutated_sample_count: number;
      mutation_records: number;
      protein_name: string | null;
      uniprot_id: string | null;
      alphafold_url: string | null;
      protein_length: number | null;
      structure_note: string | null;
    }>(`
      SELECT
        d.mutation_detail_id,
        d.gene_symbol,
        d.protein_change,
        d.amino_acid_position,
        d.amino_acids,
        d.variant_classification,
        d.mutated_sample_count,
        d.mutation_records,
        p.protein_name,
        p.uniprot_id,
        p.alphafold_url,
        p.protein_length,
        p.structure_note
      FROM coad_web.mutation_details d
      LEFT JOIN coad_web.protein_structure_targets p
        ON p.gene_symbol = d.gene_symbol
      WHERE ($1::text IS NULL OR d.gene_symbol = $1)
        AND ($2::text IS NULL OR d.variant_classification = $2)
      ORDER BY d.mutated_sample_count DESC, d.mutation_records DESC, d.display_order
      LIMIT $3
      OFFSET $4
    `, [geneSymbol, variantClassification || null, pageSize, currentOffset]);

    res.json({
      items: rows.map((row) => ({
      mutationDetailId: numeric(row.mutation_detail_id),
      geneSymbol: row.gene_symbol,
      proteinChange: row.protein_change,
      aminoAcidPosition: nullableNumeric(row.amino_acid_position),
      aminoAcids: row.amino_acids,
      variantClassification: row.variant_classification,
      mutatedSampleCount: numeric(row.mutated_sample_count),
      mutationRecords: numeric(row.mutation_records),
      protein: row.protein_name && row.uniprot_id && row.alphafold_url ? {
        proteinName: row.protein_name,
        uniprotId: row.uniprot_id,
        alphafoldUrl: row.alphafold_url,
        proteinLength: nullableNumeric(row.protein_length),
        structureNote: row.structure_note || ""
      } : null
      })),
      totalRows,
      page: currentPage,
      pageSize,
      totalPages
    });
  } catch (error) {
    sendDatabaseError(res, error, "Unable to load mutation table.");
  }
});

app.get("/api/mutation-analysis/genes/:geneSymbol", async (req: Request, res: Response<MutationGeneDetailResponse | ErrorResponse>) => {
  const geneSymbol = normalizeGeneSymbol(String(req.params.geneSymbol));
  if (!geneSymbol) {
    res.status(400).json({ message: "Invalid gene symbol." });
    return;
  }

  try {
    const rows = await queryRows<{
      gene_symbol: string;
      mutation_records: number;
      mutated_sample_count: number;
      mutated_sample_percent: string;
      top_variant_classification: string | null;
      display_order: number;
      protein_name: string | null;
      uniprot_id: string | null;
      alphafold_url: string | null;
      protein_length: number | null;
      project_reason: string | null;
      structure_note: string | null;
    }>(`
      SELECT
        g.gene_symbol,
        g.mutation_records,
        g.mutated_sample_count,
        g.mutated_sample_percent,
        g.top_variant_classification,
        g.display_order,
        p.protein_name,
        p.uniprot_id,
        p.alphafold_url,
        p.protein_length,
        p.project_reason,
        p.structure_note
      FROM coad_web.mutation_gene_frequencies g
      LEFT JOIN coad_web.protein_structure_targets p
        ON p.gene_symbol = g.gene_symbol
      WHERE g.gene_symbol = $1
    `, [geneSymbol]);

    const row = rows[0];
    if (!row) {
      res.status(404).json({ message: "Gene not found in coad_web mutation summary." });
      return;
    }

    res.json({
      geneSymbol: row.gene_symbol,
      mutationRecords: numeric(row.mutation_records),
      mutatedSampleCount: numeric(row.mutated_sample_count),
      mutatedSamplePercent: numeric(row.mutated_sample_percent),
      topVariantClassification: row.top_variant_classification,
      displayOrder: numeric(row.display_order),
      protein: row.protein_name && row.uniprot_id && row.alphafold_url ? {
        proteinName: row.protein_name,
        uniprotId: row.uniprot_id,
        alphafoldUrl: row.alphafold_url,
        proteinLength: nullableNumeric(row.protein_length),
        projectReason: row.project_reason || "",
        structureNote: row.structure_note || ""
      } : null
    });
  } catch (error) {
    sendDatabaseError(res, error);
  }
});

app.get("/api/mutation-analysis/genes/:geneSymbol/hotspots", async (req: Request, res: Response<MutationHotspotResponse[] | ErrorResponse>) => {
  const geneSymbol = normalizeGeneSymbol(String(req.params.geneSymbol));
  if (!geneSymbol) {
    res.status(400).json({ message: "Invalid gene symbol." });
    return;
  }

  try {
    const rows = await queryRows<{
      gene_symbol: string;
      protein_change: string;
      amino_acid_position: number | null;
      amino_acids: string | null;
      mutation_label: string;
      sample_count: number;
      mutation_records: number;
      variant_classification: string | null;
      cbioportal_mutation_mapper_url: string;
      display_order: number;
    }>(`
      SELECT
        gene_symbol,
        protein_change,
        amino_acid_position,
        amino_acids,
        mutation_label,
        sample_count,
        mutation_records,
        variant_classification,
        cbioportal_mutation_mapper_url,
        display_order
      FROM coad_web.mutation_hotspots
      WHERE gene_symbol = $1
      ORDER BY display_order, sample_count DESC
    `, [geneSymbol]);

    res.json(rows.map((row) => ({
      geneSymbol: row.gene_symbol,
      proteinChange: row.protein_change,
      aminoAcidPosition: nullableNumeric(row.amino_acid_position),
      aminoAcids: row.amino_acids,
      mutationLabel: row.mutation_label,
      sampleCount: numeric(row.sample_count),
      mutationRecords: numeric(row.mutation_records),
      variantClassification: row.variant_classification,
      cbioportalMutationMapperUrl: row.cbioportal_mutation_mapper_url,
      displayOrder: numeric(row.display_order)
    })));
  } catch (error) {
    sendDatabaseError(res, error);
  }
});

app.get("/api/mutation-analysis/genes/:geneSymbol/mutations", async (req: Request, res: Response<MutationHotspotResponse[] | ErrorResponse>) => {
  const geneSymbol = normalizeGeneSymbol(String(req.params.geneSymbol));
  if (!geneSymbol) {
    res.status(400).json({ message: "Invalid gene symbol." });
    return;
  }

  try {
    const rows = await queryRows<{
      gene_symbol: string;
      protein_change: string;
      amino_acid_position: number | null;
      amino_acids: string | null;
      variant_classification: string;
      mutated_sample_count: number;
      mutation_records: number;
      display_order: number;
    }>(`
      SELECT
        gene_symbol,
        protein_change,
        amino_acid_position,
        amino_acids,
        variant_classification,
        mutated_sample_count,
        mutation_records,
        display_order
      FROM coad_web.mutation_details
      WHERE gene_symbol = $1
      ORDER BY amino_acid_position NULLS LAST, mutated_sample_count DESC, mutation_records DESC, display_order
    `, [geneSymbol]);

    res.json(rows.map((row) => ({
      geneSymbol: row.gene_symbol,
      proteinChange: row.protein_change,
      aminoAcidPosition: nullableNumeric(row.amino_acid_position),
      aminoAcids: row.amino_acids,
      mutationLabel: row.variant_classification,
      sampleCount: numeric(row.mutated_sample_count),
      mutationRecords: numeric(row.mutation_records),
      variantClassification: row.variant_classification,
      cbioportalMutationMapperUrl: `https://www.cbioportal.org/mutation_mapper?standaloneMutationMapperGeneTab=${encodeURIComponent(row.gene_symbol)}`,
      displayOrder: numeric(row.display_order)
    })));
  } catch (error) {
    sendDatabaseError(res, error, "Unable to load all mutation locations.");
  }
});

app.get("/api/mutation-analysis/proteins/:uniprotId/structure", async (req: Request, res: Response<Buffer | ErrorResponse>) => {
  const uniprotId = normalizeUniprotId(String(req.params.uniprotId));
  if (!uniprotId) {
    res.status(400).json({ message: "Invalid UniProt ID." });
    return;
  }

  try {
    const targets = await queryRows<{ uniprot_id: string }>(`
      SELECT uniprot_id
      FROM coad_web.protein_structure_targets
      WHERE uniprot_id = $1
    `, [uniprotId]);

    if (!targets[0]) {
      res.status(404).json({ message: "Protein structure target not found in coad_web." });
      return;
    }

    const proteinPosition = requestedProteinPosition(req);
    const fragment = rcsbAlphaFoldId(uniprotId, proteinPosition);
    const cacheKey = proteinPosition ? `${uniprotId}:${fragment.entryId}` : uniprotId;
    const cached = proteinStructureCache.get(cacheKey);
    if (cached && Date.now() - cached.fetchedAt < proteinStructureCacheLifetimeMs) {
      setStructureHeaders(res, cached);
      res.send(cached.data);
      return;
    }

    const rcsbUrl = `https://models.rcsb.org/${encodeURIComponent(fragment.entryId)}.bcif`;
    const rcsbResponse = await fetch(rcsbUrl, {
      headers: {
        Accept: "application/octet-stream",
        "User-Agent": "COAD-Cancer-Predictor/0.1 (research structure fragment viewer)"
      },
      signal: AbortSignal.timeout(15000)
    });

    if (rcsbResponse.ok) {
      const data = Buffer.from(await rcsbResponse.arrayBuffer());
      if (!data.length || data.length > 40 * 1024 * 1024) {
        throw new Error("RCSB computed structure fragment was empty or exceeded the allowed size.");
      }
      const record: CachedProteinStructure = {
        data,
        sourceUrl: rcsbUrl,
        fetchedAt: Date.now(),
        contentType: "application/octet-stream",
        structureFormat: "bcif",
        entryId: fragment.entryId,
        fragmentStart: fragment.fragmentStart,
        fragmentEnd: fragment.fragmentEnd,
        selectedResidueLocal: fragment.selectedResidueLocal || undefined
      };
      proteinStructureCache.set(cacheKey, record);
      setStructureHeaders(res, record);
      res.send(data);
      return;
    }

    const predictionResponse = await fetch(`https://alphafold.ebi.ac.uk/api/prediction/${encodeURIComponent(uniprotId)}`, {
      headers: {
        Accept: "application/json",
        "User-Agent": "COAD-Cancer-Predictor/0.1 (research structure viewer)"
      },
      signal: AbortSignal.timeout(15000)
    });
    if (predictionResponse.status === 404) {
      res.status(404).json({ message: "No RCSB fragment or AlphaFold structure is currently available for this protein position." });
      return;
    }
    if (!predictionResponse.ok) {
      throw new Error(`AlphaFold prediction lookup returned ${predictionResponse.status}.`);
    }

    const predictions = await predictionResponse.json() as AlphaFoldPrediction[];
    const prediction = predictions.find((item) => item.pdbUrl);
    if (!prediction?.pdbUrl) {
      res.status(404).json({ message: "AlphaFold structure is not available for this protein." });
      return;
    }

    const structureResponse = await fetch(prediction.pdbUrl, {
      headers: {
        Accept: "chemical/x-pdb,text/plain",
        "User-Agent": "COAD-Cancer-Predictor/0.1 (research structure viewer)"
      },
      signal: AbortSignal.timeout(30000)
    });
    if (!structureResponse.ok) {
      throw new Error(`AlphaFold structure download returned ${structureResponse.status}.`);
    }

    const data = Buffer.from(await structureResponse.arrayBuffer());
    if (!data.length || data.length > 30 * 1024 * 1024) {
      throw new Error("AlphaFold structure file was empty or exceeded the allowed size.");
    }

    proteinStructureCache.set(cacheKey, {
      data,
      sourceUrl: prediction.pdbUrl,
      fetchedAt: Date.now(),
      contentType: "chemical/x-pdb",
      structureFormat: "pdb",
      entryId: prediction.entryId || uniprotId
    });

    res.set({
      "Cache-Control": "public, max-age=86400",
      "Content-Type": "chemical/x-pdb",
      "X-Structure-Format": "pdb",
      "X-Structure-Entry": prediction.entryId || uniprotId,
      "X-Structure-Source": prediction.pdbUrl,
      "X-AlphaFold-Entry": prediction.entryId || uniprotId,
      "X-AlphaFold-Version": String(prediction.latestVersion || ""),
      "X-AlphaFold-Source": prediction.pdbUrl
    });
    res.send(data);
  } catch (error) {
    res.status(502).json({
      message: "Unable to load the AlphaFold protein structure.",
      detail: errorDetail(error)
    });
  }
});

app.get("/api/mutation-analysis/drugs", async (_req: Request, res: Response<DrugListResponse[] | ErrorResponse>) => {
  try {
    const rows = await queryRows<{
      drug_slug: string;
      drug_name: string;
      nci_drug_url: string;
      nci_cancer_type: string;
      evidence_label: string;
      compound_name: string | null;
      chembl_id: string | null;
      molecular_formula: string | null;
      molecule_type: string | null;
      source_name: string;
      source_url: string;
      display_order: number;
    }>(`
      SELECT
        d.drug_slug,
        d.drug_name,
        d.nci_drug_url,
        d.nci_cancer_type,
        d.evidence_label,
        c.compound_name,
        c.chembl_id,
        c.molecular_formula,
        c.molecule_type,
        s.source_name,
        s.source_url,
        d.display_order
      FROM coad_web.coad_treatment_drugs d
      JOIN coad_web.coad_drug_sources s
        ON s.source_key = d.source_key
      LEFT JOIN coad_web.coad_drug_compounds c
        ON c.drug_slug = d.drug_slug
      ORDER BY d.display_order, c.compound_name NULLS LAST
    `);

    res.json(rows.map((row) => ({
      drugSlug: row.drug_slug,
      drugName: row.drug_name,
      nciDrugUrl: row.nci_drug_url,
      nciCancerType: row.nci_cancer_type,
      evidenceLabel: row.evidence_label,
      compoundName: row.compound_name,
      chemblId: row.chembl_id,
      molecularFormula: row.molecular_formula,
      moleculeType: row.molecule_type,
      sourceName: row.source_name,
      sourceUrl: row.source_url
    })));
  } catch (error) {
    sendDatabaseError(res, error);
  }
});

app.get("/api/mutation-analysis/drugs/:chemblId", async (req: Request, res: Response<DrugDetailResponse | ErrorResponse>) => {
  const chemblId = normalizeChemblId(String(req.params.chemblId));
  if (!chemblId) {
    res.status(400).json({ message: "Invalid ChEMBL ID." });
    return;
  }

  try {
    const rows = await queryRows<{
      drug_slug: string;
      drug_name: string;
      nci_drug_url: string;
      nci_cancer_type: string;
      evidence_label: string;
      compound_name: string;
      chembl_id: string;
      molecular_formula: string | null;
      molecule_type: string | null;
      canonical_smiles: string | null;
      standard_inchi_key: string | null;
      max_phase: string | null;
      structure_image_url_or_svg: string | null;
      chembl_source_note: string | null;
      source_name: string;
      source_url: string;
    }>(`
      SELECT
        d.drug_slug,
        d.drug_name,
        d.nci_drug_url,
        d.nci_cancer_type,
        d.evidence_label,
        c.compound_name,
        c.chembl_id,
        c.molecular_formula,
        c.molecule_type,
        c.canonical_smiles,
        c.standard_inchi_key,
        c.max_phase,
        c.structure_image_url_or_svg,
        c.chembl_source_note,
        s.source_name,
        s.source_url
      FROM coad_web.coad_drug_compounds c
      JOIN coad_web.coad_treatment_drugs d
        ON d.drug_slug = c.drug_slug
      JOIN coad_web.coad_drug_sources s
        ON s.source_key = d.source_key
      WHERE c.chembl_id = $1
      ORDER BY d.display_order
      LIMIT 1
    `, [chemblId]);

    const row = rows[0];
    if (!row) {
      res.status(404).json({ message: "Compound not found in coad_web." });
      return;
    }

    const indications = await queryRows<{
      indication_text: string | null;
      mesh_heading: string | null;
      efo_term: string | null;
    }>(`
      SELECT indication_text, mesh_heading, efo_term
      FROM coad_web.coad_drug_indications
      WHERE chembl_id = $1
      ORDER BY mesh_heading NULLS LAST, efo_term NULLS LAST
      LIMIT 12
    `, [chemblId]);

    res.json({
      drugSlug: row.drug_slug,
      drugName: row.drug_name,
      nciDrugUrl: row.nci_drug_url,
      nciCancerType: row.nci_cancer_type,
      evidenceLabel: row.evidence_label,
      compoundName: row.compound_name,
      chemblId: row.chembl_id,
      molecularFormula: row.molecular_formula,
      moleculeType: row.molecule_type,
      sourceName: row.source_name,
      sourceUrl: row.source_url,
      canonicalSmiles: row.canonical_smiles,
      standardInchiKey: row.standard_inchi_key,
      maxPhase: nullableNumeric(row.max_phase),
      structureImageUrlOrSvg: row.molecular_formula ? row.structure_image_url_or_svg : null,
      chemblSourceNote: row.chembl_source_note,
      indications: indications.map((item) => ({
        indicationText: item.indication_text,
        meshHeading: item.mesh_heading,
        efoTerm: item.efo_term
      }))
    });
  } catch (error) {
    sendDatabaseError(res, error);
  }
});

app.all(["/api/tables", "/api/tables/*", "/api/analysis/overview"], (_req: Request, res: Response<ErrorResponse>) => {
  res.status(410).json({
    message: "Raw database browsing is disabled. This website exposes only curated read-only project summaries."
  });
});

app.get(["/proteins.html", "/chembl.html"], (_req: Request, res: Response) => {
  res.redirect(301, "/mutation-analysis.html");
});

app.get("/contact.html", (_req: Request, res: Response) => {
  res.redirect(301, "/about.html");
});

app.get("/workflow.html", (_req: Request, res: Response) => {
  res.status(404).send("Workflow page has been removed.");
});

app.get("*", (_req: Request, res: Response) => {
  res.sendFile(path.join(staticDir, "index.html"));
});

app.listen(port, "0.0.0.0", () => {
  console.log(`COAD Cancer Predictor listening on port ${port}`);
});
