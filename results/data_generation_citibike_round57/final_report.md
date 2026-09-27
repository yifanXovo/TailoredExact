
# Local Citi Bike data reconstruction round — final report

## Decision and paths

Completion status: **local_data_only_round_complete**.  Source classification:
**citibike443_source_valid_with_documented_issues**.  Legacy audit: **multiple_legacy_generator_versions_found**.
Dataset design: **adaptive_citibike_dataset_design_frozen**.  Generation:
**citibike_derived_candidate_dataset_complete_with_subfamilies**.  Compatibility:
**exactebrp_input_compatible**.  Preservation:
**all_historical_datasets_preserved**.

- ExactEBRP: `E:\codes\ExactEBRP`; branch `codex/round56-paper-benchmark-time-horizon`;
  HEAD `6b721dea0dfcadbe80cc862ab3a74c25a211d784`.
- Legacy Hybrid GA: `E:\codes\Hybrid GA`; branch
  `master`; HEAD
  `ecfbb6a49307e6a321f31e84f052d3325d1dd7af`.
- Capacity source: `E:\codes\Hybrid GA\testdata\CitiBike\coords\citibike_selected_443_capacity_list.txt` — 443 rows,
  SHA-256 `92ca9b05e66d1425bbc801be2dd9c0776b1a9707e62a60b821d941aa98625ae1`.
- Coordinate source: `E:\codes\Hybrid GA\testdata\CitiBike\coords\citibike_selected_443_coords_utm18n_meters.txt` — 443 rows,
  SHA-256 `c5fd892cc82e07332d4796edb0527182d9c60883acc9b87a5410dab569f990d1`.

Capacity and coordinate rows are aligned line by line.  The legacy loader maps
both source row i values to one-based internal index i+1.  The older companion
snapshot confirms 438 pairs by coordinate and capacity, four more by coordinate
with a changed capacity snapshot, and lacks one coordinate.  These annotation
issues do not alter the explicit source-row pairing.  The authoritative files
contain no IDs or names; companion IDs/names are included only where mapped.
One zero-capacity row is preserved but excluded from generated service subsets.

## Legacy findings and current format

Multiple legacy generator versions exist.  Generic routines synthesize every
field; the Citi Bike routine reads 414- or 443-row local lists, uses random or
anchor-nearest subsets, an artificial centroid depot, unseeded random inventory
and targets, target-squared weights, random minimum ratios, and Euclidean
distance / 1.5.  Its writer emits the current seven-field text shape plus a
matrix, while its reader rebuilds the matrix from points.  Working-tree changes
to capacity filtering, target bands, and weight scale are documented and were
not modified.

Retained rules are paired source-row alignment, positive-capacity eligibility,
spatial locality, the centroid depot, exact source capacities/coordinates,
homogeneous Q vectors, external T, and Euclidean UTM / 1.5 travel seconds.
Adapted or replaced rules are deterministic anchor choice/ties, two meaningful
geographic regimes, controlled inventory totals, a shared target comparison
profile, bounded target-derived weights/minimum ratios, and a points-only
single-authority file representation.

The current ExactEBRP parser requires `V M [Q...]`, five depot-inclusive arrays,
and either V+1 points or a matrix.  This family writes V+1 points, so the parser
rebuilds the matrix.  T is a scenario-manifest/`--T` value; pickup/drop remain
the current 60/60-second defaults.

## Frozen family design

Canonical name: **citibike443-regional-v1**.  Root: `E:\codes\ExactEBRP\reference\citibike443-regional-v1`.  Its classification
is `generated_untested_paper_candidate`, not final paper evidence.

Four independent source selections exist for each V: two compact nearest-V
regions and two regional farthest-first selections within the anchor's nearest
2V eligible stations.  Four anchors per V are farthest-separated after a
SHA-256-ranked start.  The depot is the three-decimal centroid.  Real-derived
fields are service coordinates and capacities; all inventories, targets,
weights, minimum ratios, depot and fleet/scenario settings are synthetic.

Each selection shares one target profile across shortage, exact-balance and
surplus initial-inventory regimes.  Shortage/surplus magnitude is 12% of total
target (at least V); local transfers guarantee both surplus and deficit stations.
Weights are bounded target-squared values normalized to one.  Minimum ratios are
0.10+0.40 times target fill ratio.  Points are serialized at source precision;
travel time is symmetric Euclidean meters / 1.5 m/s.

Coverage is V=[8, 12, 20, 30, 50], M={"8":[1,2],"12":[1,2],"20":[2,3],"30":[3,5],"50":[4,7]}, Q=[20, 30], and
T=[1800, 3600, 10800, 18000] seconds.  Counts are 20 geographic
selections, 60 station landscapes, 240
complete parser input/fleet variants, and 960 future T
scenarios.  Per V there are 4 selections, 12 landscapes, 48 inputs, and 192
scenarios.

## Pilot, validation, and preservation

The structural pilot used six small/medium/large cases across both geography
rules and all inventory-total rules.  It found no structural defect, so no
generated instance was replaced and the initial current-project rules were
frozen unchanged.  No performance criterion was examined.

All 240 inputs pass structural and Python parser-
semantic checks.  The standalone current-C++-parser probe accepted all
240 files.  All 60 landscapes map every
station to authoritative source rows; distance and inventory validation pass
for all 60/60 rows.
Deterministic regeneration achieved byte equality for all 349
dataset files and removed the guarded temporary directory.

All historical dataset tree hashes, both repositories' starting HEAD/status,
the three pre-existing ExactEBRP tracked edits, the legacy tracked edits, and
the two authoritative source hashes are unchanged.  The legacy project was
read-only.  No optimizer executable, K1-AM-SF, P-GRB, VD-P, Gurobi, CPLEX, HGA,
branch-and-cut, or runtime experiment was executed.  No commit, push, pull
request update, pull request creation, or merge occurred.

## Limitations and next experiment

The family has no trip/demand observations, uses an artificial centroid depot,
straight-line travel at a fixed 1.5 m/s, synthetic operational fields,
homogeneous Q, and no difficulty/performance qualification.  The companion IDs
are inferred only through exact local coordinate/capacity matching.

Next, preregister the 960-row structural matrix and a balanced screening subset
before any solve.  Run K1-AM-SF and P-GRB with identical one-thread budgets and
all four T values; retain every result, avoid replacing instances, and use the
inventory/geography labels only for stratified analysis.

## Main artifacts

- Dataset README: `E:\codes\ExactEBRP\reference\citibike443-regional-v1\README.md`
- Selection/landscape/fleet/T manifests: `E:\codes\ExactEBRP\reference\citibike443-regional-v1\manifests`
- Source mappings: `E:\codes\ExactEBRP\reference\citibike443-regional-v1\mappings`
- Source and legacy audits: `E:\codes\ExactEBRP\results\data_generation_citibike_round57`
- Validation tables: `E:\codes\ExactEBRP\results\data_generation_citibike_round57`
- Reproduction commands: `E:\codes\ExactEBRP\results\data_generation_citibike_round57\reproduction_commands.md`
