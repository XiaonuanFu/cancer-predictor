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
REPORT_FILENAME = "tcga_coad_integrated_analysis.html"
REPORT_TITLE = "TCGA COAD Sequencing And Multi-Omics Integrated Analysis"
ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"


def run_json(sql: str):
    wrapped = f"SELECT COALESCE(json_agg(row_to_json(q)), '[]'::json) FROM ({sql}) q;"
    result = subprocess.run(
        ["docker", "exec", "bio-postgres", "psql", "-U", "bio", "-d", "bio", "-At", "-v", "ON_ERROR_STOP=1", "-c", wrapped],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip() or "[]")


def run_sql(sql: str):
    subprocess.run(
        ["docker", "exec", "bio-postgres", "psql", "-U", "bio", "-d", "bio", "-v", "ON_ERROR_STOP=1", "-c", sql],
        check=True,
        capture_output=True,
        text=True,
    )


def prepare_coad_cache():
    run_sql(
        """
        DROP TABLE IF EXISTS bio_tcga._report_coad_mc3_maf_cache;
        CREATE UNLOGGED TABLE bio_tcga._report_coad_mc3_maf_cache AS
        SELECT
          substring(m.tumor_sample_barcode from 1 for 12) AS patient_barcode,
          m.tumor_sample_barcode,
          m.hugo_symbol,
          m.variant_classification,
          m.variant_type,
          m.chromosome,
          m.start_position,
          m.hgvsp_short,
          m.t_depth,
          m.t_alt_count,
          m.ncallers
        FROM bio_tcga.mc3_public_maf m
        JOIN bio_tcga.tcga_cdr_tcga_cdr c
          ON c.type = 'COAD'
         AND c.bcr_patient_barcode = substring(m.tumor_sample_barcode from 1 for 12);
        CREATE INDEX ON bio_tcga._report_coad_mc3_maf_cache(patient_barcode);
        CREATE INDEX ON bio_tcga._report_coad_mc3_maf_cache(tumor_sample_barcode);
        CREATE INDEX ON bio_tcga._report_coad_mc3_maf_cache(hugo_symbol);
        ANALYZE bio_tcga._report_coad_mc3_maf_cache;
        """
    )


def drop_coad_cache():
    run_sql("DROP TABLE IF EXISTS bio_tcga._report_coad_mc3_maf_cache;")


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


def render_table(rows, headers, fields) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{esc(row.get(f))}</td>" for f in fields) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def build_data():
    prepare_coad_cache()
    summary = run_json(
        """
        SELECT
          (SELECT count(*) FROM bio_tcga.tcga_cdr_tcga_cdr WHERE type = 'COAD')::bigint AS clinical_patients,
          (SELECT count(*) FROM bio_tcga._report_coad_mc3_maf_cache)::bigint AS mutation_records,
          (SELECT count(distinct tumor_sample_barcode) FROM bio_tcga._report_coad_mc3_maf_cache)::bigint AS tumor_samples,
          (SELECT count(distinct patient_barcode) FROM bio_tcga._report_coad_mc3_maf_cache)::bigint AS mutated_patients,
          (SELECT count(distinct hugo_symbol) FROM bio_tcga._report_coad_mc3_maf_cache)::bigint AS mutated_genes
        """
    )[0]
    clinical_gender = run_json(
        """
        SELECT gender AS label, count(*)::int AS value
        FROM bio_tcga.tcga_cdr_tcga_cdr
        WHERE type='COAD'
        GROUP BY gender
        ORDER BY value DESC
        """
    )
    clinical_vital = run_json(
        """
        SELECT vital_status AS label, count(*)::int AS value
        FROM bio_tcga.tcga_cdr_tcga_cdr
        WHERE type='COAD'
        GROUP BY vital_status
        ORDER BY value DESC
        """
    )
    clinical_stage = run_json(
        """
        SELECT COALESCE(NULLIF(ajcc_pathologic_tumor_stage,''),'(missing)') AS label, count(*)::int AS value
        FROM bio_tcga.tcga_cdr_tcga_cdr
        WHERE type='COAD'
        GROUP BY COALESCE(NULLIF(ajcc_pathologic_tumor_stage,''),'(missing)')
        ORDER BY value DESC
        LIMIT 16
        """
    )
    age_bins = run_json(
        """
        WITH ages AS (
          SELECT age_at_initial_pathologic_diagnosis::int AS age
          FROM bio_tcga.tcga_cdr_tcga_cdr
          WHERE type='COAD' AND age_at_initial_pathologic_diagnosis ~ '^[0-9]+$'
        )
        SELECT bucket AS label, count(*)::int AS value
        FROM (
          SELECT CASE
            WHEN age < 40 THEN '<40'
            WHEN age < 50 THEN '40-49'
            WHEN age < 60 THEN '50-59'
            WHEN age < 70 THEN '60-69'
            WHEN age < 80 THEN '70-79'
            ELSE '80+'
          END AS bucket,
          CASE
            WHEN age < 40 THEN 1 WHEN age < 50 THEN 2 WHEN age < 60 THEN 3
            WHEN age < 70 THEN 4 WHEN age < 80 THEN 5 ELSE 6 END AS ord
          FROM ages
        ) b
        GROUP BY bucket, ord
        ORDER BY ord
        """
    )
    omics_coverage = run_json(
        """
        WITH coad AS (
          SELECT bcr_patient_barcode FROM bio_tcga.tcga_cdr_tcga_cdr WHERE type='COAD'
        )
        SELECT 'Clinical CDR patients' AS label, count(*)::int AS value FROM coad
        UNION ALL
        SELECT 'MC3 mutation tumor samples', count(distinct m.tumor_sample_barcode)::int
        FROM bio_tcga._report_coad_mc3_maf_cache m
        UNION ALL
        SELECT 'RNA-seq samples', count(*)::int
        FROM bio_tcga.matrix_rnaseq_gene_expression_samples s JOIN coad c ON substring(s.sample_id from 1 for 12)=c.bcr_patient_barcode
        UNION ALL
        SELECT 'miRNA samples', count(*)::int
        FROM bio_tcga.matrix_mirna_ebadj_samples s JOIN coad c ON substring(s.sample_id from 1 for 12)=c.bcr_patient_barcode
        UNION ALL
        SELECT 'Methylation 450 samples', count(*)::int
        FROM bio_tcga.matrix_methylation450_beta_samples s JOIN coad c ON substring(s.sample_id from 1 for 12)=c.bcr_patient_barcode
        UNION ALL
        SELECT 'Methylation 27+450 samples', count(*)::int
        FROM bio_tcga.matrix_methylation27_450_beta_samples s JOIN coad c ON substring(s.sample_id from 1 for 12)=c.bcr_patient_barcode
        UNION ALL
        SELECT 'RPPA CORE samples', count(*)::int FROM bio_tcga.rppa_pancan_clean WHERE tumortype='CORE'
        UNION ALL
        SELECT 'Sample quality rows', count(*)::int FROM bio_tcga.sample_quality_annotations WHERE cancer_type='COAD'
        """
    )
    variant_classification = run_json(
        """
        SELECT variant_classification AS label, count(*)::bigint AS value
        FROM bio_tcga._report_coad_mc3_maf_cache
        GROUP BY variant_classification
        ORDER BY value DESC
        LIMIT 18
        """
    )
    variant_type = run_json(
        """
        SELECT variant_type AS label, count(*)::bigint AS value
        FROM bio_tcga._report_coad_mc3_maf_cache
        GROUP BY variant_type
        ORDER BY value DESC
        """
    )
    top_genes = run_json(
        """
        SELECT hugo_symbol AS label,
               count(*)::bigint AS variants,
               count(distinct patient_barcode)::bigint AS patients
        FROM bio_tcga._report_coad_mc3_maf_cache
        WHERE hugo_symbol NOT IN ('Unknown','')
        GROUP BY hugo_symbol
        ORDER BY patients DESC, variants DESC
        LIMIT 25
        """
    )
    chromosome = run_json(
        """
        SELECT chromosome AS label, count(*)::bigint AS value
        FROM bio_tcga._report_coad_mc3_maf_cache
        GROUP BY chromosome
        ORDER BY CASE WHEN chromosome ~ '^[0-9]+$' THEN chromosome::int ELSE 100 END, chromosome
        """
    )
    burden_bins = run_json(
        """
        WITH per_sample AS (
          SELECT tumor_sample_barcode, count(*)::int AS n
          FROM bio_tcga._report_coad_mc3_maf_cache
          GROUP BY tumor_sample_barcode
        )
        SELECT bucket AS label, count(*)::int AS value
        FROM (
          SELECT CASE
            WHEN n < 100 THEN '<100'
            WHEN n < 250 THEN '100-249'
            WHEN n < 500 THEN '250-499'
            WHEN n < 1000 THEN '500-999'
            WHEN n < 2000 THEN '1000-1999'
            ELSE '2000+'
          END AS bucket,
          CASE
            WHEN n < 100 THEN 1 WHEN n < 250 THEN 2 WHEN n < 500 THEN 3
            WHEN n < 1000 THEN 4 WHEN n < 2000 THEN 5 ELSE 6 END AS ord
          FROM per_sample
        ) b
        GROUP BY bucket, ord
        ORDER BY ord
        """
    )
    burden_summary = run_json(
        """
        WITH per_sample AS (
          SELECT tumor_sample_barcode, count(*)::int AS n
          FROM bio_tcga._report_coad_mc3_maf_cache
          GROUP BY tumor_sample_barcode
        )
        SELECT round(avg(n),1)::text AS avg_mutations,
               percentile_disc(0.5) within group (order by n)::int AS median_mutations,
               min(n)::int AS min_mutations,
               max(n)::int AS max_mutations
        FROM per_sample
        """
    )[0]
    vaf_bins = run_json(
        """
        WITH v AS (
          SELECT CASE WHEN t_depth ~ '^[0-9]+$' AND t_alt_count ~ '^[0-9]+$' AND t_depth::numeric > 0
                      THEN t_alt_count::numeric / t_depth::numeric END AS vaf
          FROM bio_tcga._report_coad_mc3_maf_cache
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
            ELSE '>=50%' END AS bucket,
          CASE
            WHEN vaf IS NULL THEN 99 WHEN vaf < 0.05 THEN 1 WHEN vaf < 0.10 THEN 2
            WHEN vaf < 0.20 THEN 3 WHEN vaf < 0.30 THEN 4 WHEN vaf < 0.50 THEN 5 ELSE 6 END AS ord
          FROM v
        ) b
        GROUP BY bucket, ord
        ORDER BY ord
        """
    )
    stage_gene_heatmap = run_json(
        """
        WITH coad AS (
          SELECT bcr_patient_barcode, COALESCE(NULLIF(ajcc_pathologic_tumor_stage,''),'(missing)') AS stage
          FROM bio_tcga.tcga_cdr_tcga_cdr
          WHERE type='COAD'
        ),
        top_genes AS (
          SELECT hugo_symbol
          FROM bio_tcga._report_coad_mc3_maf_cache m
          JOIN coad c ON c.bcr_patient_barcode=m.patient_barcode
          WHERE hugo_symbol NOT IN ('Unknown','')
          GROUP BY hugo_symbol
          ORDER BY count(distinct c.bcr_patient_barcode) DESC, count(*) DESC
          LIMIT 12
        ),
        top_stages AS (
          SELECT stage
          FROM coad
          GROUP BY stage
          ORDER BY count(*) DESC
          LIMIT 10
        ),
        agg AS (
          SELECT c.stage, m.hugo_symbol, count(distinct c.bcr_patient_barcode)::int AS value
          FROM bio_tcga._report_coad_mc3_maf_cache m
          JOIN coad c ON c.bcr_patient_barcode=m.patient_barcode
          JOIN top_genes tg ON tg.hugo_symbol=m.hugo_symbol
          JOIN top_stages ts ON ts.stage=c.stage
          GROUP BY c.stage, m.hugo_symbol
        )
        SELECT ts.stage, tg.hugo_symbol, COALESCE(agg.value,0)::int AS value
        FROM top_stages ts
        CROSS JOIN top_genes tg
        LEFT JOIN agg ON agg.stage=ts.stage AND agg.hugo_symbol=tg.hugo_symbol
        ORDER BY ts.stage, tg.hugo_symbol
        """
    )
    representative = run_json(
        """
        WITH coad AS (
          SELECT bcr_patient_barcode, ajcc_pathologic_tumor_stage, vital_status
          FROM bio_tcga.tcga_cdr_tcga_cdr
          WHERE type='COAD'
        )
        SELECT m.hugo_symbol, m.variant_classification, m.variant_type, m.chromosome,
               m.start_position, m.tumor_sample_barcode, c.ajcc_pathologic_tumor_stage,
               c.vital_status, m.hgvsp_short, m.t_depth, m.t_alt_count, m.ncallers
        FROM bio_tcga._report_coad_mc3_maf_cache m
        JOIN coad c ON c.bcr_patient_barcode=m.patient_barcode
        WHERE m.hugo_symbol IN ('APC','TP53','KRAS','PIK3CA','SMAD4')
        LIMIT 12
        """
    )
    quality_rows = run_json(
        """
        SELECT patient_barcode, aliquot_barcode, platform, patient_annotation, do_not_use
        FROM bio_tcga.sample_quality_annotations
        WHERE cancer_type='COAD'
        LIMIT 10
        """
    )
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "clinical_gender": clinical_gender,
        "clinical_vital": clinical_vital,
        "clinical_stage": clinical_stage,
        "age_bins": age_bins,
        "omics_coverage": omics_coverage,
        "variant_classification": variant_classification,
        "variant_type": variant_type,
        "top_genes": top_genes,
        "chromosome": chromosome,
        "burden_bins": burden_bins,
        "burden_summary": burden_summary,
        "vaf_bins": vaf_bins,
        "stage_gene_heatmap": stage_gene_heatmap,
        "representative": representative,
        "quality_rows": quality_rows,
    }


GLOSSARY = [
    {"term": "COAD", "plain": "Colon Adenocarcinoma, a common type of colon cancer."},
    {"term": "Adenocarcinoma", "plain": "Cancer that starts in gland-like cells that make mucus or fluids."},
    {"term": "TCGA", "plain": "The Cancer Genome Atlas, a public cancer data project."},
    {"term": "MC3", "plain": "A TCGA mutation dataset that combines calls from several mutation-finding tools."},
    {"term": "MAF", "plain": "Mutation Annotation Format; a mutation table where one row is usually one DNA change."},
    {"term": "Somatic mutation", "plain": "A DNA change that appears in tumor cells after birth, not inherited from parents."},
    {"term": "Matched normal", "plain": "Normal tissue or blood from the same person, used for comparison."},
    {"term": "Variant", "plain": "A DNA difference compared with the reference genome."},
    {"term": "SNP / SNV", "plain": "A one-letter DNA change, like C changing to T."},
    {"term": "INS / DEL", "plain": "Insertion means extra DNA letters; deletion means missing DNA letters."},
    {"term": "Missense", "plain": "A DNA change that swaps one amino acid in a protein."},
    {"term": "Nonsense", "plain": "A DNA change that creates an early stop signal in a protein."},
    {"term": "Frameshift", "plain": "An insertion/deletion that changes how DNA is read in groups of three."},
    {"term": "Tumor mutation burden", "plain": "How many mutations a tumor sample has."},
    {"term": "VAF", "plain": "Variant Allele Fraction: the fraction of sequencing reads that show the mutation."},
    {"term": "Depth", "plain": "How many sequencing reads cover a DNA position."},
    {"term": "Alt count", "plain": "How many reads support the mutated version."},
    {"term": "Caller", "plain": "Software that decides whether a DNA change is a real mutation."},
    {"term": "ncallers", "plain": "How many callers agreed on the same mutation."},
    {"term": "AJCC stage", "plain": "A cancer staging system; later stages usually mean cancer has spread more."},
    {"term": "OS", "plain": "Overall Survival: whether and when the patient died."},
    {"term": "RNA-seq", "plain": "Sequencing RNA to measure gene activity."},
    {"term": "Methylation", "plain": "Chemical tags on DNA that can affect gene activity."},
    {"term": "miRNA", "plain": "Small RNAs that help regulate genes."},
    {"term": "RPPA", "plain": "A method that measures protein levels across many samples."},
    {"term": "Adaptyv Bio", "plain": "A protein expression and binding assay service; useful later if you want to test mutation-derived protein ideas."},
]


def render_report(data, echarts_src: str) -> str:
    summary = data["summary"]
    burden = data["burden_summary"]
    heat_x = sorted({row["hugo_symbol"] for row in data["stage_gene_heatmap"]})
    heat_y = sorted({row["stage"] for row in data["stage_gene_heatmap"]})
    heat_values = [[heat_x.index(row["hugo_symbol"]), heat_y.index(row["stage"]), int(row["value"] or 0)] for row in data["stage_gene_heatmap"]]
    heat_max = max([item[2] for item in heat_values] or [1])
    top_gene_rows = [
        {"label": row["label"], "patients": fmt_int(row["patients"]), "variants": fmt_int(row["variants"])}
        for row in data["top_genes"][:15]
    ]
    representative = data["representative"]
    quality_rows = data["quality_rows"]
    css = """
    :root { --ink:#17212b; --muted:#5c6b78; --line:#d9e1e8; --panel:#f7f9fb; --blue:#1769aa; --green:#218380; --red:#c8553d; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:#fff; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; }
    header { padding:34px 42px 24px; background:#f8fafc; border-bottom:1px solid var(--line); }
    main { max-width:1320px; margin:0 auto; padding:28px 42px 52px; }
    h1 { margin:0 0 10px; font-size:30px; letter-spacing:0; }
    h2 { margin:34px 0 14px; font-size:22px; }
    p { line-height:1.66; color:#2d3a46; }
    .meta { color:var(--muted); font-size:14px; }
    .back-link { display:inline-block; margin-bottom:14px; color:var(--blue); font-weight:700; text-decoration:none; }
    .back-link:hover { text-decoration:underline; }
    .cards { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin:18px 0; }
    .card { border:1px solid var(--line); border-radius:8px; padding:15px; background:#fff; }
    .card span { display:block; color:var(--muted); font-size:12px; font-weight:700; text-transform:uppercase; }
    .card strong { display:block; margin-top:8px; font-size:24px; }
    .note { border-left:4px solid var(--green); background:#f2fbfa; padding:13px 15px; margin:14px 0; }
    .chart-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }
    .chart { min-height:390px; border:1px solid var(--line); border-radius:8px; padding:8px; background:#fff; }
    .wide { grid-column:1 / -1; min-height:520px; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { border-bottom:1px solid var(--line); padding:8px 9px; text-align:left; vertical-align:top; }
    th { background:var(--panel); color:#314253; }
    code { background:#eef3f7; padding:1px 5px; border-radius:4px; }
    .footer { margin-top:30px; color:var(--muted); font-size:13px; }
    @media (max-width: 920px) { header, main { padding-left:18px; padding-right:18px; } .cards, .chart-grid { grid-template-columns:1fr; } .wide { grid-column:auto; } }
    """
    return f"""<!doctype html>
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
    <div class="meta">Generated at: {esc(data["generated_at"])} · Cancer type: COAD / Colon Adenocarcinoma · Data source: bio_tcga schema</div>
  </header>
  <main>
    <a class="back-link" href="/#analysis">← Back to report list</a>
    <section>
      <h2>1. What This Report Covers</h2>
      <p>COAD is the colon adenocarcinoma cohort in TCGA. This report links COAD clinical information from <code>tcga_cdr_tcga_cdr</code>, cancer sequencing mutations from <code>mc3_public_maf</code>, and RNA-seq, miRNA, methylation, RPPA, and sample-quality annotation tables to support data-structure understanding and early biological signal review.</p>
      <div class="cards">
        <div class="card"><span>COAD Clinical Patients</span><strong>{fmt_int(summary["clinical_patients"])}</strong></div>
        <div class="card"><span>MC3 Mutation Records</span><strong>{fmt_int(summary["mutation_records"])}</strong></div>
        <div class="card"><span>Tumor Samples</span><strong>{fmt_int(summary["tumor_samples"])}</strong></div>
        <div class="card"><span>Patients With Mutations</span><strong>{fmt_int(summary["mutated_patients"])}</strong></div>
        <div class="card"><span>Mutated Genes</span><strong>{fmt_int(summary["mutated_genes"])}</strong></div>
      </div>
      <div class="note">Plain-language reading: this report does not make clinical conclusions. It answers which clinical, mutation, and other omics data can be reviewed together in the local COAD dataset.</div>
    </section>

    <section>
      <h2>2. Clinical And Multi-Omics Coverage</h2>
      <div class="chart-grid">
        <div id="genderChart" class="chart"></div>
        <div id="vitalChart" class="chart"></div>
        <div id="stageChart" class="chart"></div>
        <div id="ageChart" class="chart"></div>
        <div id="omicsChart" class="chart wide"></div>
      </div>
    </section>

    <section>
      <h2>3. COAD Sequencing Mutation Landscape</h2>
      <p>The COAD mutation table comes from MC3 MAF. A mutation record means that a tumor sample has a DNA change at a genomic position and that the change has been annotated to a gene or functional region.</p>
      <div class="chart-grid">
        <div id="variantClassChart" class="chart"></div>
        <div id="variantTypeChart" class="chart"></div>
        <div id="topGenesChart" class="chart"></div>
        <div id="chromosomeChart" class="chart"></div>
        <div id="burdenChart" class="chart"></div>
        <div id="vafChart" class="chart"></div>
        <div id="stageGeneHeatmap" class="chart wide"></div>
      </div>
      <div class="note">Common COAD driver pathways often involve APC, TP53, KRAS, PIK3CA, and SMAD4. This report shows count distributions in the local database; it is not a formal driver-gene call.</div>
    </section>

    <section>
      <h2>4. Mutation Burden Overview</h2>
      <p>In the local data, each COAD tumor sample has an average of about <strong>{esc(burden.get("avg_mutations"))}</strong> mutation records, with a median of about <strong>{esc(burden.get("median_mutations"))}</strong> and a range from <strong>{esc(burden.get("min_mutations"))}</strong> to <strong>{esc(burden.get("max_mutations"))}</strong>. Samples with especially high mutation counts can be checked later for MSI, POLE, sample quality, or sequencing coverage.</p>
    </section>

    <section>
      <h2>5. Top Mutated Genes</h2>
      {render_table(top_gene_rows, ["Gene", "Patients", "Mutation Records"], ["label", "patients", "variants"])}
    </section>

    <section>
      <h2>6. Representative COAD Mutation Records</h2>
      {render_table(representative, ["Gene", "Functional Class", "Type", "Chromosome", "Start", "Sample", "Stage", "Vital Status", "Protein Change", "Tumor Depth", "Alt Reads", "Callers"], ["hugo_symbol", "variant_classification", "variant_type", "chromosome", "start_position", "tumor_sample_barcode", "ajcc_pathologic_tumor_stage", "vital_status", "hgvsp_short", "t_depth", "t_alt_count", "ncallers"])}
    </section>

    <section>
      <h2>7. Sample Quality Annotation Examples</h2>
      <p>The sample-quality annotation table helps identify aliquots with pathology, platform, or exclusion notes. Formal analysis should prioritize filtering samples marked <code>do_not_use</code> or samples with clear exclusion reasons.</p>
      {render_table(quality_rows, ["Patient", "Aliquot", "Platform", "Patient Annotation", "do_not_use"], ["patient_barcode", "aliquot_barcode", "platform", "patient_annotation", "do_not_use"])}
    </section>

    <section>
      <h2>8. Abbreviations And Terms</h2>
      {render_table(GLOSSARY, ["Term / abbreviation", "Plain English explanation"], ["term", "plain"])}
    </section>

    <section>
      <h2>9. Next Analysis Ideas</h2>
      <p>Further COAD analysis could include high-mutation-burden sample review, patient-level co-mutation relationships among APC/TP53/KRAS/PIK3CA/SMAD4, mutation associations with OS or stage, expression differences for these genes in RNA-seq matrices, and methylation or RPPA cross-validation. If mutations are translated into candidate protein variants or antigen peptides, platforms such as Adaptyv Bio could support later expression and binding validation; this report does not call external experimental APIs.</p>
    </section>
    <p class="footer">Note: this is a local data exploration report for understanding COAD data structure and early signals. It does not replace formal statistical modeling or clinical interpretation.</p>
  </main>
  <script>
    const gender = {js(data["clinical_gender"])};
    const vital = {js(data["clinical_vital"])};
    const stage = {js(data["clinical_stage"])};
    const ageBins = {js(data["age_bins"])};
    const omics = {js(data["omics_coverage"])};
    const variantClass = {js(data["variant_classification"])};
    const variantType = {js(data["variant_type"])};
    const topGenes = {js(data["top_genes"])};
    const chromosome = {js(data["chromosome"])};
    const burdenBins = {js(data["burden_bins"])};
    const vafBins = {js(data["vaf_bins"])};
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
        grid: {{ left: 82, right: 24, top: 58, bottom: 92 }},
        xAxis: {{ type: 'category', data: labels(rows), axisLabel: {{ rotate: 38, interval: 0 }} }},
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
      pie('genderChart', 'COAD Gender Distribution', gender),
      pie('vitalChart', 'COAD vital_status Distribution', vital),
      bar('stageChart', 'AJCC Pathologic Stage Distribution', stage, 'value', '#7b4ea3'),
      bar('ageChart', 'Age At Diagnosis Bins', ageBins, 'value', '#218380'),
      bar('omicsChart', 'COAD Data Coverage', omics, 'value', '#1769aa'),
      bar('variantClassChart', 'COAD Variant Classification', variantClass, 'value', '#c8553d'),
      pie('variantTypeChart', 'COAD Variant Type', variantType),
      bar('topGenesChart', 'COAD Top mutated genes by patients', topGenes, 'patients', '#ad7a1f'),
      bar('chromosomeChart', 'COAD Chromosome Mutation Records', chromosome, 'value', '#5166a6'),
      bar('burdenChart', 'Mutation Records Per Sample Bins', burdenBins, 'value', '#2f7f91'),
      bar('vafChart', 'COAD Tumor VAF Bins', vafBins, 'value', '#2f7f91')
    ];
    const heat = echarts.init(document.getElementById('stageGeneHeatmap'));
    heat.setOption({{
      title: {{ text: 'COAD Stage x Top Gene Patient Count Heatmap', left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
      tooltip: {{ position: 'top', formatter: p => `${{heatY[p.value[1]]}} / ${{heatX[p.value[0]]}}: ${{p.value[2]}} patients` }},
      grid: {{ left: 130, right: 40, top: 64, bottom: 88 }},
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
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Data Analysis Report List</title><style>{css}</style></head>
<body><main>
  <h1>Data Analysis Report List</h1>
  <div class="meta">3 reports available · Last updated: {esc(data["generated_at"])}</div>
  <a class="card" href="reports/tcga_schema_basic_analysis.html">
    <div class="title">1. TCGA Schema Basic Analysis Report</div>
    <div class="desc">An entry-level overview of the bio_tcga schema in the local PostgreSQL container, including table scale, data types, the TCGA clinical type field, and cancer-type distributions.</div>
  </a>
  <a class="card" href="reports/tcga_mc3_sequencing_deep_dive.html">
    <div class="title">2. TCGA MC3 Cancer Sequencing Mutation Table Deep Dive</div>
    <div class="desc">A deeper analysis of the MC3 MAF cancer sequencing mutation table, covering variant types, cancer types, genes, chromosomes, VAF, caller support, and all 114 fields.</div>
  </a>
  <a class="card" href="reports/{REPORT_FILENAME}">
    <div class="title">3. {REPORT_TITLE}</div>
    <div class="desc">A COAD-focused report integrating clinical data, MC3 sequencing mutations, multi-omics sample coverage, sample-quality annotations, and term explanations.</div>
  </a>
</main></body></html>"""


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        data = build_data()
    finally:
        drop_coad_cache()
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
