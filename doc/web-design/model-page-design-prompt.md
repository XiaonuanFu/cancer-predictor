# Model Page Revision Prompt

Updated: 2026-06-25

Use this prompt to revise the Model page of the COAD Project website, `web_code/public/model.html`. Do not implement the page from this document alone unless the user explicitly asks for code changes.

Chinese request summary: 设计 Model 网页开发提示词，要求页面风格与 Overview 和 COAD Data 统一；hero 文案解释项目目的和模型开发过程；说明使用 Logistic Regression、Random Forest、Linear SVM 三个机器学习模型；不要把 `metrics`、`confusion matrix`、`important features` 做成三个 View 按钮，而是放在同一页面中同时展示和比较。

English request summary: This document is a development prompt for a later Model page revision. The Model page should match the Overview and COAD Data style, explain why the prediction model was built, explain the model-building process and limitations, compare Logistic Regression, Random Forest, and Linear SVM, and show metrics, confusion matrices, and important features together in one view.

## Copy-Paste Prompt

Revise the Model page of the COAD Project website, `model.html`, using the rules below.

### Scope

- Only revise the Model page and the minimum shared CSS/JavaScript/data needed for that page.
- Keep the website English-first. If Chinese helper text is added, include the same meaning in English.
- Keep the page read-only and educational. It must not allow visitors to upload data, edit data, or receive medical diagnosis.
- Do not expose raw local database paths, database credentials, private notebooks, or full raw expression matrices.
- Match the visual style of the existing Overview and COAD Data pages: same header, same navigation, same typography scale, similar spacing, restrained scientific color use, and compact dashboard layout.

### Page Goal

The Model page should answer these questions quickly:

1. Why did I build a cancer prediction model?
2. What data did I try first, and why did I change the data choice?
3. Which three machine learning models did I compare?
4. How well did each model perform?
5. What are the model limitations and what can be improved next time?

Machine learning means training a program to find patterns from data.

### Required Hero Copy

Use a concise hero section near the top of the page. The hero should not feel taller or more decorative than the Overview page. Keep it aligned with the same scientific project style.

Required message:

- This project combines biology and computer science.
- Programming is not only for solving logical problems; it can also be used as a scientific tool to model and predict biological patterns.
- Large cancer sequencing datasets make it possible to build more intelligent programs for research.
- Modern biology and medicine increasingly rely on computational analysis and machine learning.
- AI can detect malignant patterns in data faster, which may save researchers time and may help patients receive earlier treatment in real clinical settings.
- This project is exploratory and educational only. It is not a clinical diagnosis tool.

Suggested hero text:

> I built this prediction model because it connects my interests in biology and computer science. Through programming, I learned that code can be more than a way to solve logic problems; it can also become a scientific tool for modeling biological patterns. Cancer research now produces large sequencing datasets, and these datasets make it possible to train programs that search for disease-related signals. This project explores how machine learning can classify COAD tumor and normal samples from gene expression data, while keeping the result as research-only rather than a medical diagnosis.

### Required Model Process Copy

Add a clear section explaining the process and data-choice history. Keep the writing honest and easy for a high school audience.

Required points:

- At first, the model used data from TCGA and UCSC Xena.
- That version reached 100% accuracy.
- 100% accuracy is not automatically good. In this project, it was a warning sign that the model might be learning the difference between data sources or pipelines, instead of learning true tumor vs normal biology.
- To make the model more reliable, the project changed to a TCGA-only version.
- The current TCGA-only model uses 471 primary tumor samples and 41 solid tissue normal samples.
- The 41 normal samples are a limitation because the normal class is small. One mistake in the normal group can change the score a lot.
- Next improvements should include more normal samples, external validation data, stronger batch-effect checks, and more careful reporting of balanced accuracy and normal recall.

Batch effect means a technical difference caused by data being produced in different experiments, labs, or processing pipelines.

Suggested process text:

> My first model combined TCGA data with UCSC Xena data, and the result showed 100% accuracy. Although this looked impressive, it made the model less trustworthy because it might have learned dataset-source differences instead of real cancer biology. After that, I chose to use only TCGA COAD data. This made the comparison cleaner, but it also created a new limitation: the TCGA-only normal group has only 41 samples, compared with 471 tumor samples. In the future, I would improve this model by adding more normal samples, testing it on outside datasets, and checking batch effects more carefully.

### Models To Compare

The page must mention and compare all three models:

- Logistic Regression: a simple linear classification model.
- Random Forest: a model that combines many decision trees.
- Linear SVM: a linear support vector machine, a model that tries to separate groups with a boundary.

Do not present Random Forest as the only model, even if it has the best score in the current test split. The page should show that the project compared multiple baseline models.

### Required Data Summary

Show a compact dataset summary near the hero or process section:

| Item | Value |
|---|---:|
| Tumor samples | 471 |
| Normal samples | 41 |
| Shared genes before filtering | 19,938 |
| Model genes after filtering | 19,486 |
| Task | COAD tumor vs normal classification |
| Input | TCGA-only COAD gene expression |
| Output | Tumor-like or normal-like prediction |

Use these values only for the Model page context. Do not mix them with the COAD Data page RNA expression report counts, which use a different report context.

### Main View Requirement

Do not make `Metrics`, `Confusion matrix`, and `Important features` into three separate View buttons or tabs.

Instead, show all three result types together in one continuous view:

1. Metrics comparison.
2. Confusion matrix comparison.
3. Important features comparison.

Preferred layout:

- Use a three-column model comparison on desktop:
  - Column 1: Logistic Regression.
  - Column 2: Random Forest.
  - Column 3: Linear SVM.
- Inside each model column, show:
  - A compact metrics block.
  - A mini confusion matrix.
  - Top important features.
- On mobile, stack the three model columns vertically.

Alternative layout if the columns become too crowded:

- Use one metrics comparison table across the three models.
- Below it, show three confusion matrices in a row.
- Below that, show three important-feature lists in a row.
- Keep all three sections visible on the same page without View tabs.

### Metrics Requirements

Display these metrics for each model:

- Accuracy: proportion of all predictions that are correct.
- Balanced accuracy: average performance across tumor and normal classes, useful when classes are imbalanced.
- Precision: among predicted tumor samples, the proportion that are true tumor.
- Recall: among actual tumor samples, the proportion correctly identified.
- F1 score: a combined score using precision and recall.
- ROC-AUC: how well the model separates tumor and normal across thresholds.

Use simple tooltips or short helper text for metric definitions. Do not assume visitors already know machine learning metrics.

Current values from the frontend data:

| Model | Accuracy | Balanced accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.9417 | 0.9684 | 1.0000 | 0.9368 | 0.9674 | 1.0000 |
| Random Forest | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Linear SVM | 0.9417 | 0.9684 | 1.0000 | 0.9368 | 0.9674 | 1.0000 |

Important copy rule: If the page shows perfect or near-perfect scores, also show a warning that high scores can happen when the task is too easy, the test set is small, or hidden data-source differences exist.

### Confusion Matrix Requirements

Show one confusion matrix for each model in the same result view.

Use this label order:

- Rows: actual normal, actual tumor.
- Columns: predicted normal, predicted tumor.

Current matrices:

| Model | Actual normal -> Predicted normal | Actual normal -> Predicted tumor | Actual tumor -> Predicted normal | Actual tumor -> Predicted tumor |
|---|---:|---:|---:|---:|
| Logistic Regression | 8 | 0 | 6 | 89 |
| Random Forest | 8 | 0 | 0 | 95 |
| Linear SVM | 8 | 0 | 6 | 89 |

Explanation to include:

> A confusion matrix shows where a model was correct or wrong. The diagonal cells are correct predictions; off-diagonal cells are mistakes.

### Important Features Requirements

Show important features for all three models, not only the selected/best model.

Use model-specific wording:

- For Logistic Regression and Linear SVM, positive or negative weights show which direction the feature pushed the prediction.
- For Random Forest, feature importance shows how much the gene helped tree splits. It is relative within that model.

Current top features from the frontend data:

Logistic Regression:

- OTOP3
- DHRS7C
- PRL
- DAO
- MMP27
- FAM180B
- RIMS1
- CCKAR
- VEGFD
- OTOP2

Random Forest:

- LGI1
- PPM1H
- HPSE2
- IL6R
- DDX56

Linear SVM:

- OTOP3
- DHRS7C
- PRL

If more important-feature data is available later, show the top 10 genes for each model. Add search only if it does not make the comparison harder to scan.

Important explanation:

> Important features are predictive signals, not proof that a gene causes cancer.

### Limitation And Future Improvement Section

Add a short, honest limitation section near the results.

Required limitations:

- This is exploratory research and not medical diagnosis.
- TCGA-only normal samples are limited to 41 solid tissue normal samples.
- The classes are imbalanced: 471 tumor samples vs 41 normal samples.
- 100% accuracy in the earlier TCGA + UCSC Xena version suggested possible overfitting or batch-effect learning.
- Important genes should be interpreted as model signals, not causal proof.

Required future improvements:

- Add more normal samples from carefully matched sources.
- Test on an external validation dataset.
- Check batch effects more carefully.
- Compare results with biological literature.
- Report balanced accuracy, normal recall, and confusion matrices, not accuracy alone.

Overfitting means a model learned the training data too closely and may not work well on new data.

### Style Requirements

- Match the Overview and COAD Data page font sizes, spacing, and restrained scientific tone.
- Keep the page compact and readable, closer to a research dashboard than a marketing page.
- Use the same site header and navigation.
- Avoid oversized cards, decorative sections, or a very tall hero.
- Avoid putting cards inside cards.
- Keep chart/table labels readable on desktop and mobile.
- Use quiet borders, clean white/light backgrounds, and the existing green/ink accent system from the website.
- Keep the Model page visually aligned with the COAD Data page's compact sidebar/content rhythm, but do not add a left View menu for metrics/matrix/features.

### Implementation Notes

- Remove or hide the current `View` button group if it only switches between `Metrics`, `Confusion matrix`, and `Important features`.
- Keep all model comparison data in `web_code/public/data/coad-project-data.json` or another safe static data source. Do not query raw private database tables directly for this page.
- If JavaScript renders the model section, update it so it renders all three models at once.
- If CSS currently assumes a selected model only, update it to support three side-by-side model comparison panels.
- Ensure the page still works without horizontal overflow on mobile.

### Final Self-Check

Before finishing the Model page revision, check:

- The Model page style matches Overview and COAD Data.
- The hero explains why the model was built.
- The process section explains TCGA + UCSC Xena 100% accuracy as a reliability warning.
- The page says the current version uses TCGA-only data.
- The page states 471 tumor samples and 41 normal samples.
- Logistic Regression, Random Forest, and Linear SVM are all shown.
- Metrics, confusion matrices, and important features are visible together, without View tabs.
- The limitation section clearly says the project is research-only and not a medical diagnosis tool.
