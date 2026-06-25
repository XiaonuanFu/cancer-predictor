---
name: cancer-predictor-project
description: Project-specific conventions and memory for Nancy's cancer predictor workspace. Use this skill whenever Codex works on the cancer-predictor project, including cancer sequencing analysis, ChEMBL compound data, TCGA/COAD data, Jupyter notebooks, data processing scripts, machine learning code, documentation, reports, Docker/container setup, or the web_code application.
---

# Cancer Predictor Project

## Core Collaboration Rules

- Treat the user as a Grade 11 student (Chinese high school year 2 / 中国高二学生). Explain any concept above that level in parentheses immediately after the term.
- Write project documents primarily in English. Chinese notes are allowed, but any Chinese note must also have an English version.
- Keep explanations clear, patient, and educational. Prefer short examples over dense professional wording.
- When introducing specialized terms, include a plain explanation, for example: `variant calling (finding DNA sequence differences from sequencing data / 从测序数据中找出 DNA 差异)`.

## Local Containers And Databases

- `postgre18` contains `bio_tcga`, which stores PanCan Atlas cancer sequencing data, and `chembl`, which stores about 30 million compound records.
- `tcga_coad` stores COAD cancer-related data. COAD means colon adenocarcinoma (a type of colon cancer / 一种结肠癌).
- The Jupyter container runs both a Jupyter service and a Node service.
- Do not place database dumps, analysis datasets, private data, or generated large data under `public`.
- Do not expose local database credentials or private paths in committed files.

## Project Directory Rules

- `bio-exercise/`: FASTQ scripts. FASTQ is a sequencing read file format (a text format storing DNA reads and quality scores / 存储 DNA 读段和质量分数的文本格式).
- `py_code/`: general Python code scripts.
- `ml_study/`: machine learning scripts. Machine learning means training a program to find patterns from data (让程序从数据中学习规律).
- `py_code/script/`: data processing scripts. Put data processing code and Jupyter-related code here unless an existing local pattern clearly says otherwise.
- `data/`: sample data only. Do not put scripts here. Do not commit this data to GitHub.
- `doc/`: design documents and requirement documents.
- `docker_storage/`: local container storage to keep data after containers stop.
- `environment/`: Dockerfiles and environment setup. Dockerfile means a recipe for building a container environment (构建容器环境的配方).
- `reports/`: daily reports, weekly reports, and occasional progress reports.
- `web_code/`: the web application that displays cancer data and analysis reports. It is served through the Node service in the Jupyter container.

## File Placement Rules

- Put all Jupyter notebooks and Jupyter support code in the local project directories, especially `py_code/script/` when they process data.
- Put all `web_code` files in the local `web_code/` directory.
- Also make sure required Jupyter and `web_code` files are available inside the relevant container, using the project's existing mount or copy pattern.
- After each web development task, sync the updated `web_code` files to the container that runs the Node service; do not leave changes only in the local directory.
- Keep data out of `public/` and out of GitHub unless the user explicitly says a small sample is safe to publish.
- Before creating a new directory, check whether an existing directory above already fits the work.

## Reports

- When asked to prepare a daily report, summarize the day's work from all available chat records and project changes.
- Put daily and weekly reports under `reports/`.
- Write reports mainly in English, with optional Chinese notes only when paired with English.
- Include what was done, what was learned, problems encountered, next steps, and any files or outputs created.

## Working Style For This Project

- When editing code or notebooks, preserve existing project layout and do not move data into Git-tracked locations.
- When writing analysis explanations, make the science understandable for a Grade 11 student and define advanced terms in parentheses.
- When working with containers, check the existing Docker/container pattern before changing paths, mounts, ports, or storage.
- When touching the web app, keep it in `web_code/` locally, sync it to the container after development, and verify it can run from the Jupyter container's Node service when practical.
