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
REPORT_TITLE = "TCGA Schema Basic Analysis Report"
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
        return "Omics matrix"
    if name.startswith("tcga_cdr_") or "clinical" in name:
        return "Clinical/survival"
    if "maf" in name:
        return "Mutation"
    if "seg" in name or "abs_" in name or "snp6" in name:
        return "Copy number"
    if "rppa" in name:
        return "Protein"
    if "mirna" in name:
        return "miRNA"
    if load_mode == "xlsx_text_columns":
        return "Supplement table"
    return "Metadata"


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
            "meaning": "TCGA cancer type or project abbreviation, for example BRCA means Breast Invasive Carcinoma and LUAD means Lung Adenocarcinoma.",
            "use": "Best used as an entry-level grouping field for counting samples by cancer type, comparing clinical outcomes, or linking multi-omics matrix samples.",
        },
        {
            "field": "bcr_patient_barcode",
            "meaning": "TCGA patient barcode, the core patient-level ID for linking clinical, mutation, expression, methylation, and other tables.",
            "use": "Can be aligned with the first 12 characters of sample barcodes for cross-omics integration.",
        },
        {
            "field": "vital_status",
            "meaning": "Patient status at follow-up, commonly Alive or Dead.",
            "use": "A basic survival-analysis field, usually used together with os and os_time.",
        },
        {
            "field": "os / os_time",
            "meaning": "Overall Survival event flag and corresponding time.",
            "use": "Used for basic overall-survival outcome analysis; missingness and follow-up definitions should be checked before formal modeling.",
        },
        {
            "field": "values_text",
            "meaning": "Value vector for ultra-wide omics matrices. Each row maps to one feature, and vector positions align with sample_index in the matching *_samples table.",
            "use": "Avoids PostgreSQL table-width limits; retrieve a sample value by using sample_index.",
        },
    ]
    glossary_rows = [
        {"term": "TCGA", "plain": "The Cancer Genome Atlas, a big public cancer data project."},
        {"term": "Schema", "plain": "A named folder inside a database that groups related tables."},
        {"term": "Table", "plain": "A spreadsheet-like object in a database: rows are records, columns are fields."},
        {"term": "Field / Column", "plain": "One kind of information stored for every record, like age or cancer type."},
        {"term": "Record / Row", "plain": "One entry in a table, like one patient or one mutation."},
        {"term": "Cohort", "plain": "A group of patients or samples chosen for the same study question."},
        {"term": "Barcode", "plain": "A TCGA ID string that labels a patient, tumor sample, or normal sample."},
        {"term": "Clinical endpoint", "plain": "A health outcome used in analysis, such as survival or recurrence."},
        {"term": "OS", "plain": "Overall Survival: whether and when a patient died after diagnosis or treatment."},
        {"term": "DSS", "plain": "Disease-Specific Survival: death counted only if it is related to the cancer."},
        {"term": "DFI", "plain": "Disease-Free Interval: time before cancer comes back after being disease-free."},
        {"term": "PFI", "plain": "Progression-Free Interval: time before the cancer gets worse or returns."},
        {"term": "RNA-seq", "plain": "A sequencing method that measures which genes are turned on and how strongly."},
        {"term": "miRNA", "plain": "Small RNA molecules that help control gene expression."},
        {"term": "Methylation", "plain": "Chemical tags on DNA that can change how active a gene is."},
        {"term": "RPPA", "plain": "A lab method that measures protein levels in many samples."},
        {"term": "CNV / Copy number", "plain": "When parts of the genome are copied extra times or deleted in cancer cells."},
        {"term": "MAF", "plain": "Mutation Annotation Format, a table format for DNA mutation records."},
        {"term": "Feature", "plain": "The measured thing in a matrix, such as a gene or methylation probe."},
        {"term": "sample_index", "plain": "A number telling which sample position matches a value in a long vector."},
        {"term": "UNLOGGED table", "plain": "A faster PostgreSQL table that writes less recovery log; okay for reloadable local data."},
    ]

    type_notes = (
        "This report analyzes `tcga_cdr_tcga_cdr.type` because it is the most direct TCGA cancer-type grouping field."
        "It is not a sequencing-quality field; it is a clinical/project label. Expression, mutation, and methylation comparisons usually start by using it to define cohorts."
    )
    matrix_note = (
        "Raw RNA-seq, methylation, and miRNA matrices can contain tens of thousands of columns. The import uses feature rows plus a sample-index table, "
        "which avoids PostgreSQL table-column limits and keeps the original matrix easier to preserve."
    )
    bio_note = (
        "From a bioinformatics perspective, this schema contains clinical endpoints, MAF mutations, segment copy number, RPPA protein data, and RNA/miRNA/methylation matrices."
        "The data mainly comes from TCGA/PanCanAtlas, and sample barcodes are the main key for cross-table integration."
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
    .back-link { display:inline-block; margin-bottom:14px; color:var(--accent); font-weight:700; text-decoration:none; }
    .back-link:hover { text-decoration:underline; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; }
    th { background:var(--panel); color:#314253; font-weight:650; }
    code { background:#eef3f7; padding:1px 5px; border-radius:4px; }
    .two { grid-template-columns:1fr 1fr; }
    .footer { color:var(--muted); margin-top:36px; font-size:13px; }
    @media (max-width: 900px) { header, main { padding-left:18px; padding-right:18px; } .cards, .charts, .two { grid-template-columns:1fr; } }
    """
    html_doc = f"""<!doctype html>
<html lang="en">
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
    <div class="meta">Generated at: {esc(data["generated_at"])} · Database: PostgreSQL container bio-postgres · schema: bio_tcga</div>
  </header>
  <main>
    <a class="back-link" href="/#analysis">← Back to report list</a>
    <section>
      <h2>1. Schema Overview</h2>
      <p>{esc(bio_note)}</p>
      <div class="grid cards">
        <div class="card"><div class="label">Tables</div><div class="value">{fmt_int(total_tables)}</div></div>
        <div class="card"><div class="label">Estimated Rows</div><div class="value">{fmt_int(total_rows)}</div></div>
        <div class="card"><div class="label">Total Fields</div><div class="value">{fmt_int(total_columns)}</div></div>
        <div class="card"><div class="label">Schema Size</div><div class="value">{fmt_int(total_bytes / 1024 / 1024 / 1024)} GB</div></div>
      </div>
      <div class="grid charts" style="margin-top:16px">
        <div id="rowsChart" class="chart"></div>
        <div id="categoryChart" class="chart"></div>
        <div id="columnsChart" class="chart"></div>
        <div id="matrixSamplesChart" class="chart"></div>
      </div>
    </section>

    <section>
      <h2>2. Entry-Level Field Analysis: <code>tcga_cdr_tcga_cdr.type</code></h2>
      <p>{esc(type_notes)}</p>
      <div class="note"><strong>Field explanation:</strong> <code>type</code> is the TCGA cancer-project abbreviation. It describes which cancer cohort each clinical patient record belongs to; it is not a sequencing-platform or sample-quality field.</div>
      <div class="grid two">
        <div id="typeChart" class="chart"></div>
        <div id="vitalChart" class="chart"></div>
      </div>
      <h3>Common Field Explanations</h3>
      {render_table(clinical_field_rows, ["Field", "Meaning", "Basic use"], ["field", "meaning", "use"])}
    </section>

    <section>
      <h2>3. Omics Matrix Structure</h2>
      <p>{esc(matrix_note)}</p>
      <div class="note">When reading a matrix, first find the target sample's <code>sample_index</code> in the <code>*_samples</code> table, then split the main table's <code>values_text</code> by tab and retrieve the value at that position.</div>
    </section>

    <section>
      <h2>4. Clinical Table Example</h2>
      {render_table(sample_rows, ["Patient Barcode", "Cancer Type", "Age at Diagnosis", "Gender", "Vital Status", "OS", "OS Time"], ["bcr_patient_barcode", "type", "age_at_initial_pathologic_diagnosis", "gender", "vital_status", "os", "os_time"])}
    </section>

    <section>
      <h2>5. Abbreviations And Terms</h2>
      <p>These terms are explained in classroom-style language. Once the question behind each term is clear, the charts become easier to read.</p>
      {render_table(glossary_rows, ["Term / abbreviation", "Plain English explanation"], ["term", "plain"])}
    </section>

    <section>
      <h2>6. Table Inventory</h2>
      {render_table(table_rows, ["Table", "Category", "Rows", "Fields", "Size", "Import Mode", "Persistence"], ["table_name", "category", "rows", "columns", "size", "mode", "persistence"])}
    </section>

    <p class="footer">Note: this is the first data analysis report, focused on schema orientation and field understanding. Large-table row counts come from PostgreSQL statistics and are suitable for overview; formal audits can run exact counts on target tables.</p>
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
      bar('rowsChart', 'Top 10 Tables By Row Count', largestLabels, largestValues, '#1769aa'),
      pie('categoryChart', 'Table Category Distribution', categoryData),
      bar('columnsChart', 'Top 10 Tables By Field Count', columnLabels, columnValues, '#218380'),
      bar('matrixSamplesChart', 'Matrix Sample Counts', matrixLabels, matrixValues, '#7b4ea3'),
      bar('typeChart', 'type Field: Top 15 Cancer Types By Patient Count', typeLabels, typeValues, '#c8553d'),
      pie('vitalChart', 'vital_status Distribution', vitalData)
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
    a.card { display:block; text-decoration:none; color:inherit; border:1px solid #d8e0e8; border-radius:8px; padding:18px; background:#f9fbfd; margin-bottom:12px; }
    a.card:hover { border-color:#1769aa; }
    .title { font-size:18px; font-weight:700; margin-bottom:8px; }
    .desc { color:#384858; line-height:1.55; }
    """
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Data Analysis Report List</title><style>{css}</style></head>
<body><main>
  <h1>Data Analysis Report List</h1>
  <div class="meta">3 reports available · Last updated: {esc(data["generated_at"])}</div>
  <a class="card" href="{esc(report_href)}">
    <div class="title">1. {REPORT_TITLE}</div>
    <div class="desc">An entry-level overview of the bio_tcga schema in the local PostgreSQL container, including table scale, data types, the TCGA clinical type field, and cancer-type distributions.</div>
  </a>
  <a class="card" href="reports/tcga_mc3_sequencing_deep_dive.html">
    <div class="title">2. TCGA MC3 Cancer Sequencing Mutation Table Deep Dive</div>
    <div class="desc">A deeper analysis of the MC3 MAF cancer sequencing mutation table, covering variant types, cancer types, genes, chromosomes, VAF, caller support, and all 114 fields.</div>
  </a>
  <a class="card" href="reports/tcga_coad_integrated_analysis.html">
    <div class="title">3. TCGA COAD Sequencing And Multi-Omics Integrated Analysis</div>
    <div class="desc">A COAD-focused report integrating clinical data, MC3 sequencing mutations, multi-omics sample coverage, sample-quality annotations, and term explanations.</div>
  </a>
</main></body></html>
"""


def render_index(data) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=report-list.html">
  <title>Data Analysis</title>
</head>
<body>
  <p><a href="report-list.html">Open the Data Analysis report list</a></p>
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
