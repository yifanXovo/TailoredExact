
# Legacy Hybrid GA generation-pipeline audit

Classification: **multiple_legacy_generator_versions_found**.

The legacy project at `E:\codes\Hybrid GA` contains more than one generator.
`Instance_Generator.cpp:36-294` and `716-820` generate fully synthetic
capacities, inventory, targets, coordinates and distances using unrecorded
`random_device` state.  `CitiBikeSubsetGenerator.h:117-365` instead loads paired
Citi Bike capacity/coordinate lists, chooses either an arbitrary shuffled subset
or an anchor-nearest dense subset, places an artificial centroid depot, then
generates inventory, targets, weights and minimum ratios synthetically.  Active
call sites are split between the older 414-station sources and the requested
443-station sources (`ModelTuner.h:258-311`).

The working tree also contains uncommitted generator changes: zero/very-large
capacity filtering, wider low/high target bands, and weight normalization from
[0,10] to [0,1].  Those changes are preserved read-only and recorded in the
file/status inventory.  The old writer emits `V M [Q...]`, depot-inclusive
capacity/initial/target/weight/min-ratio arrays, points, and a distance matrix.
The paired reader ignores the serialized matrix when points are present and
recomputes Euclidean distance divided by 1.5.  T is supplied to the loader.

The historical inventory contains 3979 parse-shaped `.txt` files.
Observed V frequencies are `{"6":1,"8":13,"10":3655,"12":22,"14":18,"16":15,"51":1,"75":23,"100":46,"125":8,"150":32,"200":44,"250":27,"300":18,"350":9,"400":46,"401":1}`;
coordinate-origin counts are `{"citibike414_coordinate_match":293,"citibike443_coordinate_match":55,"synthetic_or_unknown":3631}`.
These files remain historical evidence; they are not copied or overwritten.

The new design therefore retains source-row alignment, positive-capacity
eligibility, spatially local selection, an artificial centroid depot, real
capacities/coordinates, homogeneous Q vectors, and the 1.5 m/s parser convention.
It replaces every unrecorded random choice and every uncontrolled inventory rule.
The complete retain/adapt/reject ledger is in `legacy_rule_decision_table.csv`.
