
# Dataset-design proposal: citibike443-regional-v1

Status before full generation: proposed and structurally piloted; no optimizer
evidence is used.  The family will initially be classified
`generated_untested_paper_candidate`.

## Sources and fields

The only authoritative real-world fields are station capacity and UTM 18N
coordinate from `E:\codes\Hybrid GA\testdata\CitiBike\coords\citibike_selected_443_capacity_list.txt` and `E:\codes\Hybrid GA\testdata\CitiBike\coords\citibike_selected_443_coords_utm18n_meters.txt`.
Their SHA-256 values are recorded in `source_file_audit.json`.  Station ID,
name, latitude and longitude are provenance annotations recovered by exact
coordinate/capacity matching to the local companion station table; they do not
replace the two authoritative files.  Inventory, target, weight, minimum ratio,
depot, M, Q and T are synthetic design fields.

## Geographic selections and depot

For every V in [8, 12, 20, 30, 50], the generator derives four widely separated
anchors by deterministic farthest-first selection, beginning with a SHA-256
ranked eligible source row.  Capacity-zero rows are never eligible.  Two
replicates use the V nearest stations to their anchors (`compact`).  Two use
farthest-first coverage inside the 2V nearest stations (`regional`).  Distance
ties use ascending zero-based source row index.  This gives four independent
real-station selections per V and preserves exact three-decimal source
coordinates.  The artificial depot is the three-decimal arithmetic centroid of
the selected serialized coordinates; it is never represented as a Citi Bike
station.

## Controlled synthetic profiles

Each geographic selection has one shared deterministic target profile, with a
fill fraction in [0.44,0.56] derived from SHA-256 values.  Three initial-inventory
profiles then impose station-total shortage, exact balance, and station-total
surplus.  Shortage/surplus magnitudes are 12% of total target inventory (at
least V units); local transfers ensure at least one surplus and one deficit
station.  Balanced cases use exact total equality with moderate local
imbalance.  All values are integer and remain within station capacity.

Weights adapt the legacy target-squared rule as
`max(0.1,(target/max_target)^2)`, renormalized to maximum 1.  Minimum ratio is
`0.10 + 0.40*(target/capacity)`, rounded to four decimals.  Both are explicitly
synthetic and are not claimed as observed demand.

## Format, distance, fleet, and horizons

Inputs use the current ExactEBRP text parser with depot-inclusive arrays.
Points are authoritative at three decimals.  No redundant distance matrix is
serialized; the current parser reconstructs symmetric travel seconds as
Euclidean UTM meters / 1.5.  T is external and is
bound to each immutable input hash in the scenario manifest.  Pickup/drop
service times are the current fixed defaults 60/60
seconds.

For each of 60 station landscapes (5 V x 4 geographic selections x 3 inventory
regimes), two M values are provided according to `{"8":[1,2],"12":[1,2],"20":[2,3],"30":[3,5],"50":[4,7]}` and
both Q=20 and Q=30 are written.  This yields 240 complete parser inputs and a
fully factorial 960-row T scenario manifest for T=[1800, 3600, 10800, 18000].  Per V this is
4 independent selections, 12 landscapes, 48 inputs, and 192 scenarios.

## Reproducibility and organization

All seeds are the first 64 bits of SHA-256 derivation material reduced to a
positive 31-bit integer.  Actual ordering and scalar draws are SHA-256 based,
so results do not depend on a language PRNG implementation.  LF newlines and
fixed numeric precision are mandatory.  The dataset root is
`E:\codes\ExactEBRP\reference\citibike443-regional-v1` with separate `selections`, `landscapes`, `mappings`,
`instances`, and `manifests` directories.  Audit and validation evidence stays
under `E:\codes\ExactEBRP\results\data_generation_citibike_round57`.

Known limitations are: no observed trip/demand history, an artificial centroid
depot, Euclidean rather than road-network travel, a fixed 1.5 m/s convention,
homogeneous vehicle capacities, and no performance qualification in this round.
