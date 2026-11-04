# Final audit path recovery: independent static review

Disposition: `ACCEPT_PATH_ONLY_RECOVERY_AND_NEW_METERED_FINALIZER_ATTEMPT`.
This accepts a new `final_evidence_v2` attempt through the existing exact
worker and finalizer, under one verification outer receipt. It does not
retroactively pass v1 or establish that the final evidence audit has
succeeded. No scientific producer or complete arm is to be rerun.

The independent nonimplementer read the actual source diff, witness
discovery and its selection/verification callers, ROOT definition,
finalizer sequence, v1 traceback and closed receipt. No source import,
program execution, Native, Optimize, replay, model read, compilation,
or computational validation was performed for this review.

The observed v1 failure is the reported presentation/provenance-path
error: `source.relative_to(ROOT)` receives a relative path naming
`results/unified_exact_round153/coupled/K-35-U_primal_pool/best_primal.json.gz`
while ROOT is absolute. The saved traceback ends in `ValueError` at
that conversion, not in a mathematical assertion. The attempt has
observed exit 1, no timeout or supervisor failure, and verification G1
`102.11308240005746` seconds. No completed PASS result is present in its
qualification directory. Passing checks reached before the exception
are not represented as a completed audit.

The inspected git diff changes only `witnesses()`:

- Each result path is interpreted relative to repository ROOT when
  needed, then resolved before reading, recursion and `seen` membership.
- Each explicit `upper_witness_source` is treated by that same rule.
- The local `best_primal.json.gz` inherits its already resolved absolute
  parent. The final set therefore deduplicates normalized path objects.

This matches the existing saved ROOT-relative evidence convention and
the main caller's absolute `ROOT / spec['coupled_result']`. It fixes the
specific mixed-path representation at the downstream relative-to-ROOT
reporting step and also avoids repeated traversal through relative and
absolute aliases. It does not round or replace a witness, manufacture
an upper, or change its mathematical contents. A missing witness still
fails when read; an absolute witness outside ROOT still fails the
unchanged reporting containment operation rather than being silently
relocated.

The selected-witness checks are unchanged: objective agreement with the
saved upper, true legal stocks and exact f, mass/negative mass, all
marginals, true completion slack, original-Q primal feasibility and
objective. The exact Q residuals, true RMP column minimum, support and
pricing provenance checks are likewise outside the diff. Existing
six-model-read/zero-Optimize final-audit scope remains unchanged.

The unchanged finalizer runs audit first, then scientific/research/full
panel reports and source identities; its postprocessing PASS is written
only after those steps. The new label must retain the v1 launch, source
snapshot, traceback and nonzero fee as a separate failed attempt. The
new full finalizer cost is another verification outer fee, with child
work not added again. This is necessary completion of the failed final
validation, not repetition of the scientific experiments.

| Read source or evidence | SHA256 |
| --- | --- |
| `scripts/round153_audit.py` | `c600b8ba910eb798ca09fc6ff4f6da4cc7e3d84056413f4ce8d9db4c160ec5cf` |
| `scripts/round153_finalize.py` | `e91eb37e7d4d65b0cc9b1285c62cdea4f57f2d92d1d31e9ba1c118115a2ab2fe` |
| `scripts/round153_exact_worker.py` | `f40ea001ea1a56bc2eb11536aa49574e2606356098751653a365d0030497d40d` |
| `fees/final_evidence_v1/receipt.json` | `0b935682d81b61b1ecda8f53dcf6bbc418dcd32f0a1f8f8e4dde454dc4b5aeff` |
| `fees/final_evidence_v1/stderr.log` | `f6bba2992df3dd4760c9d351044251eb74df72101e17d6a8f52fc469b9382bf1` |
| `fees/final_evidence_v1/launch.json` | `36ee57b4ae7616a154e4b4cb260fe91bd70dcc9c09dc9bafc80eb6c9df6f30cd` |

Fee paths in this table are relative to `results/unified_exact_round153`.
