# Public source and pure R57 adapter

The source is the committed public table
`results/data_generation_citibike_round57/source_station_table.csv` at R108
`d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027`, blob
`84fb8af5aaa9836d316820227e4f06e8cd4b1e63`: 69,678 exact bytes, SHA256
`9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0`.
It contains 443 rows; 442 satisfy the inherited `0<C<100` rule. Coordinate
and capacity always come from the same zero-based source row. Companion IDs,
names and latitude/longitude never re-pair, select or alter that row.

`round109_data.py` loads SourceStation objects from those public columns and
sets the family prefix to `round109-geographic-mb-evaluation-v1`. It directly
uses the original pure selection, anchor, tie, centroid, target, total repair,
sign repair, numeric formatting and points-only writer functions. Its small
landscape function retains the original arithmetic/order and replaces the two
private-file hash calls with this public-table binding. It additionally records
before/after inventories and every ordering/profile seed material; those records
do not affect any generated value. No private Hybrid GA source bytes were read
or rehashed. Their historical hashes remain provenance only.

Original hash scalars use the first eight SHA256 bytes, big endian, divided by
the original floating representation of `2^64-1`; original displayed seed
conversion and all source-row tie rules remain. The new family prefix is used
for anchors, selections, target profiles and inventory/sign-repair orders.
Four farthest anchors are selected per size. Compact takes nearest V; regional
takes a farthest-first V within the nearest 2V pool. Replicates are 1/2. The
three-decimal centroid depot is synthetic. Original four-decimal min_ratio
values are preserved, alongside six-decimal max-normalized weights.

The original build_landscape's pure arithmetic is also executed as a zero-solve
equivalence oracle, with only its source-hash function replaced by the known
public identity. Every resulting landscape field agrees after replacing the
source identity dictionary; added trace fields are excluded from that comparison.
This invokes no source loader, historical dataset generation entry point,
heuristic, LP, presolve or optimizer. No old 240-file family is regenerated.

The original writer supplies all seven point-format lines. Only its fleet
header is replaced by the expressly listed complete Q vector. Physical T,
pickup/drop 60/60 and lambda .15 are external scenario parameters. Every role
is generated once; original bytes are saved before syntax/domain checks.
Input_manifest, full selection/landscape/parsed/source mapping files and
structure_statistics record the exact result. Source_subset_overlap openly
lists every pair's shared source rows. No overlap or solver outcome causes a
replacement draw.

The empty-fleet feasibility witness uses unchanged inventory Y=b, no service,
empty departure/prefix/return loads and zero closed route time. It is valid for
every positive physical T when 0<=b<=C and D>0. The original model/evaluator
do not impose Y>=min_ratio*D; the field is compatibility metadata. These data
witnesses are never supplied as an extra Start or UB to any formal arm.

Real-derived fields are coordinates and capacity only. Depot, demands/targets,
inventory, weights, fleet and physical horizon are synthetic. All twelve new
inputs derive from one city's 443-station source, with possible shared station
subsets; they are not new cities, demand observations or iid geographic samples.
Maximum weight is one; weight sum varies by size. Fixed lambda .15 does not
hold cross-size penalty balance constant, and lambda sensitivity is untested.
