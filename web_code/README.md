# COAD Cancer Predictor Website

Node + TypeScript + Express application for Nancy's read-only COAD Cancer Predictor research website.

The site is local-first and serves multiple reference-matched pages:

- `index.html`: project overview and COAD atlas preview;
- `data.html`: COAD data, analysis workflow, and prediction model;
- `biology.html`: protein structure/mutation viewer and ChEMBL compound formulas;
- `resources.html`: glossary, sources, and contact;
- curated public JSON summaries from `public/data/coad-project-data.json`;
- read-only API routes for site data, health, and contact metadata.

## Runtime

This app is intended to run inside the Jupyter container, not as a separate host
Node process. In Docker, the app lives at:

```text
/workspace/node-app
```

The host-side mounted copy is:

```text
docker_storage/jupyter/node-app
```

Start or restart the website through the Jupyter container:

```text
docker compose restart jupyter
```

The website is exposed through the Jupyter container's Node port:

```text
http://127.0.0.1:3000/
```

For development inside the container:

```text
cd /workspace/node-app
npm install
npm run build
npm start
```

## Backend

- Source: `src/server.ts`
- Build output: `dist/server.js`
- Type check: `npm run typecheck`
- Build: `npm run build`
- Framework: Express running on Node.js

## Public API

- `GET /api/health`: reports app status.
- `GET /api/site-data`: returns curated website-facing project summaries.
- `GET /api/contact`: returns the public contact destination for the mailto flow.

Raw table browsing and arbitrary SQL endpoints are intentionally disabled. The public
website must not expose database credentials, raw datasets, local private paths,
or controls that edit, upload, delete, or modify project files.

## Contact

Set `CONTACT_EMAIL` to change the public mailto destination. The v1 contact flow
opens the visitor's email app and does not store messages.
