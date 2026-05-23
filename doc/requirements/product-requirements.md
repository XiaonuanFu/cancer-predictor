# Cancer Information Analysis Requirements

Updated: 2026-05-23

## Project Goal

Build a local cancer information analysis workspace that connects large cancer genomics datasets, chemical/drug data, PostgreSQL storage, Jupyter analysis, and a browser-based data console.

## Current Scope

- Store and inspect TCGA PanCanAtlas-related cancer datasets in PostgreSQL.
- Store and inspect ChEMBL chemical and drug discovery datasets in PostgreSQL.
- Provide a local Web console for browsing database tables and high-level metadata.
- Support exploratory analysis through JupyterLab and Python scientific packages.
- Keep local raw data and database storage outside git.

## Primary Users

- Researcher or analyst working locally with cancer genomics and chemical datasets.
- Developer building the Web console and database import utilities.

## Functional Requirements

- The user can start local PostgreSQL, JupyterLab, and Node Web services with Docker Compose.
- The user can inspect database health, schemas, tables, columns, and estimated row counts from the Web console.
- The user can separate cancer data, chemical data, and analysis overview views in the Web UI.
- The user can import TCGA raw data into the `bio_tcga` schema.
- The user can query ChEMBL tables from the `chembl` schema.
- The project keeps environment, data source, and import documentation close to the code.

## Non-Functional Requirements

- Large data files must remain outside git.
- Large table browsing should avoid expensive full-table scans.
- Database credentials documented here are for local development only.
- Import scripts should record source file provenance in PostgreSQL when possible.
- Documentation should distinguish verified current state from intended design.

## Open Questions

- Which cancer prediction task is the first modeling target: survival, cancer type classification, drug response, mutation burden, or another endpoint?
- Which TCGA modalities should be prioritized for cleaned feature tables?
- Should the Web console remain a lightweight data browser or expand into analysis workflows?
- Should large genomic example files move to Git LFS?

