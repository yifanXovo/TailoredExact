
# citibike443-regional-v1

Classification: **generated_untested_paper_candidate**.  This family has not
been performance-tested and is not final paper evidence.

This dataset uses real Citi Bike station coordinates and capacities from the
two immutable local 443-row sources listed in `source_provenance.json`.  The
source files do not themselves contain IDs or names; those annotations are
recovered from a uniquely matching local companion station table.  Inventory,
targets, weights, minimum ratios, the centroid depot, fleet settings and route
horizons are synthetic.

Each V in [8, 12, 20, 30, 50] has four independent geographic selections: two compact
nearest-V regions and two broader regional selections covering V stations
inside the nearest-2V pool.  Each selection has shortage, balanced and surplus
inventory variants sharing the same station targets.  Source mapping CSVs make
every local station traceable to a zero-based authoritative source row.

The artificial depot is the rounded centroid of the selected points.  Input
files serialize exact three-decimal UTM 18N points and omit a redundant distance
matrix.  Current ExactEBRP rebuilds travel seconds as Euclidean meters / 1.5.
Every file contains two homogeneous-Q fleet densities per V and Q in [20, 30].
T is not embedded in text; the scenario manifest binds each input SHA-256 to T
in [1800, 3600, 10800, 18000], pickup/drop defaults 60/60 seconds, and lambda 0.15.

Counts: 20 independent selections, 60
station landscapes, 240 complete parser inputs, and
960 future T scenarios.

Directory layout:

- `selections/`: geographic selection records;
- `landscapes/`: inventory/target/weight/min-ratio records;
- `mappings/`: depot and source-station provenance;
- `instances/`: current ExactEBRP text inputs;
- `manifests/`: selection, landscape, fleet/input, and T-scenario tables.

Regenerate from the ExactEBRP root with the commands in
`results/data_generation_citibike_round57/reproduction_commands.md`.  The
generator requires the legacy project at `E:\codes\Hybrid GA` and verifies the
two authoritative hashes before use.

Known limitations: no observed trip/demand history, artificial centroid depot,
straight-line rather than street-network travel, a fixed 1.5 m/s conversion,
homogeneous vehicle capacities, and no performance evidence.
