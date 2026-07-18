# Round 22 trajectory-integrity erratum

This first integrity erratum introduced a magnitude cutoff. A later independent native counterexample showed that any magnitude-based monotonicity cutoff still conflates solver behavior with evidence corruption. `trajectory_monotonicity_erratum.md` supersedes only that cutoff; the raw-value, no-repair, endpoint, and structural-integrity requirements below remain in force as historical provenance.

The first attempted Stage 2 stopped on `stage2__V12_M1__plain__900s__dense_on`. Its authoritative raw CPLEX local-progress trace contained 391,404 retained events and 3,816 full-precision negative steps in `CPXCALLBACKINFO_BEST_BND`; four exceeded the runner's former absolute `1e-7` cutoff. The largest was `6.60548520547977e-7`, and each of those four isolated excursions recovered on the next retained observation. The final raw record was `0.35720058320841552`, exactly equal to the native final lower bound in the result JSON. Timestamps, processed nodes, finalization, model gate, and endpoint evidence were otherwise valid.

The original runner treated any decrease larger than `1e-7` as corruption. That assumption conflated native callback numerical fluctuation with loss or alteration of evidence. No algorithm, arm, model, parameter, certificate rule, or recorded observation is changed by this erratum.

Before accepting any production-matrix row, Round 22 now freezes these rules:

- Raw bound and incumbent values remain full precision and are never clamped, enveloped, rounded, suppressed, or repaired.
- Every negative bound step and positive incumbent step is counted; the maximum step is reported in `trajectory_integrity_audit.csv`.
- A step is material only when it exceeds `1e-6 * max(1, |previous|, |current|)`. A material step fails trajectory integrity; a smaller native fluctuation remains visible but does not invalidate the row.
- The scale is confined to trajectory-corruption screening. It cannot promote a solver status, establish optimality, alter model correctness or independent feasibility verification, change an objective or final lower bound, or enter S0/S1/plain comparisons.

The two passed Tailored rows preceding the stopped plain row are also excluded from the replacement Stage 2 so that the entire production matrix uses one refrozen runner/protocol. The prior Stage 1 and this stopped Stage 2 attempt are retained under `attempts/pre_integrity_erratum_cf12a925`. Stage 0 and Stage 1 must pass again under the refreeze before production restarts.
