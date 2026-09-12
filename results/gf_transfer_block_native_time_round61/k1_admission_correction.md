# Current-model admissibility after archive propagation

Source review during confirmation found a retained Round60 admission condition:
the candidate had to strictly improve the model's cutoff as well as improve the
native incumbent. In a later K1 call, the global verified archive may already
be the cutoff. A candidate at equality is legal under the actual F<=U row and
may improve a missing or worse native incumbent. The existing canonical mapper
already supports this non-strict cutoff; the old preliminary gate can suppress
it before mapping. This is a scope/contract correction, not a gap threshold
tuned to the C2 performance result.

After the current serial suite finishes, the Round61 gate will require
admissibility under the current non-strict cutoff plus strict improvement of
the native incumbent. Current bounds, variable types and all linear rows are
still checked. A candidate in an incompatible Gini leaf is still rejected by
mapping. Hash deduplication remains per native call. Round60 behavior stays
unchanged.

The frozen candidate remains initialization +16 generations. Existing fixed
and Single-S candidate events had one MIP call per model and a strict initial
cutoff improvement; this equality branch does not change their admission
decisions. Preserve their actual build identities. K1 can exercise the corrected
branch across calls, so repeat both OFF and SUBMIT with the corrected paired
build under a new stage. Earlier K1 rows remain a diagnostic, never substituted
for the corrected pair. Do not infer binary identity from a final micro test.

Budget: use two of the three remaining reserved launches for the matched C2 K1
pair, at 300 seconds each. Combined with the declared final coverage and up to
three conflict solves, projected total is 71/72. No new candidate quality
selection, confirmation-driven threshold change, MIP-start arm or parameter grid.

The same post-performance build will correct a legacy fixed-model metadata
description that prints lambda=0.15 even when the new CLI accepts another lambda.
The actual model already reads the supplied lambda. Verify default and nondefault
model bytes in free build-only checks and preserve the original paired binaries.

The initial C2 K1 SUBMIT run subsequently confirmed the concrete path:
the root native-target submission returned success but no finite objective,
MIPSOL match or final integer match. Archive propagation then created a tighter
cutoff. In `L0.0_terminal_mip.gurobi_candidate_events.csv`, candidate
F=0.83709146755470198 is at the cutoff, `native_incumbent_before_available=0`,
yet status is `verified_but_not_strictly_better_than_frozen_cutoff` and submitted=0.
The whole run has 8 LP calls, 1 partial MIP, 1 terminal MIP and 1 split; OFF has
3 LP calls, 1 partial MIP, 1 terminal MIP and no split. Thus archive propagation
already changes the formal controller, while actual native processing remains
unknown. This is the case the corrected paired build must cover.
