# Data Inventory and Source Mapping

Updated: 2026-05-23

## Storage Policy

- Raw data is stored under `data/`.
- Runtime database and Jupyter storage is stored under `docker_storage/`.
- Both directories are ignored by git through `.gitignore`.

## Local Data Directories

```text
data/raw_data/   TCGA and PanCanAtlas-related raw source files
data/chembl/     ChEMBL 36 PostgreSQL dump and related chemical files
```

## Database Schemas

Observed PostgreSQL schemas:

- `bio_tcga`: TCGA/PanCanAtlas imported data.
- `chembl`: ChEMBL imported data.
- `public`: miscellaneous/default schema.

## TCGA/PanCanAtlas Local Source Files

Local files currently present under `data/raw_data/` include:

| File | Current Import Target |
| --- | --- |
| `PanCan-General_Open_GDC-Manifest_2.txt` | `bio_tcga.gdc_manifest` |
| `PanCanAtlas_miRNA_sample_information_list.txt` | `bio_tcga.mirna_sample_information` |
| `TCGA-CDR-SupplementalTableS1.xlsx` | multiple `bio_tcga.tcga_cdr_*` tables |
| `TCGA-RPPA-pancan-clean.txt` | `bio_tcga.rppa_pancan_clean` |
| `TCGA_mastercalls.abs_segtabs.fixed.txt` | `bio_tcga.abs_segtabs` |
| `TCGA_mastercalls.abs_tables_JSedit.fixed.txt` | `bio_tcga.abs_tables` |
| `broad.mit.edu_PANCAN_Genome_Wide_SNP_6_whitelisted.seg` | `bio_tcga.snp6_whitelisted_seg` |
| `clinical_PANCAN_patient_with_followup.tsv` | `bio_tcga.clinical_patient_followup` |
| `jhu-usc.edu_PANCAN_HumanMethylation450.betaValue_whitelisted.tsv` | `bio_tcga.matrix_methylation450_beta` |
| `jhu-usc.edu_PANCAN_merged_HumanMethylation27_HumanMethylation450.betaValue_whitelisted.tsv` | `bio_tcga.matrix_methylation27_450_beta` |
| `mc3.v0.2.8.PUBLIC.maf` | `bio_tcga.mc3_public_maf` |
| `mc3.v0.2.8.PUBLIC.maf.gz` | local compressed source copy; import currently uses uncompressed MAF |
| `merge_merged_reals.tar.gz` | `bio_tcga.matrix_merge_merged_reals` |
| `merged_sample_quality_annotations.tsv` | `bio_tcga.sample_quality_annotations` |
| `pancanMiRs_EBadjOnProtocolPlatformWithoutRepsWithUnCorrectMiRs_08_04_16.csv` | `bio_tcga.matrix_mirna_ebadj` |
| `EBPlusPlusAdjustPANCAN_IlluminaHiSeq_RNASeqV2.geneExp.tsv` | `bio_tcga.matrix_rnaseq_gene_expression` |

## TCGA Import Method

Import script:

```text
scripts/import_tcga_raw_data.py
```

Import command:

```bash
python3 scripts/import_tcga_raw_data.py --raw-dir data/raw_data
```

The script records source provenance in:

```text
bio_tcga.import_manifest
```

Direct tabular files are imported with text columns. Very wide matrix files are stored as feature rows plus a `values_text` vector, with sample identifiers placed in a companion `*_samples` table.

## ChEMBL Local Source Files

Local files currently present under `data/chembl/` include:

| File | Notes |
| --- | --- |
| `chembl_36_postgresql.tar.gz` | ChEMBL 36 PostgreSQL dump source |
| `version.smi.gz` | ChEMBL SMILES/version data |
| `chembl_tmp.dump` | Empty temporary dump file observed locally |

Observed imported ChEMBL schema:

- Schema: `chembl`
- Tables: 74
- Approx schema size: 38 GB

Large ChEMBL tables observed by row estimate include:

| Table | Estimated Rows |
| --- | ---: |
| `chembl.version_smi` | 33,398,330 |
| `chembl.activities` | 24,269,766 |
| `chembl.activity_properties` | 11,918,904 |
| `chembl.chembl_id_lookup` | 5,351,995 |
| `chembl.compound_structural_alerts` | 4,925,556 |
| `chembl.compound_records` | 3,779,358 |
| `chembl.molecule_dictionary` | 2,877,363 |
| `chembl.compound_properties` | 2,858,671 |
| `chembl.compound_structures` | 2,858,542 |

## Import and Quality Notes

- `bio_tcga` currently has 28 tables.
- `chembl` currently has 74 tables.
- Row counts in the Web app are estimates from PostgreSQL statistics, not exact counts.
- Some TCGA matrix tables are intentionally stored in compact raw-vector form to avoid PostgreSQL column-count and import-performance issues.
- The ChEMBL `idx_assays_desc` btree index failed during import because of long text values; a hash index with the same logical purpose was created instead.

## Source Provenance To Confirm

The file names indicate TCGA PanCanAtlas/GDC, MC3 mutation, Broad SNP6/CNV, JHU-USC methylation, RPPA, miRNA, and ChEMBL 36 sources. Add official download links, access dates, checksums, and license notes before publishing or sharing derived results.

