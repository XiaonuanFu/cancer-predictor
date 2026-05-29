# Cancer Predictor Documentation

Initialized: 2026-05-23

This directory holds planning and project reference documents for the cancer information analysis project.

## Directory Map

- `requirements/`: product goals, functional requirements, user workflows, and open questions.
- `web-design/`: Web application structure, UI design notes, API contracts, and implementation notes for `web_code/`.
- `environment/`: Docker, runtime, service, database, and local connection information.
- `data-sources/`: local data inventory, source provenance, database import mapping, and data quality notes.
- `prompts/`: daily prompt logs for recording and refining prompts used during project work.

## Current Project Snapshot

- Main local services are defined in `docker-compose.yml`.
- Web application source is in `web_code/`.
- Completed Web code should also be synced to `docker_storage/jupyter/node-app`, which is mounted in the Jupyter container as `/workspace/node-app` for the Node service.
- Database import tooling is in `scripts/import_tcga_raw_data.py`.
- Raw biomedical data is stored locally under `data/` and is ignored by git.
- Runtime storage is stored locally under `docker_storage/` and is ignored by git.
