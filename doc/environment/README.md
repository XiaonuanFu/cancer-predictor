# Environment Directory

Use this directory for local runtime, Docker, service, database, and toolchain notes.

## Current Runtime

The website runs inside the `bio-jupyter` container. Do not start a separate
host Node service for the website.

- Container app path: `/workspace/node-app`
- Host-mounted app path: `docker_storage/jupyter/node-app`
- Public website URL: `http://127.0.0.1:3000/`
- Jupyter URL: `http://127.0.0.1:8888/lab?token=bioanalysis`
- Backend source in the app: `src/server.ts`
- Compiled backend: `dist/server.js`

The Jupyter container startup script runs `npm install`, then starts the app
with `npm start` using `NODE_PORT=3000`.

## Suggested Files

- `current-container-and-database.md`: current local Docker services, images, database settings, schemas, and extensions.
- Future additions can include setup guides, troubleshooting notes, dependency upgrade logs, or deployment notes.
