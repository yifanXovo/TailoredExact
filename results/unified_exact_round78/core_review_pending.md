# Read-only core review while the frozen full screen runs

This note admits no implementation or experiment. The BDS-C full outcome is
still unknown. The full_screen_plan already calls for a core comparison if
the distinct assignment repair remains insufficient; it does not mandate
another route-neighborhood expansion.

Current source inspection confirms solveGurobiBaseline in GurobiBaseline.cpp
always writes CanonicalCompactModelSpec with strengthened=false. Its existing
gurobi_hga_start path runs its own HgaTgbcRunner options, maps a complete Start
over the original compact domain, and submits an array. It does not run the
main.cpp current-witness constructor/25-path/BDS-C controller and does not
inherit the R68 complete actual-row/readback acceptance chain merely by using
the semantic mapper. A new same-starter comparison therefore needs actual
integration and native-vector qualification, not renaming this old flag.

The current paper startup function is private to main.cpp; baseline dispatch
calls solveGurobiBaseline(instance,options) directly. A future clean interface
could pass an explicitly typed current-run verified start or invoke a shared
starter callback before compact construction, retaining the sole process
deadline and complete accounting. It must retain witnesses when native MIP
has no incumbent and publish observed availability without backdating. Avoid
duplicating subtly different constructive seed/tie/handoff rules across engines.
No archived diagnostic witness may enter a formal arm. Official P remains
unchanged; the candidate should have its own name and evidence scope.

The existing R68 native path already calls normalizeRound61Routes before
mapping. That normalizes used-vehicle ordering only within equal-Q classes
and verifies unchanged inventory/feasibility. This is why a balanced relocation
that empties a source route need not add a new symmetry workaround. Original
compact's old HGA block only strips empty routes before mapping; it would need
the same explicit handling and actual checks in a future formal integration.

A plain compact+same starter comparison would change formulation/outer proof
organization together relative to BDS-C/VD-S. It can answer the complete core
question but cannot isolate AM as the sole cause. Adding incumbent-derived
domains or new cuts would be a further mechanism, requiring an independent
validity/scope argument and stated comparison; it is not silently included
in the phrase "same compact model." Neither route counts nor a stronger LP
alone settle which representation will perform better.
