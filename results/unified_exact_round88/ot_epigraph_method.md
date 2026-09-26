# Round88 sparse OT epigraph: source-only preparation

Status: **implementation prepared, not executable-qualified or admitted**. No test, toy Optimize, real LP read/Optimize, build or compression was run while startup held the computation slot. The proposed `300 s` applies separately to each *whole supervised arm* only after a later signed `ot_epigraph_lease.json`; no real Optimize is authorized by this file.

## Fixed source and six independent arms

`scripts/round88_ot_epigraph.py` uses the three already-qualified original LP manifests from `round88_ot_closure.py`: F2 root, D7 root, D7 historical child. The intended order is F2 B1/B2, D7-root B1/B2, D7-child B1/B2. Every arm verifies input/LP SHA, frozen manifest, source/support fingerprint and script/helper SHA, reads its own original LP, runs the existing `audit_model` for actual VD-P one-hot, perspective, Gini, objective, G bounds and cutoff rows, and only then calls `relax()`. It never starts from another arm's rowbank or primal. The D7 child is a diagnostic source, not a retained ENS leaf. B2 uses only the actual local G interval; for zero width B2 is rejected and B1 is the mathematical family. No combined arm is made because full positive-width B2 implies B1.

## Exact construction and projection

The solver-free `make_plan` builds all row coefficients and RHS as `Fraction`. For each station, exact `y/D_i` order produces true-prefix `C_{ik}` and (for B2) `Q_{ik}` only for `1≤k<n_i`; adjacent recurrence rows use original selector or perspective variables. Empty prefix is zero. Full prefix is the **constant one** for C and original `G` for Q, justified by source-audited one-hot and `qsum`; no redundant full-prefix column is added. Equal ratios are merged exactly, with no epsilon tie, and every pair threshold is mapped to its two prefix indices.

For B1, each nonempty pair interval adds `v≥A`, `v≥−A`, and the pair summary `h≥ΣΔv`. For positive-width B2 it adds `u≥±(bA−B)`, `v≥±(B−aA)`, and `(b−a)h≥ΣΔ(u+v)`. All auxiliary variables are continuous, nonnegative, objective-zero. Eliminating prefixes gives the direct CDF differences on original selector/perspective columns; eliminating auxiliary variables gives the full signed B1 or B2 row family in projection. Integer `q=Gs` yields the physical pair distance exactly. This preserves the original integer feasible set and objective but does not assert the original LP or new relaxation is the integer convex hull.

The script computes `N=Σ_i(n_i−1)`, `P=Σ_pairs p_ij`, `K=#pairs with p_ij>0`. B1 predicts columns `N+P`, rows `N+2P+K`, NZ at most `3N+7P+K`; B2 predicts `2N+2P`, `2N+4P+K`, NZ at most `6N+26P+K`. It also calculates the **exact** nonzero count from rational row dictionaries, saves every exact new row and all new column names, then compares predicted column/row/NZ deltas against Gurobi's actual model after insertion. Any mismatch invalidates the arm; there is no silent repair. The qualified source manifest supplies full support and actual G domain, and the new provenance retains those values plus interval counts, identity SHA, model sizes and costs.

## Deadline, numerical evidence and limits

`prepare-supervise` is shared source fingerprint work and separately records its nested launch-to-exit wall. Qualification must additionally save and charge the **entire outer preparation command** wall, including wrapper startup and receipt writes; the nested timer is not the total shared cost. A real `supervise` starts its 300-second clock before per-arm identity checks and child launch. The child cannot read the LP until assigned to a Win32 kill-on-close Job and handed a ready flag. The clock includes source hashing, LP read, original-structure audit, relaxation, rational plan/ledger creation, row insertion, one Optimize, complete primal save and every original/new row and variable-bound residual. `run-batch` is serial and stores each arm's receipt; ordinary whole-arm deadline is `unknown`, never an optimum or a trigger to switch algorithms, and the next pre-authorized arm may continue. Identity, count, residual, unexpected infeasibility or resource failure stops the batch. There is no internal solver-time, Work, row-count or iteration fallback and no MIP transition. Per-arm supervisor wall is nested within externally measured whole batch wall; shared preparation and later offline audit are separately reported rather than subtracted from the six arms.

`OPTIMAL` plus the inherited `1e−5` original/new row and bound-residual gate is labeled only a **numerical fixed-LP objective** under the existing Gurobi parameters (Threads 1, Seed 0, Presolve −1, FeasibilityTol/OptimalityTol `1e−6`, MIPGap 0). It is not a rational lower-bound certificate or a whole-method speed claim. Infeasibility requires source/scope audit. Raw solver log, full primal, per-row residual JSONL, exact row ledger, provenance, inflight phase, child result and outer receipt remain in each arm directory. The parent must freeze hashes, admit micro tests and zero-Optimize three-source structure qualification, then issue a distinct Optimize lease before any six-arm run.

## Independent tests prepared but not run

`tests/round88_ot_epigraph_test.py` directly rescans all original states at each exact ratio threshold using `Fraction`, independently enumerates every sign pattern on tiny supports, constructs prefix/absolute-value lifts from direct sums, and checks integer one-hot `q=Gs` points at both G endpoints and an interior point. It includes a hand-calculated fractional toy, a nonproportional `q` perspective point, exact B1 full-prefix `C=1` and B2 full-prefix `Q=G` coefficient/RHS checks, zero-width B1/B2 rejection, duplicate support and wrong-domain guards, tampered-prefix recurrence, intentionally omitted pair-summary detection, and malformed child-result supervision receipts. These tests are prepared but unrun; later qualification still needs actual API/count, Windows descendant-deadline and three real LP **zero Optimize** identity/structure exercises under a separately released computation slot.

## Source-only snapshot SHA-256

| File | SHA-256 |
|---|---|
| `scripts/round88_ot_epigraph.py` | `5d49c3fc12cc806a8008e43d756bf9c46810b21e7efc2b64c2383da4624bd7da` |
| `tests/round88_ot_epigraph_test.py` | `2be3e3e51333e29fcfa3b52c17f90ce4603603dd2032979191fb96a1624913ab` |
| frozen `scripts/round88_ot_closure.py` | `129b9224ac36e44b52fcc911604938a024d79986f8bd5fe8a8ffd6b14d1b2934` |
| frozen `scripts/round88_ot_diagnostic.py` | `c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756` |
| frozen `scripts/round88_ot_math.py` | `2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840` |
| `ot_compact_epigraph_proposal.md` | `17ded1685871bc1a977b2361d5ea7ea41a6cb8828a6db5f8efcf9c8874b7ce90` |
| `ot_closure_decision.md` | `90555187dd35b7c0a076fa71c33ba0f8f6e79a1aa45e043c9a4b9e66efc78ce6` |
