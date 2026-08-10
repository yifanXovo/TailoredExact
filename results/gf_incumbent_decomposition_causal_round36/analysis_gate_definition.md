# Round 36 analysis gates

These gates were fixed after the four-arm V12_M1 integration pilot and before
the remaining 52 official rows completed.  The pilot is used only to verify
that the intended interventions are live; it is not sufficient to pass any
mechanism gate.

All comparisons use independently verified common upper bounds.  Trajectory
AUC uses the common observed window, left-continuous values, no interpolation,
and no extension beyond either run's last recorded bound event.  Timing and
Work are effort outcomes, never inputs to exact decisions or sequence hashes.

## Validity gate

Every official row must be checksum-complete, single-threaded, structurally
covered, free of bound inversion and false certification, and must satisfy its
startup/anchor contract.  Failure makes the study invalid.

## Geometry gate: HH versus BW-P

Only rows with `U_H <= U_S` (within tolerance) and `U_H < U_S` materially are
causal geometry exposures: HH and BW-P then share `U_proof`, while BW-P alone
uses the wider anchor grid.  Geometry is supported only when all of the
following hold:

1. at least four exposed rows span at least two Round-35 diagnostic patterns;
2. at least three rows and at least 60% of exposed rows change a downstream
   LP/control/target/split/closure sequence (the endpoint change alone does not
   satisfy this condition);
3. at least four rows have an outcome direction consistent with the frozen
   Round-35 pattern, and at least 60% of directionally assessable rows agree;
4. the downstream evidence includes both a weaker-SIMPLE/faster pattern and a
   V50 certification/final-gap-regression pattern.

Outcome direction uses certificate first, common-UB final gap second, observed
proof AUC third, and exact-phase time only as a final descriptive tie-break.

## Split-normalization gate: BW-P versus BW-A

Only rows with a material `U_anchor - U_proof` difference are normalization
exposures.  Split normalization is supported only when:

1. at least three exposed rows spanning two patterns change actual split
   decisions or split sequences;
2. at least two of those rows have a material proof/performance consequence;
3. the first structural divergence is not observed before a split decision in
   those supporting rows.

Different denominator values without a different split decision do not pass
the gate.  Rows with zero actual splits cannot support a rho explanation.

## Classification and follow-up

The two gates produce one of four conclusions: geometry dominant,
split-normalization dominant, both effects, or neither isolated effect
sufficient.  C6-HGA-FULL remains unchanged in every case.  A positive gate may
authorize a separately frozen Stage C validation recommendation; it never
promotes a mainline automatically.  A rho sensitivity study is recommended
only if the normalization gate passes.
