# COAD 结肠癌预测模型需求文档

更新日期：2026-05-29

## 需求来源

本需求文档根据前序会话重新整理，必须遵守一个核心范围约束：

> 模型研究范围控制在 COAD 结肠癌数据内，不做泛癌、多癌种分类。

前序会话中的项目定位包括：

- 项目发起人目前是高二学生。
- 项目目标是完成一个可展示在大学申请文书或活动经历中的科研项目。
- 原始想法是“通过已有的癌症序列去推测未知序列的癌症可能性”。
- 当前本地容器中已经有 TCGA PanCanAtlas 和 GDC TCGA-COAD 相关数据。
- 已经围绕 COAD 做过一份结肠癌测序与多组学联合分析报告。
- 第一阶段要先用简单的 TCGA COAD 数据完成可运行模型。
- 第二阶段再使用更复杂的 UCSC Xena TCGA-GTEx Toil 数据，仍然限定在结肠癌/结肠组织相关问题上。

因此，本项目不再定义为“多癌种识别”或“pan-cancer classification”，而是定义为：

> 基于 COAD 结肠癌数据的肿瘤/正常识别、分子特征预测和关键基因解释项目。

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
- 使用 TCGA-COAD 肿瘤样本和正常样本做第一阶段基线。
- 使用 UCSC Xena TCGA-GTEx Toil 中与结肠组织相关的数据做第二阶段扩展。
- 对模型重要基因进行生物学解释，形成适合高中科研项目展示的完整流程。

## 已有本地基础

本地项目中已经存在 COAD 相关上下文和数据准备工作：

- 已有 `TCGA COAD 结肠癌测序与多组学联合分析` 报告生成脚本。
- 该报告使用了 COAD 临床数据、MC3 突变表、多组学覆盖信息和样本质量注释。
- 已记录的 COAD 报告核心统计包括：459 个 COAD 临床患者、277,114 条 MC3 突变记录、406 个肿瘤样本、404 个有突变记录患者、19,586 个涉及突变的基因。
- 本地已有 GDC TCGA-COAD STAR counts 数据目录：`data/gdc_tcga_coad_star_counts/`。
- 本地 manifest 显示当前有 481 个 `Primary Tumor` RNA-seq STAR counts 文件和 41 个 `Solid Tissue Normal` RNA-seq STAR counts 文件。
- 已有导入脚本 `scripts/import_tcga_coad_star_counts.py`，目标 schema 为 `tcga_coad`，并设计了 `gdc_files`、`genes`、`star_gene_counts` 和 `protein_coding_tpm_matrix`。

这些信息决定了第一阶段应该优先做 COAD tumor/normal 表达分类，而不是多癌种分类。

## 可行性和难度判断

### 总体判断

这个项目可以做，难度为中高，但在限定为 COAD 后更清晰、更适合高中科研项目。

可行的原因：

- COAD 是明确的单一癌种，研究范围集中。
- 本地已经有 COAD 的肿瘤样本、正常样本、临床信息和突变信息。
- 使用表达矩阵做分类，比从 FASTQ/BAM 原始 reads 开始更适合当前阶段。
- tumor/normal 分类任务直观，容易解释给非专业读者。
- 关键基因解释可以把机器学习结果和结肠癌生物学联系起来。

主要难点：

- TCGA-COAD 正常样本数量明显少于肿瘤样本，类别不平衡。
- COAD 单癌种内样本量比泛癌任务少，模型更容易过拟合。
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

- 输入数据：TCGA-COAD RNA-seq STAR gene counts 或 TPM 表达特征。
- 肿瘤样本：`Primary Tumor`。
- 正常样本：`Solid Tissue Normal`。
- 标签：`tumor` 或 `normal`。
- 模型输出：一个 COAD 样本更像肿瘤组织还是正常结肠组织。
- 模型类型：logistic regression、random forest、linear SVM，可选 XGBoost。
- 重点解释：模型识别出的重要基因是否与结肠癌、细胞增殖、WNT pathway、DNA repair、免疫微环境等方向相关。

第一阶段可选扩展任务：

- 用 COAD 突变数据定义高突变负荷 vs 低突变负荷标签，训练表达或突变特征模型。
- 用临床分期定义早期 vs 晚期标签，但要注意分期标签缺失和类别不平衡。
- 用生存状态或风险分组做预后原型，但这比 tumor/normal 分类更难，不作为第一版主任务。

第一阶段成功标准：

- 能从本地 COAD 表达数据生成特征矩阵。
- 能训练一个 baseline tumor/normal 分类模型。
- 能输出 accuracy、F1、ROC-AUC、PR-AUC 和 confusion matrix。
- 能解释至少 10 个重要基因或候选特征。
- 能清楚说明这个模型是 research-only，不用于临床诊断。

### 第二阶段：UCSC Xena TCGA-GTEx Toil 复杂模型

第二阶段仍然限定在 COAD/结肠组织范围内，不扩展成泛癌任务。

推荐第二任务：

- TCGA-COAD tumor vs GTEx colon normal 分类。
- 或者将 TCGA-COAD tumor、TCGA-COAD solid tissue normal、GTEx colon normal 三类样本进行对比分析。

具体定义：

- 输入数据：UCSC Xena TCGA-GTEx Toil RNA-seq recompute 数据。
- 肿瘤样本：TCGA-COAD tumor。
- 正常样本：优先选择 GTEx colon 相关正常组织，例如 Colon - Transverse、Colon - Sigmoid；如元数据中有 TCGA adjacent normal，也单独保留。
- 标签：`tumor`、`normal`，或更细分为 `TCGA_tumor`、`TCGA_normal`、`GTEx_normal`。
- 模型输出：样本在 COAD/结肠组织背景下更接近肿瘤还是正常。

第二阶段必须检查：

- 模型是否只学到了 TCGA vs GTEx 的数据来源差异。
- GTEx colon normal 与 TCGA solid tissue normal 是否在表达空间中明显分离。
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

- GDC TCGA-COAD STAR gene counts。
- TCGA-COAD `Primary Tumor` 样本。
- TCGA-COAD `Solid Tissue Normal` 样本。
- COAD 样本 metadata。
- COAD 临床表，用于患者 ID、样本过滤和后续解释。

本地当前可用信息：

- `data/gdc_tcga_coad_star_counts/manifests/primary_tumor_files.json`：481 个 Primary Tumor 文件。
- `data/gdc_tcga_coad_star_counts/manifests/solid_tissue_normal_files.json`：41 个 Solid Tissue Normal 文件。
- `scripts/import_tcga_coad_star_counts.py`：用于导入 COAD STAR counts。
- `tcga_coad.protein_coding_tpm_matrix`：计划中的蛋白编码基因 TPM 特征矩阵视图。

### 第一阶段最低字段

每个样本至少需要：

- `file_id`。
- `case_submitter_id`。
- `sample_submitter_id`。
- `sample_type`。
- `source_group`。
- protein-coding gene TPM values。
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

## 模型输入和标签定义

### 主任务：COAD tumor vs normal

输入：

- 每个 COAD 样本的 protein-coding gene TPM 表达特征。

标签：

- `tumor`：TCGA-COAD Primary Tumor。
- `normal`：TCGA-COAD Solid Tissue Normal；第二阶段可加入 GTEx colon normal。

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

1. 导入或确认 `tcga_coad` schema 中的 STAR counts 数据。
2. 从 `gdc_files` 中提取 sample metadata 和 sample_type。
3. 从 `protein_coding_tpm_matrix` 或等价处理结果生成样本 x 基因矩阵。
4. 将 `Primary Tumor` 映射为 `tumor`，将 `Solid Tissue Normal` 映射为 `normal`。
5. 过滤非 protein-coding 基因。
6. 过滤低表达、低方差或缺失过多的基因。
7. 对 TPM 做 `log2(TPM + 1)` 转换。
8. 进行 train/test split 或 cross-validation。
9. 保证同一 `case_submitter_id` 不同时出现在训练集和测试集。
10. 处理 481 vs 41 的类别不平衡，例如 class weight、分层抽样、PR-AUC 报告。
11. 保存处理后的特征表、标签表、基因列表和数据处理记录。

第二阶段需要完成：

1. 下载并整理 UCSC Xena TCGA-GTEx Toil 表达矩阵和 phenotype 文件。
2. 只筛选 TCGA-COAD、TCGA COAD normal 如存在、GTEx colon normal 相关样本。
3. 对齐 gene identifiers 和 gene symbols。
4. 建立 `TCGA_tumor`、`TCGA_normal`、`GTEx_normal` 等标签。
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
- 把 `sample_type`、`source_group`、文件名等标签信息直接放入模型输入。
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
- random forest 或 XGBoost：非线性模型。
- linear SVM：适合高维表达特征。

### 暂缓使用的模型

以下模型可作为后续扩展，不作为第一版主线：

- 深度神经网络。
- autoencoder。
- 多组学融合模型。
- survival deep learning。

原因是第一版项目的重点是范围清晰、结果可信、解释完整，而不是模型复杂。

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

- 确认 `data/gdc_tcga_coad_star_counts/` 文件完整。
- 确认 481 个 Primary Tumor 和 41 个 Solid Tissue Normal 文件可用。
- 确认 `scripts/import_tcga_coad_star_counts.py` 可生成 `tcga_coad` schema。
- 确认 `protein_coding_tpm_matrix` 可作为第一版特征来源。

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
- 筛选 TCGA-COAD tumor 和 GTEx colon normal 样本。
- 构建第二阶段 tumor/normal 数据集。
- 训练第二阶段模型。
- 检查 TCGA vs GTEx 数据来源混杂。

### 里程碑 5：形成申请展示材料

- 整理项目摘要。
- 整理方法流程图。
- 整理结果图表。
- 整理限制和未来工作。

## 风险和限制

- 第一阶段正常样本只有 41 个，明显少于肿瘤样本。
- COAD 单癌种范围内样本量有限，模型更容易过拟合。
- TCGA Solid Tissue Normal 是邻近正常组织，不一定等同于完全健康人群结肠组织。
- GTEx normal 与 TCGA tumor 来自不同项目，第二阶段存在强数据来源混杂风险。
- 重要基因解释只能说明模型关联，不能证明生物学因果。
- 本项目是 research-only，不能用于临床诊断。

## 待确认问题

- 第一阶段是否只使用 RNA-seq TPM，还是同时加入 MC3 突变特征？
- 第一版 normal 类样本是否只用 TCGA Solid Tissue Normal，还是提前加入 GTEx colon normal？
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

