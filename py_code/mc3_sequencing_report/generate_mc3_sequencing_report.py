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
REPORT_TITLE = "TCGA MC3 Cancer Sequencing Mutation Table Deep Dive"
ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"


FIELD_CATEGORIES = {
    "gene": {"hugo_symbol", "entrez_gene_id", "symbol", "symbol_source", "hgnc_id", "gene", "gene_pheno"},
    "coordinate": {"ncbi_build", "chromosome", "start_position", "end_position", "strand", "strand_2", "cdna_position", "cds_position", "protein_position"},
    "variant function": {"variant_classification", "consequence", "impact", "variant_class", "all_effects"},
    "variant type": {"variant_type", "reference_allele", "tumor_seq_allele1", "tumor_seq_allele2", "allele", "allele_num"},
    "sample": {"tumor_sample_barcode", "matched_norm_sample_barcode", "tumor_sample_uuid", "matched_norm_sample_uuid"},
    "sequencing evidence": {"t_depth", "t_ref_count", "t_alt_count", "n_depth", "n_ref_count", "n_alt_count", "ncallers", "filter", "score"},
    "transcript/protein": {"hgvsc", "hgvsp", "hgvsp_short", "transcript_id", "exon_number", "feature", "feature_type", "biotype", "canonical", "ccds", "ensp", "swissprot", "trembl", "uniparc", "refseq", "exon", "intron", "domains", "amino_acids", "codons"},
    "external database": {"dbsnp_rs", "dbsnp_val_status", "existing_variation", "cosmic", "clin_sig", "pubmed", "dbvs"},
    "population frequency": {"gmaf", "afr_maf", "amr_maf", "asn_maf", "eas_maf", "eur_maf", "sas_maf", "aa_maf", "ea_maf", "exac_af", "exac_af_afr", "exac_af_amr", "exac_af_eas", "exac_af_fin", "exac_af_nfe", "exac_af_oth", "exac_af_sas"},
    "source/validation": {"center", "centers", "sequencing_phase", "sequence_source", "sequencer", "bam_file", "verification_status", "validation_status", "validation_method", "tumor_validation_allele1", "tumor_validation_allele2", "match_norm_validation_allele1", "match_norm_validation_allele2", "mutation_status"},
    "regulatory motif": {"motif_name", "motif_pos", "high_inf_pos", "motif_score_change"},
}


def describe_field(name: str) -> tuple[str, str]:
    for category, fields in FIELD_CATEGORIES.items():
        if name in fields:
            return category, f"Imported MAF field used for {category} interpretation; confirm exact semantics against the source MAF documentation when using it for formal analysis."
    return "other", "Imported from the raw MAF file; confirm exact semantics against source documentation before formal use."


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
        category, explanation = describe_field(col["column_name"])
        field_rows.append({
            "pos": col["ordinal_position"],
            "field": col["column_name"],
            "category": category,
            "explanation": explanation,
        })
    glossary_rows = [
        {"term": "TCGA", "plain": "The Cancer Genome Atlas, a large public project that collected cancer samples and data."},
        {"term": "MC3", "plain": "Multi-Center Mutation Calling in Multiple Cancers, a TCGA project that combined mutation calls from several tools."},
        {"term": "MAF", "plain": "Mutation Annotation Format, a table where each row usually describes one DNA mutation."},
        {"term": "Somatic mutation", "plain": "A DNA change found in tumor cells but not inherited from your parents."},
        {"term": "Germline variant", "plain": "A DNA difference you were born with and can be present in normal cells."},
        {"term": "Tumor sample", "plain": "DNA or tissue taken from the cancer part of the patient."},
        {"term": "Matched normal sample", "plain": "Non-cancer DNA from the same patient, used as a comparison baseline."},
        {"term": "Variant", "plain": "A place in DNA where the sequence is different from the reference genome."},
        {"term": "Allele", "plain": "One version of a DNA base or sequence at a genomic position."},
        {"term": "Reference allele", "plain": "The DNA letter or sequence in the reference genome."},
        {"term": "Tumor allele", "plain": "The DNA letter or sequence observed in the tumor sample."},
        {"term": "SNP / SNV", "plain": "A single-letter DNA change, like A becoming T."},
        {"term": "DNP", "plain": "A two-letter DNA change next to each other."},
        {"term": "INS", "plain": "Insertion: extra DNA letters are added."},
        {"term": "DEL", "plain": "Deletion: DNA letters are missing."},
        {"term": "Missense mutation", "plain": "A DNA change that swaps one amino acid in a protein for another."},
        {"term": "Nonsense mutation", "plain": "A DNA change that creates an early stop signal, making a shorter protein."},
        {"term": "Silent mutation", "plain": "A DNA change that does not change the amino acid."},
        {"term": "Frameshift", "plain": "An insertion or deletion that shifts how DNA letters are read in groups of three."},
        {"term": "Splice site", "plain": "A DNA region needed to cut and join RNA pieces correctly."},
        {"term": "Exon", "plain": "A gene segment that usually stays in the final RNA message."},
        {"term": "Intron", "plain": "A gene segment usually removed from RNA before making protein."},
        {"term": "Transcript", "plain": "An RNA version of a gene; one gene can have multiple transcript versions."},
        {"term": "Amino acid", "plain": "A building block of proteins."},
        {"term": "HGVS", "plain": "A standard naming system for describing DNA or protein changes."},
        {"term": "VEP", "plain": "Variant Effect Predictor, a tool that predicts what a DNA variant might do."},
        {"term": "Impact", "plain": "A rough label for how serious a variant may be: HIGH, MODERATE, LOW, or MODIFIER."},
        {"term": "Read", "plain": "A short piece of DNA sequence produced by a sequencing machine."},
        {"term": "Depth", "plain": "How many sequencing reads cover a DNA position."},
        {"term": "Alt count", "plain": "How many reads support the changed allele instead of the reference allele."},
        {"term": "VAF", "plain": "Variant Allele Fraction: alt reads divided by total reads. A 20% VAF means about 1 in 5 reads show the mutation."},
        {"term": "Caller", "plain": "A software tool that decides whether a DNA change is a real mutation."},
        {"term": "ncallers", "plain": "How many mutation-calling tools supported the same mutation."},
        {"term": "COSMIC", "plain": "A database of mutations found in cancer."},
        {"term": "ClinVar", "plain": "A database that links variants to possible medical meaning."},
        {"term": "dbSNP", "plain": "A database of known DNA variants, many of which are common inherited variants."},
        {"term": "ExAC", "plain": "A database of allele frequencies from many people, useful for spotting common variants."},
        {"term": "Adaptyv Bio", "plain": "A service that can express designed proteins and measure binding in wet-lab assays."},
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
    <div class="meta">Generated at: {esc(data["generated_at"])} · Table: bio_tcga.mc3_public_maf · Data type: TCGA MC3 MAF somatic mutation table</div>
  </header>
  <main>
    <a class="back-link" href="/#analysis">← Back to report list</a>
    <section>
      <h2>1. Table Role And Key Takeaways</h2>
      <p><code>mc3_public_maf</code> is the main cancer sequencing mutation table in this schema. MAF, or Mutation Annotation Format, stores paired tumor/normal somatic variants as one variant event per row, with gene, genomic coordinate, transcript/protein effect, sequencing depth, external database, and multi-caller consensus information.</p>
      <div class="cards">
        <div class="card"><span>Mutation Records</span><strong>{fmt_int(summary["rows"])}</strong></div>
        <div class="card"><span>Tumor Samples</span><strong>{fmt_int(summary["tumor_samples"])}</strong></div>
        <div class="card"><span>Patients</span><strong>{fmt_int(summary["patients"])}</strong></div>
        <div class="card"><span>Genes</span><strong>{fmt_int(summary["genes"])}</strong></div>
        <div class="card"><span>Fields</span><strong>{fmt_int(len(data["columns"]))}</strong></div>
      </div>
      <div class="note">Bioinformatics note: coordinates should be interpreted using <code>ncbi_build</code>; MAF coordinates are usually 1-based. <code>t_depth/t_alt_count</code> can calculate tumor VAF, <code>n_depth/n_alt_count</code> helps assess normal-sample background, and <code>ncallers</code> is a key MC3 consensus reliability signal.</div>
    </section>

    <section>
      <h2>2. Cancer Mutation Landscape</h2>
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
      <h2>3. Sequencing Evidence Quality</h2>
      <p>The median tumor depth is <strong>{esc(depth.get("median_t_depth"))}</strong>, with an average tumor depth of about <strong>{esc(depth.get("avg_t_depth"))}</strong>. The median normal depth is <strong>{esc(depth.get("median_n_depth"))}</strong>, with an average normal depth of about <strong>{esc(depth.get("avg_n_depth"))}</strong>. Entry-level filtering can prioritize events with higher <code>t_alt_count</code>, reasonable VAF, low normal-sample mutation support, and higher <code>ncallers</code>.</p>
      <p>For protein-experiment follow-up, <code>hgvsp</code>, <code>hgvsp_short</code>, <code>amino_acids</code>, and <code>protein_position</code> help translate DNA-level missense/nonsense events into candidate protein variants. If later work validates mutant proteins, antigen peptides, or binding-protein designs, expression and binding platforms such as Adaptyv Bio could be downstream validation options; this report only analyzes the local database and does not call external APIs.</p>
    </section>

    <section>
      <h2>4. Top 12 Cancer Type Distribution</h2>
      {render_table(cancer_rows, ["Cancer Type", "Mutations", "Samples", "Patients", "Avg Mutations/Sample"], ["label", "variants", "samples", "patients", "variants_per_sample"])}
    </section>

    <section>
      <h2>5. Representative Records</h2>
      {render_table(sample_rows, ["Gene", "Chromosome", "Start", "Functional Class", "Type", "Sample", "Protein Change", "Tumor Depth", "Alt Reads", "Impact", "Callers"], ["hugo_symbol", "chromosome", "start_position", "variant_classification", "variant_type", "tumor_sample_barcode", "hgvsp_short", "t_depth", "t_alt_count", "impact", "ncallers"])}
    </section>

    <section>
      <h2>6. Abbreviations And Terms</h2>
      <p>This table explains abbreviations and technical terms in AP Biology-style language. Read it first, then return to the charts and field table.</p>
      {render_table(glossary_rows, ["Term / abbreviation", "Plain English explanation"], ["term", "plain"])}
    </section>

    <section>
      <h2>7. 114 Field Explanations</h2>
      <div class="field-table">
        {render_table(field_rows, ["No.", "Field", "Category", "Explanation"], ["pos", "field", "category", "explanation"])}
      </div>
    </section>
    <p class="footer">Note: this report supports beginner-to-intermediate data understanding. The charts are aggregate statistics and do not replace formal variant filtering, driver-gene discovery, or clinical interpretation workflows.</p>
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
      bar('variantClassChart', 'Variant Classification Distribution', variantClass, 'value', '#1769aa'),
      pie('variantTypeChart', 'Variant Type Distribution', variantType),
      pie('impactChart', 'VEP Impact Distribution', impact),
      bar('chromosomeChart', 'Chromosome Mutation Record Count', chromosome, 'value', '#218380'),
      bar('topGenesChart', 'Top 25 Genes By Mutation Records', topGenes, 'value', '#c8553d'),
      bar('cancerTypeChart', 'Top 20 Cancer Types By Mutation Records', cancerTypes.map(r => ({{ label: r.label, value: r.variants }})), 'value', '#7b4ea3'),
      bar('burdenChart', 'Top 20 Cancer Types By Average Mutation Burden', burden.map(r => ({{ label: r.label, value: r.avg_mutations }})), 'value', '#ad7a1f'),
      bar('vafChart', 'Tumor VAF Bins', vafBins, 'value', '#2f7f91'),
      bar('ncallersChart', 'Supporting Caller Count: ncallers', ncallers, 'value', '#5166a6')
    ];
    const heat = echarts.init(document.getElementById('geneCancerHeatmap'));
    heat.setOption({{
      title: {{ text: 'Top Cancer Types x Top Genes Mutation Count Heatmap', left: 8, top: 8, textStyle: {{ fontSize: 15 }} }},
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
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Data Analysis Report List</title><style>{css}</style></head>
<body><main>
  <h1>Data Analysis Report List</h1>
  <div class="meta">3 reports available · Last updated: {esc(data["generated_at"])}</div>
  <a class="card" href="reports/tcga_schema_basic_analysis.html">
    <div class="title">1. TCGA Schema Basic Analysis Report</div>
    <div class="desc">An entry-level overview of the bio_tcga schema in the local PostgreSQL container, including table scale, data types, the TCGA clinical type field, and cancer-type distributions.</div>
  </a>
  <a class="card" href="reports/{REPORT_FILENAME}">
    <div class="title">2. {REPORT_TITLE}</div>
    <div class="desc">A deeper analysis of the MC3 MAF cancer sequencing mutation table, covering variant types, cancer types, genes, chromosomes, VAF, caller support, and all 114 fields.</div>
  </a>
  <a class="card" href="reports/tcga_coad_integrated_analysis.html">
    <div class="title">3. TCGA COAD Sequencing And Multi-Omics Integrated Analysis</div>
    <div class="desc">A COAD-focused report integrating clinical data, MC3 sequencing mutations, multi-omics sample coverage, sample-quality annotations, and term explanations.</div>
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
