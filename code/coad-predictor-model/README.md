# COAD Tumor vs Normal Predictor

Research-first Python project for a COAD tumor/normal RNA expression classifier.

## Data Sources

- Tumor: `bio_tcga.matrix_rnaseq_gene_expression` plus `bio_tcga.matrix_rnaseq_gene_expression_samples`, filtered to COAD patients from `bio_tcga.tcga_cdr_tcga_cdr`.
- Normal: `tcga_coad.star_counts_with_metadata`, filtered to `sample_type = 'Solid Tissue Normal'`, using `tpm_unstranded`.

The model is exploratory and research-only. Tumor and normal expression sources come from different schemas/pipelines, so reports must mention possible source effects.

## Run In Jupyter Container

From the repository root on the host:

```bash
rsync -a --delete code/coad-predictor-model/ docker_storage/jupyter/coad-predictor-model/
docker exec -i bio-jupyter bash -lc "cd /workspace/coad-predictor-model && python3 -m src.pipeline all"
```

Use the `rsync --delete` command before a fresh run. It resets the Jupyter copy, so run the pipeline again afterward to regenerate `data/`, `models/`, and `reports/`.

Outputs are written under:

```text
/workspace/coad-predictor-model/data/
/workspace/coad-predictor-model/models/
/workspace/coad-predictor-model/reports/
```

## Pipeline Steps

```bash
python3 -m src.pipeline prepare
python3 -m src.pipeline train
python3 -m src.pipeline report
```

or run everything:

```bash
python3 -m src.pipeline all
```
