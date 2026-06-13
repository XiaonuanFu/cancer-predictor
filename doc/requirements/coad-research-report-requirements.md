# COAD Research Report Requirements

Last updated: 2026-06-13

## Requirement Source

This document records the project direction of turning the COAD work into a research-style report, not only a prediction model.

COAD means colon adenocarcinoma, a type of colon cancer. The report should use TCGA-COAD data to study clinical and molecular patterns in colon cancer, then use a prediction model as one part of a broader analysis.

Chinese note: 这个项目不需要只写成"我做了一个预测模型"。更好的方向是"我对 TCGA-COAD 结肠癌数据进行了临床和分子层面的综合分析，并用机器学习模型辅助解释风险或分类"。

English note: The project should not be framed only as "I built a prediction model." A stronger framing is: "I performed an integrated clinical and molecular analysis of TCGA-COAD colon cancer data, with machine learning used as one supporting method."

## Recommended Project Positioning

Recommended title:

> Integrated Clinical and Molecular Analysis of Colon Adenocarcinoma Using TCGA-COAD Data

Alternative student-friendly title:

> Exploring Clinical and Genetic Factors Associated with Colon Adenocarcinoma Prognosis

Core goal:

> Analyze TCGA-COAD data to identify clinical variables, gene-expression patterns, mutation features, and interpretable machine-learning signals associated with colon adenocarcinoma status or prognosis.

The report should claim to:

- Analyze clinical data, such as age, sex, tumor stage, survival time, and vital status.
- Analyze molecular data, such as gene expression and mutation records.
- Compare tumor and normal samples when suitable controls are available.
- Explore survival-related or risk-related patterns.
- Build a research-only prediction model as one part of the full analysis.
- Explain important features biologically, especially when they connect to known colon cancer biology.

The report should not claim to:

- Diagnose cancer for real patients.
- Predict whether a healthy person will develop cancer in the future.
- Prove that one gene directly causes colon cancer based only on this analysis.
- Replace clinical decision-making.

## Research Questions

The report should focus on two to four clear research questions. Recommended questions:

- What clinical factors are associated with COAD patient survival?
- Which genes show abnormal expression patterns in COAD tumor samples compared with normal samples?
- Which genes are frequently mutated in COAD, and do they match known colorectal cancer biology?
- Can machine learning help classify tumor versus normal samples or divide patients into risk groups?
- Are the model's important features biologically meaningful?

Chinese note: research question 是"研究问题"，也就是这篇报告真正想回答的问题。

English note: A research question is the main question the report tries to answer.

## Analysis Modules

### 1. Clinical Data Analysis

Purpose:

Describe the patient cohort and look for clinical patterns.

Required analyses:

- Patient age distribution.
- Sex distribution.
- Tumor stage distribution.
- Survival time and vital status summary.
- Missing-value summary for important clinical fields.

Optional analyses:

- Compare survival across tumor stages.
- Compare age distribution across tumor stages.
- Test whether advanced-stage patients have worse outcomes.

Key terms:

- Clinical variable: a medical feature of a patient, such as age or stage.
- Tumor stage: how far the cancer has developed or spread.
- Prognosis: the expected future outcome of a disease.

### 2. Survival Analysis

Purpose:

Study whether different patient groups have different survival outcomes.

Required analyses:

- Kaplan-Meier survival curves for tumor stage groups if the data quality allows.
- Survival comparison between early-stage and late-stage patients.
- Clear explanation of censored data.

Optional analyses:

- Survival comparison between high-expression and low-expression groups for selected genes.
- Survival comparison between machine-learning high-risk and low-risk groups.
- Cox regression if time allows.

Key terms:

- Survival analysis: a method for studying how long patients survive and what factors are related to survival.
- Kaplan-Meier curve: a curve showing the percentage of patients still alive over time.
- Censored data: a patient record where the final event is unknown, for example because the patient was still alive at last follow-up.
- Cox regression: a statistical model for testing whether variables are associated with survival time.

### 3. Gene Expression Analysis

Purpose:

Identify genes with different activity levels in tumor and normal samples.

Required analyses:

- Tumor versus normal expression comparison when suitable normal data is available.
- Differential expression analysis to identify upregulated and downregulated genes.
- Volcano plot for differential expression results.
- Heatmap for top differentially expressed genes.

Optional analyses:

- Principal component analysis, also called PCA, to visualize whether tumor and normal samples separate.
- Gene-level explanation for selected top genes.
- Compare model-important genes with differentially expressed genes.

Key terms:

- Gene expression: how active a gene is in a cell.
- Differential expression analysis: finding genes whose expression levels are clearly different between two groups.
- Upregulated gene: a gene with higher expression in one group.
- Downregulated gene: a gene with lower expression in one group.
- Volcano plot: a plot that shows both expression difference size and statistical significance.
- Heatmap: a color-based chart that shows high and low values across many genes and samples.
- PCA: a method that reduces many gene measurements into a few summary axes for visualization.

### 4. Mutation Analysis

Purpose:

Study which genes are commonly mutated in COAD and whether they match known colorectal cancer biology.

Required analyses:

- Most frequently mutated genes in COAD.
- Mutation count per patient if mutation data quality allows.
- Short biological explanation of classic colorectal cancer genes, such as APC, TP53, and KRAS, if they appear in the data.

Optional analyses:

- Compare mutation burden across tumor stages.
- Compare survival between high-mutation and low-mutation groups.
- Visualize top mutated genes with a bar chart or oncoplot if available.

Key terms:

- Mutation: a DNA sequence change.
- Mutation burden: the total number of mutations in a sample or patient.
- Oncoplot: a chart showing mutation patterns across genes and patients.

### 5. Pathway Analysis

Purpose:

Connect gene-level findings to biological processes.

Required analyses:

- Select top differentially expressed genes or important model genes.
- Perform pathway enrichment analysis if available.
- Explain the most relevant pathways in simple biological language.

Recommended pathway topics:

- Cell cycle: the process of cell growth and division.
- DNA repair: how cells fix DNA damage.
- Immune response: how the body recognizes and responds to abnormal cells.
- Wnt signaling pathway: a cell communication pathway that is especially important in colorectal cancer.

Key terms:

- Pathway: a group of genes working together in a biological process.
- Enrichment analysis: a method that checks whether a gene list contains more genes from a pathway than expected by chance.

### 6. Machine Learning And Model Interpretation

Purpose:

Use machine learning as a supporting tool, not the whole project.

Recommended first model task:

- COAD tumor versus normal classification using RNA expression features.

Optional later model tasks:

- Early-stage versus late-stage classification.
- High-risk versus low-risk grouping.
- High mutation burden versus low mutation burden prediction.

Required model outputs:

- Train/test split description.
- Accuracy, F1 score, ROC-AUC, PR-AUC, and confusion matrix when appropriate.
- Feature importance or coefficient table.
- Biological explanation of at least 10 important genes or features.

Recommended interpretation methods:

- Logistic regression coefficients.
- Random forest feature importance.
- SHAP analysis if time allows.

Key terms:

- Machine learning: training a program to find patterns from data.
- Feature: an input variable used by a model, such as one gene's expression level.
- Feature importance: a score describing which inputs matter most to the model.
- SHAP analysis: a method for explaining how each feature changes a model's prediction.

## Recommended Report Structure

The final report should be written mainly in English.

Suggested sections:

1. Abstract
2. Introduction
3. Research Questions
4. Data Sources
5. Methods
6. Results
7. Discussion
8. Limitations
9. Conclusion
10. References

Minimum content by section:

- Abstract: summarize the purpose, data, methods, key findings, and conclusion.
- Introduction: explain COAD, TCGA, and why colon cancer analysis matters.
- Research Questions: list two to four focused questions.
- Data Sources: describe TCGA-COAD clinical, expression, and mutation data used in the project.
- Methods: explain data cleaning, statistical analysis, survival analysis, gene expression analysis, mutation analysis, and machine learning.
- Results: show the main figures and tables.
- Discussion: explain what the findings may mean biologically.
- Limitations: explain missing data, sample imbalance, non-causal interpretation, and research-only status.
- Conclusion: summarize the most important findings and future directions.

## Suggested Figures And Tables

Recommended figures:

- Patient age distribution histogram.
- Tumor stage distribution bar chart.
- Kaplan-Meier survival curve by stage.
- Tumor versus normal PCA plot.
- Differential expression volcano plot.
- Top gene expression heatmap.
- Top mutated genes bar chart.
- Model confusion matrix.
- ROC curve and PR curve.
- Feature-importance plot.

Recommended tables:

- Clinical cohort summary table.
- Differentially expressed genes table.
- Top mutated genes table.
- Model performance comparison table.
- Important model features with biological notes.

## Success Criteria

The project direction is successful if it produces:

- A clear research question and report title.
- A reproducible data-analysis workflow.
- At least three major analysis modules beyond model training.
- Multiple figures that explain the COAD dataset.
- One baseline prediction model with interpretable results.
- A discussion that connects statistics and machine learning results back to colon cancer biology.
- A limitations section that avoids exaggerated medical claims.

## Recommended Next Steps

1. Confirm which COAD clinical, expression, mutation, and normal-sample tables are cleanest in the local PostgreSQL databases.
2. Create a Jupyter notebook or Python script for clinical summary and survival analysis.
3. Create a second notebook or script for expression and mutation analysis.
4. Reuse the existing model requirements document for the tumor-versus-normal machine-learning module.
5. Start drafting the final English research report as results are generated.

