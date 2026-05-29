#!/usr/bin/env python3
import html
import json
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "docker_storage" / "jupyter" / "node-app" / "public"
REPORT_DIR = PUBLIC_DIR / "data-analysis"
REPORTS_DIR = REPORT_DIR / "reports"
ASSETS_DIR = REPORT_DIR / "assets"
REPORT_FILENAME = "tcga_mc3_sequencing_deep_dive.html"
REPORT_TITLE = "TCGA MC3 癌症测序突变表深入分析"
ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"


FIELD_EXPLANATIONS = {
    "hugo_symbol": ("基因", "HGNC/HUGO 基因符号，是突变归属到哪个基因的主字段。"),
    "entrez_gene_id": ("基因", "Entrez Gene 数字 ID，用于和 NCBI/旧注释体系连接。"),
    "center": ("来源", "产生或整合该突变调用的中心/项目来源。"),
    "ncbi_build": ("坐标", "参考基因组版本，例如 GRCh37/hg19；解释坐标时必须和这个版本一致。"),
    "chromosome": ("坐标", "染色体名称。"),
    "start_position": ("坐标", "变异起始坐标；MAF 通常使用 1-based 坐标。"),
    "end_position": ("坐标", "变异结束坐标；和 start_position 一起定位变异区间。"),
    "strand": ("坐标", "链方向，MAF 中常见为 +。"),
    "variant_classification": ("变异功能", "变异功能分类，如 Missense_Mutation、Silent、Nonsense_Mutation、Frame_Shift_Del。"),
    "variant_type": ("变异类型", "碱基层面的类型，如 SNP、DNP、INS、DEL。"),
    "reference_allele": ("等位基因", "参考基因组上的等位基因。"),
    "tumor_seq_allele1": ("等位基因", "肿瘤样本测序得到的第一个等位基因。"),
    "tumor_seq_allele2": ("等位基因", "肿瘤样本测序得到的第二个等位基因，常作为突变等位基因。"),
    "dbsnp_rs": ("外部数据库", "dbSNP rs 编号，用于识别已知 germline/常见变异。"),
    "dbsnp_val_status": ("外部数据库", "dbSNP 验证状态。"),
    "tumor_sample_barcode": ("样本", "TCGA 肿瘤样本条形码；前 12 位通常对应患者条形码。"),
    "matched_norm_sample_barcode": ("样本", "配对正常样本条形码，用于区分体细胞突变和胚系变异。"),
    "match_norm_seq_allele1": ("正常样本", "正常样本中第一个测序等位基因。"),
    "match_norm_seq_allele2": ("正常样本", "正常样本中第二个测序等位基因。"),
    "tumor_validation_allele1": ("验证", "肿瘤验证实验中的第一个等位基因。"),
    "tumor_validation_allele2": ("验证", "肿瘤验证实验中的第二个等位基因。"),
    "match_norm_validation_allele1": ("验证", "正常验证实验中的第一个等位基因。"),
    "match_norm_validation_allele2": ("验证", "正常验证实验中的第二个等位基因。"),
    "verification_status": ("验证", "突变是否经过验证/核查的状态。"),
    "validation_status": ("验证", "验证结果状态。"),
    "mutation_status": ("体细胞状态", "突变状态，通常用于标记 Somatic/Germline 等。"),
    "sequencing_phase": ("测序", "测序阶段或批次信息。"),
    "sequence_source": ("测序", "测序来源，例如 WXS/WGS/RNA 等项目字段。"),
    "validation_method": ("验证", "使用的验证方法。"),
    "score": ("调用质量", "突变调用分数；不同管线含义可能不同。"),
    "bam_file": ("文件", "相关 BAM 文件标识。"),
    "sequencer": ("测序", "测序仪或平台信息。"),
    "tumor_sample_uuid": ("样本", "肿瘤样本 UUID。"),
    "matched_norm_sample_uuid": ("样本", "配对正常样本 UUID。"),
    "hgvsc": ("HGVS", "转录本层面的 HGVS cDNA 表达，如 c.123A>T。"),
    "hgvsp": ("HGVS", "蛋白层面的 HGVS 表达，如 p.Arg123Cys。"),
    "hgvsp_short": ("HGVS", "简短蛋白变异表示，便于展示。"),
    "transcript_id": ("转录本", "变异注释对应的 Ensembl/RefSeq 转录本 ID。"),
    "exon_number": ("转录本", "变异所在外显子编号。"),
    "t_depth": ("测序证据", "肿瘤样本该位点总深度。"),
    "t_ref_count": ("测序证据", "肿瘤样本参考等位基因 reads 数。"),
    "t_alt_count": ("测序证据", "肿瘤样本突变等位基因 reads 数。"),
    "n_depth": ("测序证据", "正常样本该位点总深度。"),
    "n_ref_count": ("测序证据", "正常样本参考等位基因 reads 数。"),
    "n_alt_count": ("测序证据", "正常样本突变等位基因 reads 数；高值可能提示胚系或污染。"),
    "all_effects": ("VEP 注释", "所有候选转录本/后果注释的集合。"),
    "allele": ("VEP 注释", "被 VEP 注释的等位基因。"),
    "gene": ("VEP 注释", "Ensembl gene ID。"),
    "feature": ("VEP 注释", "Ensembl feature/transcript ID。"),
    "feature_type": ("VEP 注释", "feature 类型，例如 Transcript。"),
    "consequence": ("VEP 注释", "Sequence Ontology 后果，如 missense_variant、stop_gained。"),
    "cdna_position": ("转录本位置", "cDNA 上的位置。"),
    "cds_position": ("转录本位置", "编码序列上的位置。"),
    "protein_position": ("蛋白位置", "蛋白序列上的氨基酸位置。"),
    "amino_acids": ("蛋白变化", "参考/突变氨基酸变化。"),
    "codons": ("蛋白变化", "参考/突变密码子变化。"),
    "existing_variation": ("外部数据库", "已知变异 ID，如 dbSNP/COSMIC/ClinVar 相关标识。"),
    "allele_num": ("VEP 注释", "多等位位点中当前 allele 的编号。"),
    "distance": ("VEP 注释", "距离最近 feature 的距离，常用于上下游变异。"),
    "strand_2": ("VEP 注释", "VEP feature 链方向。"),
    "symbol": ("基因", "VEP 输出的基因符号。"),
    "symbol_source": ("基因", "基因符号来源，如 HGNC。"),
    "hgnc_id": ("基因", "HGNC ID。"),
    "biotype": ("转录本", "基因/转录本生物类型，如 protein_coding。"),
    "canonical": ("转录本", "是否为 canonical 转录本。"),
    "ccds": ("转录本", "CCDS 编号。"),
    "ensp": ("蛋白 ID", "Ensembl protein ID。"),
    "swissprot": ("蛋白 ID", "UniProt/Swiss-Prot ID。"),
    "trembl": ("蛋白 ID", "UniProt/TrEMBL ID。"),
    "uniparc": ("蛋白 ID", "UniParc ID。"),
    "refseq": ("转录本", "RefSeq 转录本/蛋白 ID。"),
    "sift": ("功能预测", "SIFT 蛋白功能影响预测，常用于 missense 解读。"),
    "polyphen": ("功能预测", "PolyPhen 蛋白功能影响预测。"),
    "exon": ("转录本位置", "外显子位置，如 3/12。"),
    "intron": ("转录本位置", "内含子位置。"),
    "domains": ("蛋白结构", "变异所在蛋白结构域/功能域注释。"),
    "gmaf": ("人群频率", "全局 minor allele frequency。"),
    "afr_maf": ("人群频率", "非洲人群等位基因频率。"),
    "amr_maf": ("人群频率", "美洲人群等位基因频率。"),
    "asn_maf": ("人群频率", "亚洲人群等位基因频率，旧字段。"),
    "eas_maf": ("人群频率", "东亚人群等位基因频率。"),
    "eur_maf": ("人群频率", "欧洲人群等位基因频率。"),
    "sas_maf": ("人群频率", "南亚人群等位基因频率。"),
    "aa_maf": ("人群频率", "African American 人群频率，旧注释字段。"),
    "ea_maf": ("人群频率", "European American 人群频率，旧注释字段。"),
    "clin_sig": ("临床注释", "ClinVar 临床显著性。"),
    "somatic": ("临床注释", "外部数据库是否标记为 somatic。"),
    "pubmed": ("文献", "相关 PubMed ID。"),
    "motif_name": ("调控 motif", "受影响的 motif 名称。"),
    "motif_pos": ("调控 motif", "motif 内位置。"),
    "high_inf_pos": ("调控 motif", "是否为高信息量 motif 位置。"),
    "motif_score_change": ("调控 motif", "motif 分数变化。"),
    "impact": ("功能影响", "VEP 影响等级：HIGH、MODERATE、LOW、MODIFIER。"),
    "pick": ("VEP 注释", "VEP 是否选择该注释作为代表注释。"),
    "variant_class": ("变异类型", "VEP 变异类别，如 SNV、deletion、insertion。"),
    "tsl": ("转录本", "Transcript Support Level，转录本支持等级。"),
    "hgvs_offset": ("HGVS", "HGVS 左/右对齐偏移。"),
    "pheno": ("临床注释", "是否有表型相关注释。"),
    "minimised": ("规范化", "变异是否已最小化表示。"),
    "exac_af": ("ExAC 频率", "ExAC 全局等位基因频率。"),
    "exac_af_afr": ("ExAC 频率", "ExAC 非洲人群频率。"),
    "exac_af_amr": ("ExAC 频率", "ExAC 美洲人群频率。"),
    "exac_af_eas": ("ExAC 频率", "ExAC 东亚人群频率。"),
    "exac_af_fin": ("ExAC 频率", "ExAC 芬兰人群频率。"),
    "exac_af_nfe": ("ExAC 频率", "ExAC 非芬兰欧洲人群频率。"),
    "exac_af_oth": ("ExAC 频率", "ExAC 其他人群频率。"),
    "exac_af_sas": ("ExAC 频率", "ExAC 南亚人群频率。"),
    "gene_pheno": ("临床注释", "基因是否与表型/疾病相关。"),
    "filter": ("调用质量", "过滤状态；PASS 或其他过滤标签。"),
    "cosmic": ("外部数据库", "COSMIC 癌症突变数据库标识。"),
    "centers": ("来源", "支持该突变调用的中心集合。"),
    "context": ("序列背景", "突变附近序列上下文，可用于突变签名分析。"),
    "dbvs": ("外部数据库", "dbVar 或结构变异相关注释字段。"),
    "ncallers": ("调用一致性", "支持该突变的 caller 数量；MC3 多 caller 共识中很重要。"),
}


def run_json(sql: str):
    wrapped = f"SELECT COALESCE(json_agg(row_to_json(q)), '[]'::json) FROM ({sql}) q;"
    result = subprocess.run(
        ["docker", "exec", "bio-postgres", "psql", "-U", "bio", "-d", "bio", "-At", "-v", "ON_ERROR_STOP=1", "-c", wrapped],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip() or "[]")


def ensure_echarts_asset() -> str:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    target = ASSETS_DIR / "echarts.min.js"
    if not target.exists() or target.stat().st_size < 100_000:
        with urllib.request.urlopen(ECHARTS_URL, timeout=30) as response:
            target.write_bytes(response.read())
    return "../assets/echarts.min.js"


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def js(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def fmt_int(value) -> str:
    return f"{int(float(value or 0)):,}"


def build_data():
    columns = run_json(
        """
        SELECT column_name, ordinal_position
        FROM information_schema.columns
        WHERE table_schema='bio_tcga' AND table_name='mc3_public_maf'
        ORDER BY ordinal_position
        """
    )
    summary = run_json(
        """
        SELECT count(*)::bigint AS rows,
               count(distinct tumor_sample_barcode)::bigint AS tumor_samples,
               count(distinct substring(tumor_sample_barcode from 1 for 12))::bigint AS patients,
               count(distinct hugo_symbol)::bigint AS genes,
               count(distinct chromosome)::bigint AS chromosomes
        FROM bio_tcga.mc3_public_maf
        """
    )[0]
    variant_classification = run_json(
        """
        SELECT variant_classification AS label, count(*)::bigint AS value
        FROM bio_tcga.mc3_public_maf
        GROUP BY variant_classification
        ORDER BY value DESC
        LIMIT 20
        """
    )
    variant_type = run_json(
        """
        SELECT variant_type AS label, count(*)::bigint AS value
        FROM bio_tcga.mc3_public_maf
        GROUP BY variant_type
        ORDER BY value DESC
        """
    )
    impact = run_json(
        """
        SELECT COALESCE(NULLIF(impact,''),'(missing)') AS label, count(*)::bigint AS value
        FROM bio_tcga.mc3_public_maf
        GROUP BY COALESCE(NULLIF(impact,''),'(missing)')
        ORDER BY value DESC
        """
    )
    chromosome = run_json(
        """
        SELECT chromosome AS label, count(*)::bigint AS value
        FROM bio_tcga.mc3_public_maf
        GROUP BY chromosome
        ORDER BY CASE WHEN chromosome ~ '^[0-9]+$' THEN chromosome::int ELSE 100 END, chromosome
        """
    )
    top_genes = run_json(
        """
        SELECT hugo_symbol AS label, count(*)::bigint AS value
        FROM bio_tcga.mc3_public_maf
        WHERE hugo_symbol NOT IN ('Unknown','')
        GROUP BY hugo_symbol
        ORDER BY value DESC
        LIMIT 25
        """
    )
    cancer_types = run_json(
        """
        WITH joined AS (
          SELECT COALESCE(NULLIF(c.type,''),'Unmapped') AS cancer_type,
                 m.tumor_sample_barcode,
                 substring(m.tumor_sample_barcode from 1 for 12) AS patient_id
          FROM bio_tcga.mc3_public_maf m
          LEFT JOIN bio_tcga.tcga_cdr_tcga_cdr c
            ON c.bcr_patient_barcode = substring(m.tumor_sample_barcode from 1 for 12)
        )
        SELECT cancer_type AS label,
               count(*)::bigint AS variants,
               count(distinct tumor_sample_barcode)::bigint AS samples,
               count(distinct patient_id)::bigint AS patients,
               round(count(*)::numeric / nullif(count(distinct tumor_sample_barcode),0), 1)::text AS variants_per_sample
        FROM joined
        GROUP BY cancer_type
        ORDER BY variants DESC
        LIMIT 20
        """
    )
    burden = run_json(
        """
        WITH per_sample AS (
          SELECT tumor_sample_barcode,
                 substring(tumor_sample_barcode from 1 for 12) AS patient_id,
                 count(*)::int AS mutation_count
          FROM bio_tcga.mc3_public_maf
          GROUP BY tumor_sample_barcode
        ),
        joined AS (
          SELECT COALESCE(NULLIF(c.type,''),'Unmapped') AS cancer_type, mutation_count
          FROM per_sample p
          LEFT JOIN bio_tcga.tcga_cdr_tcga_cdr c ON c.bcr_patient_barcode = p.patient_id
        )
        SELECT cancer_type AS label,
               count(*)::int AS samples,
               round(avg(mutation_count), 1)::text AS avg_mutations,
               percentile_disc(0.5) within group (order by mutation_count)::int AS median_mutations
        FROM joined
        GROUP BY cancer_type
        HAVING count(*) >= 20
        ORDER BY avg(mutation_count) DESC
        LIMIT 20
        """
    )
    vaf_bins = run_json(
        """
        WITH v AS (
          SELECT CASE
                   WHEN t_depth ~ '^[0-9]+$' AND t_alt_count ~ '^[0-9]+$' AND t_depth::numeric > 0
                   THEN t_alt_count::numeric / t_depth::numeric
                 END AS vaf
          FROM bio_tcga.mc3_public_maf
        )
        SELECT bucket AS label, count(*)::bigint AS value
        FROM (
          SELECT CASE
            WHEN vaf IS NULL THEN 'missing'
            WHEN vaf < 0.05 THEN '<5%'
            WHEN vaf < 0.10 THEN '5-10%'
            WHEN vaf < 0.20 THEN '10-20%'
            WHEN vaf < 0.30 THEN '20-30%'
            WHEN vaf < 0.50 THEN '30-50%'
            ELSE '>=50%'
          END AS bucket,
          CASE
            WHEN vaf IS NULL THEN 99
            WHEN vaf < 0.05 THEN 1
            WHEN vaf < 0.10 THEN 2
            WHEN vaf < 0.20 THEN 3
            WHEN vaf < 0.30 THEN 4
            WHEN vaf < 0.50 THEN 5
            ELSE 6
          END AS ord
          FROM v
        ) b
        GROUP BY bucket, ord
        ORDER BY ord
        """
    )
    depth_summary = run_json(
        """
        SELECT count(*) FILTER (WHERE t_depth ~ '^[0-9]+$')::bigint AS tumor_depth_records,
               round(avg(t_depth::numeric) FILTER (WHERE t_depth ~ '^[0-9]+$'), 1)::text AS avg_t_depth,
               percentile_disc(0.5) within group (order by t_depth::int) FILTER (WHERE t_depth ~ '^[0-9]+$')::int AS median_t_depth,
               round(avg(n_depth::numeric) FILTER (WHERE n_depth ~ '^[0-9]+$'), 1)::text AS avg_n_depth,
               percentile_disc(0.5) within group (order by n_depth::int) FILTER (WHERE n_depth ~ '^[0-9]+$')::int AS median_n_depth
        FROM bio_tcga.mc3_public_maf
        """
    )[0]
    ncallers = run_json(
        """
        WITH grouped AS (
          SELECT COALESCE(NULLIF(ncallers,''),'(missing)') AS label, count(*)::bigint AS value
          FROM bio_tcga.mc3_public_maf
          GROUP BY COALESCE(NULLIF(ncallers,''),'(missing)')
        )
        SELECT label, value,
               CASE WHEN label ~ '^[0-9]+$' THEN label::int ELSE 99 END AS ord
        FROM grouped
        ORDER BY ord
        """
    )
    heatmap = run_json(
        """
        WITH top_cancers AS (
          SELECT COALESCE(NULLIF(c.type,''),'Unmapped') AS cancer_type, count(*) AS n
          FROM bio_tcga.mc3_public_maf m
          LEFT JOIN bio_tcga.tcga_cdr_tcga_cdr c
            ON c.bcr_patient_barcode = substring(m.tumor_sample_barcode from 1 for 12)
          GROUP BY 1
          ORDER BY n DESC
          LIMIT 10
        ),
        top_genes AS (
          SELECT hugo_symbol, count(*) AS n
          FROM bio_tcga.mc3_public_maf
          WHERE hugo_symbol NOT IN ('Unknown','')
          GROUP BY hugo_symbol
          ORDER BY n DESC
          LIMIT 12
        ),
        agg AS (
          SELECT COALESCE(NULLIF(c.type,''),'Unmapped') AS cancer_type,
                 m.hugo_symbol,
                 count(*)::bigint AS value
          FROM bio_tcga.mc3_public_maf m
          LEFT JOIN bio_tcga.tcga_cdr_tcga_cdr c
            ON c.bcr_patient_barcode = substring(m.tumor_sample_barcode from 1 for 12)
          JOIN top_cancers tc ON tc.cancer_type = COALESCE(NULLIF(c.type,''),'Unmapped')
          JOIN top_genes tg ON tg.hugo_symbol = m.hugo_symbol
          GROUP BY 1, 2
        )
        SELECT tc.cancer_type, tg.hugo_symbol, COALESCE(agg.value, 0)::bigint AS value
        FROM top_cancers tc
        CROSS JOIN top_genes tg
        LEFT JOIN agg ON agg.cancer_type = tc.cancer_type AND agg.hugo_symbol = tg.hugo_symbol
        ORDER BY tc.cancer_type, tg.hugo_symbol
        """
    )
    sample_rows = run_json(
        """
        SELECT hugo_symbol, chromosome, start_position, variant_classification, variant_type,
               tumor_sample_barcode, hgvsp_short, t_depth, t_alt_count, impact, ncallers
        FROM bio_tcga.mc3_public_maf
        WHERE hugo_symbol IN ('TP53','TTN','MUC16')
        LIMIT 10
        """
    )
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "columns": columns,
        "summary": summary,
        "variant_classification": variant_classification,
        "variant_type": variant_type,
        "impact": impact,
        "chromosome": chromosome,
        "top_genes": top_genes,
        "cancer_types": cancer_types,
        "burden": burden,
        "vaf_bins": vaf_bins,
        "depth_summary": depth_summary,
        "ncallers": ncallers,
        "heatmap": heatmap,
        "sample_rows": sample_rows,
    }


def render_table(rows, headers, fields) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{esc(row.get(f))}</td>" for f in fields) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_report(data, echarts_src):
    summary = data["summary"]
    depth = data["depth_summary"]
    field_rows = []
    for col in data["columns"]:
        category, explanation = FIELD_EXPLANATIONS.get(col["column_name"], ("其他", "导入自原始 MAF 文件的字段；需要结合源文件说明进一步确认。"))
        field_rows.append({
            "pos": col["ordinal_position"],
            "field": col["column_name"],
            "category": category,
            "explanation": explanation,
        })
    glossary_rows = [
        {"term": "TCGA", "plain": "The Cancer Genome Atlas, a large public project that collected cancer samples and data.", "cn": "癌症基因组图谱项目，很多癌症组学数据来自这里。"},
        {"term": "MC3", "plain": "Multi-Center Mutation Calling in Multiple Cancers, a TCGA project that combined mutation calls from several tools.", "cn": "TCGA 的多中心突变整合项目，用多个 caller 共同判断突变。"},
        {"term": "MAF", "plain": "Mutation Annotation Format, a table where each row usually describes one DNA mutation.", "cn": "突变注释表，一行通常是一条突变记录。"},
        {"term": "Somatic mutation", "plain": "A DNA change found in tumor cells but not inherited from your parents.", "cn": "体细胞突变，肿瘤细胞里后天出现的 DNA 改变。"},
        {"term": "Germline variant", "plain": "A DNA difference you were born with and can be present in normal cells.", "cn": "胚系变异，出生就有，正常细胞也可能有。"},
        {"term": "Tumor sample", "plain": "DNA or tissue taken from the cancer part of the patient.", "cn": "肿瘤样本。"},
        {"term": "Matched normal sample", "plain": "Non-cancer DNA from the same patient, used as a comparison baseline.", "cn": "同一病人的正常样本，用来判断哪些变化是肿瘤特有。"},
        {"term": "Variant", "plain": "A place in DNA where the sequence is different from the reference genome.", "cn": "变异，DNA 和参考基因组不同的地方。"},
        {"term": "Allele", "plain": "One version of a DNA base or sequence at a genomic position.", "cn": "等位基因，某个 DNA 位置上的一个版本。"},
        {"term": "Reference allele", "plain": "The DNA letter or sequence in the reference genome.", "cn": "参考基因组上的原始碱基/序列。"},
        {"term": "Tumor allele", "plain": "The DNA letter or sequence observed in the tumor sample.", "cn": "肿瘤样本里看到的碱基/序列。"},
        {"term": "SNP / SNV", "plain": "A single-letter DNA change, like A becoming T.", "cn": "单碱基改变。"},
        {"term": "DNP", "plain": "A two-letter DNA change next to each other.", "cn": "相邻两个碱基一起变化。"},
        {"term": "INS", "plain": "Insertion: extra DNA letters are added.", "cn": "插入，DNA 多了一段。"},
        {"term": "DEL", "plain": "Deletion: DNA letters are missing.", "cn": "缺失，DNA 少了一段。"},
        {"term": "Missense mutation", "plain": "A DNA change that swaps one amino acid in a protein for another.", "cn": "错义突变，蛋白质里一个氨基酸换成另一个。"},
        {"term": "Nonsense mutation", "plain": "A DNA change that creates an early stop signal, making a shorter protein.", "cn": "无义突变，提前停止，蛋白可能变短。"},
        {"term": "Silent mutation", "plain": "A DNA change that does not change the amino acid.", "cn": "同义/沉默突变，DNA 变了但氨基酸没变。"},
        {"term": "Frameshift", "plain": "An insertion or deletion that shifts how DNA letters are read in groups of three.", "cn": "移码突变，三联密码子的阅读框被打乱。"},
        {"term": "Splice site", "plain": "A DNA region needed to cut and join RNA pieces correctly.", "cn": "剪接位点，影响 RNA 外显子拼接。"},
        {"term": "Exon", "plain": "A gene segment that usually stays in the final RNA message.", "cn": "外显子，常保留在成熟 RNA 里。"},
        {"term": "Intron", "plain": "A gene segment usually removed from RNA before making protein.", "cn": "内含子，通常会被剪掉。"},
        {"term": "Transcript", "plain": "An RNA version of a gene; one gene can have multiple transcript versions.", "cn": "转录本，一个基因可以有多个 RNA 版本。"},
        {"term": "Amino acid", "plain": "A building block of proteins.", "cn": "氨基酸，蛋白质的基本组成单位。"},
        {"term": "HGVS", "plain": "A standard naming system for describing DNA or protein changes.", "cn": "标准突变命名法。"},
        {"term": "VEP", "plain": "Variant Effect Predictor, a tool that predicts what a DNA variant might do.", "cn": "变异影响预测工具。"},
        {"term": "Impact", "plain": "A rough label for how serious a variant may be: HIGH, MODERATE, LOW, or MODIFIER.", "cn": "预测影响等级。"},
        {"term": "Read", "plain": "A short piece of DNA sequence produced by a sequencing machine.", "cn": "测序读段，机器读出的一小段 DNA。"},
        {"term": "Depth", "plain": "How many sequencing reads cover a DNA position.", "cn": "测序深度，一个位置被读到了多少次。"},
        {"term": "Alt count", "plain": "How many reads support the changed allele instead of the reference allele.", "cn": "支持突变碱基的 reads 数。"},
        {"term": "VAF", "plain": "Variant Allele Fraction: alt reads divided by total reads. A 20% VAF means about 1 in 5 reads show the mutation.", "cn": "突变等位基因比例，alt reads / 总 reads。"},
        {"term": "Caller", "plain": "A software tool that decides whether a DNA change is a real mutation.", "cn": "突变检测软件。"},
        {"term": "ncallers", "plain": "How many mutation-calling tools supported the same mutation.", "cn": "有几个 caller 同意这个突变。"},
        {"term": "COSMIC", "plain": "A database of mutations found in cancer.", "cn": "癌症突变数据库。"},
        {"term": "ClinVar", "plain": "A database that links variants to possible medical meaning.", "cn": "临床变异数据库。"},
        {"term": "dbSNP", "plain": "A database of known DNA variants, many of which are common inherited variants.", "cn": "已知变异数据库。"},
        {"term": "ExAC", "plain": "A database of allele frequencies from many people, useful for spotting common variants.", "cn": "人群频率数据库。"},
        {"term": "Adaptyv Bio", "plain": "A service that can express designed proteins and measure binding in wet-lab assays.", "cn": "蛋白表达和结合实验平台，可用于后续验证候选蛋白。"},
    ]
    sample_rows = data["sample_rows"]
    cancer_rows = [
        {
            "label": row["label"],
            "variants": fmt_int(row["variants"]),
            "samples": fmt_int(row["samples"]),
            "patients": fmt_int(row["patients"]),
            "variants_per_sample": row["variants_per_sample"],
        }
        for row in data["cancer_types"][:12]
    ]
    heat_x = sorted({row["hugo_symbol"] for row in data["heatmap"]})
    heat_y = sorted({row["cancer_type"] for row in data["heatmap"]})
    heat_values = [[heat_x.index(row["hugo_symbol"]), heat_y.index(row["cancer_type"]), int(row["value"] or 0)] for row in data["heatmap"]]
    heat_max = max([v[2] for v in heat_values] or [1])
    css = """
    :root { --ink:#17212b; --muted:#5c6b78; --line:#d9e1e8; --panel:#f7f9fb; --blue:#1769aa; --green:#218380; --red:#c8553d; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:#fff; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; }
    header { padding:34px 42px 24px; background:#f8fafc; border-bottom:1px solid var(--line); }
    main { max-width:1320px; margin:0 auto; padding:28px 42px 52px; }
    h1 { margin:0 0 10px; font-size:30px; letter-spacing:0; }
    h2 { margin:34px 0 14px; font-size:22px; }
    h3 { margin:22px 0 10px; font-size:17px; }
    p { line-height:1.66; color:#2d3a46; }
    .meta { color:var(--muted); font-size:14px; }
    .cards { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin:18px 0; }
    .card { border:1px solid var(--line); border-radius:8px; padding:15px; background:#fff; }
    .card span { display:block; color:var(--muted); font-size:12px; font-weight:700; text-transform:uppercase; }
    .card strong { display:block; margin-top:8px; font-size:24px; }
    .chart-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }
    .chart { min-height:390px; border:1px solid var(--line); border-radius:8px; padding:8px; background:#fff; }
    .wide { grid-column:1 / -1; min-height:520px; }
    .note { border-left:4px solid var(--green); background:#f2fbfa; padding:13px 15px; margin:14px 0; }
    .back-link { display:inline-block; margin-bottom:14px; color:var(--blue); font-weight:700; text-decoration:none; }
    .back-link:hover { text-decoration:underline; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { border-bottom:1px solid var(--line); padding:8px 9px; text-align:left; vertical-align:top; }
    th { background:var(--panel); color:#314253; }
    code { background:#eef3f7; padding:1px 5px; border-radius:4px; }
    .field-table td:nth-child(4) { min-width:360px; }
    .footer { margin-top:30px; color:var(--muted); font-size:13px; }
    @media (max-width: 920px) { header, main { padding-left:18px; padding-right:18px; } .cards, .chart-grid { grid-template-columns:1fr; } .wide { grid-column:auto; } }
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{REPORT_TITLE}</title>
  <style>{css}</style>
  <script src="{echarts_src}"></script>
</head>
<body>
  <header>
    <h1>{REPORT_TITLE}</h1>
    <div class="meta">生成时间：{esc(data["generated_at"])} · 表：bio_tcga.mc3_public_maf · 数据类型：TCGA MC3 MAF 体细胞突变表</div>
  </header>
  <main>
    <a class="back-link" href="/#analysis">← 回到报告清单</a>
    <section>
      <h2>1. 表定位与总体结论</h2>
      <p><code>mc3_public_maf</code> 是这个 schema 中最典型的癌症测序突变表。MAF（Mutation Annotation Format）把肿瘤/正常配对测序发现的体细胞变异按“一行一个变异事件”整理，并附带基因、基因组坐标、转录本/蛋白影响、测序深度、外部数据库和多 caller 共识信息。</p>
      <div class="cards">
        <div class="card"><span>突变记录</span><strong>{fmt_int(summary["rows"])}</strong></div>
        <div class="card"><span>肿瘤样本</span><strong>{fmt_int(summary["tumor_samples"])}</strong></div>
        <div class="card"><span>患者</span><strong>{fmt_int(summary["patients"])}</strong></div>
        <div class="card"><span>基因</span><strong>{fmt_int(summary["genes"])}</strong></div>
        <div class="card"><span>字段</span><strong>{fmt_int(len(data["columns"]))}</strong></div>
      </div>
      <div class="note">生信解释：这里的坐标应按 <code>ncbi_build</code> 字段理解；MAF 坐标通常是 1-based。字段 <code>t_depth/t_alt_count</code> 可计算肿瘤 VAF，<code>n_depth/n_alt_count</code> 用于评估正常样本背景，<code>ncallers</code> 是 MC3 共识可靠性的一个关键参考。</div>
    </section>

    <section>
      <h2>2. 癌症突变信息图谱</h2>
      <div class="chart-grid">
        <div id="variantClassChart" class="chart"></div>
        <div id="variantTypeChart" class="chart"></div>
        <div id="impactChart" class="chart"></div>
        <div id="chromosomeChart" class="chart"></div>
        <div id="topGenesChart" class="chart"></div>
        <div id="cancerTypeChart" class="chart"></div>
        <div id="burdenChart" class="chart"></div>
        <div id="vafChart" class="chart"></div>
        <div id="ncallersChart" class="chart"></div>
        <div id="geneCancerHeatmap" class="chart wide"></div>
      </div>
    </section>

    <section>
      <h2>3. 测序证据质量解读</h2>
      <p>肿瘤深度中位数为 <strong>{esc(depth.get("median_t_depth"))}</strong>，平均肿瘤深度约 <strong>{esc(depth.get("avg_t_depth"))}</strong>；正常样本深度中位数为 <strong>{esc(depth.get("median_n_depth"))}</strong>，平均正常深度约 <strong>{esc(depth.get("avg_n_depth"))}</strong>。初级筛选时可以优先关注较高 <code>t_alt_count</code>、合理 VAF、较低正常样本突变支持、较高 <code>ncallers</code> 的事件。</p>
      <p>从蛋白实验延展角度，<code>hgvsp</code>、<code>hgvsp_short</code>、<code>amino_acids</code>、<code>protein_position</code> 可以帮助把 DNA 层面的 missense/nonsense 事件转译成候选蛋白变体。若后续要验证突变蛋白、抗原肽或结合蛋白设计，Adaptyv Bio 这类表达/结合实验平台可作为下游候选验证环节；本报告仅做本地数据库分析，没有调用外部 API。</p>
    </section>

    <section>
      <h2>4. 癌种分布 Top 12</h2>
      {render_table(cancer_rows, ["癌种", "突变数", "样本数", "患者数", "平均突变/样本"], ["label", "variants", "samples", "patients", "variants_per_sample"])}
    </section>

    <section>
      <h2>5. 代表性记录样例</h2>
      {render_table(sample_rows, ["基因", "染色体", "起点", "功能分类", "类型", "样本", "蛋白变化", "肿瘤深度", "alt reads", "影响", "callers"], ["hugo_symbol", "chromosome", "start_position", "variant_classification", "variant_type", "tumor_sample_barcode", "hgvsp_short", "t_depth", "t_alt_count", "impact", "ncallers"])}
    </section>

    <section>
      <h2>6. 缩写和专业词汇解释</h2>
      <p>下面这张表用比较像 AP Bio 课堂的语言解释报告里的缩写和专业词。你可以先看这张表，再回头看图表和字段表。</p>
      {render_table(glossary_rows, ["Term / abbreviation", "Plain English explanation", "中文理解"], ["term", "plain", "cn"])}
    </section>

    <section>
      <h2>7. 114 个字段解释</h2>
      <div class="field-table">
        {render_table(field_rows, ["序号", "字段", "类别", "解释"], ["pos", "field", "category", "explanation"])}
      </div>
    </section>
    <p class="footer">说明：本报告面向初级到进阶的数据理解。图表为聚合统计，不替代正式突变筛选、驱动基因识别或临床解释流程。</p>
  </main>
  <script>
    const variantClass = {js(data["variant_classification"])};
    const variantType = {js(data["variant_type"])};
    const impact = {js(data["impact"])};
    const chromosome = {js(data["chromosome"])};
    const topGenes = {js(data["top_genes"])};
    const cancerTypes = {js(data["cancer_types"])};
    const burden = {js(data["burden"])};
    const vafBins = {js(data["vaf_bins"])};
    const ncallers = {js(data["ncallers"])};
    const heatX = {js(heat_x)};
    const heatY = {js(heat_y)};
    const heatValues = {js(heat_values)};
    const heatMax = {heat_max};

    function labels(rows) {{ return rows.map(r => r.label); }}
    function values(rows, key='value') {{ return rows.map(r => Number(r[key] || 0)); }}
    function bar(id, title, rows, key='value', color='#1769aa') {{
      const chart = echarts.init(document.getElementById(id));
      chart.setOption({{
        title: {{ text: title, left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
        tooltip: {{ trigger: 'axis' }},
        grid: {{ left: 78, right: 24, top: 58, bottom: 90 }},
        xAxis: {{ type: 'category', data: labels(rows), axisLabel: {{ rotate: 42, interval: 0 }} }},
        yAxis: {{ type: 'value' }},
        series: [{{ type: 'bar', data: values(rows, key), itemStyle: {{ color }} }}]
      }});
      return chart;
    }}
    function pie(id, title, rows) {{
      const chart = echarts.init(document.getElementById(id));
      chart.setOption({{
        title: {{ text: title, left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
        tooltip: {{ trigger: 'item' }},
        legend: {{ type: 'scroll', bottom: 0 }},
        series: [{{ type: 'pie', radius: ['36%', '68%'], center: ['50%', '48%'], data: rows.map(r => ({{ name: r.label, value: Number(r.value || 0) }})) }}]
      }});
      return chart;
    }}
    const charts = [
      bar('variantClassChart', 'Variant Classification 分布', variantClass, 'value', '#1769aa'),
      pie('variantTypeChart', 'Variant Type 分布', variantType),
      pie('impactChart', 'VEP Impact 分布', impact),
      bar('chromosomeChart', '染色体突变记录数', chromosome, 'value', '#218380'),
      bar('topGenesChart', '突变记录最多的基因 Top 25', topGenes, 'value', '#c8553d'),
      bar('cancerTypeChart', '癌种突变记录 Top 20', cancerTypes.map(r => ({{ label: r.label, value: r.variants }})), 'value', '#7b4ea3'),
      bar('burdenChart', '癌种平均突变负荷 Top 20', burden.map(r => ({{ label: r.label, value: r.avg_mutations }})), 'value', '#ad7a1f'),
      bar('vafChart', '肿瘤 VAF 分箱', vafBins, 'value', '#2f7f91'),
      bar('ncallersChart', '支持 caller 数 ncallers', ncallers, 'value', '#5166a6')
    ];
    const heat = echarts.init(document.getElementById('geneCancerHeatmap'));
    heat.setOption({{
      title: {{ text: 'Top 癌种 x Top 基因突变计数热图', left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
      tooltip: {{ position: 'top', formatter: p => `${{heatY[p.value[1]]}} / ${{heatX[p.value[0]]}}: ${{p.value[2]}}` }},
      grid: {{ left: 120, right: 40, top: 64, bottom: 88 }},
      xAxis: {{ type: 'category', data: heatX, axisLabel: {{ rotate: 45 }} }},
      yAxis: {{ type: 'category', data: heatY }},
      visualMap: {{ min: 0, max: heatMax, calculable: true, orient: 'horizontal', left: 'center', bottom: 12 }},
      series: [{{ type: 'heatmap', data: heatValues, label: {{ show: false }} }}]
    }});
    charts.push(heat);
    window.addEventListener('resize', () => charts.forEach(c => c.resize()));
  </script>
</body>
</html>"""


def render_report_list(data) -> str:
    css = """
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; color:#17212b; background:#fff; }
    main { max-width:920px; margin:0 auto; padding:36px 24px; }
    h1 { font-size:28px; margin:0 0 8px; }
    .meta { color:#607080; margin-bottom:22px; }
    a.card { display:block; text-decoration:none; color:inherit; border:1px solid #d8e0e8; border-radius:8px; padding:18px; background:#f9fbfd; margin-bottom:12px; }
    a.card:hover { border-color:#1769aa; }
    .title { font-size:18px; font-weight:700; margin-bottom:8px; }
    .desc { color:#384858; line-height:1.55; }
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Data Analysis 报告清单</title><style>{css}</style></head>
<body><main>
  <h1>Data Analysis 报告清单</h1>
  <div class="meta">当前共有 3 份报告 · 最近更新：{esc(data["generated_at"])}</div>
  <a class="card" href="reports/tcga_schema_basic_analysis.html">
    <div class="title">1. TCGA Schema 初级分析报告</div>
    <div class="desc">本地 PostgreSQL 容器中 bio_tcga schema 的初级概览，包括表规模、数据类型、TCGA 临床字段 type 的解释和癌种分布图。</div>
  </a>
  <a class="card" href="reports/{REPORT_FILENAME}">
    <div class="title">2. {REPORT_TITLE}</div>
    <div class="desc">深入分析 MC3 MAF 癌症测序突变表，覆盖变异类型、癌种、基因、染色体、VAF、caller 支持度，并解释全部 114 个字段。</div>
  </a>
  <a class="card" href="reports/tcga_coad_integrated_analysis.html">
    <div class="title">3. TCGA COAD 结肠癌测序与多组学联合分析</div>
    <div class="desc">聚焦 COAD 结肠癌，把临床、MC3 测序突变、多组学样本覆盖、样本质量注释和术语解释整合到一份报告。</div>
  </a>
</main></body></html>"""


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    data = build_data()
    echarts_src = ensure_echarts_asset()
    report_path = REPORTS_DIR / REPORT_FILENAME
    report_path.write_text(render_report(data, echarts_src), encoding="utf-8")
    list_path = REPORT_DIR / "report-list.html"
    list_path.write_text(render_report_list(data), encoding="utf-8")
    print(f"report={report_path}")
    print(f"report_list={list_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
