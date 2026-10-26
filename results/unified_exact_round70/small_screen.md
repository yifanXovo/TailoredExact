# Completed small-role screen, revision2

All nine declared E7/S12/N12 runs are complete under the same new binary,
logical processor2/mask4 and120-second whole-run cap. Every run certifies the
unchanged original objective. The six correctness micros are separate.

|Role|P-GRB wall|VD-S wall|DS wall|DS startup|DS initial UB|Final certified objective|
|---|---:|---:|---:|---:|---:|---:|
|E7|1.282|5.610|1.156|0.018933|0.020865508|0.020382504|
|S12|5.187|39.187|2.094|0.341395|0.107986736|0.058563973|
|N12|3.891|3.640|1.453|0.015698|0.919588091|0.804625520|

Using the frozen small-certified practical thresholds, DS repairs E7's
material VD-S/P startup loss and becomes close to P. S12 repairs the severe
VD-S/P loss and has a material P improvement of3.093s; N12 improves materially
over both P (2.438s) and VD-S (2.187s). These are individual fixed-seed fresh
development runs, not statistical equivalence or independent confirmation.

DS uses a different and weaker initial witness in all three cases. S12's
uncached decodes fall from13826 to247, while its initial objective deteriorates
from the final optimum to0.107986736. The exact proof/primal search recovers
the final0.058563973 objective, so total time still improves. This is an
end-to-end startup tradeoff, not a claim that descent improves HGA's solution
quality or directly strengthens lower bounds. All three descents exhaust24
seeds: E7 has48 passes/92 checks, S12 has92/224, N12 has65/186. Checks include
cache hits; uncached decoder calls and total wall are separate measurements.

The audit at this boundary covers15 revision2 runs (nine performance and six
micro),64.311s complete process wall and67 experiment Optimize calls. It
checks54 retained initial-witness/model pairs with22 incompatible Gini
intervals and zero compatible-point failures; all8 actual native Start
decisions are eligible, accepted and fully observed by the qualified MIPSOL
observer. Physical endpoints, original P fingerprints, native settings, full
interval unions, affinity readback/restoration and DS descent traces pass.
The evidence manifest contains234 compact artifacts at this boundary.

Revision1's six micros, two DS invalid-configuration failures and21 native
calls/.766s remain separately charged and retained. Their successful controls
are superseded qualification evidence, not fresh performance comparisons.

This screen satisfies the planned condition for continuing the unchanged
candidate on D3 and the remaining medium/large development roles. D3 is now
being measured; no result or general protection claim is implied here. The
complete bounded stage and overall research goal are still unfinished.
