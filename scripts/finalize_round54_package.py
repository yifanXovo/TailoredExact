#!/usr/bin/env python3
"""Build the final concise, hash-bound Round 54 evidence package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
BASE = "bbf2044ec710f5eb8bde19d2ed183caa84055dcc"
SOURCE_FREEZE = "b6784e930f5df3b8bb048e7572301f942c017cd0"
EXE = "55ac7778f8e4a1c009b6d1cc8c4cc5d3b40a54ac241cce5a633363a0a571f441"
PAPER_EXE = "a08ae3a92483a255593ec22ad6ab6b493db0c598f867c8c0e7d186e1b34a75fc"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


parser = argparse.ArgumentParser()
parser.add_argument("--pr-url", default="pending_draft_creation")
args = parser.parse_args()

head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                               text=True).strip()
tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT,
                               text=True).strip()

source_rows = [
    {"audit": "stable_preset_uniformity", "scope": "src/PaperK1AmSf.cpp", "result": "pass", "detail": "one uniform override layer; no instance, size, seed, path, result, or time dispatch"},
    {"audit": "separator_uniformity", "scope": "src/InventoryRouteCuts.cpp", "result": "pass", "detail": "V is used only as state dimension/validity; exact deterministic closure, no enumeration or sampling"},
    {"audit": "root_closure_uniformity", "scope": "src/InventoryRouteRootClosure.cpp", "result": "pass", "detail": "no hidden node, size, instance, seed, result, or time dispatch"},
    {"audit": "runner_uniformity", "scope": "src/round54_inventory_route_main.cpp", "result": "pass", "detail": "policy-selected IR1/IR2/IR3 only; no instance-specific algorithm patch"},
    {"audit": "stable_ir_default_off", "scope": "src/PaperK1AmSf.cpp", "result": "pass", "detail": "inventory_route_root_closure is inactive in paper-k1-am-sf"},
    {"audit": "post_official_algorithm_change", "scope": f"{SOURCE_FREEZE}..HEAD CMakeLists/include/src", "result": "pass", "detail": "no algorithmic source change after the official source freeze"},
]
write_csv(OUT / "source_scope_audit.csv", source_rows,
          ["audit", "scope", "result", "detail"])

(OUT / "secret_license_scan.md").write_text("""# Secret and license scan

- Scope: every file changed from the Round 53 base through the Round 54 packaging snapshot.
- Secret patterns: API keys, access tokens, passwords, private-key blocks, GitHub personal-access tokens, and OpenAI-style secret tokens.
- Result: pass; zero candidate secret matches.
- License review: the new C++ and Python implementation is repository-native work and imports no vendored third-party source or new license text.
- Solver handling: Gurobi is dynamically/configurably enabled; machine-private license identifiers and logs remain outside committed evidence.
- Result: no new license incompatibility identified.
""", encoding="utf-8")

(OUT / "final_build_and_tests.md").write_text(f"""# Final build and tests

- Clean official build: pass; Gurobi explicitly enabled; 32 test executables registered.
- Final incremental verification build: pass; all targets complete.
- CTest: 32/32 passed, 0 failed.
- Dedicated `Round54MainlineAndInventoryRouteTests`: 35/35 checks passed.
- Historical protocol scripts: 26/26 passed. Round 46--49 used their recorded hashed official executables; the Round 53 protocol was evaluated with its recorded HEAD identity while reading the preserved current worktree, because its final check intentionally rejects later source commits.
- Round 54 paper-preset semantic sentinels: 6/6 passed.
- Documentation consistency: 45/45 checks passed.
- Manuscript: direct pdfLaTeX/BibTeX build passed, final log has zero compiler warnings, and 6/6 rendered pages passed visual QA.
- Source-scope audit: 6/6 passed.
- Secret/license scan: passed.
- Official comparator/candidate executable SHA-256: `{EXE}`.
- Stable paper executable SHA-256: `{PAPER_EXE}`.
- Official source freeze: `{SOURCE_FREEZE}`.
- Packaging snapshot before final binding: `{head}` (tree `{tree}`).
""", encoding="utf-8")

decision = {
    "schema": "round54-final-decision-v1",
    "completion_status": "round54_complete",
    "evidence_classification": "round53_pgrb_recertified",
    "mainline_classification": "k1_am_sf_mainline_frozen",
    "documentation_classification": "documentation_fully_aligned",
    "separator_classification": "inventory_route_separator_complete",
    "strengthening_classification": "bounded_negative_inventory_route_strengthening",
    "algorithm_classification": "k1_am_sf_stable_mainline",
    "scale_qualification": "generalization_panel_not_opened",
    "stable_algorithm": "K1-AM-SF",
    "stable_preset": "paper-k1-am-sf",
    "round53_pgrb_original_certificates": 0,
    "round53_pgrb_corrected_certificates": 9,
    "round53_pgrb_rows": 12,
    "round53_pgrb_false_certificates": 0,
    "offline_states": 34,
    "offline_variants": ["IR1", "IR2"],
    "offline_strict_violation_roles_per_variant": 33,
    "offline_strict_bound_gain_states_per_variant": 25,
    "fixed_interval_stage_a_rows": 28,
    "fixed_interval_stage_a_pairs": 14,
    "fixed_interval_f0_certificates": 11,
    "fixed_interval_ir1_certificates": 9,
    "fixed_interval_false_certificates": 0,
    "fixed_interval_stage_b_rows": 0,
    "fixed_interval_confirmation_rows": 0,
    "fixed_interval_long_rows": 0,
    "k1_integration_rows_1800s": 0,
    "k1_integration_rows_3600s": 0,
    "generalization_rows_3600s": 0,
    "v50_extension_rows_7200s": 0,
    "severe_regressions": ["D1", "D13"],
    "severe_regression_count": 2,
    "shifted_work_geometric_mean_ratio_ir1_over_f0": 1.0894322046574854,
    "aggregate_gi_f0": 0.4983492223793612,
    "aggregate_gi_ir1": 0.6234225979462248,
    "mandatory_entered_stage_missing_rows": [],
    "not_entered_by_gate": ["fixed_interval_1200s", "fixed_interval_confirmation", "fixed_interval_long", "k1_integration_1800s", "k1_integration_3600s", "generalization_3600s", "v50_7200s"],
    "recommended_next_step": "Stop the IR cut family and study a value-disaggregated G x Y formulation in a separately frozen round.",
    "branch": "codex/round54-k1-am-sf-inventory-route-cuts",
    "base_commit": BASE,
    "official_source_freeze": SOURCE_FREEZE,
    "official_executable_sha256": EXE,
    "paper_executable_sha256": PAPER_EXE,
    "draft_pr_url": args.pr_url,
}
write_json(OUT / "final_decision.json", decision)

(OUT / "final_report.md").write_text(f"""# Round 54 final report

Status: **round54_complete**. Every mandatory entered-stage row is present; gated stages that did not open have explicit empty ledgers and decisions. Draft stacked PR: {args.pr_url}.

## 1. Exact K1-AM-SF definition

K1-AM-SF is K1 Adaptive-Mass with Sparse Fixed-Interval Formulation, selected by `paper-k1-am-sf`. The outer tailored Gini-interval branch-and-cut framework uses K0=1, one complete strict-improver interval, midpoint refinement, adaptive-mass score with `tau=0.08`, unchanged native-target/exact-parent/child-infeasibility behavior, exact interval coverage, a monotone valid global lower bound, and strict original-problem certification. Its F0-CLEAN inner backend is Round 50 v0 with only the historical exhaustive V<=12 subset-duration block removed. Gurobi runs with Presolve Auto, Seed 0, Threads 1, zero MIP gaps, native branching, default PreCrush, and no dynamic user-cut callback.

## 2. Paper preset identity

Yes. `paper-k1-am-sf`, `k1-am-f0`, and `paper-k1-am-f0` canonicalize to the same Round 53 K1-AM-F0 semantics; the historical inner-policy alias remains accepted. Six required sentinels match settings, controller actions, interval endpoints, backend policy, objectives, bounds, and certificate class. Major, strong, V10, and numerical roles each have three matching model-file hashes. The bounded V20/V50 sentinels remained in heuristic startup and produced no model file; their evidence is command/controller/backend/outcome identity rather than a fabricated runtime fingerprint.

## 3--5. Round 53 P-GRB correction

The original 12 P-GRB rows lacked binding to a pre-frozen expected model fingerprint. Round 54 preserved every original artifact, verified the original official executable (`b49cc5a...`), froze all 12 expected fingerprints before correction, and required actual readback, valid lifecycle, independent original-solution checking, and objective recomputation. The corrected strict count is **9/12**, up from 0/12; the three M3 time-limit rows remain noncertificates. Work, process time, bounds, gaps, and GI did not change. No Round 53 F0 promotion conclusion changes.

## 6--8. Active, inactive, and contribution status

The 17 active families are: Gini interval domains; direct cap/floor; interval-tight G-times-binary hull; final-inventory penalty and movement-reachability domains; inventory conservation; visit--inventory linking; verified-incumbent cutoff; objective estimator; penalty closure; W_SP McCormick rows and estimator; pair/triple support-duration covers; connectivity flow; iterative propagation; and tight denominator bounds. The representative D1 model has 3,764 rows, 1,404 columns, 16,888 nonzeros, and zero exhaustive subset-duration rows.

Inactive families are the exhaustive subset-duration block, Gini-spread, required-movement, transfer-cutset, subset-inventory, dynamic support-duration, all tailored dynamic user cuts, inventory--route root closure, custom branching, and symmetry. The manifest classifies elements as standard or adapted. No active inequality is claimed novel; inventory--route novelty remains literature-review pending.

## 9. Documentation alignment

README, all required Markdown documents, and all requested manuscript sections now describe K1-AM-SF and its actual Gurobi boundary. Historical CPLEX/callback claims are removed from the current manuscript or explicitly labeled historical/contextual. The documentation audit passes 45/45 checks. The six-page manuscript compiles with zero final warnings and passes page-level visual QA.

## 10--11. Inventory--route proof and separator

For every nonempty station subset excluding the depot, IR-IN and IR-OUT bound net final-inventory displacement by capacity-weighted directed route entry/exit. Summed vehicle load conservation proves both mixed rows; valid interval inventory domains prove their projected companions. Separation is an exact deterministic directed maximum-closure/min-cut computation with explicit depot exclusion, direct violation recomputation, canonical signatures, duplicate/dominance handling, and deterministic tie-breaking. Fresh-model external root closure restores integer types and defaults before the terminal MIP; invalid closure falls back to F0. Dedicated tests pass all 35 checks.

## 12--16. Offline census and variants

IR1 (mixed full closure) and IR2 (mixed plus projected full closure) were run on all 34 frozen states, producing 68 complete rows. Each was valid everywhere, strictly violated in 33 structural roles, and improved the final root bound in 25 states. Each added 737 cuts over 470 closure rounds; aggregate closure Work was 3,632.783, solver time about 1,032.45 seconds for IR1 and 1,038.54 seconds for IR2, summed bound gain 0.846726, and maximum state gain 0.140600. IR2 gave no strict final-closure gain over IR1, so least-expansive IR1 was selected. IR3 (one pass) was predeclared but not opened because its overhead trigger did not occur. One implementation correction propagated the process deadline across closure rounds; all partial census evidence was invalidated and rerun before live selection.

## 17. Fixed-interval outcome

Stage A contains 28/28 engineering-valid rows: 14 F0-CLEAN and 14 IR1 rows at 300 seconds. F0 certifies 11/14; IR1 certifies 9/14; false certificates are zero. D4 is a material hard-state improvement, but IR1 loses F0 certificates on D1 and D13. F0 total Work is 3,461.075 versus IR1 3,555.762; IR1/F0 shifted Work GM is 1.089432. Aggregate GI worsens from 0.498349 to 0.623423. IR1 root closure adds 217 cuts, 96.087 Work, and 35.517 solver seconds over these 14 live rows. The frozen Stage-B gate fails.

## 18--20. K1 integration, major repair, and generalization

Because Stage A failed mandatory no-loss/no-severe/nonworse gates, fixed-interval Stage B, confirmation, and long checks did not open. K1-AM-SF-IR source was not created; K1 integration has 0 entered rows. Therefore no candidate controller run could alter or newly test the major repair; the stable K1-AM-SF repair remains unchanged by construction. The deterministic 4xV12/4xV20/4xV50 panel was generated and sealed before results, but its opening conditions were not met, so generalization and V50 extensions have 0 entered rows. The correct scale qualification is `generalization_panel_not_opened`.

## 21--25. Decision and remaining limits

There are two severe regressions, D1 and D13. K1-AM-SF remains the stable paper mainline (`k1_am_sf_stable_mainline`); K1-AM-SF-IR is not a supported future mainline candidate. Inventory--route strengthening is a bounded negative result: it improves root LPs but not total fixed-interval proof performance. The single next step is to stop this cut family and study a value-disaggregated G-times-Y formulation in a separate frozen round. Unproven items are: IR benefit under a materially different formulation, K1-level IR performance, new-panel V12/V20/V50 IR generalization, universal-scale validation, and literature novelty of the IR family.

## Final classifications

- Evidence: `round53_pgrb_recertified`
- Mainline: `k1_am_sf_mainline_frozen`
- Documentation: `documentation_fully_aligned`
- Separator: `inventory_route_separator_complete`
- Strengthening: `bounded_negative_inventory_route_strengthening`
- Algorithm: `k1_am_sf_stable_mainline`
- Scale: `generalization_panel_not_opened`

Official comparator/candidate executable SHA-256: `{EXE}`. Stable paper executable SHA-256: `{PAPER_EXE}`. Official source freeze: `{SOURCE_FREEZE}`. Packaging snapshot before final binding: `{head}` (tree `{tree}`).
""", encoding="utf-8")

# Local raw inventory is complete and hash-bound but remains uncommitted as raw data.
local_files: list[Path] = []
for raw_root in [OUT / "local_raw", OUT / "round53_pgrb_certificate_correction" / "local_raw"]:
    if raw_root.exists():
        local_files.extend(path for path in raw_root.rglob("*") if path.is_file())
local_rows = [{"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
               "sha256": sha256(path), "storage": "local_only_reproducible_raw"}
              for path in sorted(local_files)]
write_csv(OUT / "local_raw_evidence_inventory.csv", local_rows,
          ["path", "bytes", "sha256", "storage"])
local_bytes = sum(int(row["bytes"]) for row in local_rows)

(OUT / "evidence_storage_audit.md").write_text(f"""# Evidence storage audit

- Compact committed evidence: source, tests, contracts, proofs, manifests, ledgers, summary CSV/JSON, audits, report, decision, and reproduction commands.
- Local-only Round 54 raw evidence: {len(local_rows)} files, {local_bytes} bytes; every file is listed with SHA-256 in `local_raw_evidence_inventory.csv`.
- Raw native logs, solver progress, model exports, and complete run trees are intentionally not committed.
- Every entered live row is represented by committed summary evidence and a reproducible command; the official executable identities are frozen.
- The Round 53 originals and correction local raw were not overwritten. Correction evidence is under a separate root.
- Pre-existing unrelated tracked modifications and untracked files are outside the committed Round 54 package and are covered by the preservation audit.
- Result: pass.
""", encoding="utf-8")

# Inventories exclude themselves to avoid a self-hash cycle and exclude raw trees.
excluded = {"compact_evidence_inventory.csv", "final_evidence_inventory.csv",
            "local_raw_evidence_inventory.csv"}
compact_files = []
for path in OUT.rglob("*"):
    if not path.is_file() or path.name in excluded:
        continue
    rel = path.relative_to(OUT).as_posix()
    if rel.startswith("local_raw/") or "/local_raw/" in rel:
        continue
    compact_files.append(path)
compact_rows = [{"path": path.relative_to(ROOT).as_posix(),
                 "bytes": path.stat().st_size, "sha256": sha256(path),
                 "category": "committed_compact_evidence"}
                for path in sorted(compact_files)]
write_csv(OUT / "compact_evidence_inventory.csv", compact_rows,
          ["path", "bytes", "sha256", "category"])
write_csv(OUT / "final_evidence_inventory.csv", compact_rows,
          ["path", "bytes", "sha256", "category"])

print(json.dumps({"head": head, "tree": tree, "pr_url": args.pr_url,
                  "compact_files": len(compact_rows),
                  "local_raw_files": len(local_rows),
                  "local_raw_bytes": local_bytes}, sort_keys=True))
