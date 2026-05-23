# Current Container and Database Information

Updated: 2026-05-23

This document records the current local environment observed from the project workspace plus the service definitions in `docker-compose.yml`.

## Docker Compose Services

Defined services:

- `postgres`
  - Container: `bio-postgres`
  - Image: `bio-postgres:18`
  - Host port: `5432`
  - Container port: `5432`
  - Data mount: `./docker_storage/pg:/var/lib/postgresql`
- `jupyter`
  - Container: `bio-jupyter`
  - Image: `bio:latest`
  - Host ports: `8888`, `3000`
  - Workspace mount: `./docker_storage/jupyter:/workspace`
  - Jupyter token: `bioanalysis`
  - Node app directory: `/workspace/node-app`

## Current Running Containers

Observed on 2026-05-23:

| Container | Image | Status | Published Ports |
| --- | --- | --- | --- |
| `bio-jupyter` | `bio:latest` | Up about 46 hours | `3000:3000`, `8888:8888` |
| `bio-postgres` | `bio-postgres:18` | Up about 46 hours | `5432:5432` |

## Local Images

Observed local images:

| Repository | Tag | Size |
| --- | --- | --- |
| `bio` | `latest` | about 5.12 GB |
| `bio-postgres` | `18` | about 1.01 GB |

## Main Python/Jupyter Environment

The `environment/Dockerfile` installs:

- System tools: `build-essential`, `git`, `curl`, `nodejs`, `npm`, `libpq-dev`
- Jupyter: `jupyterlab`, `notebook`, `ipykernel`, `jupyterlab-lsp`
- Data science: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`
- Visualization: `matplotlib`, `seaborn`, `plotly`, `altair`, `bokeh`
- File/data formats: `pyarrow`, `openpyxl`, `xlsxwriter`, `xlrd`, `lxml`, `h5py`, `tables`, `zarr`
- Database tools: `sqlalchemy`, `psycopg2-binary`, `duckdb`, `connectorx`
- Bio/chem tools: `rdkit`, `py3Dmol`, `mols2grid`, `biopython`, `gseapy`, `pyfaidx`, `pysam`
- Modeling and analysis: `lifelines`, `umap-learn`, `polars`, `networkx`
- Document support: XeLaTeX, Chinese fonts, and `pandoc`

## GATK Environment

The optional `environment/Dockerfile_gatk` is based on:

- `broadinstitute/gatk:4.6.1.0`

It installs:

- `samtools`
- `bcftools`
- `python3`
- `python3-pip`
- `nextflow`
- Common shell tools such as `curl`, `wget`, `git`, `less`, and `htop`

## PostgreSQL Connection

Local development connection:

```text
Host: 127.0.0.1
Port: 5432
Database: bio
User: bio
Password: bioanalysis
```

Container/internal connection used by the Web app:

```text
PGHOST=bio-postgres
PGPORT=5432
PGDATABASE=bio
PGUSER=bio
PGPASSWORD=bioanalysis
```

## PostgreSQL Current State

Observed database:

- Database: `bio`
- User: `bio`
- PostgreSQL version: `PostgreSQL 18.4 (Debian 18.4-1.pgdg13+1)`
- Database size: about 55 GB

Observed application schemas:

| Schema | Table Count | Approx Size |
| --- | ---: | ---: |
| `bio_tcga` | 28 | about 29 GB |
| `chembl` | 74 | about 38 GB |
| `public` | 1 | about 7 MB |

Installed PostgreSQL extensions:

| Extension | Version |
| --- | --- |
| `fuzzystrmatch` | `1.2` |
| `pg_trgm` | `1.6` |
| `plpgsql` | `1.0` |
| `postgis` | `3.6.3` |
| `rdkit` | `4.7.0` |
| `vector` | `0.8.2` |

## Useful Commands

```bash
docker compose up -d
docker compose down
docker ps
docker exec -it bio-postgres psql -U bio -d bio
open http://127.0.0.1:8888/lab?token=bioanalysis
open http://127.0.0.1:3000/
```

## Security Note

The credentials in this document are local development credentials. Do not reuse them for a public, shared, or production deployment.

