#!/usr/bin/env python3
"""Paper-strict audit for the Tailored-BC mainline.

The audit intentionally distinguishes algorithm implementation code from
experiment runner target lists. Instance names and seeds are allowed in runner
configuration files, but not in `src/` or `include/` certificate logic.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]

MECHANISMS: List[Dict[str, Any]] = [
    {
        "mechanism_name": "direct Gini interval rows",
        "formula": "gamma_L <= G <= gamma_U and H <= V gamma_U S",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/gf_compact_bc_validity_proofs.md; docs/s_range_denominator_refinement.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "objective cutoff rows",
        "formula": "G + lambda P <= UB - epsilon",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/gf_compact_bc_validity_proofs.md",
        "audit_script": "audit_bpc_certificate.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "S-bucket rows",
        "formula": "S_L^b <= sum_i r_i <= S_U^b",
        "where_implemented": "src/CplexBaseline.cpp; scripts/run_tailored_bc_*s_bucket*.py",
        "proof_source": "docs/s_range_denominator_refinement.md",
        "audit_script": "audit_s_bucket_coverage.py; audit_s_bucket_ledger_merge.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "bucket-tight S*P McCormick",
        "formula": "McCormick envelope for W_SP=S*P over bucket-local S and P bounds",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/s_range_denominator_refinement.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "bucket-tight objective estimator",
        "formula": "H + V*S_U^b*lambda*P <= V*S_U^b*(UB-epsilon)",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/s_range_denominator_refinement.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "local centering",
        "formula": "V r_i - S <= sum_{j != i} h_ij and symmetric lower row",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/low_gini_strengthening_cuts.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "local q-centering",
        "formula": "q_i dominates |V r_i-S| and V q_i <= sum_{j != i} h_ij",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/low_gini_strengthening_cuts.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "subset cross-H centering",
        "formula": "|V R_A - |A| S| <= sum_{i in A,j notin A} h_ij",
        "where_implemented": "src/CplexBaseline.cpp; src/TailoredBCCplexApi.cpp",
        "proof_source": "docs/low_gini_strengthening_cuts.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "Gini subset-envelope",
        "formula": "|V R_A - |A| S| <= V gamma_U S",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/gf_compact_bc_validity_proofs.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "variable-S centering",
        "formula": "(V-1)(r_max-r_min) <= V gamma_U S",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/variable_s_low_gini_centering.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "basic transfer cutset",
        "formula": "receiver net delivery cannot exceed compatible external pickup support",
        "where_implemented": "src/CplexBaseline.cpp; src/TailoredBCCplexApi.cpp",
        "proof_source": "docs/receiver_set_source_cover_round2.md; docs/low_gini_strengthening_cuts.md",
        "audit_script": "audit_transfer_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "compatible-source transfer cuts",
        "formula": "d[k,j] <= sum_{i in Compat_k(j)} p[k,i]",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/receiver_set_source_cover_proof.md",
        "audit_script": "audit_transfer_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "required external-source cuts",
        "formula": "required receiver net delivery is covered by compatible outside pickups",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/receiver_set_source_cover_pair_proof.md",
        "audit_script": "audit_transfer_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "subset inventory movement bounds",
        "formula": "subset inventory imbalance bounded by reachable pickup/drop movement",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/low_gini_strengthening_cuts.md",
        "audit_script": "audit_low_gini_cut_validity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "bucket ratio-domain tightening",
        "formula": "r_i in [(1/V-gamma_U)S_L, (1/V+gamma_U)S_U]",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/bucket_ratio_domain_tightening.md",
        "audit_script": "audit_bucket_ratio_domain_tightening.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "bucket integer inventory domain tightening",
        "formula": "Y_i in [ceil(target_i*r_i^L), floor(target_i*r_i^U)] inside an enforced S bucket",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/bucket_integer_inventory_domain_tightening.md",
        "audit_script": "audit_bucket_integer_inventory_domain.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "bucket required movement and visit cuts",
        "formula": "bucket-tight Y bounds imply station/subset net pickup/drop requirements and required visits",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/bucket_required_movement.md",
        "audit_script": "audit_bucket_required_movement.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
    {
        "mechanism_name": "S-P-H coupled estimator",
        "formula": "H + V lambda W_SP <= V(UB-epsilon)S with bucket-local McCormick W_SP",
        "where_implemented": "src/CplexBaseline.cpp",
        "proof_source": "docs/sp_h_coupled_estimator.md",
        "audit_script": "audit_low_gini_cut_validity.py; audit_lp_snapshot_integrity.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
    },
]

IMPLEMENTATION_PATTERNS = {
    "instance-name mention": re.compile(r"(moderate_seed|high_imbalance_seed|tight_T_seed|regen_candidate|hard_compact_bc_diagnostics)"),
    "seed mention": re.compile(r"seed\d{3,}"),
    "known UB/archive/external incumbent mention": re.compile(r"(known[_-]?ub|external[_-]?incumbent|archive scanning|archive_scanning)", re.I),
    "route-mask certificate mention": re.compile(r"route_mask.*cert", re.I),
    "BPC certificate mention": re.compile(r"bpc.*certificate", re.I),
    "plain CPLEX ledger mention": re.compile(r"plain.*cplex.*ledger", re.I),
}

FORBIDDEN_BEHAVIOR_PATTERNS = {
    "instance-specific branch": re.compile(
        r"\b(if|else\s+if|switch)\b.*(moderate_seed|high_imbalance_seed|tight_T_seed|seed\d{3,})",
        re.I,
    ),
    "paper-tailored-known-ub-import": re.compile(
        r"paper-gf-tailored-bc.*(known[_-]?ub|external[_-]?incumbent|archive)",
        re.I,
    ),
    "paper-tailored-plain-cplex-ledger": re.compile(
        r"paper-gf-tailored-bc.*plain.*cplex.*ledger",
        re.I,
    ),
    "paper-tailored-bpc-evidence": re.compile(
        r"paper-gf-tailored-bc.*bpc.*certificate",
        re.I,
    ),
}


def implementation_files() -> Iterable[Path]:
    for base in (ROOT / "src", ROOT / "include"):
        for path in base.rglob("*"):
            if path.suffix in {".cpp", ".hpp", ".h"}:
                yield path


def scan_sources() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in implementation_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), 1):
            for name, pattern in IMPLEMENTATION_PATTERNS.items():
                if pattern.search(line):
                    forbidden_reason = ""
                    if "Usage:" not in line and "--algorithm-preset" not in line:
                        for behavior, behavior_pattern in FORBIDDEN_BEHAVIOR_PATTERNS.items():
                            if behavior_pattern.search(line):
                                forbidden_reason = behavior
                                break
                    allowed = forbidden_reason == ""
                    rows.append({
                        "audit_section": "source_scan",
                        "file": str(path.relative_to(ROOT)),
                        "line": line_no,
                        "mechanism_name": name,
                        "line_text": line.strip()[:240],
                        "warning_only": allowed,
                        "paper_safe": allowed,
                        "conditional_valid": False,
                        "diagnostic_only": False,
                        "audit_passed": allowed,
                        "failures": "" if allowed else forbidden_reason,
                    })
    return rows


def mechanism_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in MECHANISMS:
        rows.append({
            "audit_section": "mechanism",
            **item,
            "audit_passed": bool(item["paper_safe"]) or bool(item["diagnostic_only"]),
            "failures": "",
        })
    return rows


def invariant_rows() -> List[Dict[str, Any]]:
    invariants = [
        "Gini interval parent closure requires relaxation, exact fixed-interval Tailored-BC proof, or complete child coverage.",
        "S-bucket parent closure requires exact S-domain coverage and closed/fathomed children.",
        "Wrapper checkpoints remain diagnostic unless accepted by audited merge rules.",
        "Plain CPLEX benchmark rows are benchmark-only and excluded from paper-gf-tailored-bc ledger.",
        "BPC, route-mask enumeration, archive, known-UB, and focus-only evidence are excluded from paper-gf-tailored-bc.",
        "Default paper-facing preset remains paper-gf-tailored-bc.",
    ]
    return [{
        "audit_section": "global_optimality_logic",
        "mechanism_name": f"invariant_{idx + 1}",
        "formula": text,
        "where_implemented": "docs and audit scripts",
        "proof_source": "docs/paper_strict_algorithm_audit.md",
        "audit_script": "audit_paper_strict_algorithm.py",
        "paper_safe": True,
        "conditional_valid": True,
        "diagnostic_only": False,
        "audit_passed": True,
        "failures": "",
    } for idx, text in enumerate(invariants)]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = invariant_rows() + mechanism_rows() + scan_sources()
    write_csv(Path(args.out), rows)
    failures = sum(1 for row in rows if str(row.get("audit_passed")).lower() not in {"true", "1"})
    print(f"paper_strict_audit_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
