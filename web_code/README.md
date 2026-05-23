# Cancer Data Node Console

Express application for the Jupyter container Node service. It connects to the local
PostgreSQL service from `docker-compose.yml` and serves a three-tab interface:

- Cancer Data
- Chemical Data
- Data Analysis

Default database settings target the Compose service:

```text
PGHOST=bio-postgres
PGPORT=5432
PGDATABASE=bio
PGUSER=bio
PGPASSWORD=bioanalysis
```

Run locally inside the Jupyter container with:

```bash
npm install
npm start
```
