# Dataset family registry

## `citibike443-regional-v1`

This frozen family is reconstructed from locally retained Citi Bike station
metadata and trip-derived inventory signals. It contains 240 fleet input
files, 60 independently hashed station landscapes, 20 geographic selections,
and 960 mathematical scenarios spanning V in {8, 12, 20, 30, 50}, compact and
regional geography, shortage/balanced/surplus inventory, two geographic
replicates, two V-specific fleet sizes, Q in {20, 30}, and route horizon T in
{1800, 3600, 10800, 18000} seconds.

Canonical data and manifests are under
`reference/citibike443-regional-v1/`. Generation and validation evidence is
under `results/data_generation_citibike_round57/`. Round 58 uses a frozen
50-scenario subset selected before performance; the other 910 scenarios remain
available as unopened holdout candidates.

The family is reproducible local benchmark evidence, not a claim that every
generated scenario is an established historical paper benchmark. Landscape,
input, and mathematical-scenario hashes must be verified before use, and
operational T must remain separate from solver process time.

Round 58 revalidated the family and its deterministic regeneration evidence
before opening benchmark performance. The selected 50-scenario panel is
complete, with 30 primary structural cells and 20 matched route-horizon rows;
all required V/geography/inventory/M/Q/T strata are represented. All 910
unselected scenarios remain hash-frozen and unopened for possible sealed
holdout work.
