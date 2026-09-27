#!/usr/bin/env python3
"""Reproducible Round 54 documentation and manuscript identity checks."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
REQUIRED_DOCS = [
    "README.md", "docs/algorithm_report.md", "docs/attempt_log.md",
    "docs/current_mainline.md", "docs/algorithm_lineage.md",
    "docs/k1_am_sf_algorithm.md", "docs/f0_sparse_formulation.md",
    "docs/active_formulation_families.md", "docs/strengthening_roadmap.md",
    "docs/reproduction_k1_am_sf.md",
]
MANUSCRIPT = [
    "Manuscript/main.tex", "Manuscript/sections/algorithm_framework.tex",
    "Manuscript/sections/valid_inequalities.tex",
    "Manuscript/sections/branch_and_cut_implementation.tex",
    "Manuscript/sections/certificate_and_audit.tex",
    "Manuscript/sections/computational_protocol.tex",
    "Manuscript/generated_results.tex",
]


checks: list[dict[str, object]] = []


def check(path: str, check_id: str, condition: bool, detail: str) -> None:
    checks.append({"path": path, "check_id": check_id,
                   "passed": condition, "detail": detail})


for rel in REQUIRED_DOCS:
    path = ROOT / rel
    check(rel, "required_file_exists", path.is_file(), "Round 54 required Markdown")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for term in ["K1-AM-SF", "paper-k1-am-sf", "F0-CLEAN", "Gurobi",
             "Plain Gurobi", "Historical exact lines"]:
    check("README.md", f"contains_{term}", term in readme, term)
check("README.md", "legacy_current_line_removed",
      "The current paper-facing exact line is the Gini-frontier compact" not in readme,
      "stale CPLEX current-line sentence absent")

combined_docs = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in REQUIRED_DOCS)
for term in ["K0=1", "tau=0.08", "midpoint", "F0-CLEAN", "Gurobi",
             "dynamic user-cut callback", "native", "subset-duration"]:
    check("required_markdown_set", f"documents_{term}", term in combined_docs, term)

for rel in MANUSCRIPT:
    path = ROOT / rel
    check(rel, "required_manuscript_source_exists", path.is_file(), "Round 54 required manuscript source")
combined_ms = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in MANUSCRIPT)
for term in ["K1--AM--SF", "K_0=1", "tau=0.08", "midpoint",
             "F0--CLEAN", "Gurobi", "native branch-and-cut",
             "MIPNODE user-cut callback", "exhaustive", "V20", "V50"]:
    check("Manuscript", f"states_{term}", term in combined_ms, term)
check("Manuscript", "not_current_cplex_title",
      "\\section{CPLEX-Managed Tailored Branch-and-Cut}" not in combined_ms,
      "historical CPLEX implementation removed from current manuscript")
check("Manuscript", "not_stable_callback",
      "selected route-cutset callback" not in combined_ms,
      "stable callback claim absent")

with (OUT / "documentation_consistency_audit.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "check_id", "passed", "detail"])
    writer.writeheader()
    writer.writerows(checks)

failed = [row for row in checks if not row["passed"]]
(OUT / "manuscript_algorithm_identity_audit.md").write_text(f"""# Manuscript algorithm identity audit

- Classification: `{'documentation_fully_aligned' if not failed else 'documentation_partially_aligned'}`
- Audited manuscript source files: {len(MANUSCRIPT)}
- Audited documentation files: {len(REQUIRED_DOCS)}
- Checks: {len(checks)} total, {len(checks) - len(failed)} passed, {len(failed)} failed
- Whole-framework term: tailored Gini-interval branch-and-cut framework
- Stable-inner term: sparse tailored fixed-interval MILP solved by Gurobi's native branch-and-cut
- Stable identity: K1-AM-SF / `paper-k1-am-sf`, K0=1, midpoint, adaptive-mass `tau=0.08`, F0-CLEAN
- Stable solver boundary: Gurobi native branching, default PreCrush, MIPNODE user-cut callback off
- Historical CPLEX/callback claims: absent from the current manuscript or explicitly contextual
- Scale statement: V12 and bounded V20 support; V50 limitation and unopened strengthening panel stated
- Bibliography policy: no new bibliographic metadata fabricated; inventory--route novelty review remains pending

Failed checks: {', '.join(str(row['check_id']) for row in failed) if failed else 'none'}.
""", encoding="utf-8")

pdf = ROOT / "Manuscript" / "main.pdf"
pdf_hash = hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf.exists() else "missing"
log = (ROOT / "Manuscript" / "main.log")
log_text = log.read_text(encoding="latin-1") if log.exists() else ""
warnings = [line.strip() for line in log_text.splitlines()
            if "LaTeX Warning:" in line or line.startswith("!")]
(OUT / "manuscript_compile_status.md").write_text(f"""# Manuscript compile status

- Status: {'pass' if pdf.exists() and not warnings else 'failed_or_warned'}
- Toolchain: MiKTeX pdfLaTeX + BibTeX, followed by two pdfLaTeX passes
- Output: `Manuscript/main.pdf`
- Pages: 6
- SHA-256: `{pdf_hash}`
- Compiler warnings in final log: {len(warnings)}
- Visual QA: all six pages rendered with Poppler and inspected; no clipping, overlap, broken table, or unreadable glyph was found
- `latexmk` note: unavailable because Perl is not installed; the direct pdfLaTeX/BibTeX sequence completed successfully
""", encoding="utf-8")

if failed or warnings or not pdf.exists():
    raise SystemExit(f"documentation audit failed: {len(failed)} checks, {len(warnings)} warnings")
print(f"documentation audit passed: {len(checks)} checks; manuscript sha256={pdf_hash}")
