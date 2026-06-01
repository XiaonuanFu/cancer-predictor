# COAD 结肠癌预测模型需求文档

更新日期：2026-05-29

## 需求来源

本需求文档根据前序会话重新整理，必须遵守一个核心范围约束：

> 模型研究范围控制在 COAD 结肠癌数据内，不做泛癌、多癌种分类。

前序会话中的项目定位包括：

- 项目发起人目前是高二学生。
- 项目目标是完成一个可展示在大学申请文书或活动经历中的科研项目。
- 原始想法是“通过已有的癌症序列去推测未知序列的癌症可能性”。
- 当前本地容器中已经有 TCGA PanCanAtlas 癌症测序数据和 TCGA-COAD 正常样本数据。
- 已经围绕 COAD 做过一份结肠癌测序与多组学联合分析报告。
- 第一阶段要先用简单的 TCGA COAD 数据完成可运行模型。
- 第二阶段再使用更复杂的 UCSC Xena TCGA-GTEx Toil 数据，仍然限定在结肠癌/结肠组织相关问题上。

因此，本项目不再定义为“多癌种识别”或“pan-cancer classification”，而是定义为：

> 基于 COAD 结肠癌数据的肿瘤/正常识别、分子特征预测和关键基因解释项目。

## 已确认实施决策

当前第一版模型按以下决策执行：

- 第一版特征优先使用 RNA expression，不先混入突变、CNV、甲基化等多组学特征。
- normal 样本从 `tcga_coad.star_counts_with_metadata` 中筛选，条件为 `sample_type = 'Solid Tissue Normal'`。
- normal 表达量字段第一版使用 `tcga_coad.star_counts_with_metadata.tpm_unstranded`。
- tumor 样本从 `bio_tcga` 中筛选 COAD 癌症样本，筛选逻辑参考已有高二学生项目会话和 COAD 联合分析报告：以 `bio_tcga.tcga_cdr_tcga_cdr WHERE type = 'COAD'` 确定 COAD 病人，再关联 `bio_tcga` 中的 RNA expression 样本。
- tumor RNA expression 第一版使用 `bio_tcga.matrix_rnaseq_gene_expression` 和 `bio_tcga.matrix_rnaseq_gene_expression_samples`。
- 第一版任务固定为 COAD `tumor vs normal` 二分类。
- 允许在 Python 处理中做统计转换，例如 `log2(TPM + 1)`、标准化和特征过滤；原始数据库表和原始文件不得修改。
- 第一版只使用 tumor 和 normal 两边共有、可对齐的 protein-coding gene symbol。
- train/test split 和随机种子无特殊要求，默认可使用 `test_size=0.2`、`random_state=42`，并保存拆分结果。
- 第一版 baseline 模型限定为 logistic regression、random forest、linear SVM；暂不引入 XGBoost 作为必做模型。
- 第一版交付以科研报告为主，Notebook 和 Python 脚本作为可复现支撑。
- 模型源码主目录放在仓库 `code/coad-predictor-model/`，同时发布同步到 Jupyter 容器可运行目录 `/workspace/coad-predictor-model/`。
- 报告语言使用中英文混合：中文解释为主，关键术语和模型指标保留英文。
- 当前阶段只记录需求，暂不创建 `code/coad-predictor-model/` 目录，也不开始写模型代码。

## 项目定位

### 推荐项目题目

中文题目：

> 基于 TCGA-COAD 基因表达数据的结肠癌肿瘤/正常预测模型及关键基因解释

英文题目：

> A Machine Learning Model for Tumor-Normal Classification in TCGA-COAD Using Gene Expression Profiles

### 项目核心目标

在 COAD 结肠癌范围内，使用公开组学数据建立一个研究型机器学习模型，根据样本的分子特征判断样本更接近结肠癌肿瘤组织还是正常结肠组织，并进一步解释哪些基因或分子特征对预测贡献较大。

该项目不应表述为：

- 预测一个健康人未来是否会得癌症。
- 输入任意未知 DNA 序列后直接判断患癌概率。
- 识别所有癌症类型。
- 可用于临床诊断或治疗决策。

该项目应表述为：

- 在 COAD 结肠癌数据范围内，根据 RNA 表达特征训练 tumor/normal 分类模型。
- 第一阶段基线明确使用 `bio_tcga` 中的癌症测序数据作为 tumor 来源，使用 `tcga_coad` 中的正常样本数据作为 normal 来源。
- 使用 UCSC Xena TCGA-GTEx Toil 中与结肠组织相关的数据做第二阶段扩展。
- 对模型重要基因进行生物学解释，形成适合高中科研项目展示的完整流程。

## 已有本地基础

本地项目中已经存在 COAD 相关上下文和数据准备工作：

- 已有 `TCGA COAD 结肠癌测序与多组学联合分析` 报告生成脚本。
- 该报告使用了 COAD 临床数据、MC3 突变表、多组学覆盖信息和样本质量注释。
- 已记录的 COAD 报告核心统计包括：459 个 COAD 临床患者、277,114 条 MC3 突变记录、406 个肿瘤样本、404 个有突变记录患者、19,586 个涉及突变的基因。
- 当前项目约定的数据分工是：`tcga_coad` 里存放 COAD 正常样本数据，`bio_tcga` 里存放癌症测序数据。
- `bio_tcga` 中的癌症数据可用于提取 COAD 肿瘤样本、突变信息、临床信息和已有 PanCanAtlas 相关组学矩阵。
- `tcga_coad` 中的正常样本数据用于构建 COAD normal 对照。
- 第一阶段模型需要把 `bio_tcga` 中的 COAD cancer/tumor 样本与 `tcga_coad` 中的 normal 样本对齐成同一套特征矩阵。

这些信息决定了第一阶段应该优先做 COAD tumor/normal 分类，并且明确区分两个数据来源：癌症样本来自 `bio_tcga`，正常样本来自 `tcga_coad`。

## 可行性和难度判断

### 总体判断

这个项目可以做，难度为中高，但在限定为 COAD 后更清晰、更适合高中科研项目。

可行的原因：

- COAD 是明确的单一癌种，研究范围集中。
- 本地已经有 COAD 相关的癌症测序数据、正常样本数据、临床信息和突变信息。
- 使用表达矩阵做分类，比从 FASTQ/BAM 原始 reads 开始更适合当前阶段。
- tumor/normal 分类任务直观，容易解释给非专业读者。
- 关键基因解释可以把机器学习结果和结肠癌生物学联系起来。

主要难点：

- TCGA-COAD 正常样本数量明显少于肿瘤样本，类别不平衡。
- COAD 单癌种内样本量比泛癌任务少，模型更容易过拟合。
- 肿瘤和正常样本来自不同 schema，必须检查基因 ID、表达量单位、处理流程和样本来源差异。
- 第二阶段使用 GTEx 正常结肠组织时，会引入 TCGA 与 GTEx 的数据来源差异。
- 模型重要基因只能说明统计关联，不能直接证明因果关系。

### 不推荐的方向

第一版不建议做：

- 泛癌分类，例如 BRCA、LUAD、COAD、SKCM 多癌种分类。
- 从原始 FASTQ/BAM 重新比对和变异检测。
- 预测普通人未来患癌风险。
- 一开始就做深度学习或复杂多组学融合。
- 没有正常对照时宣称可以判断“是否患癌”。

## 两阶段建设路线

### 第一阶段：TCGA-COAD 简单模型

第一阶段目标是使用本地已有的 TCGA-COAD/GDC COAD 数据，完成一个完整、可信、可解释的基础模型。

推荐第一任务：

- COAD tumor vs normal 分类。

具体定义：

- 输入数据：COAD 相关表达或测序特征，第一版优先使用可对齐的 RNA 表达特征。
- 肿瘤样本：从 `bio_tcga` 中筛选 COAD cancer/tumor 样本。
- 正常样本：从 `tcga_coad` 中读取 COAD normal 样本。
- 标签：`tumor` 或 `normal`。
- 模型输出：一个 COAD 样本更像肿瘤组织还是正常结肠组织。
- 模型类型：logistic regression、random forest、linear SVM。
- 重点解释：模型识别出的重要基因是否与结肠癌、细胞增殖、WNT pathway、DNA repair、免疫微环境等方向相关。

第一阶段可选扩展任务：

- 用 COAD 突变数据定义高突变负荷 vs 低突变负荷标签，训练表达或突变特征模型。
- 用临床分期定义早期 vs 晚期标签，但要注意分期标签缺失和类别不平衡。
- 用生存状态或风险分组做预后原型，但这比 tumor/normal 分类更难，不作为第一版主任务。

第一阶段成功标准：

- 能从本地 COAD 表达数据生成特征矩阵。
- 能清楚记录 tumor 样本来自 `bio_tcga`，normal 样本来自 `tcga_coad`。
- 能训练一个 baseline tumor/normal 分类模型。
- 能输出 accuracy、F1、ROC-AUC、PR-AUC 和 confusion matrix。
- 能解释至少 10 个重要基因或候选特征。
- 能清楚说明这个模型是 research-only，不用于临床诊断。

### 第二阶段：UCSC Xena TCGA-GTEx Toil 复杂模型

第二阶段仍然限定在 COAD/结肠组织范围内，不扩展成泛癌任务。

推荐第二任务：

- `bio_tcga` COAD tumor vs `tcga_coad` normal vs GTEx colon normal 分类或对比验证。
- 或者将 `bio_tcga` COAD tumor、`tcga_coad` COAD normal、GTEx colon normal 三类样本进行对比分析。

具体定义：

- 输入数据：UCSC Xena TCGA-GTEx Toil RNA-seq recompute 数据。
- 肿瘤样本：`bio_tcga` 中的 COAD tumor/cancer 样本，或 Toil 数据中对应的 TCGA-COAD tumor 样本。
- 正常样本：第一对照为 `tcga_coad` 中的 normal 样本；第二阶段优先加入 GTEx colon 相关正常组织，例如 Colon - Transverse、Colon - Sigmoid。
- 标签：`tumor`、`normal`，或更细分为 `bio_tcga_tumor`、`tcga_coad_normal`、`GTEx_normal`。
- 模型输出：样本在 COAD/结肠组织背景下更接近肿瘤还是正常。

第二阶段必须检查：

- 模型是否只学到了 TCGA vs GTEx 的数据来源差异。
- GTEx colon normal 与 `tcga_coad` normal 是否在表达空间中明显分离。
- 按组织来源、数据来源和样本类型分组后的模型表现。
- 加入或去掉 dataset source 相关变量后，模型性能是否异常变化。

第二阶段成功标准：

- 能建立 TCGA-COAD 与 GTEx colon normal 的样本映射和标签表。
- 能复现第二阶段特征矩阵构建。
- 能训练 tumor/normal 模型并报告分组指标。
- 能提供 batch effect 或 dataset-source confounding 的诊断说明。

## 数据需求

### 第一阶段必须使用的数据

第一阶段数据范围限定为 COAD：

- `bio_tcga` 中的 COAD 癌症测序数据。
- `bio_tcga` 中可用于 COAD 肿瘤样本筛选、临床关联和突变解释的表。
- `tcga_coad` 中的 COAD 正常样本数据。
- 两个 schema 中可对齐的样本 metadata、基因 ID、基因名和表达/测序特征。
- COAD 临床表，用于患者 ID、样本过滤和后续解释。

本地当前可用信息：

- `bio_tcga`：癌症测序和 PanCanAtlas 相关数据来源，用于 COAD tumor/cancer 样本。
- `tcga_coad`：COAD 正常样本数据来源，用于 normal 对照。
- `data/gdc_tcga_coad_star_counts/`：本地 COAD STAR counts 相关文件目录；使用前需要确认当前已导入到哪个 schema、哪些样本作为 normal 使用。
- `scripts/import_tcga_coad_star_counts.py`：现有 COAD STAR counts 导入脚本；如果继续使用，需要确保导入目标和当前数据分工一致。

### 第一阶段最低字段

每个样本至少需要：

- `file_id`。
- `case_submitter_id`。
- `sample_submitter_id`。
- `sample_type`。
- `source_schema`，取值如 `bio_tcga` 或 `tcga_coad`。
- `source_table` 或来源文件名。
- 可对齐的 gene expression 或测序特征。
- tumor/normal 标签。
- 数据来源文件名和 md5。

### 可加入的 COAD 辅助数据

辅助数据不作为第一版必须输入，但可以用于解释或扩展：

- MC3 MAF 突变数据。
- COAD 临床分期。
- 总体生存信息。
- 样本质量注释。
- CNV、methylation、miRNA、RPPA 等多组学数据。

### 第二阶段新增数据

第二阶段需要从 UCSC Xena TCGA-GTEx Toil 数据中筛选 COAD/结肠组织相关样本：

- Toil gene expression matrix，例如 `TcgaTargetGtex_gene_expected_count.gz`。
- phenotype/metadata 文件，例如 `TcgaTargetGTEX_phenotype.txt.gz`。
- TCGA-COAD tumor 样本。
- GTEx colon normal 样本，优先 Colon - Transverse 和 Colon - Sigmoid。
- dataset 标记：TCGA、GTEx；TARGET 默认不纳入第一版 COAD 模型。
- tissue 类型。
- tumor/normal 标签。
- gene identifier 和 gene symbol。

### 外部验证数据

如时间允许，可以寻找额外 COAD/结直肠癌数据做外部验证：

- GEO 中的结肠癌表达数据集。
- ICGC 中的结直肠癌相关队列。
- CPTAC 中的结直肠癌蛋白组或多组学数据。

外部验证不是第一版必须交付，但如果能完成，会显著增强科研项目可信度。

## Python 和 Jupyter 容器需求

本项目的模型构建使用 Python 完成，并放在 Jupyter 容器中运行。

运行环境要求：

- Jupyter 容器名称：`bio-jupyter`。
- 容器工作目录：`/workspace`。
- 宿主机对应目录：`docker_storage/jupyter/`。
- Jupyter 访问地址：`http://127.0.0.1:8888/lab?token=bioanalysis`。
- Python 主要依赖：`pandas`、`numpy`、`scikit-learn`、`scipy`、`matplotlib`、`seaborn`、`plotly`、`sqlalchemy`、`psycopg2-binary`。

代码目录要求：

- 仓库源码目录：`code/coad-predictor-model/`。
- Jupyter 容器运行目录：`/workspace/coad-predictor-model/`。
- 宿主机对应的 Jupyter 发布目录：`docker_storage/jupyter/coad-predictor-model/`。
- `code/coad-predictor-model/` 是主要维护位置；修改后需要同步发布到 `docker_storage/jupyter/coad-predictor-model/`，让 Jupyter 容器可以直接运行。

建议的仓库源码目录：

```text
code/coad-predictor-model/
  notebooks/                 Jupyter Notebook，记录探索和训练过程
  src/                       可复用 Python 模块
  reports/                   可提交的轻量模型报告和说明
  README.md                  运行说明
```

建议的 Jupyter 容器运行目录：

```text
/workspace/coad-predictor-model/
  notebooks/
  src/
  data/                      从 PostgreSQL 导出的中间特征表，通常不提交 git
  models/                    训练好的本地模型文件，通常不提交 git
  reports/                   指标、图表、解释表和模型报告
```

实现要求：

- 第一版可以先用 Notebook 完成，但关键逻辑要整理成可复用函数。
- 数据准备、模型训练、模型评估、结果解释应拆成清晰步骤。
- 不要把数据库密码、绝对个人路径或一次性实验输出硬编码到模型逻辑里。
- 大型中间数据、模型文件和图表默认保存在 `docker_storage/jupyter/coad-predictor-model/` 下，不提交到 git。
- 重要的最终方法说明和需求文档保存在 `doc/` 下。
- 需要提供从仓库源码发布到 Jupyter 容器目录的同步方式，例如使用 `rsync` 或后续脚本。
- 当前阶段不创建该目录；等正式开始实现模型时再创建并同步。

建议的发布命令：

```bash
rsync -a --delete code/coad-predictor-model/ docker_storage/jupyter/coad-predictor-model/
```

## Python 数据准备需求

Python 代码应优先从 PostgreSQL 读取已经导入的 COAD 数据，而不是在 Notebook 中重复解析大量原始 TSV 文件。

数据库连接：

- 容器内 PostgreSQL host：`bio-postgres`。
- 数据库：`bio`。
- 用户：`bio`。
- 密码：本地开发环境使用 `bioanalysis`。
- 主要 schema：`bio_tcga` 和 `tcga_coad`。
- `bio_tcga` 用于读取 COAD 癌症测序数据和肿瘤样本相关信息。
- `tcga_coad` 用于读取 COAD 正常样本数据。
- Python 数据准备必须保留 `source_schema` 字段，防止后续混淆 tumor 与 normal 的来源。

第一阶段数据准备流程：

1. 使用 `sqlalchemy` 或 `psycopg2` 从 `bio_tcga.matrix_rnaseq_gene_expression_samples` 读取 COAD tumor RNA expression 样本 metadata。
2. 使用 `bio_tcga.matrix_rnaseq_gene_expression` 读取 tumor RNA expression 矩阵值，并按 sample index 与样本表对齐。
3. 使用 `sqlalchemy` 或 `psycopg2` 从 `tcga_coad.star_counts_with_metadata` 读取 COAD normal 样本，筛选条件为 `sample_type = 'Solid Tissue Normal'`，表达量字段为 `tpm_unstranded`。
4. 建立统一样本表，将 `bio_tcga` 来源样本标记为 `tumor`，将 `tcga_coad` 来源样本标记为 `normal`。
5. 生成一个样本级 metadata 表，至少包含 `sample_id`、`case_submitter_id`、`sample_submitter_id`、`sample_type`、`source_schema`、`source_table`、`label`。
6. 将两个 schema 中可对齐的基因表达特征转换为样本 x 特征的 `pandas.DataFrame`。
7. 对齐 gene identifier/gene symbol，只保留 tumor 和 normal 两边都存在且定义一致的 protein-coding gene symbol。
8. 对表达量做统计转换，例如 `log2(TPM + 1)`；转换只发生在 Python 生成的中间特征表中，不修改原始数据库表或原始文件。
9. 过滤低表达、低方差和缺失过多的基因或特征。
10. 保存处理后的特征矩阵和标签表，例如：
   - `/workspace/coad-predictor-model/data/coad_tpm_log2_features.parquet`
   - `/workspace/coad-predictor-model/data/coad_tumor_normal_labels.csv`
   - `/workspace/coad-predictor-model/data/coad_selected_genes.txt`

normal 样本筛选 SQL：

```sql
SELECT *
FROM tcga_coad.star_counts_with_metadata
WHERE sample_type = 'Solid Tissue Normal';
```

tumor 样本筛选 SQL 参考：

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

说明：

- `bio_tcga.matrix_rnaseq_gene_expression_samples` 用于定位 COAD tumor/cancer RNA expression 样本。
- 实际表达矩阵值需要与 `bio_tcga.matrix_rnaseq_gene_expression` 按样本索引对齐。
- `tcga_coad.star_counts_with_metadata.tpm_unstranded` 是第一版 normal 表达量字段。
- 如果后续发现 `bio_tcga` 中有更适合的 COAD RNA expression 表或视图，允许替换，但必须在报告中记录替换原因。

数据准备质量检查：

- 输出 tumor 和 normal 样本数量。
- 检查 `sample_id` 或 `file_id` 是否唯一。
- 检查同一 `case_submitter_id` 是否有多个样本。
- 检查特征矩阵行数是否与标签表样本数一致。
- 检查 `source_schema` 是否与标签一致：`bio_tcga` 对应 tumor，`tcga_coad` 对应 normal。
- 检查 tumor 和 normal 特征是否使用同一 gene identifier、同一量纲或可解释的转换方式。
- 检查是否存在全空基因、常数基因或异常极值。
- 记录过滤前后基因数量。

## 模型输入和标签定义

### 主任务：COAD tumor vs normal

输入：

- 每个 COAD 样本的 RNA expression 特征；第一版优先使用可对齐的 protein-coding gene expression，并在数据准备阶段记录具体表达量单位和转换方式。

标签：

- `tumor`：从 `bio_tcga` 中筛选出的 COAD 癌症样本。
- `normal`：从 `tcga_coad` 中读取的 COAD 正常样本；第二阶段可加入 GTEx colon normal。

适合程度：

- 最适合作为第一版任务。
- 范围与 COAD 完全一致。
- 问题清晰，适合高中科研项目展示。
- 可以自然衔接到关键基因解释。

### 扩展任务 1：COAD 高突变负荷预测

输入：

- gene expression 特征。
- 可选突变特征。

标签：

- 根据 COAD MC3 MAF 计算每个样本 mutation burden。
- 按中位数或预设阈值分为 high mutation burden 和 low mutation burden。

注意事项：

- 标签阈值要透明记录。
- 高突变负荷可能与 MSI、POLE、样本质量等因素有关，需要谨慎解释。

### 扩展任务 2：COAD 分期或预后风险

输入：

- gene expression。
- mutation。
- CNV。
- 临床特征。

标签：

- AJCC stage。
- 生存时间。
- 生存状态。

注意事项：

- 难度高于 tumor/normal 分类。
- 标签缺失和删失会影响分析。
- 不建议作为第一版主任务。

## 数据处理需求

第一阶段需要完成：

1. 确认 `bio_tcga` 中哪些表用于 COAD 癌症样本和特征。
2. 确认 `tcga_coad` 中哪些表用于 COAD 正常样本和特征。
3. 从两个 schema 分别提取样本 metadata，并添加 `source_schema` 和 `label`。
4. 统一样本 ID、case ID、gene ID 和 gene symbol。
5. 只保留 tumor 与 normal 两边都能对齐的特征。
6. 过滤非目标特征、低表达、低方差或缺失过多的基因。
7. 对表达型特征做 `log2(TPM + 1)` 或等价标准化；对突变型特征记录编码方式。
8. 进行 train/test split 或 cross-validation。
9. 保证同一 `case_submitter_id` 不同时出现在训练集和测试集。
10. 处理 tumor 和 normal 的类别不平衡，例如 class weight、分层抽样、PR-AUC 报告。
11. 保存处理后的特征表、标签表、基因列表、样本来源表和数据处理记录。

第二阶段需要完成：

1. 下载并整理 UCSC Xena TCGA-GTEx Toil 表达矩阵和 phenotype 文件。
2. 只筛选 COAD tumor、`tcga_coad` normal、GTEx colon normal 相关样本。
3. 对齐 gene identifiers 和 gene symbols。
4. 建立 `bio_tcga_tumor`、`tcga_coad_normal`、`GTEx_normal` 等标签。
5. 建立 colon tissue mapping 表。
6. 检查 TCGA 与 GTEx 样本在 PCA/UMAP 中是否按数据来源分离。
7. 在模型评估中单独报告 dataset-source confounding 诊断。

## 特征工程需求

第一版特征工程应简单、透明、可解释：

- 主要特征：protein-coding gene TPM。
- 转换：`log2(TPM + 1)`。
- 过滤：低表达、低方差、缺失过多基因。
- 可选：选择 top variable genes。
- 可选：PCA 或 UMAP 用于可视化，不直接作为唯一证据。
- 可选：LASSO coefficient、random forest feature importance 或 SHAP 解释特征。

必须避免：

- 在全量数据上先做特征选择，再切分训练/测试集。
- 把 `sample_type`、`source_schema`、`source_table`、文件名等标签或来源信息直接放入模型输入。
- 同一个 case 的肿瘤和正常样本被分到不同集合。
- 只看 accuracy，不看 normal 类别的召回率。

## 模型需求

### 第一版基线模型

至少训练一个基础模型：

- logistic regression with class weight。
- random forest with class weight。
- linear SVM with class weight。

建议比较：

- logistic regression：可解释基线。
- random forest：非线性模型。
- linear SVM：适合高维表达特征。

### 暂缓使用的模型

以下模型可作为后续扩展，不作为第一版主线：

- 深度神经网络。
- autoencoder。
- 多组学融合模型。
- survival deep learning。

原因是第一版项目的重点是范围清晰、结果可信、解释完整，而不是模型复杂。

## Python 模型构建需求

模型训练应使用 `scikit-learn` 作为第一版主框架。

推荐 Notebook 顺序：

1. `01_prepare_coad_data.ipynb`：读取数据库，生成特征矩阵和标签。
2. `02_train_baseline_models.ipynb`：训练 logistic regression、random forest、linear SVM。
3. `03_evaluate_models.ipynb`：输出指标、混淆矩阵、ROC/PR 曲线。
4. `04_interpret_genes.ipynb`：提取重要基因并整理解释表。
5. `05_xena_toil_extension.ipynb`：第二阶段使用 TCGA-GTEx Toil 数据时再创建。

推荐 Python 模块：

```text
/workspace/coad-predictor-model/src/
  data.py                    数据库读取、标签构建、特征矩阵生成
  preprocessing.py           log2 转换、过滤、标准化、拆分
  train.py                   模型训练和参数配置
  evaluate.py                指标、图表和评估表
  interpret.py               特征重要性和关键基因解释
```

第一版训练流程：

1. 读取 `coad_tpm_log2_features.parquet` 和 `coad_tumor_normal_labels.csv`。
2. 按 `case_submitter_id` 做分组，避免同一患者样本同时进入训练集和测试集。
3. 默认使用 `test_size=0.2`、`random_state=42` 做 stratified split；如改用 cross-validation，需要在报告中说明。
4. 在训练集内部完成标准化、方差过滤和可选特征选择。
5. 使用 `class_weight="balanced"` 或等价策略处理 tumor/normal 类别不平衡。
6. 训练 logistic regression、random forest、linear SVM。
7. 保存模型、指标和图表。

建议保存的模型产物：

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

模型构建验收标准：

- Notebook 从头运行可以复现特征矩阵、模型和指标。
- 模型训练过程使用固定 `random_state`，默认 `42`。
- 训练集和测试集样本 ID 被保存，便于复查。
- 指标表包含 tumor 和 normal 两类的 precision/recall。
- 重要基因表包含 gene symbol、importance score、方向和中英文混合简短解释。

## 评估需求

COAD tumor/normal 分类至少报告：

- accuracy。
- F1。
- ROC-AUC。
- PR-AUC。
- confusion matrix。
- tumor precision/recall。
- normal precision/recall。
- balanced accuracy。

必须特别关注：

- normal 样本数量少，normal recall 很重要。
- 如果模型把多数样本都预测为 tumor，accuracy 可能看起来不低，但模型并不可靠。
- 交叉验证需要使用 stratified split 或类似策略。

高突变负荷或分期扩展任务至少报告：

- accuracy。
- macro F1。
- confusion matrix。
- 每个类别的 precision/recall。
- 标签定义和阈值说明。

## 结果解释需求

结果解释是本项目用于申请展示时最重要的部分之一。

需要完成：

- 找出对 COAD tumor/normal 预测贡献较大的基因。
- 使用 logistic regression coefficient、feature importance 或 SHAP 解释模型。
- 查询关键基因是否与结肠癌、肠上皮、细胞增殖、WNT pathway、DNA repair、免疫反应、肿瘤微环境等方向相关。
- 将模型结果和已有 COAD 报告中的突变、分期或多组学观察进行关联讨论。

推荐展示方式：

- COAD 样本构成表。
- tumor/normal 混淆矩阵。
- ROC 曲线和 PR 曲线。
- PCA/UMAP 样本分布图。
- 重要基因表。
- 关键基因的中英文解释表。

## 项目交付物

第一阶段应交付：

- COAD 数据处理说明。
- COAD tumor/normal 特征矩阵构建脚本或 Notebook。
- 一个 baseline tumor/normal 模型。
- 模型评估报告。
- 关键基因解释表。
- 面向大学申请活动描述的项目摘要。

第二阶段应交付：

- UCSC Xena TCGA-GTEx Toil 数据下载和筛选记录。
- TCGA-COAD 与 GTEx colon normal 的样本映射表。
- 第二阶段 tumor/normal 特征矩阵。
- 第二阶段分类模型。
- dataset-source confounding 检查结果。
- 第二阶段模型报告。

## 申请展示角度

这个项目适合强调：

- 将一个过大的医学 AI 想法收窄为 COAD 结肠癌范围内的可验证科学问题。
- 使用公开癌症数据完成从数据清洗到模型解释的完整流程。
- 先用 TCGA-COAD 做基础模型，再用 TCGA-GTEx Toil 引入更强正常对照。
- 理解样本不平衡、数据来源混杂和临床解释边界。
- 不夸大模型临床意义，而是强调 research-only 的探索性质。

建议在文书或活动描述中避免：

- “我做了一个可以预测癌症的系统”。
- “输入一个人的序列就可以判断是否会得癌症”。
- “模型可以诊断结肠癌”。
- “模型可以识别所有癌症”。

建议使用：

- “我基于 TCGA-COAD 基因表达数据建立了结肠癌肿瘤/正常分类模型。”
- “我比较了多种机器学习方法，并重点处理了肿瘤样本和正常样本不平衡的问题。”
- “我分析了模型中的重要基因，并结合结肠癌生物学背景进行解释。”
- “我进一步计划使用 UCSC Xena TCGA-GTEx Toil 数据验证模型是否受到数据来源差异影响。”

## 里程碑

### 里程碑 1：确认 COAD 数据入口

- 确认 `bio_tcga` 中用于 COAD 癌症样本的表和字段。
- 确认 `tcga_coad` 中用于 COAD 正常样本的表和字段。
- 确认两个 schema 中可对齐的 gene ID、gene symbol 和表达/测序特征。
- 确认 `source_schema` 和 `label` 映射规则：`bio_tcga` 为 tumor，`tcga_coad` 为 normal。

### 里程碑 2：完成 COAD baseline

- 构建 COAD tumor/normal 标签表。
- 构建 `log2(TPM + 1)` 特征矩阵。
- 完成 train/test split 或 stratified cross-validation。
- 训练 logistic regression、random forest 或 linear SVM。
- 输出第一版指标和混淆矩阵。

### 里程碑 3：完成 COAD 解释分析

- 提取重要基因。
- 查询关键基因的结肠癌相关背景。
- 生成解释表和可视化图。
- 将结果与已有 COAD 多组学报告衔接。

### 里程碑 4：扩展到 TCGA-GTEx Toil

- 下载 UCSC Xena TCGA-GTEx Toil 数据。
- 筛选 `bio_tcga` COAD tumor、`tcga_coad` normal 和 GTEx colon normal 样本。
- 构建第二阶段 tumor/normal 数据集。
- 训练第二阶段模型。
- 检查 TCGA vs GTEx 数据来源混杂。

### 里程碑 5：形成申请展示材料

- 整理项目摘要。
- 整理方法流程图。
- 整理结果图表。
- 整理限制和未来工作。

## 风险和限制

- 第一阶段 normal 样本来自 `tcga_coad`，tumor 样本来自 `bio_tcga`，两个来源的处理流程可能不同。
- COAD 单癌种范围内样本量有限，模型更容易过拟合。
- `tcga_coad` 中正常样本的来源和定义需要单独记录，不应默认等同于完全健康人群结肠组织。
- GTEx normal 与 TCGA tumor 来自不同项目，第二阶段存在强数据来源混杂风险。
- 重要基因解释只能说明模型关联，不能证明生物学因果。
- 本项目是 research-only，不能用于临床诊断。

## 待确认问题

- 第一阶段是否只使用 RNA-seq TPM，还是同时加入 MC3 突变特征？
- 第一版 normal 类样本是否只用 `tcga_coad`，还是提前加入 GTEx colon normal？
- 特征数量是否先控制在 top variable genes，还是使用全部 protein-coding genes？
- 关键基因解释是否需要单独生成中文术语表，延续已有 COAD 报告风格？
- 第二阶段 GTEx colon normal 是否同时使用 Colon - Transverse 和 Colon - Sigmoid？
- 是否需要把已有 COAD 联合分析报告作为模型报告的背景章节？

## 参考数据源

- TCGA 项目介绍：https://www.cancer.gov/ccg/research/genome-sequencing/tcga
- GDC Data Portal 文档：https://docs.gdc.cancer.gov/Encyclopedia/pages/GDC_Data_Portal/
- UCSC Xena：https://xena.ucsc.edu/
- UCSC Xena data pages：https://xenabrowser.net/datapages/
- UCSC Toil RNA-seq recompute Zenodo 长期记录：https://zenodo.org/records/10944168
