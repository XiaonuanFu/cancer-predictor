#!/usr/bin/env python3
"""Generate an AlphaFold hotspot structure visualization report for COAD mutations."""

from __future__ import annotations

import csv
import html
import json
import shutil
import textwrap
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "code" / "coad-predictor-model" / "reports" / "alphafold_hotspots"
API_DIR = REPORT_DIR / "api"
STRUCTURE_DIR = REPORT_DIR / "structures"
OUTPUT_HTML = REPORT_DIR / "coad_alphafold_hotspot_structures.html"
OUTPUT_NOTEBOOK = ROOT / "code" / "coad-predictor-model" / "reports" / "coad_alphafold_hotspot_structures.ipynb"
OUTPUT_SUMMARY = REPORT_DIR / "alphafold_hotspot_summary.csv"
PUBLIC_REPORT_DIR = (
    ROOT
    / "docker_storage"
    / "jupyter"
    / "node-app"
    / "public"
    / "data-analysis"
    / "reports"
    / "alphafold_hotspots"
)
INTERACTIVE_URL = "http://localhost:3000/data-analysis/reports/alphafold_hotspots/coad_alphafold_hotspot_structures.html"


HOTSPOTS = [
    {
        "gene": "KRAS",
        "uniprot": "P01116",
        "mutation": "p.G12D",
        "residue": 12,
        "wild_type": "G",
        "mutant": "D",
        "plain": "KRAS residue 12 is a classic colorectal-cancer signaling hotspot.",
    },
    {
        "gene": "KRAS",
        "uniprot": "P01116",
        "mutation": "p.G12V",
        "residue": 12,
        "wild_type": "G",
        "mutant": "V",
        "plain": "This is the same KRAS structural position as G12D but a different amino-acid change.",
    },
    {
        "gene": "BRAF",
        "uniprot": "P15056",
        "mutation": "p.V600E",
        "residue": 600,
        "wild_type": "V",
        "mutant": "E",
        "plain": "BRAF V600E is a well-known kinase-activation hotspot.",
    },
    {
        "gene": "PIK3CA",
        "uniprot": "P42336",
        "mutation": "p.E545K",
        "residue": 545,
        "wild_type": "E",
        "mutant": "K",
        "plain": "PIK3CA E545K lies in the helical-domain hotspot region.",
    },
]


AA3_TO_1 = {
    "ALA": "A",
    "ARG": "R",
    "ASN": "N",
    "ASP": "D",
    "CYS": "C",
    "GLN": "Q",
    "GLU": "E",
    "GLY": "G",
    "HIS": "H",
    "ILE": "I",
    "LEU": "L",
    "LYS": "K",
    "MET": "M",
    "PHE": "F",
    "PRO": "P",
    "SER": "S",
    "THR": "T",
    "TRP": "W",
    "TYR": "Y",
    "VAL": "V",
}


def load_prediction(uniprot: str) -> dict:
    path = API_DIR / f"{uniprot}_prediction.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    canonical = [row for row in data if row.get("uniprotAccession") == uniprot and "-2-" not in row.get("entryId", "")]
    if canonical:
        return canonical[0]
    return data[0]


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 100:
        return
    with urllib.request.urlopen(url, timeout=60) as response:
        target.write_bytes(response.read())


def parse_pdb_residues(pdb_path: Path) -> dict[int, dict]:
    residues: dict[int, dict] = {}
    with pdb_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.startswith("ATOM"):
                continue
            atom_name = line[12:16].strip()
            residue_name = line[17:20].strip()
            chain = line[21].strip()
            try:
                residue_number = int(line[22:26])
                bfactor = float(line[60:66])
            except ValueError:
                continue
            entry = residues.setdefault(
                residue_number,
                {
                    "residue_name": residue_name,
                    "aa": AA3_TO_1.get(residue_name, residue_name),
                    "chain": chain,
                    "ca_plddt": None,
                    "atom_plddt": [],
                },
            )
            entry["atom_plddt"].append(bfactor)
            if atom_name == "CA":
                entry["ca_plddt"] = bfactor
    for entry in residues.values():
        if entry["ca_plddt"] is None and entry["atom_plddt"]:
            entry["ca_plddt"] = round(sum(entry["atom_plddt"]) / len(entry["atom_plddt"]), 2)
    return residues


def confidence_label(plddt: float | None) -> str:
    if plddt is None:
        return "missing"
    if plddt > 90:
        return "very high"
    if plddt > 70:
        return "high"
    if plddt > 50:
        return "low"
    return "very low"


def js_string(value: str) -> str:
    return json.dumps(value)


def render_html(rows: list[dict], pdb_text_by_entry: dict[str, str]) -> str:
    cards = []
    scripts = []
    for idx, row in enumerate(rows):
        viewer_id = f"viewer{idx}"
        pdb_var = f"pdb{idx}"
        cards.append(
            f"""
            <section class="card">
              <div class="viewer" id="{viewer_id}"></div>
              <div class="card-body">
                <h2>{html.escape(row["gene"])} {html.escape(row["mutation"])}</h2>
                <p><strong>AlphaFold model:</strong> {html.escape(row["entry_id"])} · UniProt {html.escape(row["uniprot"])}</p>
                <p><strong>Highlighted residue:</strong> {html.escape(row["wild_type"])}{row["residue"]} → {html.escape(row["mutant"])} · structure residue is {html.escape(row["structure_aa"])}{row["residue"]}</p>
                <p><strong>Residue pLDDT:</strong> {row["residue_plddt"]:.1f} ({html.escape(row["confidence_label"])}) · <strong>model mean pLDDT:</strong> {row["model_mean_plddt"]:.2f}</p>
                <p>{html.escape(row["plain"])}</p>
              </div>
            </section>
            """
        )
        pdb_text = pdb_text_by_entry[row["entry_id"]]
        scripts.append(
            f"""
            const {pdb_var} = {js_string(pdb_text)};
            const viewer{idx} = $3Dmol.createViewer("{viewer_id}", {{ backgroundColor: "white" }});
            viewer{idx}.addModel({pdb_var}, "pdb");
            viewer{idx}.setStyle({{}}, {{ cartoon: {{ color: "spectrum" }} }});
            viewer{idx}.addStyle({{ resi: {row["residue"]} }}, {{ stick: {{ radius: 0.36, color: "#e45756" }}, sphere: {{ radius: 0.9, color: "#e45756", opacity: 0.85 }} }});
            viewer{idx}.addResLabels({{ resi: {row["residue"]} }}, {{ backgroundColor: "#17212b", fontColor: "white", fontSize: 13, showBackground: true }});
            viewer{idx}.zoomTo({{ resi: {row["residue"]} }});
            viewer{idx}.zoom(1.6);
            viewer{idx}.render();
            """
        )

    css = """
    :root { --ink:#17212b; --muted:#5c6b78; --line:#d9e1e8; --panel:#f7f9fb; --accent:#e45756; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; background:#fff; }
    header { padding:30px 40px 20px; border-bottom:1px solid var(--line); background:#f8fafc; }
    main { max-width:1260px; margin:0 auto; padding:26px 40px 50px; }
    h1 { margin:0 0 10px; font-size:30px; letter-spacing:0; }
    h2 { margin:0 0 10px; font-size:21px; }
    p { line-height:1.6; color:#2f3d49; }
    code { background:#edf2f7; border-radius:4px; padding:1px 5px; }
    .meta { color:var(--muted); font-size:14px; }
    .note { border-left:4px solid var(--accent); background:#fff6f5; padding:12px 14px; margin:16px 0 22px; }
    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
    .card { display:grid; grid-template-rows:420px auto; border:1px solid var(--line); border-radius:8px; overflow:hidden; background:#fff; }
    .viewer { width:100%; height:420px; background:#fff; position:relative; overflow:hidden; }
    .viewer canvas { position:absolute !important; left:0 !important; top:0 !important; width:100% !important; height:100% !important; }
    .card-body { padding:15px 16px 18px; border-top:1px solid var(--line); }
    table { width:100%; border-collapse:collapse; margin-top:20px; font-size:14px; }
    th, td { border-bottom:1px solid var(--line); padding:8px 9px; text-align:left; vertical-align:top; }
    th { background:var(--panel); }
    @media (max-width: 900px) { header, main { padding-left:18px; padding-right:18px; } .grid { grid-template-columns:1fr; } }
    """
    table_rows = "\n".join(
        f"<tr><td>{html.escape(row['gene'])}</td><td>{html.escape(row['mutation'])}</td><td>{html.escape(row['entry_id'])}</td><td>{row['residue']}</td><td>{row['residue_plddt']:.1f}</td><td>{html.escape(row['confidence_label'])}</td><td>{row['latest_version']}</td></tr>"
        for row in rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>COAD AlphaFold Hotspot Structure Viewer</title>
  <style>{css}</style>
  <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
</head>
<body>
  <header>
    <h1>COAD AlphaFold Hotspot Structure Viewer</h1>
    <div class="meta">Structures from AlphaFold DB · Canonical human UniProt models · Hotspot residues highlighted in red</div>
  </header>
  <main>
    <div class="note">
      AlphaFold DB provides predicted structures for the reference proteins. The red atoms mark the wild-type residue positions where the COAD hotspot mutations occur; this is not a new AlphaFold prediction of the mutant proteins.
      <br><strong>中文：</strong>AlphaFold DB 给的是标准未突变蛋白的预测结构。红色标出发生 COAD 热点突变的位置；这不是对突变体蛋白重新做 AlphaFold 预测。
    </div>
    <div class="grid">
      {''.join(cards)}
    </div>
    <h2 style="margin-top:28px;">Summary Table</h2>
    <table>
      <thead><tr><th>Gene</th><th>Mutation</th><th>AlphaFold entry</th><th>Residue</th><th>Residue pLDDT</th><th>Confidence</th><th>AF version</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
  </main>
  <script>
  window.addEventListener("load", function() {{
    {''.join(scripts)}
  }});
  </script>
</body>
</html>
"""


def make_notebook(rows: list[dict]) -> dict:
    summary_lines = "\n".join(
        f"- **{row['gene']} {row['mutation']}**: AlphaFold `{row['entry_id']}`, residue {row['residue']}, pLDDT {row['residue_plddt']:.1f} ({row['confidence_label']})."
        for row in rows
    )
    preview_lines = "\n\n".join(
        f"### {row['gene']} {row['mutation']}\n\n"
        f"![{row['gene']} {row['mutation']}](alphafold_hotspots/static/{row['slug']}.png)\n\n"
        f"AlphaFold `{row['entry_id']}` · residue pLDDT {row['residue_plddt']:.1f} ({row['confidence_label']})"
        for row in rows
    )
    source = f"""
    # COAD AlphaFold Hotspot Structure Viewer

    This notebook includes static PNG previews because JupyterLab blocks JavaScript inside HTML previews for security.

    **Important note.** AlphaFold DB provides reference protein predictions. The hotspot positions are highlighted on the reference structures, not newly predicted mutant structures.

    {summary_lines}

    ## Interactive 3D viewer

    Open this link in a normal browser tab, not the JupyterLab HTML preview:

    [{INTERACTIVE_URL}]({INTERACTIVE_URL})

    If `localhost` does not work from your browser, try:

    [http://127.0.0.1:3000/data-analysis/reports/alphafold_hotspots/coad_alphafold_hotspot_structures.html](http://127.0.0.1:3000/data-analysis/reports/alphafold_hotspots/coad_alphafold_hotspot_structures.html)

    ## Static previews visible inside Jupyter

    {preview_lines}
    """
    return {
        "cells": [
            {"cell_type": "markdown", "id": "af-hotspots-summary", "metadata": {}, "source": textwrap.dedent(source).strip()}
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    API_DIR.mkdir(parents=True, exist_ok=True)
    STRUCTURE_DIR.mkdir(parents=True, exist_ok=True)

    predictions = {uniprot: load_prediction(uniprot) for uniprot in {h["uniprot"] for h in HOTSPOTS}}
    pdb_text_by_entry: dict[str, str] = {}
    residue_maps: dict[str, dict[int, dict]] = {}
    rows: list[dict] = []

    for uniprot, prediction in predictions.items():
        entry_id = prediction["entryId"]
        pdb_path = STRUCTURE_DIR / f"{entry_id}.pdb"
        cif_path = STRUCTURE_DIR / f"{entry_id}.cif"
        download(prediction["pdbUrl"], pdb_path)
        download(prediction["cifUrl"], cif_path)
        pdb_text_by_entry[entry_id] = pdb_path.read_text(encoding="utf-8", errors="replace")
        residue_maps[entry_id] = parse_pdb_residues(pdb_path)

    for hotspot in HOTSPOTS:
        prediction = predictions[hotspot["uniprot"]]
        entry_id = prediction["entryId"]
        residue_info = residue_maps[entry_id].get(hotspot["residue"], {})
        residue_plddt = float(residue_info.get("ca_plddt") or 0.0)
        rows.append(
            {
                **hotspot,
                "entry_id": entry_id,
                "uniprot_id": prediction.get("uniprotId", ""),
                "description": prediction.get("uniprotDescription", ""),
                "organism": prediction.get("organismScientificName", ""),
                "latest_version": prediction.get("latestVersion", ""),
                "model_created_date": prediction.get("modelCreatedDate", ""),
                "model_mean_plddt": float(prediction.get("globalMetricValue", 0.0)),
                "residue_plddt": residue_plddt,
                "confidence_label": confidence_label(residue_plddt),
                "structure_aa": residue_info.get("aa", "?"),
                "structure_chain": residue_info.get("chain", ""),
                "pdb_file": str((STRUCTURE_DIR / f"{entry_id}.pdb").relative_to(REPORT_DIR)),
                "cif_file": str((STRUCTURE_DIR / f"{entry_id}.cif").relative_to(REPORT_DIR)),
                "slug": f"{hotspot['gene'].lower()}_{hotspot['mutation'].replace('p.', '').replace('.', '').lower()}",
            }
        )

    OUTPUT_HTML.write_text(render_html(rows, pdb_text_by_entry), encoding="utf-8")
    with OUTPUT_SUMMARY.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "gene",
            "mutation",
            "uniprot",
            "entry_id",
            "residue",
            "wild_type",
            "mutant",
            "structure_aa",
            "residue_plddt",
            "confidence_label",
            "model_mean_plddt",
            "latest_version",
            "model_created_date",
            "pdb_file",
            "cif_file",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    OUTPUT_NOTEBOOK.write_text(json.dumps(make_notebook(rows), ensure_ascii=False, indent=2), encoding="utf-8")
    PUBLIC_REPORT_DIR.parent.mkdir(parents=True, exist_ok=True)
    if PUBLIC_REPORT_DIR.exists():
        shutil.rmtree(PUBLIC_REPORT_DIR)
    shutil.copytree(REPORT_DIR, PUBLIC_REPORT_DIR)

    print(f"Wrote {OUTPUT_HTML}")
    print(f"Wrote {OUTPUT_NOTEBOOK}")
    print(f"Wrote {OUTPUT_SUMMARY}")
    print(f"Published interactive HTML to {PUBLIC_REPORT_DIR}")


if __name__ == "__main__":
    main()
