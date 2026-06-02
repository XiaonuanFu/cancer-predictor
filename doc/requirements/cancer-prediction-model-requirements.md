# COAD Cancer Prediction Model Requirements

Last updated: 2026-05-29

## Requirement Source

This requirements document consolidates earlier project discussions around one core scope constraint:

> Keep the model research scope within TCGA-COAD colon cancer data. Do not build a pan-cancer or multi-cancer classifier.

The earlier project framing included these decisions:

- The project owner is currently a high school sophomore.
- The goal is to build a research project that can be shown in college application essays or activity records.
- The original idea was to infer cancer likelihood from existing cancer sequence data.
- The local container already contains TCGA PanCanAtlas cancer sequencing data and TCGA-COAD normal-sample data.
- A COAD sequencing and multi-omics integrated analysis report already exists.
- Stage 1 should first build a runnable model using simple TCGA COAD data.
- Stage 2 can use the more complex UCSC Xena TCGA-GTEx Toil dataset, still limited to colon cancer or colon-tissue questions.

Therefore, this project should not be defined as "multi-cancer recognition" or "pan-cancer classification." It should be defined as:

> A project for tumor/normal classification, molecular-feature prediction, and key-gene interpretation using COAD colon cancer data.

## Confirmed Implementation Decisions

- The first model version should prioritize RNA expression features. Do not mix mutation, CNV, methylation, or other multi-omics features into the first baseline.
- Normal samples should be selected from `tcga_coad.star_counts_with_metadata` where `sample_type = 'Solid Tissue Normal'`.
- The first normal-expression field should be `tcga_coad.star_counts_with_metadata.tpm_unstranded`.
- Tumor samples should be selected from `bio_tcga` COAD cancer samples. Use `bio_tcga.tcga_cdr_tcga_cdr WHERE type = 'COAD'` to identify COAD patients, then join to RNA expression samples in `bio_tcga`.
- The first tumor RNA expression source should be `bio_tcga.matrix_rnaseq_gene_expression` plus `bio_tcga.matrix_rnaseq_gene_expression_samples`.
- The first task is fixed as COAD `tumor vs normal` binary classification.
- Python processing may apply statistical transformations such as `log2(TPM + 1)`, scaling, and feature filtering. Raw database tables and raw source files must not be modified.
- The first version should use only shared, alignable protein-coding gene symbols present on both the tumor and normal sides.
- `train/test split` and random seeds have no special project constraint. Use `test_size=0.2` and `random_state=42` by default, and save the split results.
- Baseline models are limited to logistic regression, random forest, and linear SVM. XGBoost is not required for the first version.
- The main deliverable is a research report, with notebooks and Python scripts as reproducible support.
- The model source directory should be `code/coad-predictor-model/`. It should also be published to the runnable Jupyter container directory `/workspace/coad-predictor-model/`.
- Report language should now be English. Key scientific terms and model metrics should remain in their standard English form.

## Project Positioning

### Recommended Project Title

> A Machine Learning Model for Tumor-Normal Classification in TCGA-COAD Using Gene Expression Profiles

### Core Goal

Within the COAD colon cancer scope, use public omics data to build a research-oriented machine learning model that uses molecular features to classify whether a sample is closer to colon cancer tumor tissue or normal colon tissue. The project should also explain which genes or molecular features contribute most strongly to the prediction.

The project should not claim to:

- Predict whether a healthy person will develop cancer in the future.
- Take any unknown DNA sequence and directly output cancer probability.
- Identify all cancer types.
- Provide clinical diagnosis or treatment decisions.

The project should claim to:

- Train a tumor/normal classifier from RNA expression features within TCGA-COAD data.
- Use cancer sequencing data in `bio_tcga` as the tumor source and normal samples in `tcga_coad` as the normal source for the first baseline.
- Use UCSC Xena TCGA-GTEx Toil colon-related data as a Stage 2 extension.
- Explain important genes biologically and present a complete workflow suitable for a high school research project.

## Existing Local Foundation

The local project already has COAD context and data preparation work:

- A report-generation script exists for a `TCGA COAD sequencing and multi-omics integrated analysis` report.
- That report uses COAD clinical data, MC3 mutation data, multi-omics coverage information, and sample-quality annotations.
- Recorded COAD report statistics include 459 COAD clinical patients, 277,114 MC3 mutation records, 406 tumor samples, 404 mutated patients, and 19,586 mutated genes.
- The current data split is: `tcga_coad` stores COAD normal-sample data, while `bio_tcga` stores cancer sequencing data.
- `bio_tcga` can provide COAD tumor samples, mutation information, clinical information, and existing PanCanAtlas omics matrices.
- `tcga_coad` provides COAD normal controls.
- Stage 1 should align COAD cancer/tumor samples from `bio_tcga` with normal samples from `tcga_coad` into one feature matrix.

## Feasibility And Difficulty

### Overall Judgment

The project is feasible. It is moderately difficult, but the COAD-only scope makes it clearer and more suitable for a high school research project.

Reasons it is feasible:

- COAD is a single, well-defined cancer type.
- Local data already includes COAD cancer sequencing data, normal-sample data, clinical information, and mutation information.
- Classification from expression matrices is more appropriate at this stage than starting from raw FASTQ/BAM reads.
- Tumor/normal classification is intuitive and explainable to non-specialist readers.
- Key-gene interpretation can connect machine learning results to colon cancer biology.

Main challenges:

- TCGA-COAD normal samples are much fewer than tumor samples, so the classes are imbalanced.
- A single-cancer COAD task has fewer samples than pan-cancer tasks and is more prone to overfitting.
- Tumor and normal samples come from different schemas, so gene IDs, expression units, pipelines, and sample origins must be checked carefully.
- Stage 2 GTEx normal colon tissue introduces TCGA-versus-GTEx source differences.
- Important genes show statistical association, not causal proof.

### Directions Not Recommended For The First Version

- Pan-cancer classification, such as BRCA/LUAD/COAD/SKCM multi-cancer classification.
- Re-aligning raw FASTQ/BAM and re-calling variants.
- Predicting future cancer risk for ordinary people.
- Starting with deep learning or complex multi-omics fusion.
- Claiming cancer detection without normal controls.

## Two-Stage Build Plan

### Stage 1: Simple TCGA-COAD Model

The Stage 1 goal is to use locally available TCGA-COAD/GDC COAD data to build a complete, credible, and interpretable baseline model.

Recommended first task:

- COAD tumor vs normal classification.

Definition:

- Input data: COAD-related expression or sequencing features. The first version should prioritize alignable RNA expression features.
- Tumor samples: COAD cancer/tumor samples selected from `bio_tcga`.
- Normal samples: COAD normal samples selected from `tcga_coad`.
- Labels: `tumor` or `normal`.
- Model output: whether a COAD sample looks more like tumor tissue or normal colon tissue.
- Model types: logistic regression, random forest, and linear SVM.
- Key interpretation: whether important genes relate to colon cancer, cell proliferation, WNT pathway, DNA repair, immune microenvironment, or similar biology.

Optional Stage 1 extensions:

- Define high mutation burden vs low mutation burden from COAD mutation data and train an expression or mutation-feature model.
- Define early-stage vs late-stage labels from clinical staging, while noting missing labels and class imbalance.
- Build a prognosis prototype from survival status or risk grouping. This is harder than tumor/normal classification and should not be the first main task.

Stage 1 success criteria:

- Generate a feature matrix from local COAD expression data.
- Clearly record that tumor samples come from `bio_tcga` and normal samples come from `tcga_coad`.
- Train a baseline tumor/normal classifier.
- Output accuracy, F1, ROC-AUC, PR-AUC, and confusion matrix.
- Explain at least 10 important genes or candidate features.
- Clearly state that the model is research-only and not for clinical diagnosis.

### Stage 2: UCSC Xena TCGA-GTEx Toil Extension

Stage 2 remains limited to COAD and colon-tissue questions. It should not expand into a pan-cancer task.

Recommended Stage 2 task:

- Compare or classify `bio_tcga` COAD tumor, `tcga_coad` normal, and GTEx colon normal samples.

Definition:

- Input data: UCSC Xena TCGA-GTEx Toil RNA-seq recompute data.
- Tumor samples: COAD tumor/cancer samples from `bio_tcga`, or matching TCGA-COAD tumor samples from Toil.
- Normal samples: first use `tcga_coad` normal samples; in Stage 2 add GTEx colon normal tissues such as Colon - Transverse and Colon - Sigmoid.
- Labels: `tumor` and `normal`, or more detailed labels such as `bio_tcga_tumor`, `tcga_coad_normal`, and `GTEx_normal`.
- Model output: whether a sample is closer to tumor or normal in a COAD/colon-tissue setting.

Stage 2 must check:

- Whether the model is learning TCGA-versus-GTEx source differences instead of cancer biology.
- Whether GTEx colon normal and `tcga_coad` normal samples separate strongly in expression space.
- Model performance grouped by tissue source, dataset source, and sample type.
- Whether performance changes abnormally when dataset-source-related variables are added or removed.

Stage 2 success criteria:

- Build a sample mapping and label table for TCGA-COAD and GTEx colon normal data.
- Reproduce the Stage 2 feature matrix construction.
- Train a tumor/normal model and report grouped metrics.
- Provide a diagnosis of batch effect or dataset-source confounding.

## Data Requirements

### Stage 1 Required Data

The Stage 1 scope is COAD only:

- COAD cancer sequencing data in `bio_tcga`.
- `bio_tcga` tables needed for COAD tumor-sample filtering, clinical linkage, and mutation interpretation.
- COAD normal-sample data in `tcga_coad`.
- Alignable sample metadata, gene IDs, gene names, and expression/sequencing features across both schemas.
- COAD clinical tables for patient IDs, sample filtering, and downstream interpretation.

Local sources currently available:

- `bio_tcga`: cancer sequencing and PanCanAtlas data for COAD tumor/cancer samples.
- `tcga_coad`: COAD normal-sample data for normal controls.
- `data/gdc_tcga_coad_star_counts/`: local COAD STAR counts files. Confirm which schema and samples are currently imported before using.
- `scripts/import_tcga_coad_star_counts.py`: existing import script for COAD STAR counts. If reused, confirm the target schema and data ownership match the current plan.

### Minimum Stage 1 Fields

Each sample should include at least:

- `file_id`
- `case_submitter_id`
- `sample_submitter_id`
- `sample_type`
- `source_schema`, such as `bio_tcga` or `tcga_coad`
- `source_table` or source file name
- alignable gene expression or sequencing features
- tumor/normal label
- source file name and md5

### Optional COAD Auxiliary Data

These data are not required as Stage 1 model inputs, but can support explanation or extensions:

- MC3 MAF mutation data
- COAD clinical staging
- overall survival information
- sample-quality annotations
- CNV, methylation, miRNA, RPPA, or other multi-omics data

### Stage 2 Additional Data

Stage 2 should select COAD or colon-tissue samples from UCSC Xena TCGA-GTEx Toil:

- Toil gene expression matrix, for example `TcgaTargetGtex_gene_expected_count.gz`
- phenotype/metadata file, for example `TcgaTargetGTEX_phenotype.txt.gz`
- TCGA-COAD tumor samples
- GTEx colon normal samples, preferably Colon - Transverse and Colon - Sigmoid
- dataset label: TCGA or GTEx; TARGET is not included in the first COAD model by default
- tissue type
- tumor/normal label
- gene identifier and gene symbol

### External Validation Data

If time allows, search for additional COAD or colorectal cancer datasets for external validation:

- Colon cancer expression datasets in GEO.
- Colorectal cancer cohorts in ICGC.
- Colorectal cancer proteomics or multi-omics data in CPTAC.

External validation is not required for the first version, but it would substantially strengthen the project.

## Python And Jupyter Container Requirements

Model building should be done in Python and run inside the Jupyter container.

Runtime requirements:

- Jupyter container name: `bio-jupyter`
- Container working directory: `/workspace`
- Host directory: `docker_storage/jupyter/`
- Jupyter URL: `http://127.0.0.1:8888/lab?token=bioanalysis`
- Main Python dependencies: `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `plotly`, `sqlalchemy`, `psycopg2-binary`

Code directory requirements:

- Repository source directory: `code/coad-predictor-model/`
- Jupyter runtime directory: `/workspace/coad-predictor-model/`
- Host-side Jupyter publish directory: `docker_storage/jupyter/coad-predictor-model/`
- `code/coad-predictor-model/` is the primary maintenance location. After changes, sync it to `docker_storage/jupyter/coad-predictor-model/` so the Jupyter container can run it directly.

Suggested repository source layout:

```text
code/coad-predictor-model/
  notebooks/                 Jupyter notebooks for exploration and training
  src/                       reusable Python modules
  reports/                   lightweight model reports and notes
  README.md                  run instructions
```

Suggested Jupyter runtime layout:

```text
/workspace/coad-predictor-model/
  notebooks/
  src/
  data/                      intermediate feature tables exported from PostgreSQL, usually not committed
  models/                    trained local model files, usually not committed
  reports/                   metrics, figures, interpretation tables, and model reports
```

Implementation requirements:

- The first version may start in notebooks, but core logic should be organized into reusable functions.
- Data preparation, model training, model evaluation, and result interpretation should be separate, clear steps.
- Do not hard-code database passwords, personal absolute paths, or one-off experimental outputs in model logic.
- Large intermediate data, model files, and figures should be saved under `docker_storage/jupyter/coad-predictor-model/` by default and should not be committed.
- Important final method notes and requirements documents should remain under `doc/`.
- Provide a sync method from repository source to the Jupyter container directory, such as `rsync` or a later script.
- Do not create the directory at the requirements stage. Create and sync it when model implementation officially starts.

Suggested publish command:

```bash
rsync -a --delete code/coad-predictor-model/ docker_storage/jupyter/coad-predictor-model/
```

## Python Data Preparation Requirements

Python code should read imported COAD data from PostgreSQL first, rather than repeatedly parsing large raw TSV files in notebooks.

Database connection:

- PostgreSQL host inside container: `bio-postgres`
- Database: `bio`
- User: `bio`
- Local development password: `bioanalysis`
- Main schemas: `bio_tcga` and `tcga_coad`
- `bio_tcga` is used for COAD cancer sequencing data and tumor-sample information.
- `tcga_coad` is used for COAD normal-sample data.
- Python data preparation must preserve `source_schema` to prevent later confusion between tumor and normal origins.

Stage 1 data preparation workflow:

1. Use `sqlalchemy` or `psycopg2` to read COAD tumor RNA expression sample metadata from `bio_tcga.matrix_rnaseq_gene_expression_samples`.
2. Read tumor RNA expression matrix values from `bio_tcga.matrix_rnaseq_gene_expression` and align them with the samples table by sample index.
3. Use `sqlalchemy` or `psycopg2` to read COAD normal samples from `tcga_coad.star_counts_with_metadata`, filtering to `sample_type = 'Solid Tissue Normal'` and using `tpm_unstranded` as the expression field.
4. Build a unified sample table. Mark `bio_tcga` samples as `tumor` and `tcga_coad` samples as `normal`.
5. Generate sample-level metadata containing at least `sample_id`, `case_submitter_id`, `sample_submitter_id`, `sample_type`, `source_schema`, `source_table`, and `label`.
6. Convert alignable gene expression features from both schemas into a sample-by-feature `pandas.DataFrame`.
7. Align gene identifiers and gene symbols. Keep only protein-coding gene symbols present and consistently defined on both tumor and normal sides.
8. Apply expression transformations such as `log2(TPM + 1)` only to Python-generated intermediate feature tables, not to raw database tables or raw files.
9. Filter low-expression, low-variance, or high-missingness genes/features.
10. Save processed feature matrices and label tables, for example:
   - `/workspace/coad-predictor-model/data/coad_tpm_log2_features.parquet`
   - `/workspace/coad-predictor-model/data/coad_tumor_normal_labels.csv`
   - `/workspace/coad-predictor-model/data/coad_selected_genes.txt`

Normal-sample filtering SQL:

```sql
SELECT *
FROM tcga_coad.star_counts_with_metadata
WHERE sample_type = 'Solid Tissue Normal';
```

Tumor-sample filtering SQL reference:

```sql
WITH coad_patients AS (
  SELECT bcr_patient_barcode
  FROM bio_tcga.tcga_cdr_tcga_cdr
  WHERE type = 'COAD'
)
SELECT s.*
FROM bio_tcga.matrix_rnaseq_gene_expression_samples s
JOIN coad_patients c
  ON substring(s.sample_id from 1 for 12) = c.bcr_patient_barcode;
```

Notes:

- `bio_tcga.matrix_rnaseq_gene_expression_samples` locates COAD tumor/cancer RNA expression samples.
- Actual expression matrix values must be aligned with `bio_tcga.matrix_rnaseq_gene_expression` by sample index.
- `tcga_coad.star_counts_with_metadata.tpm_unstranded` is the first-version normal expression field.
- If a better COAD RNA expression table or view is later found in `bio_tcga`, it may replace the initial table, but the report must record the reason.

Data preparation quality checks:

- Output tumor and normal sample counts.
- Check whether `sample_id` or `file_id` is unique.
- Check whether the same `case_submitter_id` has multiple samples.
- Check that the feature matrix row count matches the label table sample count.
- Check that `source_schema` matches the label: `bio_tcga` means tumor, `tcga_coad` means normal.
- Check that tumor and normal features use the same gene identifier and a common or interpretable expression scale.
- Check for all-empty genes, constant genes, or extreme outliers.
- Record gene counts before and after filtering.

## Model Inputs And Label Definitions

### Main Task: COAD Tumor vs Normal

Input:

- RNA expression features for each COAD sample. The first version should prioritize alignable protein-coding gene expression and record the expression unit and transformation method during data preparation.

Labels:

- `tumor`: COAD cancer samples selected from `bio_tcga`.
- `normal`: COAD normal samples selected from `tcga_coad`; Stage 2 may add GTEx colon normal.

Fit for purpose:

- Best first-version task.
- Scope is fully aligned with COAD.
- The problem is clear and suitable for high school research presentation.
- It connects naturally to key-gene interpretation.

### Extension Task 1: COAD High Mutation Burden Prediction

Input:

- gene expression features
- optional mutation features

Labels:

- Calculate per-sample mutation burden from COAD MC3 MAF.
- Split into high mutation burden and low mutation burden using the median or a predefined threshold.

Notes:

- The threshold must be transparently recorded.
- High mutation burden may relate to MSI, POLE, sample quality, or other factors, so interpretation must be cautious.

### Extension Task 2: COAD Stage Or Prognosis Risk

Input:

- gene expression
- mutation
- CNV
- clinical features

Labels:

- AJCC stage
- survival time
- survival status

Notes:

- This is harder than tumor/normal classification.
- Missing labels and censoring affect analysis.
- It is not recommended as the first main task.

## Data Processing Requirements

Stage 1 must complete:

1. Confirm which `bio_tcga` tables provide COAD cancer samples and features.
2. Confirm which `tcga_coad` tables provide COAD normal samples and features.
3. Extract sample metadata from both schemas and add `source_schema` and `label`.
4. Normalize sample IDs, case IDs, gene IDs, and gene symbols.
5. Keep only features alignable between tumor and normal samples.
6. Filter non-target features, low-expression genes, low-variance genes, or features with excessive missingness.
7. Apply `log2(TPM + 1)` or equivalent scaling to expression features; record the encoding method for mutation features.
8. Run train/test split or cross-validation.
9. Ensure the same `case_submitter_id` does not appear in both train and test sets.
10. Handle tumor/normal class imbalance with class weights, stratified sampling, PR-AUC reporting, or similar methods.
11. Save processed feature tables, label tables, gene lists, sample-source tables, and data-processing records.

Stage 2 must complete:

1. Download and organize UCSC Xena TCGA-GTEx Toil expression matrices and phenotype files.
2. Select only COAD tumor, `tcga_coad` normal, and GTEx colon normal samples.
3. Align gene identifiers and gene symbols.
4. Build labels such as `bio_tcga_tumor`, `tcga_coad_normal`, and `GTEx_normal`.
5. Build a colon tissue mapping table.
6. Check whether TCGA and GTEx samples separate by dataset source in PCA/UMAP.
7. Report dataset-source confounding diagnostics separately in model evaluation.

## Feature Engineering Requirements

The first version should be simple, transparent, and interpretable:

- Main feature type: protein-coding gene TPM.
- Transformation: `log2(TPM + 1)`.
- Filtering: low expression, low variance, and excessive missingness.
- Optional: select top variable genes.
- Optional: use PCA or UMAP for visualization, not as the only evidence.
- Optional: use LASSO coefficients, random forest feature importance, or SHAP for feature interpretation.

Must avoid:

- Performing feature selection on the full dataset before train/test split.
- Including `sample_type`, `source_schema`, `source_table`, file names, or other label/source leakage fields in model inputs.
- Placing tumor and normal samples from the same case into different splits.
- Reporting only accuracy while ignoring normal-class recall.

## Model Requirements

### First-Version Baselines

Train at least one baseline model, and ideally compare:

- logistic regression with class weight
- random forest with class weight
- linear SVM with class weight

Recommended comparison roles:

- logistic regression: interpretable baseline
- random forest: nonlinear model
- linear SVM: suitable for high-dimensional expression features

### Models To Defer

The following may be future extensions but should not be first-version requirements:

- deep neural networks
- autoencoders
- multi-omics fusion models
- survival deep learning

The first version should prioritize clear scope, credible results, and complete interpretation over model complexity.

## Python Model-Building Requirements

Use `scikit-learn` as the main first-version framework.

Recommended notebook order:

1. `01_prepare_coad_data.ipynb`: read the database and generate the feature matrix and labels.
2. `02_train_baseline_models.ipynb`: train logistic regression, random forest, and linear SVM.
3. `03_evaluate_models.ipynb`: output metrics, confusion matrix, ROC curve, and PR curve.
4. `04_interpret_genes.ipynb`: extract important genes and prepare interpretation tables.
5. `05_xena_toil_extension.ipynb`: create only when Stage 2 TCGA-GTEx Toil data is used.

Recommended Python modules:

```text
/workspace/coad-predictor-model/src/
  data.py                    database reads, label construction, feature matrix generation
  preprocessing.py           log2 transformation, filtering, scaling, splitting
  train.py                   model training and parameter configuration
  evaluate.py                metrics, plots, and evaluation tables
  interpret.py               feature importance and key-gene interpretation
```

First-version training workflow:

1. Read `coad_tpm_log2_features.parquet` and `coad_tumor_normal_labels.csv`.
2. Group by `case_submitter_id` to prevent samples from the same patient entering both train and test.
3. Use `test_size=0.2` and `random_state=42` for stratified split by default. If cross-validation is used, describe it in the report.
4. Complete scaling, variance filtering, and optional feature selection inside the training set.
5. Use `class_weight="balanced"` or an equivalent strategy for tumor/normal imbalance.
6. Train logistic regression, random forest, and linear SVM.
7. Save models, metrics, and figures.

Suggested saved artifacts:

```text
/workspace/coad-predictor-model/models/
  logistic_regression.joblib
  random_forest.joblib
  linear_svm.joblib

/workspace/coad-predictor-model/reports/
  metrics_summary.csv
  confusion_matrix.png
  roc_curve.png
  pr_curve.png
  important_genes.csv
  model_run_notes.md
```

Model-building acceptance criteria:

- Notebooks can be run from the beginning to reproduce the feature matrix, models, and metrics.
- Training uses a fixed `random_state`, defaulting to `42`.
- Train and test sample IDs are saved for review.
- The metrics table includes precision and recall for both tumor and normal.
- The important-gene table includes gene symbol, importance score, direction, and a short English explanation.

## Evaluation Requirements

COAD tumor/normal classification must report at least:

- accuracy
- F1
- ROC-AUC
- PR-AUC
- confusion matrix
- tumor precision/recall
- normal precision/recall
- balanced accuracy

Special attention:

- Normal samples are few, so normal recall is important.
- If the model predicts most samples as tumor, accuracy may look acceptable while the model remains unreliable.
- Cross-validation should use stratified split or a comparable strategy.

High mutation burden or stage-extension tasks must report at least:

- accuracy
- macro F1
- confusion matrix
- precision/recall for each class
- label definitions and threshold descriptions

## Result Interpretation Requirements

Result interpretation is one of the most important parts of this project for application presentation.

Required:

- Identify genes that contribute strongly to COAD tumor/normal prediction.
- Interpret models using logistic regression coefficients, feature importance, or SHAP.
- Check whether key genes relate to colon cancer, intestinal epithelium, cell proliferation, WNT pathway, DNA repair, immune response, tumor microenvironment, or similar topics.
- Discuss model results alongside existing COAD report observations about mutation, stage, or multi-omics data.

Recommended presentation assets:

- COAD sample composition table.
- tumor/normal confusion matrix.
- ROC and PR curves.
- PCA/UMAP sample distribution plot.
- important-gene table.
- key-gene explanation table.

## Deliverables

Stage 1 deliverables:

- COAD data-processing notes.
- COAD tumor/normal feature matrix construction script or notebook.
- A baseline tumor/normal model.
- Model evaluation report.
- Key-gene interpretation table.
- A project summary suitable for college application activity descriptions.

Stage 2 deliverables:

- UCSC Xena TCGA-GTEx Toil download and filtering record.
- TCGA-COAD to GTEx colon normal sample mapping table.
- Stage 2 tumor/normal feature matrix.
- Stage 2 classification model.
- Dataset-source confounding check results.
- Stage 2 model report.

## Application Presentation Angle

The project should emphasize:

- Narrowing an overly broad medical AI idea into a verifiable scientific question within COAD colon cancer.
- Using public cancer data for a complete workflow from data cleaning to model interpretation.
- Building a baseline with TCGA-COAD first, then adding stronger normal controls from TCGA-GTEx Toil.
- Understanding sample imbalance, dataset-source confounding, and clinical-interpretation boundaries.
- Avoiding exaggerated clinical claims and presenting the model as research-only.

Avoid these phrases:

- "I built a system that can predict cancer."
- "Entering a person's sequence can determine whether they will develop cancer."
- "The model can diagnose colon cancer."
- "The model can identify all cancers."

Prefer these phrases:

- "I built a colon cancer tumor/normal classifier using TCGA-COAD gene expression data."
- "I compared several machine learning methods and focused on the imbalance between tumor and normal samples."
- "I analyzed important genes from the model and interpreted them in the context of colon cancer biology."
- "I plan to use UCSC Xena TCGA-GTEx Toil data to test whether the model is affected by dataset-source differences."

## Milestones

### Milestone 1: Confirm COAD Data Entry Points

- Confirm the tables and fields in `bio_tcga` used for COAD cancer samples.
- Confirm the tables and fields in `tcga_coad` used for COAD normal samples.
- Confirm alignable gene IDs, gene symbols, and expression/sequencing features across both schemas.
- Confirm `source_schema` and `label` mapping rules: `bio_tcga` means tumor, `tcga_coad` means normal.

### Milestone 2: Complete COAD Baseline

- Build the COAD tumor/normal label table.
- Build the `log2(TPM + 1)` feature matrix.
- Complete train/test split or stratified cross-validation.
- Train logistic regression, random forest, or linear SVM.
- Output the first metrics and confusion matrix.

### Milestone 3: Complete COAD Interpretation Analysis

- Extract important genes.
- Research colon-cancer-related background for key genes.
- Generate interpretation tables and visualizations.
- Connect the results to the existing COAD multi-omics report.

### Milestone 4: Extend To TCGA-GTEx Toil

- Download UCSC Xena TCGA-GTEx Toil data.
- Select `bio_tcga` COAD tumor, `tcga_coad` normal, and GTEx colon normal samples.
- Build the Stage 2 tumor/normal dataset.
- Train the Stage 2 model.
- Check TCGA-versus-GTEx dataset-source confounding.

### Milestone 5: Build Application Materials

- Prepare the project summary.
- Prepare the method flow diagram.
- Prepare result figures and tables.
- Prepare limitations and future work.

## Risks And Limitations

- In Stage 1, normal samples come from `tcga_coad` while tumor samples come from `bio_tcga`; the two sources may use different processing pipelines.
- A single-cancer COAD scope has limited sample size, making overfitting more likely.
- The source and definition of normal samples in `tcga_coad` must be recorded separately; they should not be assumed to represent fully healthy general-population colon tissue.
- GTEx normal and TCGA tumor samples come from different projects, so Stage 2 has a strong dataset-source confounding risk.
- Important-gene interpretation shows model association, not biological causality.
- This project is research-only and cannot be used for clinical diagnosis.

## Open Questions

- Should Stage 1 use only RNA-seq TPM, or also add MC3 mutation features?
- Should the first normal class use only `tcga_coad`, or add GTEx colon normal earlier?
- Should the feature count first be limited to top variable genes, or should all protein-coding genes be used?
- Should the key-gene interpretation generate a separate glossary?
- Should Stage 2 use both Colon - Transverse and Colon - Sigmoid from GTEx?
- Should the existing COAD integrated analysis report become a background chapter in the model report?

## Reference Data Sources

- TCGA project overview: https://www.cancer.gov/ccg/research/genome-sequencing/tcga
- GDC Data Portal documentation: https://docs.gdc.cancer.gov/Encyclopedia/pages/GDC_Data_Portal/
- UCSC Xena: https://xena.ucsc.edu/
- UCSC Xena data pages: https://xenabrowser.net/datapages/
- UCSC Toil RNA-seq recompute Zenodo long-term record: https://zenodo.org/records/10944168
