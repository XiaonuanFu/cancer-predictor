#!/usr/bin/env python3
import csv
import html
import json
import subprocess
import textwrap
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "docker_storage" / "jupyter" / "node-app" / "public"
REPORT_DIR = PUBLIC_DIR / "data-analysis"
REPORTS_DIR = REPORT_DIR / "reports"
ASSETS_DIR = REPORT_DIR / "assets"
REPORT_FILENAME = "tcga_schema_basic_analysis.html"
REPORT_TITLE = "TCGA Schema 初级分析报告"
ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"


def run_psql_json(sql: str):
    wrapped = f"""
    SELECT COALESCE(json_agg(row_to_json(q)), '[]'::json)
    FROM (
    {sql}
    ) q;
    """
    result = subprocess.run(
        [
            "docker",
            "exec",
            "bio-postgres",
            "psql",
            "-U",
            "bio",
            "-d",
            "bio",
            "-At",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            wrapped,
        ],
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


def classify_table(name: str, load_mode: str | None) -> str:
    if name.startswith("matrix_"):
        return "组学矩阵"
    if name.startswith("tcga_cdr_") or "clinical" in name:
        return "临床/生存"
    if "maf" in name:
        return "突变"
    if "seg" in name or "abs_" in name or "snp6" in name:
        return "拷贝数"
    if "rppa" in name:
        return "蛋白"
    if "mirna" in name:
        return "miRNA"
    if load_mode == "xlsx_text_columns":
        return "补充表"
    return "元数据"


def fmt_int(value) -> str:
    return f"{int(value or 0):,}"


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def js(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_report_data():
    table_stats = run_psql_json(
        """
        SELECT
          s.relname AS table_name,
          s.n_live_tup::bigint AS row_count,
          c.relpersistence AS persistence,
          pg_total_relation_size(c.oid)::bigint AS bytes,
          pg_size_pretty(pg_total_relation_size(c.oid)) AS size_pretty,
          COUNT(col.column_name)::int AS column_count,
          m.source_file,
          m.load_mode,
          m.note
        FROM pg_stat_user_tables s
        JOIN pg_class c ON c.relname = s.relname
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = s.schemaname
        LEFT JOIN information_schema.columns col
          ON col.table_schema = s.schemaname AND col.table_name = s.relname
        LEFT JOIN bio_tcga.import_manifest m ON m.table_name = s.relname
        WHERE s.schemaname = 'bio_tcga'
        GROUP BY s.relname, s.n_live_tup, c.oid, c.relpersistence, m.source_file, m.load_mode, m.note
        ORDER BY s.relname
        """
    )
    for row in table_stats:
        row["category"] = classify_table(row["table_name"], row.get("load_mode"))
        row["persistence_label"] = "UNLOGGED" if row.get("persistence") == "u" else "LOGGED"

    column_stats = run_psql_json(
        """
        SELECT table_name, COUNT(*)::int AS column_count
        FROM information_schema.columns
        WHERE table_schema = 'bio_tcga'
        GROUP BY table_name
        ORDER BY column_count DESC, table_name
        """
    )
    clinical_columns = run_psql_json(
        """
        SELECT column_name, ordinal_position
        FROM information_schema.columns
        WHERE table_schema = 'bio_tcga'
          AND table_name = 'tcga_cdr_tcga_cdr'
        ORDER BY ordinal_position
        """
    )
    type_distribution = run_psql_json(
        """
        SELECT COALESCE(NULLIF(type, ''), '(missing)') AS cancer_type, COUNT(*)::int AS patient_count
        FROM bio_tcga.tcga_cdr_tcga_cdr
        GROUP BY COALESCE(NULLIF(type, ''), '(missing)')
        ORDER BY patient_count DESC, cancer_type
        """
    )
    vital_distribution = run_psql_json(
        """
        SELECT COALESCE(NULLIF(vital_status, ''), '(missing)') AS vital_status, COUNT(*)::int AS patient_count
        FROM bio_tcga.tcga_cdr_tcga_cdr
        GROUP BY COALESCE(NULLIF(vital_status, ''), '(missing)')
        ORDER BY patient_count DESC, vital_status
        """
    )
    age_summary = run_psql_json(
        """
        SELECT
          COUNT(*) FILTER (WHERE age_at_initial_pathologic_diagnosis ~ '^[0-9]+(\\.[0-9]+)?$')::int AS numeric_count,
          ROUND(AVG(age_at_initial_pathologic_diagnosis::numeric), 1)::text AS avg_age,
          MIN(age_at_initial_pathologic_diagnosis::numeric)::text AS min_age,
          MAX(age_at_initial_pathologic_diagnosis::numeric)::text AS max_age
        FROM bio_tcga.tcga_cdr_tcga_cdr
        WHERE age_at_initial_pathologic_diagnosis ~ '^[0-9]+(\\.[0-9]+)?$'
        """
    )
    matrix_samples = run_psql_json(
        """
        SELECT 'RNA-seq gene expression' AS matrix_name, COUNT(*)::int AS sample_count
        FROM bio_tcga.matrix_rnaseq_gene_expression_samples
        UNION ALL
        SELECT 'Methylation 450 beta', COUNT(*)::int
        FROM bio_tcga.matrix_methylation450_beta_samples
        UNION ALL
        SELECT 'Methylation 27+450 beta', COUNT(*)::int
        FROM bio_tcga.matrix_methylation27_450_beta_samples
        UNION ALL
        SELECT 'miRNA EBadj', COUNT(*)::int
        FROM bio_tcga.matrix_mirna_ebadj_samples
        UNION ALL
        SELECT 'merge_merged_reals', COUNT(*)::int
        FROM bio_tcga.matrix_merge_merged_reals_samples
        ORDER BY sample_count DESC
        """
    )
    sample_rows = run_psql_json(
        """
        SELECT bcr_patient_barcode, type, age_at_initial_pathologic_diagnosis, gender, vital_status, os, os_time
        FROM bio_tcga.tcga_cdr_tcga_cdr
        ORDER BY bcr_patient_barcode
        LIMIT 8
        """
    )
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "table_stats": table_stats,
        "column_stats": column_stats,
        "clinical_columns": clinical_columns,
        "type_distribution": type_distribution,
        "vital_distribution": vital_distribution,
        "age_summary": age_summary[0] if age_summary else {},
        "matrix_samples": matrix_samples,
        "sample_rows": sample_rows,
    }


def render_table(rows, headers, fields) -> str:
    body = []
    for row in rows:
        cells = "".join(f"<td>{esc(row.get(field))}</td>" for field in fields)
        body.append(f"<tr>{cells}</tr>")
    head = "".join(f"<th>{esc(label)}</th>" for label in headers)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_report(data, echarts_src: str) -> str:
    table_stats = data["table_stats"]
    total_tables = len(table_stats)
    total_rows = sum(int(row["row_count"] or 0) for row in table_stats)
    total_bytes = sum(int(row["bytes"] or 0) for row in table_stats)
    total_columns = sum(int(row["column_count"] or 0) for row in table_stats)
    largest = sorted(table_stats, key=lambda r: int(r["row_count"] or 0), reverse=True)[:10]
    category_counts = {}
    for row in table_stats:
        category_counts.setdefault(row["category"], {"tables": 0, "rows": 0})
        category_counts[row["category"]]["tables"] += 1
        category_counts[row["category"]]["rows"] += int(row["row_count"] or 0)

    category_chart = [{"name": k, "value": v["tables"]} for k, v in category_counts.items()]
    largest_labels = [row["table_name"] for row in largest]
    largest_values = [int(row["row_count"] or 0) for row in largest]
    widest = data["column_stats"][:10]
    type_top = data["type_distribution"][:15]
    clinical_field_rows = [
        {
            "field": "type",
            "meaning": "TCGA 癌种/项目简称，例如 BRCA 表示 Breast Invasive Carcinoma，LUAD 表示 Lung Adenocarcinoma。",
            "use": "最适合作为初级分组字段，用来按癌种统计样本数、比较临床结局或连接多组学矩阵样本。",
        },
        {
            "field": "bcr_patient_barcode",
            "meaning": "TCGA 病人条形码，是连接临床、突变、表达、甲基化等表的核心患者级 ID。",
            "use": "可与样本条形码的前 12 个字符对齐，做跨组学整合。",
        },
        {
            "field": "vital_status",
            "meaning": "随访时患者状态，常见值为 Alive 或 Dead。",
            "use": "生存分析的基础字段，通常和 os/os_time 联合使用。",
        },
        {
            "field": "os / os_time",
            "meaning": "Overall Survival 事件标记和对应时间。",
            "use": "用于初级总体生存结局分析；正式建模前需要检查缺失和随访口径。",
        },
        {
            "field": "values_text",
            "meaning": "超宽组学矩阵的数值向量。每行对应一个 feature，向量位置与同名 *_samples 表的 sample_index 对齐。",
            "use": "避免 PostgreSQL 单表上万列限制；分析某个样本时按 sample_index 取值。",
        },
    ]

    type_notes = (
        "本报告选择 `tcga_cdr_tcga_cdr.type` 做字段分析，因为它是最直观的 TCGA 癌种分组字段。"
        "它不是测序质量字段，而是临床/项目标签；后续做表达、突变或甲基化比较时，通常先用它定义队列。"
    )
    matrix_note = (
        "RNA-seq、甲基化和 miRNA 这类矩阵原始文件列数可达上万。导入时采用 feature 行 + sample 索引表的结构，"
        "这是为了绕开 PostgreSQL 单表列数限制，也让原始矩阵更容易保留。"
    )
    bio_note = (
        "从生信角度看，这个 schema 同时包含 clinical endpoint、MAF 突变、segment copy number、RPPA 蛋白、RNA/miRNA/甲基化矩阵。"
        "这些数据来源主要是 TCGA/PanCanAtlas，样本条形码是跨表整合的主线。"
    )

    table_rows = [
        {
            "table_name": row["table_name"],
            "category": row["category"],
            "rows": fmt_int(row["row_count"]),
            "columns": fmt_int(row["column_count"]),
            "size": row["size_pretty"],
            "mode": row.get("load_mode") or "",
            "persistence": row["persistence_label"],
        }
        for row in table_stats
    ]
    sample_rows = [
        {
            **row,
            "os": "event" if str(row.get("os")) == "1" else ("censored" if str(row.get("os")) == "0" else row.get("os")),
        }
        for row in data["sample_rows"]
    ]

    css = """
    :root { --ink:#17212b; --muted:#607080; --line:#d8e0e8; --panel:#f6f8fb; --accent:#1769aa; --accent2:#218380; }
    * { box-sizing: border-box; }
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; color:var(--ink); background:#ffffff; }
    header { padding:32px 40px 22px; border-bottom:1px solid var(--line); background:#f9fbfd; }
    main { padding:28px 40px 48px; max-width:1280px; margin:0 auto; }
    h1 { margin:0 0 10px; font-size:30px; letter-spacing:0; }
    h2 { margin:34px 0 14px; font-size:22px; }
    h3 { margin:22px 0 10px; font-size:17px; }
    p { line-height:1.65; color:#2a3744; }
    .meta { color:var(--muted); font-size:14px; }
    .grid { display:grid; gap:14px; }
    .cards { grid-template-columns:repeat(4,minmax(0,1fr)); margin-top:18px; }
    .card { border:1px solid var(--line); border-radius:8px; padding:16px; background:#fff; }
    .card .label { color:var(--muted); font-size:13px; }
    .card .value { font-size:26px; font-weight:700; margin-top:8px; }
    .note { border-left:4px solid var(--accent2); background:#f2fbfa; padding:12px 14px; margin:14px 0; }
    .charts { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .chart { min-height:390px; border:1px solid var(--line); border-radius:8px; background:#fff; padding:8px; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; }
    th { background:var(--panel); color:#314253; font-weight:650; }
    code { background:#eef3f7; padding:1px 5px; border-radius:4px; }
    .two { grid-template-columns:1fr 1fr; }
    .footer { color:var(--muted); margin-top:36px; font-size:13px; }
    @media (max-width: 900px) { header, main { padding-left:18px; padding-right:18px; } .cards, .charts, .two { grid-template-columns:1fr; } }
    """
    html_doc = f"""<!doctype html>
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
    <div class="meta">生成时间：{esc(data["generated_at"])} · 数据库：PostgreSQL 容器 bio-postgres · schema：bio_tcga</div>
  </header>
  <main>
    <section>
      <h2>1. Schema 总览</h2>
      <p>{esc(bio_note)}</p>
      <div class="grid cards">
        <div class="card"><div class="label">表数量</div><div class="value">{fmt_int(total_tables)}</div></div>
        <div class="card"><div class="label">估算总行数</div><div class="value">{fmt_int(total_rows)}</div></div>
        <div class="card"><div class="label">字段总数</div><div class="value">{fmt_int(total_columns)}</div></div>
        <div class="card"><div class="label">schema 体积</div><div class="value">{fmt_int(total_bytes / 1024 / 1024 / 1024)} GB</div></div>
      </div>
      <div class="grid charts" style="margin-top:16px">
        <div id="rowsChart" class="chart"></div>
        <div id="categoryChart" class="chart"></div>
        <div id="columnsChart" class="chart"></div>
        <div id="matrixSamplesChart" class="chart"></div>
      </div>
    </section>

    <section>
      <h2>2. 初级字段分析：<code>tcga_cdr_tcga_cdr.type</code></h2>
      <p>{esc(type_notes)}</p>
      <div class="note"><strong>字段解释：</strong><code>type</code> 是 TCGA 癌种项目简称。它用于描述每条患者临床记录属于哪个癌种队列，不是测序平台字段，也不是样本质量字段。</div>
      <div class="grid two">
        <div id="typeChart" class="chart"></div>
        <div id="vitalChart" class="chart"></div>
      </div>
      <h3>常用字段解释</h3>
      {render_table(clinical_field_rows, ["字段", "含义", "初级用途"], ["field", "meaning", "use"])}
    </section>

    <section>
      <h2>3. 组学矩阵结构说明</h2>
      <p>{esc(matrix_note)}</p>
      <div class="note">读取矩阵时，可以先在 <code>*_samples</code> 表中找到目标样本的 <code>sample_index</code>，再按 tab 拆分主表 <code>values_text</code>，取对应位置的值。</div>
    </section>

    <section>
      <h2>4. 临床表样例</h2>
      {render_table(sample_rows, ["患者条形码", "癌种 type", "诊断年龄", "性别", "生存状态", "OS", "OS 时间"], ["bcr_patient_barcode", "type", "age_at_initial_pathologic_diagnosis", "gender", "vital_status", "os", "os_time"])}
    </section>

    <section>
      <h2>5. 表清单</h2>
      {render_table(table_rows, ["表", "类别", "行数", "字段数", "体积", "导入模式", "持久化"], ["table_name", "category", "rows", "columns", "size", "mode", "persistence"])}
    </section>

    <p class="footer">说明：本报告是第一份 data analysis 报告，面向 schema 初识和字段理解。大表行数来自 PostgreSQL 统计信息，适合概览；正式审计可对目标表单独 count。</p>
  </main>
  <script>
    const largestLabels = {js(largest_labels)};
    const largestValues = {js(largest_values)};
    const categoryData = {js(category_chart)};
    const columnLabels = {js([row["table_name"] for row in widest])};
    const columnValues = {js([int(row["column_count"]) for row in widest])};
    const typeLabels = {js([row["cancer_type"] for row in type_top])};
    const typeValues = {js([int(row["patient_count"]) for row in type_top])};
    const vitalData = {js([{"name": row["vital_status"], "value": int(row["patient_count"])} for row in data["vital_distribution"]])};
    const matrixLabels = {js([row["matrix_name"] for row in data["matrix_samples"]])};
    const matrixValues = {js([int(row["sample_count"]) for row in data["matrix_samples"]])};

    function bar(id, title, labels, values, color) {{
      const chart = echarts.init(document.getElementById(id));
      chart.setOption({{
        title: {{ text: title, left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
        tooltip: {{ trigger: 'axis' }},
        grid: {{ left: 76, right: 24, top: 56, bottom: 86 }},
        xAxis: {{ type: 'category', data: labels, axisLabel: {{ rotate: 40, interval: 0 }} }},
        yAxis: {{ type: 'value' }},
        series: [{{ type: 'bar', data: values, itemStyle: {{ color }} }}]
      }});
      return chart;
    }}
    function pie(id, title, data) {{
      const chart = echarts.init(document.getElementById(id));
      chart.setOption({{
        title: {{ text: title, left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
        tooltip: {{ trigger: 'item' }},
        legend: {{ type: 'scroll', bottom: 0 }},
        series: [{{ type: 'pie', radius: ['38%', '68%'], center: ['50%', '48%'], data }}]
      }});
      return chart;
    }}
    const charts = [
      bar('rowsChart', '行数最多的表 Top 10', largestLabels, largestValues, '#1769aa'),
      pie('categoryChart', '表类型分布', categoryData),
      bar('columnsChart', '字段数最多的表 Top 10', columnLabels, columnValues, '#218380'),
      bar('matrixSamplesChart', '矩阵样本数', matrixLabels, matrixValues, '#7b4ea3'),
      bar('typeChart', 'type 字段：患者数最多的癌种 Top 15', typeLabels, typeValues, '#c8553d'),
      pie('vitalChart', 'vital_status 分布', vitalData)
    ];
    window.addEventListener('resize', () => charts.forEach(chart => chart.resize()));
  </script>
</body>
</html>
"""
    return html_doc


def render_report_list(report_href: str, data) -> str:
    css = """
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; color:#17212b; background:#fff; }
    main { max-width:920px; margin:0 auto; padding:36px 24px; }
    h1 { font-size:28px; margin:0 0 8px; }
    .meta { color:#607080; margin-bottom:22px; }
    a.card { display:block; text-decoration:none; color:inherit; border:1px solid #d8e0e8; border-radius:8px; padding:18px; background:#f9fbfd; }
    a.card:hover { border-color:#1769aa; }
    .title { font-size:18px; font-weight:700; margin-bottom:8px; }
    .desc { color:#384858; line-height:1.55; }
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Data Analysis 报告清单</title><style>{css}</style></head>
<body><main>
  <h1>Data Analysis 报告清单</h1>
  <div class="meta">当前共有 1 份报告 · 最近更新：{esc(data["generated_at"])}</div>
  <a class="card" href="{esc(report_href)}">
    <div class="title">1. {REPORT_TITLE}</div>
    <div class="desc">本地 PostgreSQL 容器中 bio_tcga schema 的初级概览，包括表规模、数据类型、TCGA 临床字段 type 的解释和癌种分布图。</div>
  </a>
</main></body></html>
"""


def render_index(data) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=report-list.html">
  <title>Data Analysis</title>
</head>
<body>
  <p><a href="report-list.html">打开 Data Analysis 报告清单</a></p>
</body>
</html>
"""


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    data = build_report_data()
    echarts_src = ensure_echarts_asset()
    report_path = REPORTS_DIR / REPORT_FILENAME
    report_path.write_text(render_report(data, echarts_src), encoding="utf-8")
    report_list_path = REPORT_DIR / "report-list.html"
    report_list_path.write_text(render_report_list(f"reports/{REPORT_FILENAME}", data), encoding="utf-8")
    index_path = REPORT_DIR / "index.html"
    index_path.write_text(render_index(data), encoding="utf-8")
    print(f"report={report_path}")
    print(f"report_list={report_list_path}")
    print(f"index={index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
