# Web Code Design

Updated: 2026-05-23

## Current Implementation

Source directory: `web_code/`

Deployment/runtime copy:

- Local source changes should be kept in `web_code/`.
- After local Web code changes are completed, copy/sync the runnable Node app into the Jupyter container Node service directory.
- Current expected Node service directory inside the mounted Jupyter workspace: `/workspace/node-app`.
- Current host-side mounted path for that service directory: `docker_storage/jupyter/node-app`.

Technology stack:

- Node.js
- Express
- PostgreSQL client library `pg`
- Static HTML, CSS, and JavaScript

Application entry points:

- Backend: `web_code/server.js`
- Frontend HTML: `web_code/public/index.html`
- Frontend behavior: `web_code/public/app.js`
- Frontend styles: `web_code/public/styles.css`

## Product Shape

The current Web app is a local data console named `OncoChem Console`. It is designed to run from the Jupyter container's Node service and connect to the local PostgreSQL service.

Primary navigation:

- `Cancer Data`
- `Chemical Data`
- `Data Analysis`

## Backend API

- `GET /api/health`: checks PostgreSQL connectivity and returns database, user, server version, Node port, and latency.
- `GET /api/tables`: lists non-system PostgreSQL base tables with schema, table name, category, estimated rows, and columns.
- `GET /api/tables/:schema/:name/sample`: returns a small sample from a selected table.
- `GET /api/analysis/overview`: returns total table counts, estimated row counts, category summaries, and widest tables.

## Table Classification

The backend classifies tables by name:

- Cancer terms include `cancer`, `tcga`, `gdc`, `tumor`, `mutation`, `variant`, `clinical`, `survival`, `cnv`, `gene`, `patient`, and `sample`.
- Chemical terms include `chem`, `drug`, `compound`, `molecule`, `smiles`, `pubchem`, `chembl`, `tox`, `admet`, and `ligand`.
- Other tables are grouped as analysis data.

## Performance Notes

- The app uses PostgreSQL planner estimates from `pg_class.reltuples` instead of `COUNT(*)`.
- This is intentional because ChEMBL and TCGA tables are large.
- Exact counts should be added only for small tables or explicitly requested analysis jobs.

## Local Runtime

Default local URL:

```text
http://127.0.0.1:3000/
```

The Node service is started by `environment/start-services.sh` when the Jupyter container finds a Node app at `/workspace/node-app`.

## Web Code Workflow

When changing the Web application:

1. Edit and keep source files in `web_code/`.
2. Verify the local source tree has the expected `package.json`, `server.js`, and `public/` files.
3. Sync the completed code to `docker_storage/jupyter/node-app` so the Jupyter container's Node service can run it from `/workspace/node-app`.
4. Restart or refresh the Node service if needed.
5. Verify the app at `http://127.0.0.1:3000/`.

## Next Design Tasks

- Verify the deployed copy inside `docker_storage/jupyter/node-app`.
- Add a table detail view that uses `/api/tables/:schema/:name/sample`.
- Add schema filters and search for large databases.
- Add provenance display from `bio_tcga.import_manifest`.
- Add explicit loading and error states for slow database metadata requests.
