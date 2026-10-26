# Round 51 final report — tight subset-duration Big-M, symmetry re-audit, and sparse root-guided branching

## Decision

Round 51 is a bounded negative result. **No new fixed-interval backend is promoted.** Production remains the Round 50 `interval-mip-v0` backend: historical formulation, v0 cardinality symmetry, and native Gurobi default branching. K1-AM is unchanged.

All implemented candidates are mathematically/correctness audited and reproducible, but each fails at least one predeclared performance or regression gate:

- M1 (`m1-tight-big-m-v0`) is valid and greatly improves coefficient ranges, but its core Work is 1.1620× baseline, it loses D4’s certificate, and it has severe D3/D4 regressions.
- S1 and S1-R1 reduce aggregate M1-v0 development Work to 0.9100× and 0.9553×, respectively, but both lose mandatory D13; S1 also loses D12, and S1-R1 severely regresses D14.
- A1 (`a1-root-sparse-2x2`) preserves certificates but totals 1.0048× paired M1-v0 Work and severely regresses D4’s capped gap.
- The sole authorized A1-R1 (`a1r-root-sparse-top1`) removes A1’s severe regression but totals 1.0162× paired M1-v0 Work.

No A1 development/confirmation, interaction, key-long, or K1 integration experiment was opened because the corresponding frozen prerequisite failed. This is a gate outcome, not an incomplete experiment.

## 1. M1 numerical effect on every affected state

M1 replaces only strengthened exhaustive subset-duration rows for V≤12 with the exact row value `M_S=max(0,tsp[S])`. All 120,540 target-row changes match that formula; every non-target row is unchanged. The 15 affected states group as follows (states in one row have identical numerical ranges):

| States | max matrix: old → M1 (reduction) | max |RHS|: old → M1 (reduction) | matrix range: old → M1 (reduction) |
|---|---:|---:|---:|
| D1 | 100,000 → 14,815.36 (85,184.64) | 1,200,396.60 → 45,530.72 (1,154,865.88) | 4,444,444.44 → 658,460.55 (3,785,983.90) |
| D2 | 100,000 → 10,441.02 (89,558.98) | 998,393.47 → 38,458.75 (959,934.73) | 4,444,444.44 → 464,045.35 (3,980,399.09) |
| D3, D4, D5 | 100,000 → 14,202.91 (85,797.09) | 1,199,250.89 → 43,045.82 (1,156,205.07) | 4,444,444.44 → 631,240.45 (3,813,204.00) |
| D6, D7, D8 | 100,000 → 11,748.09 (88,251.91) | 1,198,890.65 → 41,002.84 (1,157,887.81) | 4,444,444.44 → 522,137.23 (3,922,307.22) |
| D12, C1, C2 | 100,000 → 11,601.85 (88,398.15) | 1,199,013.34 → 39,653.31 (1,159,360.02) | 4,444,444.44 → 515,637.95 (3,928,806.49) |
| C6 | 100,000 → 13,962.29 (86,037.71) | 998,665.41 → 42,324.58 (956,340.83) | 2,300,000.00 → 321,132.70 (1,978,867.30) |
| C7 | 100,000 → 11,524.94 (88,475.06) | 1,199,408.55 → 35,305.99 (1,164,102.55) | 4,444,444.44 → 512,219.36 (3,932,225.08) |
| C8 | 100,000 → 12,234.39 (87,765.61) | 1,000,253.25 → 37,368.77 (962,884.48) | 4,444,444.44 → 543,750.51 (3,900,693.93) |
| C9 | 100,000 → 12,768.96 (87,231.04) | 800,256.11 → 39,517.92 (760,738.19) | 4,444,444.44 → 567,509.44 (3,876,935.01) |

Thus the maximum matrix coefficient falls by 85.2–89.6%, maximum absolute RHS falls by 760,738–1,164,103, and the matrix range ratio falls by 1.98–3.98 million on every affected state. D9–D11, D13–D14, and C3–C5 are Big-M-unaffected and remain byte-identical. The complete unrounded table is `numerical_conditioning_before_after.csv`.

## 2. M1 optimization behavior

The numerical improvement did not translate into a safe optimization improvement. On the nine-state core, baseline certifies 5 states and M1 certifies 4; aggregate Work rises from 1313.5133 to 1526.3584 (+212.8451, 1.1620×). D4 changes from exact to capped. D3 has a severe capped-gap regression, and D4 is severe by certificate loss.

Root behavior is mixed and mostly non-improving: the root relaxation improves only on D2 by about 2.77e-5, is unchanged on D1 and all unaffected core states, and is lower on D3–D6. Final root-cut bound improves only on D6, is unchanged on D9–D11, and is lower on D1–D5. M1 does not improve total certificate count or aggregate Work. It harms D2, D3, D4, D5, and D6 in Work, with D4 the decisive status harm; only D1 shows a small Work reduction.

The old coefficient 100,000 is retained as an explicit historical/default-off policy, not asserted safe. The corrected Round 50 numerical interpretation and M1 proof are in `round50_numerical_audit_correction.md` and `big_m_validity_proof.md`.

## 3. Symmetry after M1 and the D13 negative control

Both symmetry candidates looked acceptable on the 120-second M1 core: S1 used 0.8999× M1-v0 Work and S1-R1 used 0.9929×, with no core certificate loss or severe regression. Their behavior remained nonuniform on the full D1–D14 development panel:

- S1 uses 4470.8537 versus 4913.0624 Work (0.9100×), but loses D12 and D13; both losses are severe.
- S1-R1 uses 4693.3819 versus 4913.0624 Work (0.9553×), but loses D13 and has a separate severe D14 capped-gap regression.

D13 is Big-M-unaffected and its M1-v0 model is byte-identical to the historical model. Its Round 50 symmetry regression reproduces under both S1 and S1-R1, proving that M1 neither caused nor repaired it. The final symmetry remains v0 cardinality; no symmetry candidate reaches confirmation.

## 4. A1 selections and child-bound evidence

A1’s rule is state-dependent but invariant: original fractional semantic primitives only, at most four candidates, at most two per family, exactly two disposable child LP probes per candidate, product score, and at most two positive priorities. The official core selected:

| State | Priority 2: variable / family / score / (down, up delta) | Priority 1: variable / family / score / (down, up delta) |
|---|---|---|
| D1 | default fallback: all valid candidates had zero improvement | — |
| D2 | `x_0_4_1` / routing_arc / 1.890e-9 / (0, 1.890e-2) | `z_0_1` / visit_selection / 1.000e-14 / (0, 0) |
| D3 | default fallback: all valid candidates had zero improvement | — |
| D4 | `z_2_11` / visit_selection / 6.061e-12 / (0, 6.061e-5) | `z_1_5` / visit_selection / 2.418e-12 / (0, 2.418e-5) |
| D5 | `p_2_8` / pickup_quantity / 1.076e-13 / (1.076e-6, 0) | `d_0_6` / drop_quantity / 1.000e-14 / (0, 0) |
| D6 | `x_0_11_5` / routing_arc / 1.208e-5 / (9.267e-4, 1.303e-2) | `z_0_5` / visit_selection / 7.523e-6 / (9.267e-4, 8.118e-3) |
| D9 | `x_0_20_14` / routing_arc / 1.934e-8 / (0, 1.934e-1) | `z_0_20` / visit_selection / 1.903e-10 / (~0, 1.903e-3) |
| D10 | `x_2_14_20` / routing_arc / 1.637e-8 / (0, 1.637e-1) | `mode_2_20` / operation_mode / 1.938e-10 / (0, 1.938e-3) |
| D11 | `z_1_2` / visit_selection / 2.246e-8 / (3.838e-5, 5.851e-4) | `p_0_14` / pickup_quantity / 1.000e-14 / (0, 0) |

All 72 core probes are fresh canonical-model reads, every imposed bound reads back exactly, and all fingerprints match. A1’s 23 build-only models are byte-identical to M1-v0. The complete evidence, including all four candidates rather than only selected variables, is in `adaptive_branching_probe_evidence.csv`.

## 5. Probe overhead and repayment

Across A1’s nine core states:

- required root LPs consume 4.1278 Work and 1.4590 solver seconds;
- 72 child probes consume 30.4981 Work and 11.1990 solver seconds;
- terminal MIPs consume 1500.0441 Work and 720.0990 solver seconds;
- total A1 is 1534.6699 Work, 732.7570 solver seconds, and 739.1423 process seconds.

The paired M1-v0 comparator uses 1527.4006 Work and 735.5189 process seconds. A1’s terminal MIPs alone save 27.3565 Work, but the 34.6258 root-plus-probe Work more than consumes that benefit, leaving +7.2694 Work and +3.6234 process seconds end to end. The probes therefore do not repay their cost.

A1-R1 uses the identical root/probe phase, then assigns priority 1 only to the best variable. It cures D4’s severe regression but its terminal MIPs use 1516.5079 Work and its total rises to 1551.1338 versus 1526.3764 paired M1-v0 (+24.7574, 1.0162×). It also fails the aggregate gate.

## 6. Certificate and severe-regression comparison

A1 avoids the certificate losses seen in Round 50 whole-family priority candidates: it preserves all four paired M1-v0 core certificates and emits zero false certificates. However, it does **not** avoid all severe regressions: D4’s capped gap rises from 0.10279 to 0.15563 (1.514×, +0.05284), triggering the frozen rule. A1-R1 preserves certificates and has zero severe regressions, but remains aggregate-Work-worse.

For context, Round 50 B1 lost D3/D13 and severely regressed D14, B2 lost D4/D10, and B3 severely regressed D4. Sparse probing improves certificate safety but does not yield a promotable end-to-end policy here.

## 7. Promotion outcome

No formulation or policy is promoted:

- M1: rejected at core; retained only as the audited experimental baseline for the ordered symmetry/adaptive studies.
- S1 and S1-R1: rejected after full D1–D14 development; final symmetry is v0.
- A1 and A1-R1: rejected at core; final branching is native Gurobi default.
- Interaction: not opened because neither component passed independent confirmation.
- K1-AM: unchanged because no new fixed-interval backend passed.

## 8. Mathematical validity, reproducibility, uniformity, and paper safety

M1 is mathematically valid for its target rows, and A1/A1-R1 are deterministic, uniform, auditably bounded algorithms with no instance, size, runtime, Work, node, memory, machine, or history dispatch. The canonical-model, lifecycle, priority-readback, cap, certificate, and raw-evidence audits pass. They are suitable for an OR-paper description as carefully bounded **negative experimental results**.

They are not suitable to claim as a production improvement: every candidate violates a frozen promotion gate. The paper-safe production statement is therefore that Round 51 found no uniformly safe improvement and retained Round 50 unchanged.

## Verification and evidence map

- Complete build: pass; complete configured CTest suite: 29/29 pass.
- Cross-stage certificate audit: 122/122 evidence-valid rows, zero false certificates.
- Default-off equivalence: 23/23 canonical models match Round 50; four sampled runtime rows exactly reproduce status, certificate, and Work.
- Pre-existing user changes: all three tracked blob hashes and the complete tracked diff hash remain unchanged.
- Raw evidence: locally available and inventoried in `raw_evidence_inventory.csv`; compact evidence is committed.
- Principal decisions: `big_m_decision.json`, `symmetry_m1_decision.json`, `adaptive_branching_decision.json`, and `final_decision.json`.
- Principal combined audits: `certificate_audit.csv`, `default_off_equivalence.csv`, `severe_regression_audit.csv`, and `experiment_stage_audit.csv`.
