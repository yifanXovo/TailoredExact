# Engineering smoke and invalidation status

Raw smoke directories are preserved under `runs/` and are excluded from every
official development/validation/holdout table by their missing official stage
tag and nonfrozen executable hash.

- Untagged static/root-LP/composite rows used executable hashes beginning
  `30ca0559` or `87054975`. They established K4/block model construction but
  predate the final generalized infeasible-block certificate correction.
- Early sibling rows with hashes beginning `4b3f3709` exercised terminal-ready
  coverage. `sibling-core-factored__smoke` and
  `sibling-core-factored__block_smoke` were manually interrupted after their
  corresponding base runs demonstrated that retaining a waiting leaf in the
  next-frontier competitor set obstructed sibling progression. These partial
  directories are retained as invalidated implementation-path evidence.
- Corrected base/factored sibling smoke rows with hash beginning `23a522f8`
  passed strict certification and motivated the frozen factoring refinement,
  but still predate the final reporting-only algorithm-arm strings.
- The only executable accepted for official rows is SHA-256
  `82178ffbbb8106c06661fcec8fd57ce7fe63b1fb9b6340b9d85bd269fc013fbe`.

No smoke value participates in development gates, candidate ranking,
validation, or holdout selection.
