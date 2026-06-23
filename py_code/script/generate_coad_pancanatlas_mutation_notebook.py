#!/usr/bin/env python3
"""Generate a COAD PanCanAtlas mutation landscape notebook."""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "coad-predictor-model"
    / "reports"
    / "coad_pancanatlas_mutation_landscape_report.ipynb"
)


def md(source: str):
    clean_source = textwrap.dedent(source).strip()
    return {
        "cell_type": "markdown",
        "id": "md-" + hashlib.sha1(clean_source.encode("utf-8")).hexdigest()[:10],
        "metadata": {},
        "source": clean_source,
    }


def code(source: str):
    clean_source = textwrap.dedent(source).strip()
    return {
        "cell_type": "code",
        "id": "code-" + hashlib.sha1(clean_source.encode("utf-8")).hexdigest()[:10],
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": clean_source,
    }


def build_notebook():
    nb = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    nb["cells"] = [
        md(
            """
            # COAD PanCanAtlas Mutation Landscape Report

            **English.** This notebook analyzes COAD (colon adenocarcinoma / a type of colon cancer) mutation records from the local TCGA PanCanAtlas database. It focuses on which genes are mutated most often, where mutations occur, recurrent mutation hotspots, tumor mutation burden, variant allele fraction, co-mutation patterns, and stage-level mutation frequencies.

            **中文。** 这个 notebook 分析本地 TCGA PanCanAtlas 数据库里的 COAD（colon adenocarcinoma，结肠腺癌 / 一种结肠癌）突变记录。重点包括：哪些基因突变最多、突变位置在哪里、反复出现的突变热点、每个肿瘤样本的突变数量、VAF（variant allele fraction，突变等位基因比例 / 支持突变的测序 reads 占比）、共同突变模式，以及不同分期中的突变频率。

            **Important scope note.** This is an exploratory data analysis report, not a clinical diagnosis. The numbers describe this local database snapshot.
            """
        ),
        md(
            """
            ## 1. Setup

            The notebook reads database settings from environment variables first. If they are not set, it uses the local project settings in `src/config.py`.

            Optional environment variables: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.

            If you see a database password error, run this notebook from the `coad-predictor-model` project folder or set `PGPASSWORD` in the Jupyter environment.
            """
        ),
        code(
            '''
            from pathlib import Path
            import os
            import sys
            import warnings

            import numpy as np
            import pandas as pd
            import matplotlib.pyplot as plt
            import seaborn as sns
            import psycopg2
            from sqlalchemy import create_engine
            from sqlalchemy.engine import URL

            warnings.filterwarnings("ignore", category=UserWarning)
            sns.set_theme(style="whitegrid", context="notebook")
            pd.set_option("display.max_columns", 50)
            pd.set_option("display.max_rows", 80)

            REPORT_DIR = Path.cwd()
            if REPORT_DIR.name != "reports":
                REPORT_DIR = Path("/workspace/coad-predictor-model/reports")
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            PROJECT_ROOT = REPORT_DIR.parent
            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))

            try:
                from src import config as project_config
            except Exception:
                project_config = None

            def get_db_setting(env_names, config_name, default=None):
                """Read a setting from environment variables, then project config."""
                if isinstance(env_names, str):
                    env_names = (env_names,)
                for env_name in env_names:
                    value = os.getenv(env_name)
                    if value:
                        return value
                if project_config is not None and hasattr(project_config, config_name):
                    return getattr(project_config, config_name)
                return default

            def configure_database():
                """Create database helpers for this notebook session."""
                global DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_URL, engine
                global read_sql, run_sql, REPORT_DIR

                DB_HOST = get_db_setting(("PGHOST", "DB_HOST"), "DB_HOST", "bio-postgres")
                DB_PORT = int(get_db_setting(("PGPORT", "DB_PORT"), "DB_PORT", 5432))
                DB_NAME = get_db_setting(("PGDATABASE", "DB_NAME"), "DB_NAME", "bio")
                DB_USER = get_db_setting(("PGUSER", "DB_USER"), "DB_USER", "bio")
                DB_PASSWORD = get_db_setting(("PGPASSWORD", "DB_PASSWORD"), "DB_PASSWORD")

                if not DB_PASSWORD:
                    raise RuntimeError(
                        "Database password was not found. Set PGPASSWORD or run from the "
                        "coad-predictor-model project where src/config.py is available. / "
                        "没有找到数据库密码。请设置 PGPASSWORD，或者从包含 src/config.py 的 "
                        "coad-predictor-model 项目目录运行。"
                    )

                DB_URL = URL.create(
                    "postgresql+psycopg2",
                    username=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                )
                engine = create_engine(DB_URL)

                def _read_sql(sql, params=None):
                    return pd.read_sql_query(sql, engine, params=params)

                def _run_sql(sql):
                    with psycopg2.connect(
                        host=DB_HOST,
                        port=DB_PORT,
                        dbname=DB_NAME,
                        user=DB_USER,
                        password=DB_PASSWORD,
                    ) as conn:
                        conn.autocommit = True
                        with conn.cursor() as cur:
                            cur.execute(sql)

                read_sql = _read_sql
                run_sql = _run_sql

            def ensure_database_ready():
                """Recover database helpers after a kernel restart or out-of-order run."""
                if "read_sql" not in globals() or "run_sql" not in globals():
                    configure_database()

            configure_database()
            REPORT_DIR
            '''
        ),
        md(
            """
            ## 2. Build a COAD Mutation Cache

            The source MAF table (`mc3_public_maf`) contains many cancer types. A MAF file (Mutation Annotation Format / 突变注释格式) is a table where each row is usually one DNA change in one tumor sample.

            To make analysis faster, we create a small unlogged cache table containing only COAD rows and the columns needed in this report. This table can be safely rebuilt.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            cache_sql = """
            DROP TABLE IF EXISTS bio_tcga._nb_coad_pancanatlas_maf_cache;

            CREATE UNLOGGED TABLE bio_tcga._nb_coad_pancanatlas_maf_cache AS
            SELECT
              substring(m.tumor_sample_barcode from 1 for 12) AS patient_barcode,
              m.tumor_sample_barcode,
              c.gender,
              c.vital_status,
              COALESCE(NULLIF(c.ajcc_pathologic_tumor_stage, ''), '(missing)') AS ajcc_stage,
              c.age_at_initial_pathologic_diagnosis,
              c.os,
              c.os_time,
              m.hugo_symbol,
              m.entrez_gene_id,
              m.variant_classification,
              m.variant_type,
              m.chromosome,
              m.start_position,
              m.end_position,
              m.reference_allele,
              m.tumor_seq_allele2,
              m.hgvsc,
              m.hgvsp,
              m.hgvsp_short,
              m.exon_number,
              m.exon,
              m.protein_position,
              m.amino_acids,
              m.codons,
              m.impact,
              m.consequence,
              m.context,
              m.t_depth,
              m.t_ref_count,
              m.t_alt_count,
              m.n_depth,
              m.n_ref_count,
              m.n_alt_count,
              m.ncallers,
              m.filter,
              m.mutation_status,
              m.cosmic
            FROM bio_tcga.mc3_public_maf m
            JOIN bio_tcga.tcga_cdr_tcga_cdr c
              ON c.type = 'COAD'
             AND c.bcr_patient_barcode = substring(m.tumor_sample_barcode from 1 for 12);

            CREATE INDEX IF NOT EXISTS _nb_coad_maf_sample_idx
              ON bio_tcga._nb_coad_pancanatlas_maf_cache(tumor_sample_barcode);
            CREATE INDEX IF NOT EXISTS _nb_coad_maf_patient_idx
              ON bio_tcga._nb_coad_pancanatlas_maf_cache(patient_barcode);
            CREATE INDEX IF NOT EXISTS _nb_coad_maf_gene_idx
              ON bio_tcga._nb_coad_pancanatlas_maf_cache(hugo_symbol);
            CREATE INDEX IF NOT EXISTS _nb_coad_maf_position_idx
              ON bio_tcga._nb_coad_pancanatlas_maf_cache(chromosome, start_position);

            ANALYZE bio_tcga._nb_coad_pancanatlas_maf_cache;
            """
            run_sql(cache_sql)
            print("COAD cache table rebuilt.")
            '''
        ),
        md(
            """
            ## 3. Dataset Overview

            A patient barcode is the first 12 characters of a TCGA sample barcode. Here we count clinical patients, tumor samples with mutation data, mutation records, and mutated genes.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            summary = read_sql("""
            SELECT
              (SELECT COUNT(*) FROM bio_tcga.tcga_cdr_tcga_cdr WHERE type = 'COAD')::int AS clinical_patients,
              COUNT(*)::int AS mutation_records,
              COUNT(DISTINCT tumor_sample_barcode)::int AS tumor_samples_with_mutation_data,
              COUNT(DISTINCT patient_barcode)::int AS patients_with_mutation_data,
              COUNT(DISTINCT NULLIF(hugo_symbol, ''))::int AS mutated_genes
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache;
            """)
            display(summary)

            clinical_stage = read_sql("""
            SELECT ajcc_stage, COUNT(DISTINCT patient_barcode)::int AS patients
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            GROUP BY ajcc_stage
            ORDER BY patients DESC, ajcc_stage;
            """)
            display(clinical_stage.head(12))
            '''
        ),
        md(
            """
            ## 4. Variant Types and Functional Classes

            Variant type tells the DNA-level change, such as SNP/SNV (single-letter DNA change / 单个 DNA 字母改变), DEL (deletion / 缺失), or INS (insertion / 插入). Variant classification describes the functional effect, such as missense mutation (one amino acid changes / 一个氨基酸改变), nonsense mutation (early stop signal / 提前终止信号), or frameshift (reading frame shift / 读码框改变).
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            variant_class = read_sql("""
            SELECT variant_classification AS label, COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            GROUP BY variant_classification
            ORDER BY mutation_records DESC;
            """)
            variant_type = read_sql("""
            SELECT variant_type AS label, COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            GROUP BY variant_type
            ORDER BY mutation_records DESC;
            """)

            fig, axes = plt.subplots(1, 2, figsize=(15, 5))
            sns.barplot(data=variant_class.head(12), x="mutation_records", y="label", ax=axes[0], color="#4c78a8")
            axes[0].set_title("Top Variant Classifications")
            axes[0].set_xlabel("Mutation records")
            axes[0].set_ylabel("")
            sns.barplot(data=variant_type, x="label", y="mutation_records", ax=axes[1], color="#f58518")
            axes[1].set_title("Variant Types")
            axes[1].set_xlabel("")
            axes[1].set_ylabel("Mutation records")
            plt.tight_layout()
            plt.show()

            display(variant_class.head(15))
            display(variant_type)
            '''
        ),
        md(
            """
            ## 5. Most Frequently Mutated Genes

            The key denominator is tumor samples with mutation data. A gene's mutation frequency means: among COAD tumor samples in this local database, what percent have at least one mutation record in that gene?
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            tumor_sample_count = int(summary.loc[0, "tumor_samples_with_mutation_data"])
            top_genes = read_sql("""
            SELECT
              hugo_symbol,
              COUNT(*)::int AS mutation_records,
              COUNT(DISTINCT tumor_sample_barcode)::int AS mutated_samples,
              ROUND(100.0 * COUNT(DISTINCT tumor_sample_barcode)
                    / NULLIF((SELECT COUNT(DISTINCT tumor_sample_barcode)
                              FROM bio_tcga._nb_coad_pancanatlas_maf_cache), 0), 1) AS sample_frequency_pct
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            WHERE COALESCE(hugo_symbol, '') NOT IN ('', 'Unknown')
            GROUP BY hugo_symbol
            ORDER BY mutated_samples DESC, mutation_records DESC
            LIMIT 30;
            """)
            display(top_genes)

            plt.figure(figsize=(10, 8))
            sns.barplot(
                data=top_genes.head(20),
                x="sample_frequency_pct",
                y="hugo_symbol",
                color="#54a24b",
            )
            plt.title("Top COAD Mutated Genes by Sample Frequency")
            plt.xlabel("Tumor samples mutated (%)")
            plt.ylabel("Gene")
            plt.tight_layout()
            plt.show()

            top_genes.to_csv(REPORT_DIR / "coad_pancanatlas_top_mutated_genes.csv", index=False)
            '''
        ),
        md(
            """
            ## 6. Where Are the Mutations?

            We look at mutation locations in three ways:

            1. Chromosome distribution: which chromosomes contain more mutation records.
            2. Recurrent genomic loci: exact DNA positions repeated in several samples.
            3. Protein hotspots: repeated protein changes such as `KRAS p.G12D`.

            A hotspot (repeated mutation position / 反复出现的突变位置) can be biologically important because different tumors independently hit the same position.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            chromosome_counts = read_sql("""
            SELECT chromosome, COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            GROUP BY chromosome
            ORDER BY
              CASE WHEN chromosome ~ '^[0-9]+$' THEN chromosome::int ELSE 100 END,
              chromosome;
            """)

            genomic_hotspots = read_sql("""
            SELECT
              hugo_symbol,
              chromosome,
              start_position,
              end_position,
              reference_allele,
              tumor_seq_allele2 AS alt_allele,
              variant_classification,
              COUNT(DISTINCT tumor_sample_barcode)::int AS mutated_samples,
              COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            WHERE COALESCE(hugo_symbol, '') NOT IN ('', 'Unknown')
            GROUP BY hugo_symbol, chromosome, start_position, end_position,
                     reference_allele, tumor_seq_allele2, variant_classification
            HAVING COUNT(DISTINCT tumor_sample_barcode) >= 3
            ORDER BY mutated_samples DESC, mutation_records DESC
            LIMIT 30;
            """)

            protein_hotspots = read_sql("""
            SELECT
              hugo_symbol,
              hgvsp_short,
              protein_position,
              amino_acids,
              variant_classification,
              COUNT(DISTINCT tumor_sample_barcode)::int AS mutated_samples,
              COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            WHERE COALESCE(hugo_symbol, '') NOT IN ('', 'Unknown')
              AND hgvsp_short LIKE 'p.%%'
              AND hgvsp_short <> 'p.?'
            GROUP BY hugo_symbol, hgvsp_short, protein_position, amino_acids, variant_classification
            HAVING COUNT(DISTINCT tumor_sample_barcode) >= 3
            ORDER BY mutated_samples DESC, mutation_records DESC
            LIMIT 30;
            """)

            exon_summary = read_sql("""
            SELECT
              hugo_symbol,
              COALESCE(NULLIF(exon_number, ''), NULLIF(exon, ''), '(missing)') AS exon_label,
              COUNT(DISTINCT tumor_sample_barcode)::int AS mutated_samples,
              COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            WHERE hugo_symbol IN ('APC', 'TP53', 'KRAS', 'PIK3CA', 'SMAD4')
            GROUP BY hugo_symbol, COALESCE(NULLIF(exon_number, ''), NULLIF(exon, ''), '(missing)')
            ORDER BY hugo_symbol, mutated_samples DESC, mutation_records DESC
            LIMIT 60;
            """)

            plt.figure(figsize=(12, 4))
            sns.barplot(data=chromosome_counts, x="chromosome", y="mutation_records", color="#4c78a8")
            plt.title("COAD Mutation Records by Chromosome")
            plt.xlabel("Chromosome")
            plt.ylabel("Mutation records")
            plt.tight_layout()
            plt.show()

            display(genomic_hotspots)
            display(protein_hotspots)
            display(exon_summary)

            genomic_hotspots.to_csv(REPORT_DIR / "coad_pancanatlas_genomic_hotspots.csv", index=False)
            protein_hotspots.to_csv(REPORT_DIR / "coad_pancanatlas_protein_hotspots.csv", index=False)
            '''
        ),
        md(
            """
            ## 7. Tumor Mutation Burden and VAF

            Tumor mutation burden (TMB / 肿瘤突变负荷) here means the number of mutation records per tumor sample. This is a simple count, not a clinically standardized TMB per megabase.

            VAF (variant allele fraction / 突变等位基因比例) is calculated as `t_alt_count / t_depth`, meaning the fraction of tumor sequencing reads that support the mutated allele.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            burden = read_sql("""
            SELECT
              tumor_sample_barcode,
              patient_barcode,
              ajcc_stage,
              vital_status,
              COUNT(*)::int AS mutation_records,
              COUNT(DISTINCT NULLIF(hugo_symbol, ''))::int AS mutated_genes
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            GROUP BY tumor_sample_barcode, patient_barcode, ajcc_stage, vital_status
            ORDER BY mutation_records DESC;
            """)
            burden_summary = burden[["mutation_records", "mutated_genes"]].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]).round(1)
            display(burden_summary)
            display(burden.head(15))

            vaf = read_sql("""
            SELECT
              CASE
                WHEN t_depth ~ '^[0-9]+$'
                 AND t_alt_count ~ '^[0-9]+$'
                 AND t_depth::numeric > 0
                THEN t_alt_count::numeric / t_depth::numeric
              END AS tumor_vaf,
              variant_classification,
              hugo_symbol
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache;
            """)
            vaf = vaf.dropna(subset=["tumor_vaf"])
            vaf = vaf[(vaf["tumor_vaf"] >= 0) & (vaf["tumor_vaf"] <= 1)]

            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            sns.histplot(burden["mutation_records"], bins=40, ax=axes[0], color="#4c78a8")
            axes[0].set_title("Mutation Records per Tumor Sample")
            axes[0].set_xlabel("Mutation records")
            axes[0].set_ylabel("Tumor samples")
            axes[0].set_yscale("log")

            sns.histplot(vaf["tumor_vaf"], bins=40, ax=axes[1], color="#e45756")
            axes[1].set_title("Tumor VAF Distribution")
            axes[1].set_xlabel("Tumor VAF = alt reads / depth")
            axes[1].set_ylabel("Mutation records")
            plt.tight_layout()
            plt.show()

            burden.to_csv(REPORT_DIR / "coad_pancanatlas_sample_mutation_burden.csv", index=False)
            '''
        ),
        md(
            """
            ## 8. Co-Mutation Patterns Among Top Genes

            Co-mutation (共同突变) means the same tumor sample has mutations in two genes. This heatmap shows the percent of tumor samples that have both genes mutated.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            top_gene_list = top_genes.head(15)["hugo_symbol"].tolist()
            sample_gene = read_sql("""
            SELECT tumor_sample_barcode, hugo_symbol, COUNT(*)::int AS mutation_records
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            WHERE hugo_symbol = ANY(%(genes)s)
            GROUP BY tumor_sample_barcode, hugo_symbol;
            """, params={"genes": top_gene_list})

            binary = (
                sample_gene.assign(mutated=1)
                .pivot_table(index="tumor_sample_barcode", columns="hugo_symbol", values="mutated", fill_value=0)
                .reindex(columns=top_gene_list, fill_value=0)
            )
            # Include samples with no mutation in the selected genes so percentages use all tumor samples.
            all_samples = burden["tumor_sample_barcode"].sort_values().unique()
            binary = binary.reindex(all_samples, fill_value=0)
            co_counts = binary.T.dot(binary)
            co_pct = co_counts / len(binary) * 100

            plt.figure(figsize=(10, 8))
            sns.heatmap(co_pct, cmap="Blues", annot=True, fmt=".1f", square=True, cbar_kws={"label": "% of tumor samples"})
            plt.title("Co-Mutation Frequency Among Top COAD Genes")
            plt.tight_layout()
            plt.show()

            display(co_pct.round(1))
            co_pct.round(2).to_csv(REPORT_DIR / "coad_pancanatlas_top_gene_comutation_pct.csv")
            '''
        ),
        md(
            """
            ## 9. Mutation Frequency by AJCC Stage

            AJCC stage (a cancer staging system / 癌症分期系统) roughly describes how far the cancer has grown or spread. This plot shows, for each stage group, what percent of samples have each top gene mutated.

            This is descriptive only. It does not prove that a gene causes a stage difference.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            stage_gene = read_sql("""
            WITH stage_denominator AS (
              SELECT ajcc_stage, COUNT(DISTINCT tumor_sample_barcode)::numeric AS stage_samples
              FROM bio_tcga._nb_coad_pancanatlas_maf_cache
              GROUP BY ajcc_stage
            ),
            gene_counts AS (
              SELECT ajcc_stage, hugo_symbol, COUNT(DISTINCT tumor_sample_barcode)::numeric AS mutated_samples
              FROM bio_tcga._nb_coad_pancanatlas_maf_cache
              WHERE hugo_symbol = ANY(%(genes)s)
              GROUP BY ajcc_stage, hugo_symbol
            )
            SELECT
              d.ajcc_stage,
              g.hugo_symbol,
              COALESCE(c.mutated_samples, 0)::int AS mutated_samples,
              d.stage_samples::int AS stage_samples,
              ROUND(100.0 * COALESCE(c.mutated_samples, 0) / NULLIF(d.stage_samples, 0), 1) AS mutation_frequency_pct
            FROM stage_denominator d
            CROSS JOIN (SELECT unnest(%(genes)s::text[]) AS hugo_symbol) g
            LEFT JOIN gene_counts c
              ON c.ajcc_stage = d.ajcc_stage
             AND c.hugo_symbol = g.hugo_symbol
            ORDER BY d.ajcc_stage, g.hugo_symbol;
            """, params={"genes": top_gene_list[:12]})

            stage_order = (
                stage_gene.groupby("ajcc_stage")["stage_samples"].max()
                .sort_values(ascending=False)
                .index.tolist()
            )
            stage_matrix = (
                stage_gene.pivot(index="ajcc_stage", columns="hugo_symbol", values="mutation_frequency_pct")
                .reindex(index=stage_order, columns=top_gene_list[:12])
            )

            plt.figure(figsize=(12, 6))
            sns.heatmap(stage_matrix, cmap="YlGnBu", annot=True, fmt=".1f", cbar_kws={"label": "Mutated samples (%)"})
            plt.title("Top Gene Mutation Frequency by AJCC Stage")
            plt.xlabel("Gene")
            plt.ylabel("AJCC stage")
            plt.tight_layout()
            plt.show()

            display(stage_gene.head(40))
            stage_gene.to_csv(REPORT_DIR / "coad_pancanatlas_stage_gene_frequency.csv", index=False)
            '''
        ),
        md(
            """
            ## 10. Short Biological Reading

            **English.** In COAD, the most frequent genes are expected to include classic colorectal cancer genes such as APC, TP53, KRAS, PIK3CA, and SMAD4. APC is often involved early in colorectal tumor development; TP53 is linked to DNA damage control; KRAS and PIK3CA affect growth signaling; SMAD4 is part of the TGF-beta pathway (a cell communication pathway that can control growth).

            **中文。** 在 COAD 中，常见高频突变基因通常包括 APC、TP53、KRAS、PIK3CA、SMAD4 等经典结直肠癌相关基因。APC 常和结直肠肿瘤早期发展有关；TP53 和 DNA 损伤控制有关；KRAS、PIK3CA 会影响细胞生长信号；SMAD4 属于 TGF-beta 通路（调节细胞生长和交流的一条信号通路）。

            **How to read hotspots.** If one exact protein change appears in many samples, it may be a driver mutation (a mutation that helps cancer grow / 推动癌症生长的突变). But this notebook only counts recurrence; formal driver-gene analysis needs additional statistical modeling and biological validation.
            """
        ),
        code(
            '''
            if "ensure_database_ready" not in globals():
                raise RuntimeError("Please run Section 1. Setup first, then run this cell again. / 请先运行第 1 节 Setup，然后再运行这个单元。")
            ensure_database_ready()

            key_gene_records = read_sql("""
            SELECT
              hugo_symbol,
              variant_classification,
              hgvsp_short,
              chromosome,
              start_position,
              reference_allele,
              tumor_seq_allele2 AS alt_allele,
              tumor_sample_barcode,
              ajcc_stage,
              t_depth,
              t_alt_count,
              ncallers
            FROM bio_tcga._nb_coad_pancanatlas_maf_cache
            WHERE hugo_symbol IN ('APC', 'TP53', 'KRAS', 'PIK3CA', 'SMAD4')
            ORDER BY hugo_symbol, tumor_sample_barcode, chromosome, start_position
            LIMIT 30;
            """)
            display(key_gene_records)
            '''
        ),
        md(
            """
            ## 11. Limitations and Next Steps

            **Limitations.**

            - This report counts mutation records from MC3 MAF; it does not re-run variant calling (finding DNA sequence differences from raw sequencing reads / 从原始测序数据中重新寻找 DNA 差异).
            - TMB here is a simple mutation-record count, not a clinically standardized mutations-per-megabase value.
            - Stage and survival relationships are observational; they can be affected by confounders (other variables that mix up the explanation / 混杂因素).
            - `scikit-bio` is not used as a main tool here because this task analyzes annotated cancer mutation tables, not microbiome diversity, phylogenetic trees, FASTA/FASTQ sequence alignment, or UniFrac/PCoA workflows.

            **Next steps.**

            - Compare high-mutation-burden samples with MSI/POLE annotations if available.
            - Add survival analysis for selected genes, with clear caveats and enough sample size.
            - Connect mutation status with RNA-seq expression for the same patients.
            - Review recurrent hotspots in external cancer knowledge bases before treating them as driver mutations.
            """
        ),
    ]
    return nb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    nb = build_notebook()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
