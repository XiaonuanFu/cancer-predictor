# Mutation Analysis Page Development Prompt

Updated: 2026-06-26

Use this prompt to revise the Mutation Analysis page of the COAD Project website, `web_code/public/mutation-analysis.html`. Do not implement the page from this document alone unless the user explicitly asks for code changes.

Chinese request summary: 设计 Mutation Analysis 网页开发提示词。页面必须访问本地数据库中的 `coad_web` schema，把来自 `bio_tcga` 的 COAD mutation gene data 和来自 `chembl` 的 drug compound formula data 整理到 `coad_web` 中；未来网站要发布到云上，所以数据库必须小，只保留 COAD 相关数据；`coad_web` 必须是自包含 schema，即使云端没有完整 `bio_tcga` 或 `chembl` 也能独立运行；顶部用柱状图展示突变基因；尽量展示基因对应蛋白和右侧 AlphaFold structure；下方用 cBioPortal Mutation Mapper 展示基因/蛋白突变；COAD treatment drugs 来源使用 NCI drug page；风格与前几页统一；点击药物后用右抽屉展示化合物详情、适应症、结构等。

English request summary: This document is a development prompt for a later Mutation Analysis page revision. The page must use a read-only backend API connected to the local `coad_web` PostgreSQL schema. Because the website may later be deployed to the cloud, the database must stay small and COAD-only. The `coad_web` schema must be self-contained, so the deployed website can run even when the full `bio_tcga` and `chembl` schemas are not available. The page should show top mutated COAD genes, protein and AlphaFold structure context when available, cBioPortal Mutation Mapper-style mutation visualization, NCI-sourced COAD treatment drugs, and a right-side drug detail drawer using ChEMBL-derived local data.

## Copy-Paste Prompt

Revise the Mutation Analysis page of the COAD Cancer Predictor website, `mutation-analysis.html`, using the rules below.

### Scope

- Only revise the Mutation Analysis page and the minimum shared CSS, JavaScript, backend API, and database-facing code needed for that page.
- Keep the site English-first. If Chinese helper text is added, include the same meaning in English.
- Keep the page read-only and educational. It must not allow visitors to upload mutation files, edit data, run free SQL, or receive medical treatment recommendations.
- Match the current Overview, COAD Data, and Model pages: same header, navigation, typography scale, spacing, restrained scientific color use, and compact dashboard style.
- Do not expose raw local database paths, database credentials, private notebooks, database dumps, or large raw PanCanAtlas/ChEMBL tables.

### Main Page Goal

The page should help a visitor answer these questions quickly:

1. Which genes are most frequently mutated in COAD?
2. What protein does a selected gene make, when this information is available?
3. Where do important mutations appear on the protein?
4. Can the selected protein structure be viewed with AlphaFold?
5. Which treatment drugs are relevant to colon or colorectal cancer, and what chemical information is stored locally?

Plain explanation: a mutation is a DNA sequence change. A protein is a molecule made from a gene that can do work inside a cell.

### Required Database Rule

This page must access the local PostgreSQL database through safe read-only API routes.

- Use the website-facing schema name: `coad_web`.
- Design `coad_web` as the deployable cloud database schema, not only as a local helper schema.
- Keep `coad_web` small. It should contain only COAD-related website data, not pan-cancer data, full TCGA tables, or full ChEMBL tables.
- Make `coad_web` self-contained. Self-contained means the website can run from `coad_web` alone after deployment, without needing the original `bio_tcga` or `chembl` schemas.
- Do not query the full `bio_tcga` or `chembl` schemas directly from frontend code.
- Do not make runtime API routes depend on `bio_tcga`, `chembl`, or other large source schemas.
- Do not keep this page as static-only data from `public/data/coad-project-data.json`.
- The backend may load small fallback labels from static JSON only for layout text, but mutation genes, protein targets, drug list, formulas, indications, and compound details must come from `coad_web`.
- Use parameterized SQL queries. Parameterized SQL means using placeholders for user-selected values, so the database treats them as data instead of executable SQL.
- Frontend API calls must use `GET` routes only.

### Cloud Deployment And Self-Contained Schema

The future cloud deployment should not require large local research databases.

Required cloud rules:

- The cloud database should contain the `coad_web` schema and only the curated COAD website subset.
- The cloud database should not include the full `bio_tcga` schema.
- The cloud database should not include the full `chembl` schema.
- The website must still work if only `coad_web` exists.
- The local development process may use `bio_tcga` and `chembl` as source schemas, but only during data preparation or refresh scripts.
- After curation, all fields needed by the page must be stored inside `coad_web`.
- Include enough source/provenance columns in `coad_web` so visitors can see where the data came from without needing access to the original large schemas.
- Keep the schema portable. Portable means it can be exported, imported, and run on a smaller cloud PostgreSQL database.

Suggested size-control rules:

- Store summary rows, not raw mutation records for every mutation if the page only needs top genes and hotspots.
- Store selected COAD treatment drugs, not the full NCI drug list.
- Store selected ChEMBL compounds linked to those drugs, not all ChEMBL molecules.
- Store external AlphaFold, cBioPortal, NCI, and ChEMBL URLs instead of copying large external files into the database.
- Store small structure images or SVGs only when necessary; prefer URL references for large molecular or protein assets.

### Required `coad_web` Data Preparation

Before the frontend page is considered complete, curate these local website tables or views in `coad_web`.

Required mutation-related tables or views:

```text
coad_web.mutation_gene_frequencies
coad_web.mutation_hotspots
coad_web.protein_structure_targets
coad_web.mutation_mapper_targets
```

Required drug and compound tables or views:

```text
coad_web.coad_treatment_drugs
coad_web.coad_drug_compounds
coad_web.coad_drug_indications
coad_web.coad_drug_sources
```

Data movement requirement:

- Copy or materialize only the curated COAD mutation summaries needed by the website from `bio_tcga` into `coad_web`.
- Copy or materialize only the curated ChEMBL drug compound fields needed by the website from `chembl` into `coad_web`.
- Do not copy the full ChEMBL schema or full TCGA mutation table into `coad_web`.
- Do not leave required display fields only in `bio_tcga` or `chembl`; every field needed by the website must be duplicated or summarized inside `coad_web`.
- Treat `bio_tcga` and `chembl` as build-time source schemas, not runtime dependencies for the cloud website.
- Record source table names and import dates in `coad_web.coad_drug_sources` or a similar provenance table. Provenance means a note showing where data came from.

Suggested mutation fields:

```text
gene_symbol
mutated_sample_count
mutated_sample_percent
total_mutation_records
top_variant_classification
source_schema
source_table
display_order
```

Suggested protein fields:

```text
gene_symbol
protein_name
uniprot_id
alphafold_url
protein_length
project_reason
structure_note
```

Suggested hotspot fields:

```text
gene_symbol
protein_change
amino_acid_position
mutation_label
sample_count
variant_classification
cbioportal_mutation_mapper_url
display_order
```

Suggested drug fields:

```text
drug_name
nci_drug_url
nci_cancer_type
evidence_label
display_order
```

Suggested compound fields copied from curated ChEMBL records:

```text
drug_name
compound_name
chembl_id
molecular_formula
canonical_smiles
standard_inchi_key
max_phase
molecule_type
structure_image_url_or_svg
source_schema
source_table
```

Suggested indication fields:

```text
drug_name
chembl_id
indication_text
mesh_heading
efo_term
source_schema
source_table
```

### Backend API Requirements

Add read-only API routes for the Mutation Analysis page.

Suggested routes:

```text
GET /api/mutation-analysis/genes
GET /api/mutation-analysis/genes/:geneSymbol
GET /api/mutation-analysis/genes/:geneSymbol/hotspots
GET /api/mutation-analysis/drugs
GET /api/mutation-analysis/drugs/:chemblId
```

Expected behavior:

- `/genes` returns top mutated genes from `coad_web.mutation_gene_frequencies`.
- `/genes/:geneSymbol` returns gene summary plus protein target data from `coad_web.protein_structure_targets`, when available.
- `/genes/:geneSymbol/hotspots` returns protein mutation positions from `coad_web.mutation_hotspots` or `coad_web.mutation_mapper_targets`.
- `/drugs` returns NCI-sourced COAD treatment drug rows joined to curated ChEMBL compound formula rows.
- `/drugs/:chemblId` returns one compound detail view, including formula, SMILES, indication, source notes, and structure data if available.

Error and loading states:

- Show a quiet loading state while database queries run.
- Show a friendly empty state if a selected gene has no protein or AlphaFold record.
- Show a friendly empty state if a selected drug has no matched ChEMBL compound.
- Backend errors must not leak database credentials, local paths, or raw SQL.

### Layout Requirements

Use one continuous research dashboard layout, not a marketing landing page.

Recommended order:

1. Compact page header: `Mutation Analysis`
2. Top mutated genes bar chart
3. Selected gene and protein detail area
4. AlphaFold structure viewer on the right
5. cBioPortal Mutation Mapper section below
6. COAD treatment drug table
7. Right-side drug detail drawer opened by clicking a drug row

Keep the first screen useful. The top bar chart must be visible near the top without a large decorative hero.

### Top Mutated Gene Bar Chart

At the top of the page, show a horizontal or vertical bar chart listing mutated genes.

Requirements:

- Use ECharts unless another existing chart pattern in the site is clearly better.
- Data source: `coad_web.mutation_gene_frequencies`.
- Show at least the top 10 mutated genes by mutated sample count.
- Include both count and percentage in the tooltip.
- Clicking a bar selects that gene and updates the protein, AlphaFold, and Mutation Mapper sections.
- Do not add mutated gene percentages together, because one tumor sample can have mutations in multiple genes.

Suggested chart title:

```text
Most frequently mutated COAD genes
```

Suggested chart explanation:

```text
Each bar shows how many COAD tumor samples contain at least one mutation in that gene. One sample can appear in more than one gene bar.
```

### Gene And Protein Detail Area

When a gene is selected, show a compact detail panel.

Required fields when available:

- Gene symbol
- Mutated sample count
- Mutated sample percent
- Top variant classification
- Protein name
- UniProt ID
- Protein length
- Why this gene/protein is shown

Plain explanations:

- Variant classification means the type of mutation effect, such as missense or nonsense.
- UniProt ID means a stable protein database identifier.

If protein data is missing:

- Do not hide the selected gene.
- Show the mutation summary and a note: `Protein structure data is not available yet for this selected gene.`

### AlphaFold Structure Requirement

If possible, show the selected gene's protein structure on the right side.

Preferred implementation:

- Use the AlphaFold DB URL stored in `coad_web.protein_structure_targets.alphafold_url`.
- If a safe embedded viewer is practical, use a professional protein viewer such as Mol* or an AlphaFold/PDBe-supported viewer.
- If embedding is not practical in the current static HTML + Express setup, show a polished structure preview card and a clear external button: `Open AlphaFold DB`.

Required explanatory copy:

```text
AlphaFold structures are predicted protein shapes. They are useful for research learning, but they are not always experimentally measured structures.
```

### cBioPortal Mutation Mapper Requirement

Use cBioPortal Mutation Mapper for the gene/protein mutation display below the structure area.

Reference URL:

```text
https://www.cbioportal.org/mutation_mapper
```

Preferred behavior:

- Use the cBioPortal Mutation Mapper component or embed/link pattern if it can be added without rewriting the whole website architecture.
- If the component requires React and the current page remains static HTML, implement a local linear protein mutation map that visually follows the Mutation Mapper idea, then provide a button to open the selected gene in cBioPortal Mutation Mapper.
- The local display must use database records from `coad_web.mutation_hotspots` or `coad_web.mutation_mapper_targets`, not hard-coded frontend data.

Required display:

- Protein length axis when available.
- Mutation markers placed by amino acid position.
- Labels such as `KRAS p.G12D` or `BRAF p.V600E` when available.
- Sample count per mutation hotspot.
- Variant classification.

Plain explanation:

```text
Mutation Mapper shows where mutations appear along a protein. This helps visitors see whether many samples share a similar mutation location.
```

### COAD Treatment Drug List

List COAD treatment drugs below the mutation/protein sections.

Source requirement:

- Use the National Cancer Institute drug page as the source for the treatment drug list:
  `https://www.cancer.gov/about-cancer/treatment/drugs`
- Prefer the NCI cancer-type drug list for colon and rectal cancer if the page provides that category.
- Store the exact NCI URL, access date, and source note in `coad_web.coad_drug_sources`.
- The page should clearly label these as treatment context, not as treatment advice.

Required drug table columns:

- Drug name
- Linked ChEMBL compound or `No local ChEMBL match yet`
- Molecular formula
- Evidence label
- NCI source

Suggested explanation:

```text
The drug list is sourced from the National Cancer Institute. The chemical formulas and compound details are shown from the local curated ChEMBL-derived records in `coad_web`.
```

### Drug Detail Right Drawer

When the user clicks a drug row, open a right-side drawer.

Drawer requirements:

- The drawer slides in from the right on desktop.
- On mobile, it can become a full-width bottom or full-screen panel.
- It must have a clear close button, support Escape key close, and return focus to the clicked drug row.
- The background page should remain visible but not confusing.
- Do not navigate away from the page when opening the drawer.

Drawer content must be queried from `coad_web`, mainly from ChEMBL-derived curated tables:

- Drug name
- Compound name
- ChEMBL ID
- Molecular formula
- SMILES string, if available
- InChIKey, if available
- Indication text, if available
- NCI source link
- ChEMBL source note
- Compound structure image or SVG if available

Plain explanations:

- Molecular formula shows which atoms are in a molecule.
- SMILES is a text format for describing chemical structure.
- Indication means the disease or condition a drug is used for.

### Style Requirements

- Match the current site header, navigation, font scale, and dashboard spacing.
- Keep cards compact. Do not put cards inside other cards.
- Use light borders, clear labels, and quiet scientific colors.
- Avoid a giant hero section. This is an analysis page, so the data should appear quickly.
- Keep the bar chart, protein section, Mutation Mapper section, and drug table readable on mobile.
- Use table row hover states and selected states for gene/drug interactions.
- Use the same button and link styling as existing pages.
- Keep all claims research-only and educational.

### Accessibility Requirements

- The bar chart needs an `aria-label` and a nearby text summary.
- Drug rows must be keyboard-selectable.
- The right drawer must trap focus while open and close with Escape.
- External links must clearly say when they open AlphaFold, cBioPortal, NCI, or ChEMBL.
- Do not rely on color alone to mark selected genes, mutation types, or drawer states.

### Data Quality Checks Before Finishing

Run these checks before presenting the completed page:

- Confirm API responses come from `coad_web`, not hard-coded page arrays.
- Confirm curated COAD mutation data came from `bio_tcga`-derived local tables.
- Confirm curated molecular formula and structure fields came from `chembl`-derived local tables copied into `coad_web`.
- Confirm the page can run when only `coad_web` is available and the full `bio_tcga` and `chembl` schemas are absent.
- Confirm `coad_web` contains only COAD-related curated website data and is small enough for future cloud deployment.
- Confirm each displayed drug has an NCI source note or a clear `source pending` placeholder.
- Confirm no raw database credentials, unrestricted table browser route, or free SQL endpoint is exposed.
- Confirm selecting a bar updates the gene/protein/Mutation Mapper sections.
- Confirm clicking a drug opens the right drawer and closing it returns focus correctly.
- Confirm the page works on desktop and mobile widths without chart labels or drawer text overlapping.

### Suggested Acceptance Criteria

The revision is complete when:

- The Mutation Analysis page loads mutation genes from `/api/mutation-analysis/genes`.
- A top mutated genes bar chart appears above the gene/protein detail area.
- Selecting a gene updates protein details, AlphaFold action, and mutation hotspot display.
- Mutation Mapper-style display uses local `coad_web` hotspot data and links to cBioPortal Mutation Mapper.
- The drug table is sourced from NCI-curated local records and joined to ChEMBL-derived formulas in `coad_web`.
- Clicking a drug opens a right-side detail drawer populated by `/api/mutation-analysis/drugs/:chemblId`.
- The deployed database design is COAD-only, small, and self-contained in `coad_web`.
- Runtime API routes do not require full `bio_tcga` or `chembl` schemas.
- The page visually matches the previous pages and remains read-only.

## External Source Links

- cBioPortal Mutation Mapper: `https://www.cbioportal.org/mutation_mapper`
- National Cancer Institute drug information page: `https://www.cancer.gov/about-cancer/treatment/drugs`
- AlphaFold DB: `https://alphafold.ebi.ac.uk/`
- ChEMBL: `https://www.ebi.ac.uk/chembl/`
