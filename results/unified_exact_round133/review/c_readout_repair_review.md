# C-R3 physical readout repair review

The original derived analyzer omitted the reported objective required by
`full_fleet`. Its caught comparison exception did not stop the subsequent
exact binary64 matrix/point residual calculation. The repaired helper uses
the unchanged raw-point SHA to identify the same eight vectors, reconstructs
their routes, derives inventory and physical objective, and supplies that
objective to the established complete fleet checker. It preserves the
original failed analysis and its exact row/domain facts. This is an accepted
readout repair, with zero new Optimize, Env or rational row recalculations.

All eight physical points pass. The cold model replay's final status is
TIME_LIMIT (9), with loaded objective `0.31538912105344014` and physical
objective `0.31538912105343897`; the signed physical-minus-loaded difference
is approximately `-1.17e-15`. Native/physical penalty contributions also
agree at this scale. The stored MIPSOL_4 has a larger native G epigraph
value, by approximately `0.006408285071099`, than the same route's physical
G. That allowed positive epigraph slack is not evidence of the original
native-under-physical mismatch.

The cold replay did not reproduce the original mismatch direction. The
unchanged original workflow C-R2 did reproduce native OPTIMAL with the
approximately `4.24e-7` physical gap. This analysis does not identify the
original hidden numerical cause, certify the replay's remaining MIP tree,
or treat residual tolerances as objective error bounds. Diagnostic vectors
are not transferred into D/D3 production starts, bounds or cutoffs.
