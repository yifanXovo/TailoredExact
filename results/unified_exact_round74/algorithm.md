# Frozen complete methods in the D7 validation

No solver implementation or algorithm parameter changes in R74. Exact source
and executable identities, all four commands and their input are frozen in
campaign/identity.json. Read the R73 algorithm.md and seed_extension.md for
the constructive seed, and R71 algorithm.md for the complete DS-X proof path.

|Arm|Preset/path|Startup and subsequent proof|
|---|---|---|
|P-GRB|plain-baseline, method gurobi|Original compact/native defaults, no external Start, cuts or imported bounds|
|DS-X|research-round71-vds-interroute-descent|24 fully decoded descents, followed by VD-S/AM|
|JDS-X|research-round73-vds-joint-seeded-descent|One direct physical construction, unchanged24 random seeds plus its25th seed, followed by the same VD-S/AM|
|K1-R|research-round65-k1-h with witness-audit and zero-stop repairs|Existing full HGA and K1-AM proof; separate protection reference|

JDS-X constructs unvisited pickup/drop motifs with integer quantities, all
eligible insertion positions and the original objective. It retains the
verified physical witness, completes its order to a full chromosome and
appends that seed after the original24. Each descent fully decodes the finite
generated neighborhood until no strict gain remains. The proxy orders only;
it does not reject candidates in this path. Seed20260626 and gain threshold
1e-12 are unchanged. The method does not enumerate all served-node transfers,
exchanges or quantity vectors, and has no local/global primal optimality claim.

The proof uses the inherited one-hot inventory/Gini-product representation,
verified full native Starts and complete interval coverage. AM uses one initial
interval, midpoint splits, normalized child-bound threshold0.08, depth8 and
minimum width1e-4. These mathematical controller choices contain no internal
seconds/Work allocation. K1-R remains a separate measured reference, never a
runtime fallback or a source of JDS-X witnesses/bounds.

The inherited route-derived strengthening is admitted for symmetric metric
travel; these research presets reject unsupported nonmetric inputs. The D7
input uses the same parser-generated Euclidean travel convention. This scope
restriction and its numerical metric check are inherited from R67, not a new
equivalence claim for arbitrary travel matrices.

All arms use Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested gaps0,
FeasibilityTol1e-6, IntFeasTol1e-5 and OptimalityTol1e-6. The same default-off
native evidence observer records physical routes, scoped bounds and completed
observation times. It changes no search decision. Its full-domain aggregation
and forced-termination qualification are documented in R73 runtime_design.md
and runtime_checkpoint.md. Numerical certification is not rational proof.

The single1200s process allowance includes startup, all native calls, mapping,
verification, observation and exit. Its shutdown reserve and owned-child hard
stop terminate the whole method. The300/600/900s observations are reporting
points only. Neither experiment arm selection nor K1 protection fractions are
solver inputs. See plan.md for admission, fixed comparison criteria and the
still-pending next gate; a validation stage is not overall goal completion.
