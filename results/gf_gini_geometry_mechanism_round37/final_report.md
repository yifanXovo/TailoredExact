# Round 37 final report

## Outcome

The study confirms a real structural Gini-cell relaxation mechanism, but rejects G1 as a mainline performance change. G1 remains a default-off diagnostic; **C6-HGA-FULL, K=4, rho=0.01 remains mainline**.

## Stage 0 and engineering

Round 36 reporting was consolidated into immutable intermediate Stage B and terminal Stage C records, with PR 83's current merged state recorded separately. A hash-guarded cleanup removed 79 proven top-level transient/intermediate files (17,209,698 bytes) while retaining raw runs, invalidations, manifests, and the uncompressed trajectory fixture required by tests.

The 103 Round 36 historical runs pass lifecycle, coverage, counter, timestamp, and certificate audits. Exact CSV streams now use round-trip precision: 81/103 old Work ledgers lost aggregate reconstructability at 1e-7, while new ledgers reconstruct to floating summation error. Bounds and certificates were unaffected.

After G1 implementation, default-off C6 passed 18/18 contemporaneous mechanism equivalence comparisons against the frozen Round 36 executable.

## Geometry and experiments

Prior forensics rejected a generic low-G skew: 12/14 weakest initial LP cells were interior cells 1 or 2. The 12-row development panel was frozen before any candidate result.

| Stage | Cap | Pairs | G1 exposed | Improves | Regresses | Ties |
|---|---:|---:|---:|---:|---:|---:|
| Smoke | 180 s | 6 | 5 | 1 | 1 | 4 |
| Diagnostic | 480 s | 3 | 3 | 2 | 1 | 0 |
| Confirmation | 900 s | 2 | 2 | 1 | 1 | 0 |

Every exposed pilot reproduced the prior weakest-cell index and strictly increased that cell's valid LP bound. Yet the downstream sign is stable and bidirectional: the V20 tight-T final common-UB gap improvement grows from 0.07526 to 0.11225 across caps, whereas the V50 high-imbalance regression stays near -0.028964. AUC has the same signs.

The local gain is therefore causal but insufficient as a global policy criterion. A forced split changes leaf topology and front-loads two child LPs; the global bound remains controlled by the minimum relevant leaf, so a locally stronger cell can still delay more useful native targets or closures elsewhere.

## Exactness and final audit

All 22 official runs pass root/parent-child coverage, monotone bounds, verifier consistency, environment/model lifecycle balance, optimize counter identities, and round-trip Work/node reconstruction. There are 6 strict certificates, 16 valid non-certificates, and zero false certificates. All 11 pairs differ only in the explicit geometry policy and run-local paths.

The final independent clean build passes 16/16 C++ and 28/28 Python test scripts. Its PE hash differs from the same-size frozen research binary, so no byte-reproducible-link claim is made.

## Decision

Do not promote G1 and do not broaden validation. Retain it default-off for mechanism diagnostics. G2 remains untested and requires a new predeclared round. No merge is authorized by this research result.
