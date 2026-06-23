# COAD Data Page Revision Prompt

Updated: 2026-06-23

Use this prompt to revise the second website page, `web_code/public/data.html`. Do not implement the page from this document alone unless the user explicitly asks for code changes.

Chinese request summary: 第二页只改 COAD data 页面方案；本次文档要求不要直接修改网页代码。
English request summary: This document is a prompt for a later COAD data page revision; do not change the web page code during this document-only task.

## Copy-Paste Prompt

Revise the second page of the COAD Cancer Predictor website, `data.html`, using the rules below.

### Scope

- Only revise the COAD data page and the minimum shared JavaScript/CSS needed for that page.
- Keep the home page visual style, typography scale, restrained color use, and professional scientific tone.
- Keep the website English-first. If Chinese helper text is added, include the same meaning in English.
- Do not expose raw local database paths, private notebook paths, database credentials, or full raw data tables.
- Treat the page as read-only educational research content, not as a medical diagnosis tool.

### Layout Changes

1. Reduce the top title area height.
   - Remove the visible `COAD Data` kicker/title text from the top of the second page.
   - Keep the browser `<title>` and navigation label if needed, but do not show a large `COAD Data` block in the page body.
   - The first visible content should begin higher on the screen and feel aligned with the home page style.

2. Move the left menu upward and leftward.
   - Place the left menu close to the upper-left of the main content area.
   - Remove menu descriptions from the menu buttons.
   - Use only these three menu labels:
     - `Clinical`
     - `RNA expression`
     - `Mutation`

3. Merge the right side into one content area.
   - Do not split the right side into separate definition and chart panels.
   - Use one unified content panel or one continuous content region for the selected menu item.
   - Inside that region, show key numbers, charts, and explanatory notes together.

4. Map each left menu item to the correct Jupyter report:
   - `Clinical` maps to `coad_clinical_survival_report`.
   - `RNA expression` maps to `coad_gene_expression_analysis_report`.
   - `Mutation` maps to `coad_pancanatlas_mutation_landscape_report`.

### Chart Requirements

- Prefer ECharts for every chart.
- If ECharts cannot display a specialized biological chart clearly, use another professional biological visualization library, such as a heatmap, volcano plot, genome/mutation, or bioinformatics visualization library. If no suitable library is available or the chart cannot be rebuilt accurately, use a screenshot from the matching Jupyter notebook output.
- Every chart must include a short explanation below or beside it.
- Chart explanations should use simple English suitable for a high school audience. Define advanced terms in parentheses, for example: `hazard ratio (a number comparing risk between groups)`.
- Do not show charts without context; every chart needs a clear title, source report label, and one-sentence takeaway.

### Clinical Section Data

Source report: `coad_clinical_survival_report`.

Use these checked values:

| Metric | Value |
|---|---:|
| Total COAD patients | 459 |
| Patients with age | 459 |
| Patients with stage I-IV | 448 |
| Patients with usable OS | 442 |
| Observed death events | 98 |

Clinical charts to build with ECharts:

- Age distribution bar chart:
  - `<40`: 12
  - `40-49`: 43
  - `50-59`: 71
  - `60-69`: 119
  - `70-79`: 126
  - `80+`: 88
  - Explanation: Most patients are older adults, with the largest groups in `60-69` and `70-79`.
- Stage distribution bar chart:
  - Stage I: 76
  - Stage II: 178
  - Stage III: 129
  - Stage IV: 65
  - Missing/unknown stage: 11
  - Explanation: Stage II and Stage III are the largest groups in this clinical summary.
- Gender split donut or bar chart:
  - Male: 243
  - Female: 216
  - Explanation: The gender split is close, with slightly more male patients.
- Survival by stage grouped bar or line chart:
  - Stage I: 74 patients with OS, 4 death events, 1-year 97.2%, 3-year 94.6%, 5-year 78.9%.
  - Stage II: 169 patients with OS, 27 death events, 1-year 95.6%, 3-year 91.3%, 5-year 77.2%.
  - Stage III: 127 patients with OS, 31 death events, 1-year 88.2%, 3-year 71.1%, 5-year 55.0%.
  - Stage IV: 61 patients with OS, 31 death events, 1-year 68.8%, 3-year 42.3%, 5-year 37.1%.
  - Explanation: Later stages have lower survival percentages in this report.
- Prognosis factor chart:
  - Age per 10 years: hazard ratio 1.34, p = 0.0007.
  - Male vs female: hazard ratio 0.98, p = 0.9053.
  - Stage per level increase: hazard ratio 2.36, p = 0.0000.
  - Explanation: Stage relates more strongly to prognosis than gender in this analysis.

### RNA Expression Section Data

Source report: `coad_gene_expression_analysis_report`.

Use these checked values:

| Metric | Value |
|---|---:|
| Samples | 757 |
| Tumor samples | 449 |
| Normal samples | 308 |
| Genes | 17,974 |

Data sources:

- Tumor source: `bio_tcga.matrix_rnaseq_gene_expression`
- Normal source: `toil_gtex_colon_normal.expression_log2_tpm`

RNA expression charts to build with ECharts:

- Tumor vs normal sample count bar or donut chart:
  - Tumor: 449
  - Normal: 308
  - Explanation: The expression analysis compares tumor samples with normal colon-related samples.
- Differential expression category bar chart:
  - Upregulated in tumor: 14,993 genes
  - Not significant or small effect: 2,873 genes
  - Downregulated in tumor: 108 genes
  - Explanation: Differential expression means checking which genes are more or less active in tumor samples.
- Top upregulated genes horizontal bar chart:
  - ADAM6: log2 fold change 15.0982
  - EEF1A1P9: 12.8840
  - CLDN2: 11.6137
  - DPEP1: 11.3124
  - EIF5AL1: 10.6812
  - TNS4: 10.5349
  - CDH3: 10.5236
  - CLDN1: 10.4895
  - NME2: 10.4626
  - ETV4: 10.4168
  - Explanation: Positive log2 fold change means higher expression in tumor samples.
- Top downregulated genes horizontal bar chart:
  - RPL21: log2 fold change -6.2248
  - SPATA4: -4.9664
  - KRTAP13-2: -4.9009
  - FAM166B: -4.7477
  - RERGL: -4.1701
  - CYP4B1: -4.0381
  - IGSF5: -4.0126
  - ZACN: -4.0053
  - OR5K2: -3.9758
  - A4GNT: -3.6143
  - Explanation: Negative log2 fold change means lower expression in tumor samples than in normal samples.
- Volcano plot:
  - Prefer ECharts scatter plot only if the exact gene-level table is available to the frontend.
  - If ECharts cannot show this biological chart clearly, use a professional biological plotting library before falling back to the Jupyter notebook screenshot.
  - Explanation: A volcano plot shows both effect size and statistical evidence for many genes.
- Heatmap of top differentially expressed genes:
  - Prefer ECharts or a professional biological heatmap library if exact matrix data is available.
  - Otherwise, use the Jupyter notebook screenshot.
  - Explanation: A heatmap uses color to show expression patterns across samples and genes.

### Mutation Section Data

Source report: `coad_pancanatlas_mutation_landscape_report`.

Use these checked values:

| Metric | Value |
|---|---:|
| Clinical patients | 459 |
| Mutation records | 277,114 |
| Tumor samples with mutation data | 406 |
| Patients with mutation data | 404 |
| Mutated genes | 19,586 |

Mutation charts to build with ECharts:

- Variant type bar or donut chart:
  - SNP: 250,637
  - DEL: 21,166
  - INS: 5,299
  - ONP: 12
  - Explanation: SNPs are the most common variant type in this mutation dataset.
- Functional class bar chart:
  - Missense_Mutation: 144,030
  - Silent: 57,664
  - 3'UTR: 20,267
  - Frame_Shift_Del: 14,562
  - Nonsense_Mutation: 10,835
  - Intron: 8,686
  - 5'UTR: 6,607
  - Frame_Shift_Ins: 3,931
  - Splice_Site: 3,322
  - RNA: 3,125
  - Explanation: Missense mutations change one amino acid in a protein; silent mutations do not change the amino acid.
- Most frequently mutated genes horizontal bar chart:
  - APC: 291 mutated samples, 71.7%
  - TTN: 247, 60.8%
  - TP53: 226, 55.7%
  - KRAS: 176, 43.3%
  - MUC16: 140, 34.5%
  - SYNE1: 138, 34.0%
  - PIK3CA: 128, 31.5%
  - OBSCN: 122, 30.0%
  - FAT4: 116, 28.6%
  - ZFHX4: 104, 25.6%
  - Explanation: A sample can have mutations in more than one gene, so these percentages should not be added together.
- Mutation hotspot chart:
  - KRAS p.G12D: 49 mutated samples
  - BRAF p.V600E: 48
  - KRAS p.G12V: 35
  - PIK3CA p.E545K: 33
  - KRAS p.G13D: 30
  - APC p.R1450*: 26
  - TP53 p.R175H: 24
  - Explanation: A hotspot is a mutation position that appears repeatedly in different tumor samples.
- Tumor mutation burden summary:
  - Counted tumor samples: 406
  - Mean mutation records per sample: 682.5
  - Median mutation records per sample: 181.5
  - Maximum mutation records in one sample: 13,582
  - Explanation: A few samples have very high mutation counts, so the mean is much higher than the median.
- Co-mutation heatmap:
  - Prefer ECharts heatmap if the co-mutation matrix is available.
  - If ECharts cannot show this biological heatmap clearly, use a professional biological visualization library before falling back to the notebook screenshot.
  - Explanation: Co-mutation means two genes are mutated in the same sample.
- Mutation frequency by AJCC stage:
  - Prefer ECharts heatmap if the full stage-by-gene table is available.
  - If ECharts cannot show this biological heatmap clearly, use a professional biological visualization library before falling back to the notebook screenshot.
  - Explanation: This checks whether common mutation genes appear at different rates across cancer stages.

### Style Requirements

- Match the home page font sizes and spacing more closely than the current second page.
- Keep the design professional and restrained: clean background, light borders, quiet colors, no oversized decorative blocks.
- Use compact scientific dashboard spacing, but keep text readable.
- Avoid splitting content into too many cards. The left menu can be a compact sidebar; the selected content should feel like one coherent area.
- Ensure mobile layout stacks cleanly: menu on top, then unified content area.
- Do not let chart labels overlap on desktop or mobile.

### Data Quality Checks Before Finishing

Run a self-check before presenting the page:

- Clinical stage counts must add to 459: `76 + 178 + 129 + 65 + 11 = 459`.
- Clinical gender counts must add to 459: `243 + 216 = 459`.
- RNA sample counts must add to 757: `449 + 308 = 757`.
- RNA differential expression categories must add to 17,974 genes: `14,993 + 2,873 + 108 = 17,974`.
- Mutation variant types must add to 277,114 records: `250,637 + 21,166 + 5,299 + 12 = 277,114`.
- Do not mix the RNA expression report counts with the model-page counts. The existing model summary may mention 512 samples, 471 tumor, 41 normal, and 19,486 model genes; those belong to the model dataset context, not this second-page report view.
- Do not add mutation gene percentages together; one tumor sample can contain mutations in multiple genes.
- If a chart uses only top categories rather than the full table, label it as `Top categories` or `Shown categories`.
- Check all chart titles, legends, and explanations for obvious number mismatches.
