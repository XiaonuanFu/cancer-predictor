# COAD Cancer Predictor Website Design Requirements

Updated: 2026-06-21

## Purpose

Build a polished, English-first project website for Nancy's COAD cancer predictor project.

COAD means colon adenocarcinoma, a type of colon cancer. The website should explain the project, show the selected COAD PanCanAtlas analysis, connect the analysis to relevant ChEMBL compound information, and present the final prediction model in a clear, interactive, read-only format.

Chinese note: 网站主要用英文展示；如果需要中文提示，必须同时给出英文版本。

English note: The website should be mainly in English. If Chinese helper text is added, it must also include an English version.

## Target Audience

- High school research presentation audience.
- Biology or computer science teachers.
- Students who know basic biology but may not know omics, ChEMBL, or machine learning.
- Reviewers who want to understand the project without opening the local database or notebooks.

Important writing rule: explain advanced terms with short plain-language definitions. Example: machine learning (training a program to find patterns from data).

## Main Website Goal

The site should answer five questions quickly:

1. What is this project about?
2. Which COAD PanCanAtlas data was used, and what does it mean?
3. What are the key analysis steps and the final prediction model?
4. Which ChEMBL compounds are relevant to COAD treatment, and what are their molecular formulas?
5. What do the biology and computer science terms mean?
6. Which data sources, tools, and papers support the project?
7. Where did the data and code come from?

## Technical Stack Requirements

Website code requirements:

- Runtime and backend framework: Node.js + TypeScript + Express.
- Backend database: PostgreSQL 18.
- The backend should expose safe read-only API routes for website display.
- TypeScript types should be used for API responses, database query results, and frontend-facing data objects where practical.

## Content Scope

### In Scope

- Project introduction for a COAD-focused cancer predictor.
- COAD-only PanCanAtlas data explanation.
- Key data analysis process for this project.
- Final prediction model summary and evaluation.
- Selected ChEMBL compounds related to COAD or colorectal cancer treatment.
- Molecular formulas for selected compounds.
- A glossary page explaining biology and computer science terms.
- A combined data, tools, and literature reference page.
- AlphaFold-based protein structure display for selected COAD-related proteins.
- cBioPortal MutationMapper links or views for selected mutation locations.
- Data sources and GitHub project link.
- Interactive read-only charts, filters, and summaries.
- Contact-by-email feature.
- Local running first; cloud deployment later.

### Out of Scope

- Pan-cancer comparison pages.
- Full TCGA/PanCanAtlas database browser.
- Full ChEMBL database browser.
- Editing, uploading, deleting, or changing any project data.
- Publicly exposing raw database credentials, local file paths, private notebooks, database dumps, or large generated datasets.
- Clinical diagnosis or treatment recommendation claims.

## Page Structure

### 1. Home / Project Overview

Purpose: introduce the project immediately.

Required content:

- Project title: `COAD Cancer Predictor`.
- One-sentence summary: a research website that analyzes COAD colon cancer data and explains a tumor/normal prediction model.
- Short project background:
  - What COAD is.
  - Why colon cancer data analysis matters.
  - What public biomedical data means.
- Short project workflow:
  - COAD data selection.
  - Data cleaning and feature preparation.
  - Model training.
  - Model evaluation.
  - Biological interpretation.
- Clear research-only notice:
  - This project is for education and research.
  - It is not a medical diagnosis tool.

Design direction:

- Modern scientific style.
- Clean white or soft-light background.
- Strong first viewport with the project name, a short subtitle, and a compact visual summary.
- Avoid a generic marketing page; the first screen should show this specific COAD project.

### 2. COAD PanCanAtlas Data

Purpose: explain only the COAD PanCanAtlas data used in this project.

Required content:

- COAD definition: colon adenocarcinoma, a type of colon cancer.
- PanCanAtlas definition: a TCGA project that organized multi-cancer molecular data; this website only uses the COAD-related part.
- Dataset explanation:
  - COAD patient/sample selection.
  - Tumor samples.
  - Normal or comparison samples if used by the model.
  - Clinical information, when used.
  - RNA expression data, when used.
  - Mutation data, when used.
- What each data type means:
  - Clinical data: patient and disease information.
  - RNA expression: how active genes are in a sample.
  - Mutation data: DNA sequence changes found in tumor samples.
- Show only project-relevant counts and summaries, not full raw tables.

Required interactions:

- Filter or highlight COAD dataset sections by data type.
- Interactive sample-count cards or charts.
- Expandable explanations for terms such as RNA expression, mutation, and feature matrix.

### 3. Analysis Workflow

Purpose: show the key data analysis process from raw selected data to final model.

Required steps:

1. Select COAD samples from local PanCanAtlas/TCGA-related tables.
2. Clean sample metadata and labels.
3. Build a feature matrix (a table where each row is a sample and each column is a measurable feature).
4. Train a tumor vs normal prediction model.
5. Evaluate model performance with clear metrics.
6. Interpret important genes or molecular features.

Required visual format:

- A simple workflow diagram.
- One concise explanation for each step.
- Links to relevant reports or notebooks when safe to show.

### 4. Prediction Model

Purpose: present the final model without overclaiming.

Required content:

- Model task: COAD tumor vs normal classification.
- Input features: COAD/colon-related gene expression features or other final selected features.
- Output: predicted class, such as tumor-like or normal-like.
- Final selected model name, after the project decides it.
- Evaluation metrics:
  - Accuracy.
  - Precision.
  - Recall.
  - F1 score.
  - ROC-AUC if available.
- Model explanation:
  - Important genes or features.
  - What the features may mean biologically.
- Limitation statement:
  - This is exploratory research.
  - The data sources may have batch effects (technical differences caused by data being produced in different experiments or pipelines).
  - The model should not be used for clinical diagnosis.

Required interactions:

- Toggle between metric cards, confusion matrix, and important-feature chart.
- Search or filter important genes/features.
- Tooltips explaining metrics in simple language.

### 5. Protein Structure And Mutation Site Viewer

Purpose: connect model interpretation and mutation analysis to visible protein-level biology.

Required content:

- Use AlphaFold DB to show predicted protein structures for selected COAD-related proteins.
- Clearly explain that AlphaFold structures are predicted structures, not always experimentally measured structures.
- Use cBioPortal MutationMapper to show mutation locations on a linear protein map.
- Focus only on selected project-relevant genes/proteins, such as important model features or common COAD mutation genes.
- Explain protein structure in simple language: the 3D shape of a protein, which can affect how it works.
- Explain mutation location in simple language: the position where a DNA change affects a protein.

Required display fields:

- Gene symbol.
- Protein name, when available.
- UniProt ID, when available.
- AlphaFold DB link.
- cBioPortal MutationMapper link.
- Mutation or hotspot label, when available.
- Short project note explaining why this protein is shown.

Required interactions:

- Select a gene/protein from a small curated list.
- Open or embed the AlphaFold structure view when technically practical.
- Open MutationMapper for mutation-location visualization.
- Show a short explanation panel beside the visual.

Implementation notes:

- Preferred AlphaFold reference link: `https://alphafold.ebi.ac.uk/`.
- Preferred cBioPortal MutationMapper link: `https://www.cbioportal.org/mutation_mapper`.
- If embedding is difficult, provide clear external buttons instead of copying large structure files into `public/`.
- Do not allow visitors to upload mutation files or edit mutation records from this website.

### 6. ChEMBL COAD Compound Formulas

Purpose: show selected ChEMBL compounds related to COAD treatment, but only the molecular formulas and minimal context.

Required content:

- ChEMBL definition: a public database of bioactive molecules, drug-like compounds, and activity data.
- Only include compounds related to COAD, colorectal cancer, or treatments commonly connected to COAD research.
- Display fields:
  - Compound or drug name.
  - ChEMBL ID.
  - Molecular formula.
  - Short evidence label, such as approved drug, clinical use, or research compound, if available.
  - Source note.
- Do not display the full ChEMBL database.
- Do not display unnecessary activity tables, assay tables, or all compound properties.

Required interactions:

- Search by compound name or ChEMBL ID.
- Filter by evidence label.
- Sort by compound name or molecular formula.

Important data rule:

- The website should show a curated project subset, not live unrestricted access to the `chembl` schema.

### 7. Glossary Of Biology And Computer Science Terms

Purpose: give visitors one place to understand all professional terms used by the website.

Required content:

- One page explaining both biology and computer science terms.
- Terms should be written in simple English.
- Chinese helper notes are allowed only if the same meaning is also written in English.
- Each term should include:
  - Term.
  - Category: biology, computer science, statistics, machine learning, database, or web.
  - Plain-language definition.
  - Where the term appears in this project.

Required biology terms:

- COAD.
- Colon adenocarcinoma.
- TCGA.
- PanCanAtlas.
- ChEMBL.
- AlphaFold.
- cBioPortal.
- Gene.
- RNA expression.
- Mutation.
- Protein.
- Protein structure.
- Molecular formula.
- Tumor sample.
- Normal sample.
- Clinical data.

Required computer science and statistics terms:

- Database.
- Schema.
- Table.
- API.
- Frontend.
- Backend.
- Feature matrix.
- Machine learning.
- Classification.
- Model training.
- Model evaluation.
- Accuracy.
- Precision.
- Recall.
- F1 score.
- ROC-AUC.
- Read-only access.

Required interactions:

- Search terms.
- Filter by category.
- Expand/collapse definitions.

### 8. Data, Tools, Literature, And GitHub

Purpose: make the project transparent and put all reference links in one page.

This page should combine data sources, software tools, literature references, and the GitHub project.

Required page sections:

- Data sources.
- Tools and databases.
- Literature and reference links.
- GitHub project.

Required content:

- Data sources:
  - TCGA/PanCanAtlas COAD-related data.
  - COAD normal/comparison data if used.
  - ChEMBL compound data.
  - Any generated project reports used by the website.
- Tools and databases:
  - AlphaFold DB for predicted protein structures.
  - cBioPortal MutationMapper for protein mutation-location visualization.
  - ChEMBL for compound information.
  - Python or notebook tools used by the project, when relevant.
- Literature and reference links:
  - TCGA/PanCanAtlas reference.
  - ChEMBL reference.
  - AlphaFold DB reference.
  - cBioPortal reference.
  - COAD or colorectal cancer background references.
- GitHub project:
  - Repository: `https://github.com/XiaonuanFu/cancer-predictor`
- For each source, show:
  - Source name.
  - What part of the project uses it.
  - Link.
  - Access date or project import date, when available.
  - Short license/citation note, when available.

Do not show:

- Local private file paths.
- Database passwords.
- Full database dumps.
- Large raw data files.

### 9. Contact

Purpose: allow visitors to contact Nancy without changing project data.

Required content:

- A contact form or mail link.
- Fields:
  - Name.
  - Email.
  - Message.
- Clear message:
  - Visitors can send questions or feedback.
  - Visitors cannot modify the website data or project files.

Implementation preference:

- Store the contact destination email in an environment variable, such as `CONTACT_EMAIL`.
- Do not commit private email credentials.
- If using a backend form endpoint, protect it with basic spam prevention and rate limiting.
- If no backend email service is ready, use a safe `mailto:` link first.

## Website-Facing Data Schema

Create one small website-facing schema for project data. Suggested name:

```text
coad_project_web
```

This schema should contain only curated data needed by the website. It should not copy all PanCanAtlas or ChEMBL records.

### Suggested Tables Or Views

```text
coad_project_web.project_summary
coad_project_web.coad_dataset_summary
coad_project_web.coad_analysis_steps
coad_project_web.prediction_model_summary
coad_project_web.model_metrics
coad_project_web.model_important_features
coad_project_web.glossary_terms
coad_project_web.reference_links
coad_project_web.protein_structure_targets
coad_project_web.mutation_mapper_targets
coad_project_web.coad_chembl_compound_formulas
coad_project_web.data_sources
```

### Minimum Fields

`project_summary`

- `section_key`
- `title`
- `body`
- `display_order`

`coad_dataset_summary`

- `dataset_key`
- `source_name`
- `data_type`
- `description`
- `sample_count`
- `feature_count`
- `note`

`coad_analysis_steps`

- `step_number`
- `step_name`
- `input_data`
- `method_summary`
- `output_summary`

`prediction_model_summary`

- `model_name`
- `task`
- `input_features`
- `output_label`
- `training_summary`
- `limitations`

`model_metrics`

- `metric_name`
- `metric_value`
- `plain_english_meaning`
- `display_order`

`model_important_features`

- `feature_name`
- `feature_type`
- `importance_value`
- `plain_english_note`

`glossary_terms`

- `term`
- `category`
- `plain_english_definition`
- `project_context`
- `display_order`

`reference_links`

- `reference_name`
- `reference_type`
- `url`
- `used_for`
- `citation_note`
- `display_order`

`protein_structure_targets`

- `gene_symbol`
- `protein_name`
- `uniprot_id`
- `alphafold_url`
- `project_reason`
- `structure_note`

`mutation_mapper_targets`

- `gene_symbol`
- `protein_change`
- `mutation_label`
- `cbioportal_mutation_mapper_url`
- `project_reason`
- `display_order`

`coad_chembl_compound_formulas`

- `compound_name`
- `chembl_id`
- `molecular_formula`
- `evidence_label`
- `source_note`

`data_sources`

- `source_name`
- `source_url`
- `used_for`
- `access_or_import_date`
- `citation_note`

## Read-Only And Security Requirements

The public website must be read-only for data and files.

Required rules:

- Frontend must not include edit, delete, upload, or admin controls.
- Public API routes should use `GET` for data display.
- Do not expose unrestricted SQL query endpoints.
- Do not expose database credentials in frontend code.
- Use a read-only database user for website queries when possible.
- Query only the curated `coad_project_web` schema.
- Keep raw data and large generated data out of `public/`.
- Do not allow visitors to modify notebooks, reports, source files, or database tables.
- Do not allow public visitors to upload mutation files into the website.
- Do not store large AlphaFold structure files in `public/` unless they are small, curated, and necessary.
- Email/contact submission is allowed, but it must not write into research data tables.

## Interaction Requirements

The website should feel interactive but safe.

Allowed interactions:

- Chart filters.
- Search boxes for displayed tables.
- Sort controls.
- Tooltips.
- Expand/collapse explanations.
- Tab or section navigation.
- Searchable glossary terms.
- Reference-link filtering by data, tool, or literature.
- External links to AlphaFold DB and cBioPortal MutationMapper.
- Contact email form or `mailto:` link.
- Links to GitHub and public data sources.

Not allowed interactions:

- Editing project records.
- Uploading files.
- Running arbitrary SQL.
- Uploading mutation files through the public website.
- Changing model results.
- Triggering local scripts from the public website.
- Downloading private or raw local datasets.

## Visual Design Requirements

The design should be beautiful, scientific, and easy to read.

Style goals:

- English-first scientific portfolio style.
- Clean typography.
- Strong spacing and clear section hierarchy.
- COAD-specific visuals, not generic cancer decoration.
- Charts should be simple and readable.
- Data tables should be compact and searchable.

Suggested visual sections:

- Project overview hero.
- COAD dataset cards.
- Analysis workflow timeline.
- Model performance dashboard.
- Important feature chart.
- AlphaFold protein structure section.
- cBioPortal MutationMapper mutation-location section.
- ChEMBL compound formula table.
- Glossary page.
- Data, tools, literature, and GitHub reference page.
- Contact section.

Avoid:

- Dark, heavy, hard-to-read theme.
- Overly decorative shapes that do not explain the project.
- Claims that the model can diagnose cancer.
- Huge raw tables on the page.

## Local First, Cloud Later

Current running mode:

- The website is running locally during design and testing.
- Existing web code is in `web_code/`.
- Existing design documentation is in `doc/web-design/`.

Later deployment:

- After the design is complete, the website may be deployed on a cloud server.
- Before cloud deployment, remove or hide local-only paths and credentials.
- Use environment variables for server settings.
- Use a read-only production database connection or prebuilt static JSON summaries.
- Confirm that only curated website-facing data is deployed.

## Acceptance Checklist

- The website introduction clearly explains Nancy's COAD project.
- Only COAD PanCanAtlas-related data is introduced.
- The analysis process and final prediction model are shown clearly.
- ChEMBL content only lists selected COAD-related compounds and molecular formulas.
- PanCanAtlas, ChEMBL, and project-derived website data are grouped under one small website-facing schema.
- A glossary explains biology and computer science terms in simple English.
- Data sources, tools, literature links, and GitHub project are visible on one reference page.
- AlphaFold is used or linked for selected protein structure visualization.
- cBioPortal MutationMapper is used or linked for selected mutation-location visualization.
- Visitors can interact with charts/tables and send email.
- Visitors cannot modify data, files, notebooks, or database records.
- The website is primarily English.
- The design is visually polished and suitable for local testing now and cloud deployment later.
