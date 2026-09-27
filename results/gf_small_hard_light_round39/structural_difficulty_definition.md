# Round 39 structural difficulty definition

The label is a deterministic function of the frozen instance text. It uses no
solver, incumbent, bound, Work, node, time, certificate, machine, or winner
field. The score is 100 times a weighted sum of normalized dimension (0.12),
active-station fraction (0.16), imbalance L1 per station (0.15), fleet-capacity
pressure (0.13), support-duration or single-station pressure (0.18), spatial
distance coefficient of variation (0.08), plausible ordered-pair density
(0.09), and vehicle-assignment multiplicity (0.09). Exact formulas and clipping
are implemented in `scripts/round39_instance_tools.py`.

Labels were frozen before official results: `small-easy` is score below 60,
`small-medium` is 60 through below 78, and `small-hard` is at least 78. Frozen
ranges are 41.734 to 57.392, 60.259 to 77.364, and 82.215 to 94.964 for easy, medium, and hard.

Medium/hard acceptance additionally requires meaningful surplus and deficit
support, active repositioning, nonzero initial objective, route alternatives,
and frozen tightness conditions. Rejected candidates and their structural
reasons are retained in `rejected_generation_manifest.csv`.
